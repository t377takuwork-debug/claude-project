' Task Scheduler wrapper: run a .cmd without showing a console window.
' Usage: wscript.exe //B //Nologo run_hidden.vbs "full\path\to\script.cmd"
' Run(..., 0, True): 0 = hidden window, True = wait for exit
' (keeps ExecutionTimeLimit / MultipleInstancesPolicy meaningful).
' NOTE: ASCII only in this file - WSH reads it as ANSI, so UTF-8
' Japanese comments get garbled and can corrupt the parser's line breaks.
Set sh = CreateObject("WScript.Shell")
sh.Run """" & WScript.Arguments(0) & """", 0, True
