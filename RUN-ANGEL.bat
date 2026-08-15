@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "angel.py"
    exit /b 0
)

where py >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 with Tk support, then run BUILD-ANGEL.bat.
    pause
    exit /b 1
)

start "" pyw -3 "angel.py"
exit /b 0
