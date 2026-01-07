Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

strScriptPath = WScript.ScriptFullName
strScriptDir = Left(strScriptPath, InStrRev(strScriptPath, "\"))

Set oShellLink = WshShell.CreateShortcut(strDesktop & "\斯能服务器管理系统.lnk")
oShellLink.TargetPath = strScriptDir & "PermissionClient.exe"
oShellLink.WorkingDirectory = strScriptDir
oShellLink.Description = "斯能服务器管理系统客户端"
oShellLink.IconLocation = strScriptDir & "resources\app_icon.ico"
oShellLink.Save

MsgBox "桌面快捷方式创建成功！" & vbCrLf & "位置: " & strDesktop & "\斯能服务器管理系统.lnk", vbInformation, "完成"
