@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo        ANGEL AI 3.6 INSTALLER
echo ==========================================
python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.61+ and try again.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed.
  pause
  exit /b 1
)
python -c "from pathlib import Path; import py_compile, sys; files=sorted(Path('angel').rglob('*.py')); failed=[]; [failed.append(str(p)) for p in files if (lambda ok: not ok)(py_compile.compile(str(p), doraise=False))]; print(f'Checked {len(files)} Python files.'); sys.exit(1 if failed else 0)"
if errorlevel 1 (
  echo Angel core syntax check failed.
  pause
  exit /b 1
)
python -c "from angel.brain import Brain; from angel.config import Config; b=Brain(Config.from_env()); print('Angel AI 6.0 core OK'); print('Knowledge folder:', b.knowledge.library_path)"
if errorlevel 1 (
  echo Angel core check failed.
  pause
  exit /b 1
)
echo.
for /f %%N in ('python -c "import json; d=json.load(open('data/knowledge_index.json',encoding='utf-8')); print(sum(1 for x in d if x['name'][:1].isdigit()))"') do set N=%%N
echo Knowledge files: %N%
echo Angel AI 6.0 installation ready.
echo Use START-ANGEL.bat to launch.
pause
