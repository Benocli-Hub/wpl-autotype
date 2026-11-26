@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PYW="

if not defined PYW call :try_where pythonw
if not defined PYW call :try_where pyw
if defined PYW goto :run

echo.
echo Python 3.8+ with tkinter is required.
echo Add the folder containing pythonw.exe to PATH and try again.
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
