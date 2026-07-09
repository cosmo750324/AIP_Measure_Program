# oscilloscope_capture_gui_v2.py
"""GUI 版的示波器畫面擷取工具，依照您提供的範例程式實作。

功能：
1. 輸入 VISA 位址（支援 USB 或 LAN）
2. 輸入或選擇要儲存的 PNG 檔案路徑
3. 為四個通道（CH1~CH4）分別設定標籤（可留空）
4. 按下「擷取畫面」後會依序
   - 開啟儀器
   - 設定通道標籤
   - 送出螢幕截圖指令
   - 讀取二進位 PNG 資料並寫檔
   - 關閉儀器連線
5. 失敗時會顯示錯誤訊息，成功時會顯示儲存路徑。

使用方式：
    python oscilloscope_capture_gui_v2.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyvisa
import time
import os
import shutil

# ------------------------------------------------------------
# 1. 主要的擷取功能（與您給的範例程式相同）
# ------------------------------------------------------------

def capture_oscilloscope_screen(resource_string, filename, labels=None):
    """根據 VISA 位址與標籤設定擷取示波器畫面，回傳儲存的檔案路徑。

    Parameters
    ----------
    resource_string: str
        VISA address, e.g. 'USB0::0x0957::0x179A::MY12345678::0::INSTR'
    filename: str
        完整的檔案路徑（含 .jpg）
    labels: list of str or None
        四個通道的標籤文字，長度最多 4，空字串視為不設定。
    """
    rm = pyvisa.ResourceManager()
    instrument = None
    try:
        instrument = rm.open_resource(resource_string)
        instrument.timeout = 5000
        # 取得儀器 ID（僅作為 log）
        idn = instrument.query("*IDN?")
        print(f"Connected to: {idn.strip()}")
        # 先發送 STOP 以暫停示波器
        try:
            instrument.write("STOP")
        except Exception as stop_err:
            print(f"[Warning] STOP 指令失敗: {stop_err}")

        # 判斷機型以選擇截圖指令
        if "DSO" in idn or "MSO-X" in idn:
            screenshot_cmd = "*CLS;:HARDcopy:INKSaver 0;:DISPlay:DATA? PNG, COLOR;"
        else:
            screenshot_cmd = "*CLS;:DISPlay:DATA? PNG,SCR,ON,NORMAL;"

        # 建立標籤指令（若有）
        label_cmds = []
        if labels:
            label_cmds.append(":DISP:LAB ON")  # 開啟標籤顯示
            for i, txt in enumerate(labels):
                if txt:  # 空字串略過
                    label_cmds.append(f":CHAN{i+1}:LAB \"{txt}\"")
        # 合併指令
        # 合併指令
        full_cmd = ";".join(label_cmds + [screenshot_cmd]) if label_cmds else screenshot_cmd
        print("Sending command to instrument …")
        # 設定較長的 timeout 以避免 VI_ERROR_TMO（設定 120 秒）
        instrument.timeout = 300000  # 300 秒（5 分鐘）
        # 設定足夠的緩衝區
        instrument.chunk_size = 20_000_000
        # 直接使用 query_binary_values 發送指令並取得 PNG 二進位資料
        img_bytes = instrument.query_binary_values(full_cmd, datatype="B", container=bytes)
        # 轉換 PNG 為 JPEG 並寫入檔案
        from PIL import Image
        import io
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        image = Image.open(io.BytesIO(img_bytes))
        rgb_image = image.convert("RGB")  # JPEG 需要 RGB 格式
        rgb_image.save(filename, format="JPEG")
        print(f"Screenshot saved to {filename}")
        # 圖片儲存完成後，發送 RUN 恢復示波器
        try:
            instrument.write("RUN")
        except Exception as run_err:
            print(f"[Warning] RUN 指令失敗: {run_err}")
        return filename
    finally:
        if instrument:
            instrument.close()
            print("Instrument connection closed.")

# ------------------------------------------------------------
# 2. 相關的 UI 輔助函式
# ------------------------------------------------------------

def choose_file():
    """跳出檔案儲存對話框，回傳選擇的完整路徑。"""
    file_path = filedialog.asksaveasfilename(
        title="選擇儲存 JPG 檔案",
        defaultextension=".jpg",
        filetypes=[("JPG 圖片", "*.jpg"), ("All files", "*.*")],
    )
    if file_path:
        save_path_var.set(file_path)

def scan_resources(target_var: tk.StringVar):
    """使用 pyvisa 掃描可用的 VISA 資源，優先選取 USB。"""
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        if not resources:
            messagebox.showinfo("掃描結果", "未偵測到任何 VISA 資源。")
            return
        usb_res = [r for r in resources if "USB" in r.upper()]
        selected = usb_res[0] if usb_res else resources[0]
        target_var.set(selected)
        messagebox.showinfo("掃描完成", f"已設定 VISA 位址: {selected}")
    except Exception as e:
        messagebox.showerror("掃描錯誤", f"無法取得 VISA 資源: {e}")

def on_capture():
    """從 UI 取得參數，呼叫 capture_oscilloscope_screen，並顯示結果。"""
    resource = visa_var.get().strip()
    filename = save_path_var.get().strip()
    labels = [lab1_var.get().strip(), lab2_var.get().strip(), lab3_var.get().strip(), lab4_var.get().strip()]
    # 移除末端的空字串（允許少於 4 個）
    labels = [l for l in labels if l]

    if not resource:
        messagebox.showwarning("輸入錯誤", "請先填寫 VISA 位址（或使用掃描）。")
        return
    if not filename:
        messagebox.showwarning("輸入錯誤", "請先選擇儲存檔案路徑。")
        return
    try:
        result_path = capture_oscilloscope_screen(resource, filename, labels if labels else None)
        messagebox.showinfo("完成", f"螢幕已儲存至 {result_path}")
    except Exception as err:
        messagebox.showerror("錯誤", str(err))

# ------------------------------------------------------------
# 3. 建立 GUI 介面
# ------------------------------------------------------------

def main():
    global visa_var, save_path_var, lab1_var, lab2_var, lab3_var, lab4_var
    root = tk.Tk()
    # 讓第二欄 (Entry) 可以彈性拉伸，避免按鈕被遮蔽
    root.columnconfigure(1, weight=1)
    root.title("示波器畫面擷取 (GUI)"
               )
    root.geometry("540x380")

    # VISA 位址
    ttk.Label(root, text="VISA 位址:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    visa_var = tk.StringVar()
    ttk.Entry(root, textvariable=visa_var, width=45).grid(row=0, column=1, sticky="we", padx=10, pady=5)
    ttk.Button(root, text="掃描", command=lambda: scan_resources(visa_var)).grid(row=0, column=2, padx=5, pady=5)

    # 儲存檔案路徑
    ttk.Label(root, text="JPG 儲存路徑:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    save_path_var = tk.StringVar()
    ttk.Entry(root, textvariable=save_path_var, width=35, state="readonly").grid(row=1, column=1, sticky="we", padx=10, pady=5)
    ttk.Button(root, text="選擇…", command=choose_file).grid(row=1, column=2, padx=5, pady=5)

    # 四個通道標籤（可留空）
    ttk.Label(root, text="通道標籤（CH1~CH4）:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    lab1_var = tk.StringVar()
    lab2_var = tk.StringVar()
    lab3_var = tk.StringVar()
    lab4_var = tk.StringVar()
    ttk.Entry(root, textvariable=lab1_var, width=10).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=5)
    ttk.Entry(root, textvariable=lab2_var, width=10).grid(row=2, column=1, sticky="w", padx=(80, 0), pady=5)
    ttk.Entry(root, textvariable=lab3_var, width=10).grid(row=2, column=1, sticky="w", padx=(150, 0), pady=5)
    ttk.Entry(root, textvariable=lab4_var, width=10).grid(row=2, column=1, sticky="w", padx=(220, 0), pady=5)
    # 加點說明文字（可選）
    ttk.Label(root, text="(留空則不設定標籤)").grid(row=2, column=2, sticky="w", padx=5, pady=5)

    # 擷取按鈕
    ttk.Button(root, text="擷取畫面", command=on_capture).grid(row=3, column=0, columnspan=3, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
