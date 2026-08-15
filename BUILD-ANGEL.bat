@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [Angel] Locating Python...
where py >nul 2>nul
if errorlevel 1 (
    echo [Angel] Python Launcher was not found. Install Python 3 with Tk support.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [Angel] Creating .venv...
    py -3 -m venv .venv
    if errorlevel 1 exit /b 1
)

echo [Angel] Installing build requirements...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 exit /b 1

echo [Angel] Running automated tests...
".venv\Scripts\python.exe" -m pytest -q tests -p no:cacheprovider
if errorlevel 1 (
    echo [Angel] Tests failed. Packaging stopped.
    exit /b 1
)

echo [Angel] Packaging Angel...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean Angel.spec
if errorlevel 1 exit /b 1

if not exist "dist\Angel.exe" (
    echo [Angel] Packaging completed without dist\Angel.exe.
    exit /b 1
)

echo.
echo [Angel] Build complete: %CD%\dist\Angel.exe
exit /b 0
