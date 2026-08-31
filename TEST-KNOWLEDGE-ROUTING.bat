@echo off
setlocal
cd /d "%~dp0"
py -3 -c "from angel.knowledge import KnowledgeBase; from pathlib import Path; kb=KnowledgeBase(Path('.\data')); print('KnowledgeBase.retrieve:', kb.retrieve.__qualname__); print('PASS: retrieve is a bound KnowledgeBase method.')"
if errorlevel 1 (
  echo FAIL: Knowledge routing import/test failed.
  pause
  exit /b 1
)
echo PASS: Knowledge routing is callable.
pause
