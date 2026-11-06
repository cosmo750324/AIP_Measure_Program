import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from gui.json_tree_editor import JsonTreeEditor

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_PATH = os.path.join(_project_root, "cfg", "projects.json")
TEST_PROGRAMS_PATH = os.path.join(_project_root, "cfg", "test_programs.json")
CURRENT_TEMP_PATH = os.path.join(_project_root, "cfg", "current_temp.json")
ITEM_CONFIG_FILENAME = "config.json"
TEMP_TOLERANCE = 0.01


def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_current_temp():
    """Read cfg/current_temp.json — the externally-maintained 'what temperature
    is the chamber at right now' setting. Returns None if missing/invalid."""
    data = load_json(CURRENT_TEMP_PATH)
    if isinstance(data, dict):
        return data.get("current_temp")
    return None


def _point_values(point):
    """Expand one entry of a points list into actual temperatures. Handles plain
    numbers and {"type": "sweep", "start", "end", "gap"} ranges."""
    if point is None:
        return []
    if isinstance(point, dict) and point.get("type") == "sweep":
        start, end, gap = point.get("start"), point.get("end"), point.get("gap")
        if start is None or end is None or not gap:
            return []
        step = gap if end >= start else -gap
        vals, t, guard = [], start, 0
        while guard < 1000:
            vals.append(t)
            if (step > 0 and t >= end) or (step < 0 and t <= end):
                break
            t += step
            guard += 1
        return vals
    if isinstance(point, (int, float)):
        return [point]
    try:
        return [float(point)]
    except (TypeError, ValueError):
        return []


def load_temp_list():
    """Read cfg/current_temp.json's 'temps' and expand any sweep entries into
    actual temperatures — same {"type": "sweep", "start", "end", "gap"} convention
    used by a test item's thermal.points. Returns [] if missing/invalid."""
    data = load_json(CURRENT_TEMP_PATH)
    if not (isinstance(data, dict) and isinstance(data.get("temps"), list)):
        return []
    values = []
    for p in data["temps"]:
        values.extend(_point_values(p))
    return values


def _fmt_point(point):
    if isinstance(point, dict) and point.get("type") == "sweep":
        return f'{point.get("start")}~{point.get("end")}(step{point.get("gap")})'
    return str(point)


def load_temp_plan_summary():
    """Compact, human-readable form of cfg/current_temp.json's 'temps' for display
    (e.g. '125, 85~-40(step5)') — sweeps shown as a range, not expanded point-by-point.
    Use load_temp_list() when you need the actual expanded values."""
    data = load_json(CURRENT_TEMP_PATH)
    if not (isinstance(data, dict) and isinstance(data.get("temps"), list)):
        return ""
    return ", ".join(_fmt_point(p) for p in data["temps"])


def thermal_points_match(current_temp, points):
    """True if current_temp hits one of a test item's required thermal.points."""
    if current_temp is None or not isinstance(points, list):
        return False
    try:
        current_temp = float(current_temp)
    except (TypeError, ValueError):
        return False
    return any(abs(v - current_temp) <= TEMP_TOLERANCE for p in points for v in _point_values(p))


class TestRunnerWindow(tk.Toplevel):
    """選專案 -> 點測試項目即時載入 cfg/<專案>/<測項>/config.json 並顯示內容。"""

    CHECK_ON = "☑"
    CHECK_OFF = "☐"

    def __init__(self, master):
        super().__init__(master)
        self.title("Test Item 專案 / 測項設定")
        self.geometry("900x560")

        self.projects = load_json(PROJECTS_PATH)
        self.test_items = [t for t in load_json(TEST_PROGRAMS_PATH) if t.get("Executable") == "Y"]
        self.checked = set()

        self.confirmed = False
        self.selected_project = None
        self.selected_items = []
        self.item_configs = {}
        self.current_config_item = None
        self.current_temp = load_current_temp()

        self._build_top_bar()
        self._build_main()
        self._build_confirm_bar()
        self._build_status_bar()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ---------------- Top bar: project + current temperature ----------------
    def _build_top_bar(self):
        bar = ttk.Frame(self, padding=10)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        ttk.Label(bar, text="專案:").grid(row=0, column=0, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_map = {}
        values = []
        for p in sorted(self.projects, key=lambda x: (x.get("category", ""), x.get("name", ""))):
            label = f"{p.get('code', '')} - {p.get('name', '')}"
            values.append(label)
            self.project_map[label] = p
        self.project_combo = ttk.Combobox(bar, textvariable=self.project_var, values=values, state="readonly")
        self.project_combo.grid(row=0, column=1, sticky="ew")
        self.project_combo.bind("<<ComboboxSelected>>", self._on_project_selected)

        self.temp_label_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.temp_label_var).grid(row=0, column=2, padx=(15, 5))
        ttk.Button(bar, text="重新讀取溫度", command=self._reload_current_temp).grid(row=0, column=3)
        self._update_temp_label()

    def _update_temp_label(self):
        if self.current_temp is None:
            self.temp_label_var.set("目前溫度:未設定(cfg/current_temp.json)")
        else:
            self.temp_label_var.set(f"目前溫度:{self.current_temp}°C")

    def _reload_current_temp(self):
        self.current_temp = load_current_temp()
        self._update_temp_label()
        self._refresh_thermal_indicators()
        self._set_status("已重新讀取目前溫度設定")

    # ---------------- Main: test item tree + loaded config preview ----------------
    def _build_main(self):
        main = ttk.Frame(self, padding=(10, 0, 10, 10))
        main.grid(row=1, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        left = ttk.Labelframe(main, text="測試項目(依設定檔載入,點選切換勾選)")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.item_tree = ttk.Treeview(left, columns=("chk", "temp"), show="tree headings", selectmode="none")
        self.item_tree.heading("#0", text="測試項目")
        self.item_tree.heading("chk", text="選取")
        self.item_tree.heading("temp", text="溫度需求")
        self.item_tree.column("chk", width=50, anchor="center")
        self.item_tree.column("temp", width=90, anchor="center")
        self.item_tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.item_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.item_tree.configure(yscrollcommand=vsb.set)
        self.item_tree.bind("<Button-1>", self._on_item_click)

        self._populate_items()

        right = ttk.Labelframe(main, text="設定內容(config.json — 雙擊數值編輯,右鍵新增/刪除)")
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.config_editor = JsonTreeEditor(right)
        self.config_editor.grid(row=0, column=0, sticky="nsew")

        save_row = ttk.Frame(right)
        save_row.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        save_row.columnconfigure(0, weight=1)
        ttk.Button(save_row, text="儲存設定", command=self._on_save_config).grid(row=0, column=0, sticky="e")

    def _populate_items(self):
        self.item_tree.delete(*self.item_tree.get_children())
        self.checked.clear()
        groups = {}
        for t in self.test_items:
            groups.setdefault(t.get("group", ""), []).append(t)
        for group in sorted(groups.keys()):
            gid = self.item_tree.insert("", "end", text=group, tags=("group",))
            for t in sorted(groups[group], key=lambda x: x.get("name", "")):
                self.item_tree.insert(gid, "end", iid=t["id"], text=t["name"],
                                       values=(self.CHECK_OFF, "-"), tags=("item",))

    def _on_item_click(self, event):
        row = self.item_tree.identify_row(event.y)
        if not row or "item" not in self.item_tree.item(row, "tags"):
            return
        if row in self.checked:
            self.checked.discard(row)
            self.item_tree.set(row, "chk", self.CHECK_OFF)
        else:
            self.checked.add(row)
            self.item_tree.set(row, "chk", self.CHECK_ON)
        self._show_config_preview(self.item_tree.item(row, "text"))

    def _on_project_selected(self, event=None):
        label = self.project_var.get()
        self.selected_project = self.project_map.get(label)
        cat = (self.selected_project or {}).get("category") or "-"
        self._set_status(f"已選擇專案:{label}(分類:{cat})")
        self.current_config_item = None
        self.config_editor.load({})
        self._refresh_thermal_indicators()

    def _refresh_thermal_indicators(self):
        """Mark each test item: ✓ needs measuring at the current temp, - not
        applicable (no thermal.points in its config, or no config at all)."""
        all_rows = [iid for gid in self.item_tree.get_children() for iid in self.item_tree.get_children(gid)]
        for row in all_rows:
            if not self.selected_project:
                self.item_tree.set(row, "temp", "-")
                continue
            config = self._load_one_config(self.item_tree.item(row, "text")) or {}
            points = (config.get("thermal") or {}).get("points") if isinstance(config, dict) else None
            if not points:
                self.item_tree.set(row, "temp", "-")
            elif thermal_points_match(self.current_temp, points):
                self.item_tree.set(row, "temp", "✓ 需量測")
            else:
                self.item_tree.set(row, "temp", "")

    def _show_config_preview(self, item_name):
        self.current_config_item = item_name
        if not self.selected_project:
            self.config_editor.load({})
            self._set_status("請先選擇專案。")
            return
        config = self._load_one_config(item_name)
        if config is None:
            self.config_editor.load({})
            self._set_status(f"{item_name} 尚無設定檔,右鍵新增欄位後按「儲存設定」建立新檔")
            return
        self.config_editor.load(config)
        self._set_status(f"已載入 {item_name} 的設定")

    def _on_save_config(self):
        if not self.selected_project or not self.current_config_item:
            messagebox.showwarning("提示", "請先選擇專案與測試項目")
            return
        data = self.config_editor.to_json()
        item_dir = os.path.join(_project_root, "cfg", self._project_code(), self.current_config_item)
        os.makedirs(item_dir, exist_ok=True)
        with open(os.path.join(item_dir, ITEM_CONFIG_FILENAME), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._set_status(f"已儲存 {self.current_config_item} 的設定")

    # ---------------- Confirm / exit ----------------
    def _build_confirm_bar(self):
        bar = ttk.Frame(self, padding=(10, 0, 10, 10))
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)
        ttk.Button(bar, text="確認退出", command=self._on_confirm).grid(row=0, column=0, sticky="e")

    def _on_confirm(self):
        if not self.project_var.get():
            messagebox.showwarning("提示", "請先選擇專案")
            return
        all_rows = [iid for gid in self.item_tree.get_children() for iid in self.item_tree.get_children(gid)]
        self.selected_project = self.project_map.get(self.project_var.get())
        self.selected_items = [self.item_tree.item(r, "text") for r in all_rows if r in self.checked]
        self._create_project_folders()
        self.item_configs = self._load_item_configs()
        self.confirmed = True
        self.destroy()

    def _project_code(self):
        return self.selected_project.get("code") or self.selected_project.get("name")

    def _create_project_folders(self):
        """Create data/<project_code>/<test_item> (results go here) and
        cfg/<project_code>/<test_item> (settings are read from here)."""
        project_code = self._project_code()
        for base in ("data", "cfg"):
            base_dir = os.path.join(_project_root, base, project_code)
            os.makedirs(base_dir, exist_ok=True)
            for item_name in self.selected_items:
                os.makedirs(os.path.join(base_dir, item_name), exist_ok=True)

    def _load_one_config(self, item_name):
        """Read cfg/<project_code>/<item_name>/config.json, or None if not set up yet."""
        path = os.path.join(_project_root, "cfg", self._project_code(), item_name, ITEM_CONFIG_FILENAME)
        return load_json(path) if os.path.isfile(path) else None

    def _load_item_configs(self):
        return {item_name: self._load_one_config(item_name) for item_name in self.selected_items}

    # ---------------- Status bar ----------------
    def _build_status_bar(self):
        self.status = ttk.Label(self, text="Ready", anchor="w", padding=5)
        self.status.grid(row=3, column=0, sticky="ew")

    def _set_status(self, msg):
        self.status.config(text=msg)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    win = TestRunnerWindow(root)
    win.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
