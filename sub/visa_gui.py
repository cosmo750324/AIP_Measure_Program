import json
import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa
import threading
import concurrent.futures
import os

# Per-resource query timeout. Lower = faster scan, but may miss slow-to-respond instruments.
QUERY_TIMEOUT_MS = 800
MAX_PARALLEL_QUERIES = 8

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visa_scan_cache.json")


def _normalize_addr(addr: str) -> str:
    """Normalize USBx -> USB0 and strip trailing ::0 so USB0/USB1/USB3 match."""
    a = addr.upper().strip()
    # USBx -> USB0
    if a.startswith("USB") and a[3].isdigit():
        a = "USB0" + a[4:]
    # Remove ::0 before ::INSTR (e.g. ::0::INSTR -> ::INSTR)
    a = a.replace("::0::INSTR", "::INSTR")
    return a


def _load_cache():
    """Cache of previously-seen resources, keyed by normalized address:
    - good: resources that answered *IDN? last time (still queried every scan, to
      confirm they're still connected, but queried first/fast since real devices
      respond quickly).
    - ghosts: resources that failed to respond last time — skipped entirely on a
      normal scan so we don't pay their timeout again. "完整掃描" re-checks them.
    """
    if not os.path.isfile(CACHE_PATH):
        return {"good": {}, "ghosts": []}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"good": data.get("good", {}), "ghosts": data.get("ghosts", [])}
    except Exception:
        return {"good": {}, "ghosts": []}


def _save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _query_idn(rm, resource):
    """Open a resource, ask *IDN?, close it. Returns '' on any failure/timeout."""
    try:
        instr = rm.open_resource(resource, timeout=QUERY_TIMEOUT_MS)
        try:
            return instr.query('*IDN?').strip()
        finally:
            instr.close()
    except Exception:
        return ""


def scan_instruments(tree, full_scan=False):
    """Scan VISA resources and list only those that return an *IDN? response.
    Runs in a background thread to keep the UI responsive; individual instrument
    queries run in parallel (instead of one-at-a-time) so a scan with several
    unreachable/ghost VISA resources doesn't serialize their timeouts.
    Ensures each instrument is displayed only once (dedup by normalized address).

    Resources that failed to answer on a previous scan are remembered in
    CACHE_PATH and skipped entirely (not even opened) unless full_scan=True.
    """
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        root.after(0, lambda: [tree.delete(i) for i in tree.get_children()])
        if not resources:
            root.after(0, lambda: save_btn.config(state='disabled'))
            return

        cache = _load_cache()
        good_cache = cache["good"]
        ghost_set = set(cache["ghosts"])

        # ASRL (COM ports) never carries VISA instruments here; skip up front.
        # Dedup by normalized address (same physical device re-enumerated on a
        # different USB bus number still collapses to one candidate).
        candidates = []
        seen = set()
        for res in resources:
            if res.upper().startswith("ASRL"):
                continue
            norm = _normalize_addr(res)
            if norm in seen:
                continue
            seen.add(norm)
            candidates.append((res, norm))

        to_query = []
        skipped = 0
        for res, norm in candidates:
            if not full_scan and norm in ghost_set and norm not in good_cache:
                skipped += 1
                continue
            to_query.append((res, norm))

        total = len(to_query)
        progress = {"done": 0}

        def report_progress():
            progress["done"] += 1
            n = progress["done"]
            root.after(0, lambda: scan_btn.config(text=f"掃描中…({n}/{total})"))

        found = []
        failed_norms = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL_QUERIES) as pool:
            future_to_res = {pool.submit(_query_idn, rm, res): (res, norm) for res, norm in to_query}
            for future in concurrent.futures.as_completed(future_to_res):
                res, norm = future_to_res[future]
                idn = future.result()
                report_progress()
                if idn:
                    found.append((get_category(idn), idn, res, norm))
                else:
                    failed_norms.append(norm)

        for cat, idn, res, norm in found:
            good_cache[norm] = {"idn": idn, "category": cat, "resource": res}
            ghost_set.discard(norm)
        for norm in failed_norms:
            good_cache.pop(norm, None)
            ghost_set.add(norm)
        _save_cache({"good": good_cache, "ghosts": sorted(ghost_set)})

        def apply_results():
            for cat, idn, res, norm in found:
                tree.insert('', 'end', values=(cat, idn, res))
            scan_btn.config(text="掃描儀器")
            save_btn.config(state='normal' if found else 'disabled')
            if skipped:
                info_var.set(f"已略過 {skipped} 個已知無效 resource(勾選「完整掃描」可重新檢查)")
            else:
                info_var.set("")

        root.after(0, apply_results)
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Failed to list VISA resources: {e}"))


def on_scan():
    # Launch scanning in a daemon thread
    threading.Thread(target=scan_instruments, args=(result_tree,),
                      kwargs={"full_scan": full_scan_var.get()}, daemon=True).start()

# Save results to a file in the same directory as this script
def save_results():
    try:
        # Gather all rows
        rows = []
        for item in result_tree.get_children():
            rows.append(result_tree.item(item)['values'])
        if not rows:
            messagebox.showinfo("保存結果", "沒有儀器資料可供保存。")
            return
        # Determine file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(script_dir, "instrument_list.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("Category\tIDN\tResource\n")
            for r in rows:
                # Ensure we have three columns
                if len(r) < 3:
                    continue
                f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
        messagebox.showinfo("保存結果", f"儀器清單已保存至 {out_path}")
        # Close the application after saving
        root.destroy()
    except Exception as e:
        messagebox.showerror("保存失敗", f"無法保存儀器資料: {e}")

# ---------------------------------------------------------------------------
# Build GUI
root = tk.Tk()
root.title("VISA Instrument Scanner")
root.geometry("620x420")

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Scan controls: scan button + "full scan" override (ignore the ghost-resource cache)
scan_row = ttk.Frame(main_frame)
scan_row.pack(pady=(0, 2))
scan_btn = ttk.Button(scan_row, text="掃描儀器", command=on_scan)
scan_btn.pack(side=tk.LEFT, padx=(0, 10))
full_scan_var = tk.BooleanVar(value=False)
ttk.Checkbutton(scan_row, text="完整掃描(忽略快取)", variable=full_scan_var).pack(side=tk.LEFT)

info_var = tk.StringVar(value="")
ttk.Label(main_frame, textvariable=info_var, foreground="#666666").pack(pady=(0, 8))

# Treeview to display results: Resource address + IDN string
columns = ("Category", "IDN", "Resource")
result_tree = ttk.Treeview(main_frame, columns=columns, show='headings')
# Define simple categorization based on IDN string
def get_category(idn):
    low = idn.lower()
    if "6705" in low:
        return "1. Power Supply"
    if "owon" in low:
        return "3. Function Generator"
    if "mso" in low or low.startswith("dso") or "oscilloscope" in low or "scope" in low:
        return "2. Scope"
    if "temptronic" in low:
        return "4. Thermal"
    if any(k in low for k in ["psu", "power supply", "power"]):
        return "1. Power Supply"
    if any(k in low for k in ["function generator", "function", "generator"]):
        if "function" in low and "generator" in low:
            return "3. Function Generator"
    if any(k in low for k in ["thermal", "temperature", "oven"]):
        return "4. Thermal"
    if any(k in low for k in ["meter", "multimeter", "amperemeter", "voltmeter"]):
        return "5. Meter"
    return "6. Other"

result_tree.heading("Category", text="類別")
result_tree.heading("IDN", text="儀器 IDN")
result_tree.heading("Resource", text="資源位置")
result_tree.column("Category", width=150, anchor='w')
result_tree.column("IDN", width=300, anchor='w')
result_tree.column("Resource", width=280, anchor='w')
result_tree.pack(fill=tk.BOTH, expand=True)

# Vertical scrollbar
vsb = ttk.Scrollbar(main_frame, orient="vertical", command=result_tree.yview)
result_tree.configure(yscrollcommand=vsb.set)
vsb.pack(side='right', fill='y')

# Save/Confirm button
save_btn = ttk.Button(main_frame, text="確認儀器", command=save_results, state='disabled')
save_btn.pack(pady=(10, 0))

# Auto‑scan once UI is ready
root.after(100, on_scan)

root.mainloop()
