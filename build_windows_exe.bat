@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [1/5] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1

set "PY=.venv\Scripts\python.exe"

echo [2/5] Installing dependencies...
%PY% -m pip install --upgrade pip
if errorlevel 1 exit /b 1
%PY% -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1

echo [3/5] Validating source...
%PY% -m compileall -q angel_platform run_angel_platform.py
if errorlevel 1 exit /b 1

echo [4/5] Building onedir EXE (more reliable launch than onefile)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
%PY% -m PyInstaller --noconfirm --clean AngelPlatform.spec
if errorlevel 1 exit /b 1

echo [5/5] Build complete.
echo Launch file: dist\AngelPlatform\AngelPlatform.exe
if exist "dist\AngelPlatform\AngelPlatform.exe" (
  echo SUCCESS: EXE exists.
) else (
  echo ERROR: EXE was not created.
  exit /b 1
)
endlocal
