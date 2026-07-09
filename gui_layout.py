import tkinter as tk
from tkinter import ttk
import subprocess
import os

class PhisonAIPMeasureApp(tk.Tk):
    """Main GUI for Phison AIP Measure.

    - 三個主要按鍵：儀器搜尋、選擇專案、開始測試
    - 兩個勾選框：Thermal?、Instr?
    - 底部狀態列顯示目前操作訊息
    """
    def __init__(self):
        super().__init__()
        self.title("Phison AIP Measure")
        self.geometry("800x400")
        self.configure(bg="#f5f5f5")

        # ----- Toolbar (三個按鍵) -----
        self._create_toolbar()

        # ----- 主內容：兩個勾選框 -----
        self._create_main_content()

        # ----- 狀態列 -----
        self._create_status_bar()

        # 讓視窗在大小變動時保持合理排版
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # -------------------------------------------------
    # Toolbar with three buttons
    # -------------------------------------------------
    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=10)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure((0, 1, 2), weight=1)

        btn_search = ttk.Button(toolbar, text="儀器搜尋", command=self._on_search)
        btn_project = ttk.Button(toolbar, text="選擇專案", command=self._on_select_project)
        btn_start = ttk.Button(toolbar, text="開始測試", command=self._on_start_test)

        btn_search.grid(row=0, column=0, padx=5, sticky="ew")
        btn_project.grid(row=0, column=1, padx=5, sticky="ew")
        btn_start.grid(row=0, column=2, padx=5, sticky="ew")

    # -------------------------------------------------
    # Main content: two checkboxes and a result label
    # -------------------------------------------------
    def _create_main_content(self):
        main = ttk.Frame(self, padding=20)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)

        # 勾選狀態
        self.chk1_var = tk.BooleanVar(value=False)
        self.chk2_var = tk.BooleanVar(value=False)
        chk1 = ttk.Checkbutton(main, text="Thermal?", variable=self.chk1_var)
        chk2 = ttk.Checkbutton(main, text="Instr?", variable=self.chk2_var)
        chk1.grid(row=0, column=0, sticky="w", pady=2)
        chk2.grid(row=1, column=0, sticky="w", pady=2)

        # 測試結果顯示區（預留）
        self.result_label = ttk.Label(main, text="測試結果將顯示於此", background="#ffffff", anchor="center")
        self.result_label.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        self.result_label.configure(relief="solid")

    # -------------------------------------------------
    # Status bar at the bottom
    # -------------------------------------------------
    def _create_status_bar(self):
        self.status = ttk.Label(self, text="Ready", anchor="w", padding=5)
        self.status.grid(row=2, column=0, sticky="ew")
        self.grid_rowconfigure(2, weight=0)

    # -------------------------------------------------
    # Button callbacks (placeholder – replace with real logic)
    # -------------------------------------------------
    def _on_search(self):
        self._set_status("執行儀器搜尋…")
        # 開啟 visa_gui.py（使用新視窗）
        visa_path = r"D:\Claude_AI\Python Program\sub\visa_gui.py"
        if os.path.isfile(visa_path):
            try:
                # 在 Windows 上以新 console 執行該腳本
                subprocess.Popen(["python", visa_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self._set_status("已開啟 visa_gui.py")
            except Exception as e:
                self._set_status(f"開啟失敗: {e}")
        else:
            self._set_status("visa_gui.py 不存在於指定路徑")

    def _on_select_project(self):
        # 直接執行 config_viewer_ui.py，不開啟檔案對話框
        self._set_status("執行 config_viewer_ui.py…")
        cfg_path = r"D:\Claude_AI\Python Program\sub\config_viewer_ui.py"
        if os.path.isfile(cfg_path):
            try:
                subprocess.Popen(["python", cfg_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self._set_status("已開啟 config_viewer_ui.py")
            except Exception as e:
                self._set_status(f"開啟 config_viewer_ui.py 失敗: {e}")
        else:
            self._set_status("config_viewer_ui.py 不存在於指定路徑")

    def _on_start_test(self):
        self._set_status("開始測試…")
        chk1 = self.chk1_var.get()
        chk2 = self.chk2_var.get()
        self.result_label.config(text=f"測試中… (Thermal={chk1}, Instr={chk2})")
        # TODO: 在此處加入真正的測試流程
        self.after(2000, self._test_finished)

    def _test_finished(self):
        self.result_label.config(text="測試完成")
        self._set_status("測試完成")

    def _set_status(self, msg: str):
        self.status.config(text=msg)

if __name__ == "__main__":
    app = PhisonAIPMeasureApp()
    app.mainloop()
