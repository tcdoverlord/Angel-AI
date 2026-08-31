@echo off
setlocal
cd /d "%~dp0"
title Angel AI 2.7 - Windows Preflight

echo ==========================================
echo     ANGEL AI 2.7 - WINDOWS PREFLIGHT
echo ==========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher ^(py^) was not found.
  goto :fail
)

py -3 --version
if errorlevel 1 goto :fail

echo.
echo Checking all Angel Python files...
py -3 -c "from pathlib import Path; import py_compile,sys; files=sorted(Path('angel').rglob('*.py')); bad=[]; [bad.append(str(p)) for p in files if py_compile.compile(str(p),doraise=False) is None]; print('Checked',len(files),'files.'); sys.exit(1 if bad else 0)"
if errorlevel 1 goto :fail

echo.
echo Checking launcher import...
py -3 -c "import launcher; print('Launcher import OK')"
if errorlevel 1 goto :fail

echo.
echo PREFLIGHT PASSED
pause
exit /b 0

:fail
echo.
echo PREFLIGHT FAILED
pause
exit /b 1
