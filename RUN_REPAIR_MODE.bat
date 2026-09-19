@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo       ANGEL PLATFORM - REPAIR MODE
echo ==========================================
echo.
echo Running directly from Python source...
echo Close Angel's window to stop the application.
echo.

python run_angel_platform.py

echo.
echo Angel Platform has stopped.
pause
endlocal
