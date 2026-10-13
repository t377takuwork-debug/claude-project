' Show a small message that closes by itself after 60 seconds. Usage: wscript //B research_alert.vbs "message"
Set sh = CreateObject("WScript.Shell")
sh.Popup WScript.Arguments(0), 60, "Threads research", 48
