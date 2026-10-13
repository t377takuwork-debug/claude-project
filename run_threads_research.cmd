@echo off
rem X / Threads research (daily): collect -> make shortlist. Called from Windows Task Scheduler (ThreadsResearchDaily) at logon.
rem Guide: docs\sop\sop_research_auto_collect.md   Log: research_data\logs\threads_research.log (append)
rem Exit codes: 0 ok / 3 Threads login expired / 4 X cookies unusable / 5 stopped halfway / 6 nothing found
set "PROJ=C:\Users\PC_User\claude project"
set "PY=C:\Users\PC_User\AppData\Local\Python\pythoncore-3.14-64\python.exe"
cd /d "%PROJ%"
if not exist "research_data\logs" mkdir "research_data\logs"
set "LOG=research_data\logs\threads_research.log"
echo ===== %date% %time% start ===== >> "%LOG%"

"%PY%" collect_threads.py --daily >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo collect_threads exit code: %RC% >> "%LOG%"
if "%RC%"=="3" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "Threads research: login expired. Please run threads_login.py again."
) else if not "%RC%"=="0" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "Threads research: problem (code %RC%). See research_data\logs\threads_research.log"
)

"%PY%" collect_x.py --daily >> "%LOG%" 2>&1
set "RCX=%ERRORLEVEL%"
echo collect_x exit code: %RCX% >> "%LOG%"
if "%RCX%"=="4" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "X research: cookies unusable. Please update x_cookies.local.json."
) else if not "%RCX%"=="0" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "X research: problem (code %RCX%). See research_data\logs\threads_research.log"
)

"%PY%" make_shortlist.py >> "%LOG%" 2>&1
echo ===== %date% %time% end ===== >> "%LOG%"
