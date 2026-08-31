@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Angel AI 6.0 - Final GitHub Build

where py >nul 2>nul
if errorlevel 1 goto :fail
set "PY=py -3"
set "ANGEL_PROJECT_ROOT=%CD%"

echo.
echo ==============================================
echo          ANGEL AI 5.9 FINAL BUILD
echo ==============================================
echo.

echo [1/10] Creating persistent data tree...
for %%D in ("data" "data\knowledge" "data\knowledge_backups" "data\inbox" "data\gpts" "data\gpts\Angel" "data\memory") do if not exist "%%~D" mkdir "%%~D"
if not exist "data\learning_schema.sql" goto :fail

echo [2/10] Checking icon...
if not exist "Angel_AI.ico" goto :fail
if not exist "Angel_AI.png" goto :fail

echo [3/10] Validating Python...
%PY% -c "from pathlib import Path; files=sorted(Path('angel').rglob('*.py')); [compile(p.read_text(encoding='utf-8-sig'),str(p),'exec') for p in files]; compile(Path('AngelAI_direct.py').read_text(encoding='utf-8-sig'),'AngelAI_direct.py','exec'); print(f'Validated {len(files)} Angel Python files plus entry point.')"
if errorlevel 1 goto :fail

echo [4/10] Validating Learning schema...
%PY% -c "import sqlite3; from pathlib import Path; c=sqlite3.connect(':memory:'); c.executescript(Path('data/learning_schema.sql').read_text(encoding='utf-8-sig')); c.close(); print('Learning schema OK.')"
if errorlevel 1 goto :fail

echo [5/10] Counting knowledge...
%PY% -c "from pathlib import Path; print(f'Knowledge files: {sum(1 for p in Path(\"data/knowledge\").rglob(\"*\") if p.is_file())}')"

echo [6/10] Cleaning previous PyInstaller output...
if exist "build\AngelAI" rmdir /s /q "build\AngelAI"
if exist "dist\AngelAI.exe" del /q "dist\AngelAI.exe" >nul 2>nul
if exist "dist\data" rmdir /s /q "dist\data"

echo [7/10] Building one-file AngelAI.exe...
%PY% -m PyInstaller --noconfirm --clean "AngelAI.spec"
if errorlevel 1 goto :fail
if not exist "dist\AngelAI.exe" goto :fail

echo [8/10] Confirming no bundled persistent data...
if exist "dist\data" goto :fail

echo [9/10] Confirming persistent data exists outside dist...
if not exist "data\knowledge" goto :fail

echo [10/10] FINAL BUILD SUCCESSFUL
echo.
echo Application:
echo   %CD%\dist\AngelAI.exe
echo.
echo Persistent data:
echo   %CD%\data\
echo.
echo Ollama remains available for normal questions.
echo Local knowledge is additional authoritative context.
echo.
echo ==============================================
echo       ANGEL AI 5.9 BUILD SUCCESSFUL
echo ==============================================
echo.
pause
exit /b 0

:fail
echo.
echo ==============================================
echo       ANGEL AI 5.9 BUILD FAILED
echo ==============================================
echo.
pause
exit /b 1
