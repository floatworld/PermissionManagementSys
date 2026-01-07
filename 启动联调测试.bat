@echo off
chcp 65001 >nul
echo ============================================================
echo 斯能服务器管理系统 - 联调测试启动脚本
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [1/3] 启动下位机服务器...
start "斯能服务器 - 下位机" cmd /k "cd /d %~dp0Server && python start_server.py"
echo     ✓ 服务器正在启动(新窗口)...

echo.
echo [2/3] 等待服务器初始化...
timeout /t 3 /nobreak >nul
echo     ✓ 等待完成

echo.
echo [3/3] 启动上位机客户端...
timeout /t 1 /nobreak >nul
start "斯能服务器 - 上位机" cmd /k "cd /d %~dp0 && python UIManagement/main_window.py"
echo     ✓ 客户端正在启动(新窗口)...

echo.
echo ============================================================
echo ✓ 联调环境启动完成!
echo ============================================================
echo.
echo 提示:
echo   - 服务器地址: http://127.0.0.1:5000
echo   - 关闭窗口即可停止服务
echo   - 查看详细日志请参考各窗口输出
echo.
echo ============================================================
pause
