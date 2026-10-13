@echo off
rem Threads research (daily): collect -> make shortlist. Called from Windows Task Scheduler at logon.
rem Log: research_data\logs\threads_research.log (append)
set "PROJ=C:\Users\PC_User\claude project"
set "PY=C:\Users\PC_User\AppData\Local\Python\pythoncore-3.14-64\python.exe"
cd /d "%PROJ%"
if not exist "research_data\logs" mkdir "research_data\logs"
set "LOG=research_data\logs\threads_research.log"
echo ===== %date% %time% start ===== >> "%LOG%"
"%PY%" collect_threads.py --daily --scrolls 5 >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo collect exit code: %RC% >> "%LOG%"
if "%RC%"=="3" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "Threads research: login expired. Please run threads_login.py again."
)
"%PY%" collect_x.py --daily >> "%LOG%" 2>&1
set "RCX=%ERRORLEVEL%"
echo collect_x exit code: %RCX% >> "%LOG%"
if "%RCX%"=="4" (
  wscript //B //Nologo "%PROJ%\research_alert.vbs" "X research: cookies unusable. Please update x_cookies.local.json."
)
"%PY%" make_shortlist.py >> "%LOG%" 2>&1
echo ===== %date% %time% end ===== >> "%LOG%"
