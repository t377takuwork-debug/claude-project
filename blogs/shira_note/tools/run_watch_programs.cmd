@echo off
rem Windowsタスクスケジューラ用ラッパー（Day 3: 毎日07:00）
rem ログ: tools\output\scheduler_watch.log（追記式。発火確認はこのファイルを見る）
set PYTHONIOENCODING=utf-8
echo ===== %date% %time% ===== >> "C:\Users\PC_User\claude project\blogs\shira_note\tools\output\scheduler_watch.log"
"C:\Users\PC_User\AppData\Local\Python\bin\python.exe" "C:\Users\PC_User\claude project\blogs\shira_note\tools\watch_programs.py" >> "C:\Users\PC_User\claude project\blogs\shira_note\tools\output\scheduler_watch.log" 2>&1
