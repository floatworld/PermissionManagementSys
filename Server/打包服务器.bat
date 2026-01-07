@echo off
chcp 65001 >nul
echo ====================================
echo 斯能服务器管理系统 - 服务器端打包
echo ====================================
echo.
echo 正在检查环境...
python --version
echo.
echo 正在打包服务器程序...
echo.
python build_server.py
echo.
if %ERRORLEVEL% EQU 0 (
    echo ====================================
    echo 打包成功！
    echo ====================================
    echo.
    echo 部署文件位于: dist 文件夹
    echo.
) else (
    echo ====================================
    echo 打包失败！请查看错误信息
    echo ====================================
)
pause
