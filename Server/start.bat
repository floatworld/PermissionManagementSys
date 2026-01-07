@echo off
chcp 65001 > nul
title 斯能服务器管理系统 - 服务器端

echo ====================================
echo 斯能服务器管理系统 - 服务器启动
echo ====================================
echo.

echo [1/2] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)
echo.

echo [2/2] 启动服务器...
python start_server.py

pause
