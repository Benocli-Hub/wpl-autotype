# -*- coding: utf-8 -*-
"""
WPLSoft 指令自动录入器（半自动，一次一题）

操作顺序：
  1. 选好要录入的程序 -> 点「开始录入」
  2. 立刻切到 WPLSoft，在「指令模式」里单击要开始录入的那一行
     （只单击选中，不要双击；若已双击弹出「输入指令」框，请先按 Esc 关掉）
  3. 程序检测到你点中 WPLSoft 后自动开始：
       回车 -> 弹出「输入指令」框 -> 输入指令 -> 回车 -> 自动跳到下一行
  4. 录入过程中按 Esc 可随时中止。

运行：
  D:\\Anaconda3\\envs\\ForAgents\\pythonw.exe wpl_autotype_gui.py
"""

import ctypes
import glob
import os
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ------------------------------------------------------------------ Win32
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_ESCAPE = 0x1B
VK_LBUTTON = 0x01
VK_RETURN = 0x0D
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


def _send(*items):
    arr = (INPUT * len(items))(*items)
    user32.SendInput(len(items), arr, ctypes.sizeof(INPUT))


def _vk_item(vk, up=False):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, 0)
    return inp


def _unicode_item(ch, up=False):
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki = KEYBDINPUT(0, ord(ch), flags, 0, 0)
    return inp


def press_enter():
    _send(_vk_item(VK_RETURN), _vk_item(VK_RETURN, True))


def type_text(text, char_delay=0.012):
    for ch in text:
        _send(_unicode_item(ch), _unicode_item(ch, True))
        time.sleep(char_delay)


def esc_pressed():
    return bool(user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)


def left_button_down():
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)


def foreground_exe():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value.lower()
        return ""
    finally:
        kernel32.CloseHandle(h)


# ------------------------------------------------------------------ 示例
# 只保留一个最小示例；真正的指令表放在 programs/*.txt
DEMO = ["LD X0", "OUT Y0", "END"]
BUILTIN = [("示例", DEMO)]

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM_DIR = os.path.join(HERE, "programs")


def load_programs(folder=PROGRAM_DIR):
    """读取 programs/*.txt：一行一条指令，文件名即程序名，; 或 # 开头为注释。"""
    items = []
    for path in sorted(glob.glob(os.path.join(folder, "*.txt"))):
        lines = []
        with open(path, encoding="utf-8-sig") as fh:
            for raw in fh:
                code = raw.split(";")[0].strip()
                if not code or code.startswith("#"):
                    continue
                lines.append(" ".join(code.split()))
        if lines:
            items.append((os.path.splitext(os.path.basename(path))[0], lines))
    return items


_loaded = load_programs()
PROGRAMS = _loaded if _loaded else BUILTIN


# ------------------------------------------------------------------ GUI
class App:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.abort = False
        self.messages = []

        root.title("WPLSoft 指令自动录入器")
        root.resizable(False, False)

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="要录入的程序（一次一题）：",
                  font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        self.var = tk.StringVar(value=PROGRAMS[0][0])
        for name, lines in PROGRAMS:
            ttk.Radiobutton(frm, text=f"{name}    （{len(lines)} 条）",
                            value=name, variable=self.var,
                            command=self.refresh_count).pack(anchor="w", padx=10)

        self.lbl_count = ttk.Label(frm, text="", foreground="#0057b8")
        self.lbl_count.pack(anchor="w", pady=(6, 8))

        self.btn = ttk.Button(frm, text="开始录入", command=self.start)
        self.btn.pack(fill="x", ipady=6)

        self.lbl_state = ttk.Label(frm, text="就绪", font=("Microsoft YaHei", 10),
                                   foreground="#1a7f37")
        self.lbl_state.pack(anchor="w", pady=(8, 2))

        self.bar = ttk.Progressbar(frm, length=420, mode="determinate")
        self.bar.pack(fill="x", pady=(0, 8))

        self.txt = tk.Text(frm, width=58, height=13, state="disabled",
                           font=("Consolas", 9), bg="#fafafa", relief="groove")
        self.txt.pack(fill="both")

        ttk.Label(frm, foreground="#666",
                  text="用法：点「开始录入」→ 切到 WPLSoft 单击「指令模式」第一行（只单击）→ 自动录入；按 Esc 中止",
                  wraplength=430, justify="left").pack(anchor="w", pady=(8, 0))

        self.refresh_count()
        root.after(100, self.pump)

    # -- 工具 --------------------------------------------------------
    def refresh_count(self):
        lines = dict(PROGRAMS)[self.var.get()]
        self.lbl_count.config(text=f"本程序共 {len(lines)} 条指令")

    def log(self, msg):
        self.messages.append(msg)

    def set_state(self, msg, color="#1a7f37"):
        self.lbl_state.config(text=msg, foreground=color)

    def pump(self):
        while self.messages:
            msg = self.messages.pop(0)
            self.txt.config(state="normal")
            self.txt.insert("end", msg + "\n")
            self.txt.see("end")
            self.txt.config(state="disabled")
        self.root.after(100, self.pump)

    # -- 流程 --------------------------------------------------------
    def start(self):
        if self.running:
            return
        self.running = True
        self.abort = False
        self.btn.config(state="disabled")
        self.bar["value"] = 0
        self.bar["maximum"] = len(dict(PROGRAMS)[self.var.get()])
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.config(state="disabled")
        self.log(f"已选择：{self.var.get()}")
        self.set_state("等待你点击 WPLSoft 的「指令模式」第一行 …", "#b58900")
        threading.Thread(target=self.worker, daemon=True).start()

    def wait_for_click(self):
        """等用户单击到 WPLSoft 窗口上"""
        time.sleep(0.7)                      # 忽略点「开始录入」这一下
        while not self.abort:
            if esc_pressed():
                return False
            if left_button_down():
                time.sleep(0.35)             # 等鼠标松开、行选中生效
                for _ in range(15):          # 最多再确认 1.5 s
                    if "wplsoft" in foreground_exe():
                        return True
                    time.sleep(0.1)
                self.set_state("检测到点击，但当前不是 WPLSoft 窗口，继续等待 …", "#b58900")
            time.sleep(0.05)
        return False

    def worker(self):
        lines = dict(PROGRAMS)[self.var.get()]
        try:
            if not self.wait_for_click():
                self.finish("已取消")
                return
            self.set_state("开始录入 …", "#0057b8")
            time.sleep(0.25)
            for idx, ins in enumerate(lines, 1):
                if self.abort or esc_pressed():
                    self.finish(f"已中止（完成 {idx - 1}/{len(lines)} 条）")
                    return
                press_enter()                # 打开「输入指令」框
                time.sleep(0.28)
                type_text(ins)
                time.sleep(0.08)
                press_enter()                # 确定并跳到下一行
                time.sleep(0.16)
                self.log(f"{idx:02d}. {ins}")
                self.root.after(0, lambda v=idx: self.bar.configure(value=v))
                self.root.after(0, lambda v=idx: self.set_state(
                    f"录入中 … {v}/{len(lines)}", "#0057b8"))
            self.finish(f"全部完成，共 {len(lines)} 条。请点「编译」检查。")
            for _ in range(2):
                user32.MessageBeep(0x40)
                time.sleep(0.12)
        except Exception as exc:             # noqa: BLE001
            self.finish(f"出错：{exc}", "#c0392b")

    def finish(self, msg, color="#1a7f37"):
        self.running = False
        self.root.after(0, lambda: self.set_state(msg, color))
        self.root.after(0, lambda: self.btn.config(state="normal"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
