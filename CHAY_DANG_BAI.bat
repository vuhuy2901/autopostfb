@echo off
chcp 65001 > nul
title CHAY DANG BAI FACEBOOK - 30 NHOM TU DONG
cd /d "%~dp0"

echo ========================================================
echo   HE THONG TU DONG DANG BAI FACEBOOK GROUP
echo ========================================================
echo.
python auto_pilot.py
echo.
echo ========================================================
echo   DA KET THUC PHIEN DANG BAI.
echo ========================================================
pause
