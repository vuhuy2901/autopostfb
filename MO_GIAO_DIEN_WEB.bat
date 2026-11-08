@echo off
chcp 65001 >nul
title GIAO DIEN WEB QUAN LY AUTO POST FACEBOOK GROUP
cd /d "%~dp0"
echo ===============================================================
echo   DANG KHOI DONG GIAO DIEN WEB AUTO POST FACEBOOK GROUP...
echo   Trinh duyet se tu dong mo tai: http://127.0.0.1:5000
echo ===============================================================
python web_app.py
pause
