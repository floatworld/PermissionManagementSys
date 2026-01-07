@echo off
chcp 65001 >nul
echo ====================================
echo 配置服务器地址
echo ====================================
echo.
echo 当前默认服务器地址: 192.168.110.77:5000
echo.
echo 如需修改，请手动编辑 config.json 文件
echo 修改 server.host 和 server.port 配置项
echo.
notepad config.json
pause
