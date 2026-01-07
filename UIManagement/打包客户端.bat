@echo off
chcp 65001 >nul
echo ====================================
echo 斯能服务器管理系统 - 客户端打包
echo ====================================
echo.
echo 正在检查环境...
python --version
echo.
echo 正在打包客户端程序...
echo.
python build_client.py
echo.
if %ERRORLEVEL% EQU 0 (
    echo ====================================
    echo 打包成功！
    echo ====================================
    echo.
    echo 部署文件位于: dist 文件夹
    echo 默认服务器: 192.168.110.77:5000
    echo.
    echo 可将 dist 文件夹复制到任意客户端使用
    echo.
) else (
    echo ====================================
    echo 打包失败！请查看错误信息
    echo ====================================
)
pause
