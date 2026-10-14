@echo off
rem X algorithm weights watcher (every 3 days). Called from Windows Task Scheduler (XAlgoWeightsCheck) at logon.
rem The script itself skips when less than 3 days have passed. Guide: docs\sop\sop_research_auto_collect.md
rem Exit codes: 0 ok / 10 changed / 2 fetch failed / 3 parse failed.  Log: research\data\logs\x_algo.log (append)
set "HERE=C:\Users\PC_User\claude project\research"
set "PY=C:\Users\PC_User\AppData\Local\Python\pythoncore-3.14-64\python.exe"
cd /d "%HERE%"
if not exist "data\logs" mkdir "data\logs"
set "LOG=data\logs\x_algo.log"
echo ===== %date% %time% start ===== >> "%LOG%"
"%PY%" x_algo_weights.py >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo x_algo_weights exit code: %RC% >> "%LOG%"
if "%RC%"=="10" (
  wscript //B //Nologo "%HERE%\research_alert.vbs" "X algorithm weights CHANGED. Tell Claude: X algorithm update. Details: research\data\x_algo\changes.md"
) else if "%RC%"=="3" (
  wscript //B //Nologo "%HERE%\research_alert.vbs" "X algorithm weights: file layout changed (code 3). Script needs a fix."
)
echo ===== %date% %time% end ===== >> "%LOG%"
