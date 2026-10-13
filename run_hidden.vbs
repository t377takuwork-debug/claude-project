' Run a .cmd without showing a window. Usage: wscript //B //Nologo run_hidden.vbs "C:\path\to\file.cmd"
Set sh = CreateObject("WScript.Shell")
sh.Run """" & WScript.Arguments(0) & """", 0, True
