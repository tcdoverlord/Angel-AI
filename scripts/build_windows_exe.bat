@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller
python -m compileall -q angel_platform run_angel_platform.py
if errorlevel 1 (echo Python validation failed.& exit /b 1)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --noconfirm --clean --onefile --windowed --name AngelPlatform run_angel_platform.py
if errorlevel 1 (echo PyInstaller build failed.& exit /b 1)
if not exist dist\AngelPlatform.exe (echo EXE was not created.& exit /b 1)
echo SUCCESS: dist\AngelPlatform.exe
exit /b 0
