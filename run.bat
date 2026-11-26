@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PYW="

rem 优先用 PATH 里的 pythonw / pyw，但要求同目录 python.exe 能 import tkinter
call :try_where pythonw
if not defined PYW call :try_where pyw
if defined PYW goto :run

echo.
echo 未找到可用的 Python：需要 Python 3.8+ 且带 tkinter（官方安装包默认带）。
echo 也可以把 pythonw.exe 所在目录加入 PATH 后重试。
echo.
pause
exit /b 1

:run
start "" "%PYW%" "%~dp0wpl_autotype_gui.py"
exit /b 0

:try_where
for /f "delims=" %%i in ('where %1 2^>nul') do (
    if not defined PYW call :check "%%i"
)
exit /b 0

:check
set "CAND=%~1"
for %%f in ("%CAND%") do set "PYD=%%~dpfpython.exe"
if not exist "%PYD%" exit /b 0
"%PYD%" -c "import tkinter" >nul 2>nul
if errorlevel 1 exit /b 0
set "PYW=%CAND%"
exit /b 0
