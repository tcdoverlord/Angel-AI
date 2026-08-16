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
if not exist "test-output" mkdir "test-output"
".venv\Scripts\python.exe" -m pytest -q tests -p no:cacheprovider --basetemp "test-output\pytest-build"
if errorlevel 1 (
    echo [Angel] Tests failed. Packaging stopped.
    exit /b 1
)

echo [Angel] Packaging Angel...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean Angel.spec
if errorlevel 1 exit /b 1

if not exist "dist\Angel\Angel.exe" (
    echo [Angel] Packaging completed without dist\Angel\Angel.exe.
    exit /b 1
)

if not exist "_internal" mkdir "_internal"
xcopy /e /i /y "dist\Angel\_internal" "_internal" >nul
if errorlevel 1 (
    echo [Angel] Could not place the runtime support files in the project root.
    exit /b 1
)

copy /y "dist\Angel\Angel.exe" "Angel.exe" >nul
if errorlevel 1 (
    echo [Angel] Could not place Angel.exe in the project root.
    exit /b 1
)

echo.
echo [Angel] Build complete: %CD%\Angel.exe
exit /b 0
