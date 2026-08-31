@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul || goto :fail
py -3 -c "import json,re; d=json.load(open('data/knowledge_index.json',encoding='utf-8')); nums=[int(x['name'].split('_',1)[0]) for x in d if re.match(r'^\d+_',x['name'])]; print('Managed sources:',len(d)); print('Numbered sources:',len(nums)); print('Highest numbered source:',max(nums)); print('Novel Baker:',sum(341<=n<=377 for n in nums)); print('Moonlit:',sum(378<=n<=603 for n in nums)); assert len(nums)==603 and max(nums)==603; print('KNOWLEDGE PREFLIGHT PASSED')"
if errorlevel 1 goto :fail
pause
exit /b 0
:fail
echo KNOWLEDGE PREFLIGHT FAILED
pause
exit /b 1
