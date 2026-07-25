@echo off
rem Windowsタスクスケジューラ用ラッパー: Threads長期アクセストークンの自動リフレッシュ
rem ログ: tools\output\scheduler_threads_refresh.log（追記式。発火確認はこのファイルを見る）
rem 新トークンはthreads_auth.local.jsonへ直接上書きされ、ログには出力されない
echo ===== %date% %time% ===== >> "C:\Users\PC_User\claude project\brands\mbticode\tools\output\scheduler_threads_refresh.log"
powershell -ExecutionPolicy Bypass -File "C:\Users\PC_User\claude project\brands\mbticode\tools\threads_connect_test.ps1" -Step refresh >> "C:\Users\PC_User\claude project\brands\mbticode\tools\output\scheduler_threads_refresh.log" 2>&1
