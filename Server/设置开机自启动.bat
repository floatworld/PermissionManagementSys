@echo off
chcp 65001 >nul
echo ====================================
echo 设置服务器开机自启动
echo ====================================
echo.
echo 注意：此脚本需要管理员权限运行
echo.
pause
echo.
echo 正在导入任务计划...
schtasks /create /tn "PermissionServer" /xml "PermissionServer_Startup.xml" /f
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo ✓ 开机自启动设置成功！
    echo ====================================
    echo.
    echo 任务名称: PermissionServer
    echo 触发时间: 系统启动时
    echo 运行权限: 最高权限
    echo.
    echo 可通过以下命令管理：
    echo - 查看任务: schtasks /query /tn "PermissionServer"
    echo - 运行任务: schtasks /run /tn "PermissionServer"
    echo - 停止任务: taskkill /f /im PermissionServer.exe
    echo - 删除任务: schtasks /delete /tn "PermissionServer" /f
    echo.
) else (
    echo.
    echo ====================================
    echo ✗ 设置失败！
    echo ====================================
    echo 请确保：
    echo 1. 以管理员身份运行此脚本
    echo 2. PermissionServer_Startup.xml 文件存在
    echo 3. PermissionServer.exe 路径正确（当前设置为 C:\PermissionServer\）
    echo.
)
pause
