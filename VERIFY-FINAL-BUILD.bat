@echo off
setlocal
cd /d "%~dp0"
set FAIL=0
if exist "dist\AngelAI.exe" (echo PASS dist\AngelAI.exe) else (echo FAIL dist\AngelAI.exe & set FAIL=1)
if exist "data" (echo PASS data\) else (echo FAIL data\ & set FAIL=1)
if exist "data\knowledge" (echo PASS data\knowledge\) else (echo FAIL data\knowledge & set FAIL=1)
if exist "data\learning_schema.sql" (echo PASS learning schema) else (echo FAIL learning schema & set FAIL=1)
if exist "dist\data" (echo FAIL duplicate dist\data & set FAIL=1) else (echo PASS no dist\data)
if exist "AngelAI.exe" (echo FAIL root AngelAI.exe & set FAIL=1) else (echo PASS no root AngelAI.exe)
if exist "launcher.py" (echo FAIL launcher & set FAIL=1) else (echo PASS no launcher)
if exist "CREATE-ANGEL-SHORTCUT.ps1" (echo FAIL shortcut & set FAIL=1) else (echo PASS no shortcut)
if "%FAIL%"=="0" (
 echo.
 echo FINAL GITHUB BUILD VERIFICATION PASSED
 exit /b 0
)
echo FINAL GITHUB BUILD VERIFICATION FAILED
exit /b 1
