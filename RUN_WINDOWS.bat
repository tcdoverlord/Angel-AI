@echo off
setlocal
cd /d "%~dp0"
if exist "dist\AngelPlatform\AngelPlatform.exe" (
  start "Angel Platform" "dist\AngelPlatform\AngelPlatform.exe"
) else (
  echo EXE not found. Run build_windows_exe.bat first.
  pause
  exit /b 1
)
endlocal
