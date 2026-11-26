# WPLSoft 指令自动录入器

> 半自动把 IL 指令表逐条敲进台达 **WPLSoft** 的梯形图编辑器。
> 你只需要点一下要开始的那一行，剩下的 `回车 → 输入指令 → 回车 → 下一行` 全部自动完成。

台达 WPLSoft 的工程文件（`.dvp`）是闭源二进制，没有明文助记符，也**不支持导入 IL 文本**；
手工录入一支几十条的步进程序要点几百次键鼠。这个工具用 Windows `SendInput` 驱动键盘，
配合 WPLSoft 自带的「输入指令」对话框完成录入。

---

## 1. 工作原理

WPLSoft 在「指令模式」列表里录入一条指令的固定节奏是：

1. 单击选中目标行；
2. 按 `Enter` → 弹出「输入指令(&I)」对话框，输入框内容被**全选**（默认是 `NOP`）；
3. 键入 `LD X0` 之类的文本；
4. 按 `Enter`（= 确定）→ 写入该行，光标**自动跳到下一行**。

所以「录入一支程序」= 重复执行 `Enter → 打字 → Enter`，本工具就是把这个循环自动化：

```
选中第一行 → [Enter → 键入指令 → Enter] × N → 完成提示音
```

关键实现点：

| 机制 | 说明 |
|---|---|
| `SendInput` + `KEYEVENTF_UNICODE` | 直接发送 Unicode 字符，**与输入法、键盘布局无关** |
| `GetForegroundWindow` + 进程名校验 | 只有前台确实是 `wplsoft.exe` 才开始，误点别处不会乱敲 |
| `GetAsyncKeyState(VK_LBUTTON)` | 用「单击」作为启动信号，不用计时器猜时机 |
| `GetAsyncKeyState(VK_ESCAPE)` | 全程可随时按 Esc 中止 |

---

## 2. 环境要求

- Windows 10 / 11
- Python 3.8+（自带 `tkinter`、`ctypes`，**无任何第三方依赖**）
- 台达 WPLSoft 2.x

---

## 3. 快速开始

```bat
:: 双击 run.bat，或
python wpl_autotype_gui.py
```

操作四步：

1. 打开 WPLSoft，`文件 → 新建` 一个工程；
2. 在 GUI 里选好要录的程序 → 点「开始录入」（窗口会提示等待点击）；
3. 切到 WPLSoft，在「指令模式」里**单击**要开始的那一行（只单击，不要双击）；
4. 看到进度条开始走就松手，中途按 `Esc` 可中止；结束后按 `编译` 检查。

---

## 4. 自定义指令表

程序列表来自 `programs/` 目录，**文件名就是程序名**，一行一条指令：

```text
# 支持以 ; 或 # 开头的注释行
LD X0
OUT Y0       ; 行尾注释会被自动去掉
END
```

- 编码用 UTF-8（带不带 BOM 都行）；
- 连续空格会被规范成一个空格；
- 增删 `programs/*.txt` 后重启 GUI 生效；
- 若 `programs/` 为空，会退回内置的最小示例。

仓库内附 `programs/example.txt` 作为格式参考，复制一份改成自己的程序即可。

---

## 5. 常见问题

**点了「开始录入」没反应？**
工具在等你**单击 WPLSoft 窗口**。若提示「检测到点击，但当前不是 WPLSoft 窗口」，
说明前台进程不是 `wplsoft.exe`，切回 WPLSoft 再点一次即可。

**中途漏字 / 顺序错乱？**
在 `wpl_autotype_gui.py` 的 `worker()` 里调大各段 `time.sleep()`（默认 0.28 / 0.08 / 0.16 秒），
机器较慢或 WPLSoft 反应慢时建议整体放大约 1.5 倍。

**提示「输入指令」框挡住了？**
启动前先按 `Esc` 关掉残留的输入框，再点「开始录入」并单击第一行。

**能不能直接生成 .dvp？**
不能，`.dvp` 为闭源二进制（文件头 + 混淆程序块 + GBK 装置批注表），没有公开格式，
也无导入接口。本工具只负责「机械地重复键入」。

**其他 PLC 软件能用吗？**
任何「回车弹出输入框、输入后回车确认并跳行」的编辑器理论上都适用，
只需改掉进程名校验（`foreground_exe()` 里的 `"wplsoft"`）。

---

## 6. 目录结构

```
wpl-autotype/
├─ wpl_autotype_gui.py     # 主程序（tkinter GUI + SendInput 录入引擎）
├─ run.bat                 # Windows 一键启动
├─ programs/               # 指令表：一个 .txt 一支程序
│   └─ example.txt         # 格式示例
├─ README.md
└─ LICENSE
```

---

## 7. 限制与免责

- 仅在 Windows 桌面、WPLSoft 前台运行、键盘无其他输入时可靠；
- 录入过程中**请勿移动鼠标或敲键盘**，否则输入会打到别处；
- 工具不修改 WPLSoft 安装文件、不读写 `.dvp`，只是模拟人工按键；
- 请自行确认生成的程序正确性，务必在 WPLSoft 里 `编译` 并在仿真中验证后再下载到 PLC。

---

## English

`wpl-autotype` is a tiny Windows GUI that types IL instruction lists into Delta's
**WPLSoft** ladder editor semi-automatically. `.dvp` project files are closed-source
binaries with no IL import, so the only practical way to enter a long program is
keyboard automation. Click the first row in WPLSoft's instruction list, and the tool
replays `Enter → type → Enter` for every line using `SendInput` with
`KEYEVENTF_UNICODE` (IME/layout independent). Press `Esc` to abort.
Requires Python 3.8+ and WPLSoft 2.x. No third-party dependencies.

---

## License

MIT，见 [LICENSE](LICENSE)。
