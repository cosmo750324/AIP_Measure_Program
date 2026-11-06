import os
import subprocess
import tkinter as tk

from gui.test_runner_window import TestRunnerWindow, load_current_temp, load_temp_plan_summary

_script_dir = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_script_dir, "img", "phison_logo.png")
VISA_GUI_PATH = os.path.join(_script_dir, "sub", "visa_gui.py")

DARK_BG = "#1a1a1a"
BTN_BG = "#d9d9d9"
FIELD_BG = "#c9c9c9"


class PhisonAIPMeasureApp(tk.Tk):
    """Main front panel for Phison AIP Measure.

    外觀對齊既有 LabVIEW VI(Phison_AnalogIP_Measure.vi,見 img/Main.png)的面板本體,
    不重現 LabVIEW IDE 的標題列/選單/工具列。
    """

    def __init__(self):
        super().__init__()
        self.title("Phison AIP Measure")
        self.geometry("928x512")
        self.configure(bg=DARK_BG)

        self.logo_img = tk.PhotoImage(file=LOGO_PATH) if os.path.isfile(LOGO_PATH) else None

        self._build_header()
        self._build_button_row()
        self._build_canvas_area()
        self._build_bottom_bar()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._refresh_current_temp()

    # ---------------- Header: logo + Thermal? ----------------
    def _build_header(self):
        header = tk.Frame(self, bg=DARK_BG)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.columnconfigure(0, weight=1)

        if self.logo_img is not None:
            tk.Label(header, image=self.logo_img, bg=DARK_BG).grid(row=0, column=0, sticky="w")
        else:
            tk.Label(header, text="PHISON", font=("Arial", 24, "bold italic"),
                     fg="#f5a623", bg=DARK_BG).grid(row=0, column=0, sticky="w")

        right = tk.Frame(header, bg=DARK_BG)
        right.grid(row=0, column=1, sticky="e")

        self.thermal_var = tk.BooleanVar(value=False)
        tk.Label(right, text="Thermal?", fg="white", bg=DARK_BG).grid(row=0, column=0, padx=(0, 15))
        tk.Checkbutton(right, variable=self.thermal_var, bg=DARK_BG, activebackground=DARK_BG,
                        selectcolor="#333333").grid(row=1, column=0)

        self.temp_list_var = tk.StringVar(value="")
        tk.Label(right, text="執行溫度", fg="white", bg=DARK_BG).grid(row=0, column=1, padx=(15, 10))
        tk.Entry(right, textvariable=self.temp_list_var, state="readonly",
                 readonlybackground=FIELD_BG, width=24).grid(row=1, column=1, padx=(15, 10))

    # ---------------- Button row: INITIALIZE / TEST_ITEM / INSTR? ----------------
    def _build_button_row(self):
        row = tk.Frame(self, bg=DARK_BG)
        row.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        tk.Button(row, text="▷ INITIALIZE", bg=BTN_BG, relief="raised", bd=2,
                  command=self._on_test_item).pack(side="left", padx=(0, 8))
        tk.Button(row, text="▷ TEST_ITEM", bg=BTN_BG, relief="raised", bd=2).pack(side="left", padx=(0, 8))
        tk.Button(row, text="INSTR?", bg=BTN_BG, relief="raised", bd=2,
                  command=self._on_initialize).pack(side="left")

    # ---------------- Large blank canvas area ----------------
    def _build_canvas_area(self):
        canvas_wrap = tk.Frame(self, bg=DARK_BG)
        canvas_wrap.grid(row=2, column=0, sticky="nsew", padx=10)
        canvas_wrap.rowconfigure(0, weight=1)
        canvas_wrap.columnconfigure(0, weight=1)
        tk.Frame(canvas_wrap, bg="white", highlightbackground="white",
                 highlightthickness=1).grid(row=0, column=0, sticky="nsew")

    # ---------------- Bottom: status bar + Exit ----------------
    def _build_bottom_bar(self):
        bottom = tk.Frame(self, bg=DARK_BG)
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        bottom.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        tk.Entry(bottom, textvariable=self.status_var, state="readonly",
                 readonlybackground=FIELD_BG).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.current_temp_var = tk.StringVar(value="")
        tk.Label(bottom, text="目前溫度", fg="white", bg=DARK_BG).grid(row=0, column=1, padx=(0, 5))
        tk.Entry(bottom, textvariable=self.current_temp_var, state="readonly",
                 readonlybackground=FIELD_BG, width=10).grid(row=0, column=2, padx=(0, 10))

        tk.Button(bottom, text="✕ Exit", bg="#d9534f", fg="white", relief="raised", bd=2,
                  command=self.destroy).grid(row=0, column=3)

    # ---------------- Button callbacks ----------------
    def _on_initialize(self):
        if not os.path.isfile(VISA_GUI_PATH):
            self._set_status("visa_gui.py 不存在於指定路徑")
            return
        try:
            subprocess.Popen(["python", VISA_GUI_PATH], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self._set_status("已開啟儀器搜尋 (visa_gui.py)")
        except Exception as e:
            self._set_status(f"開啟失敗: {e}")

    def _on_test_item(self):
        TestRunnerWindow(self)

    def _refresh_current_temp(self):
        plan = load_temp_plan_summary()
        self.temp_list_var.set(f"{plan}°C" if plan else "未設定")

        current = load_current_temp()
        self.current_temp_var.set(f"{current}°C" if current is not None else "未設定")

    def _set_status(self, msg):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = PhisonAIPMeasureApp()
    app.mainloop()
