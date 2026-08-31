@echo off
cd /d "%~dp0"
if exist "%CD%\dist\AngelAI.exe" (
 start "" "%CD%\dist\AngelAI.exe"
 exit /b 0
)
echo dist\AngelAI.exe not found. Run BUILD-EXE.bat first.
pause
