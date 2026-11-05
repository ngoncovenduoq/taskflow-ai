@echo off
setlocal
cd /d "%~dp0"
title TaskFlow AI - Chay ung dung

if not exist ".venv\Scripts\python.exe" (
    echo Chua cai thu vien. Chay SETUP.bat truoc.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" app_launcher.py
set "taskflowExitCode=%errorlevel%"
echo.
echo TaskFlow AI da dung.
pause
exit /b %taskflowExitCode%
