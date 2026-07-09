import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa
import threading
import os


def scan_instruments(tree):
    """Scan all VISA resources and list only those that return an *IDN? response.
    Runs in a background thread to keep the UI responsive.
    Ensures each instrument is displayed only once.
    """
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        # Clear previous entries
        for item in tree.get_children():
            tree.delete(item)
        if not resources:
            # No resources; keep confirm button hidden
            root.after(0, lambda: save_btn.config(state='disabled'))
            return
        seen = set()
        for res in resources:
            try:
                instr = rm.open_resource(res)
                # Try a standard *IDN? query; ignore if it raises or returns empty
                try:
                    idn = instr.query('*IDN?').strip()
                except Exception:
                    idn = ""
                instr.close()
                if idn and idn not in seen:  # only show if we got a response and not seen
                    seen.add(idn)
                    tree.insert('', 'end', values=(get_category(idn), idn, res))
            except Exception:
                # If opening the resource fails, just skip it (no UI entry)
                continue
        # Enable confirm button after scanning completes
        root.after(0, lambda: save_btn.config(state='normal'))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to list VISA resources: {e}")


def on_scan():
    # Launch scanning in a daemon thread
    threading.Thread(target=scan_instruments, args=(result_tree,), daemon=True).start()

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

# Scan button (keeps for manual refresh)
scan_btn = ttk.Button(main_frame, text="掃描儀器", command=on_scan)
scan_btn.pack(pady=(0, 10))

# Treeview to display results: Resource address + IDN string
columns = ("Category", "IDN", "Resource")
result_tree = ttk.Treeview(main_frame, columns=columns, show='headings')
# Define simple categorization based on IDN string
def get_category(idn):
    low = idn.lower()
    # Specific rules with numeric prefixes
    if "6705" in low:
        return "1. Power Supply"
    # Detect oscilloscopes – MSO, DSO, or generic scope keywords
    if "mso" in low or low.startswith("dso") or "oscilloscope" in low or "scope" in low:
        return "2. Scope"
    if "temptronic" in low:
        return "4. Thermal"
    # General rules
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
