@echo off
setlocal
cd /d "%~dp0"
title TaskFlow AI - Cai dat

echo === CAI DAT TASKFLOW AI ===
echo Can Python 3.10 va ket noi Internet.

if not exist ".venv\Scripts\python.exe" (
    py -3.10 -m venv .venv
    if errorlevel 1 (
        echo Khong tim thay Python 3.10. Hay cai Python 3.10 roi thu lai.
        goto :failed
    )
)

set "taskflowReq=requirements-lock.txt"
if not exist "%taskflowReq%" (
    echo CANH BAO: Chua co requirements-lock.txt; dang dung requirements.txt chua khoa phien ban.
    set "taskflowReq=requirements.txt"
)

echo Dang cai thu vien tu %taskflowReq% ...
".venv\Scripts\python.exe" -m pip install -r "%taskflowReq%"
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" backend\check_release.py
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" setup_local.py
if errorlevel 1 goto :failed

echo.
echo CAI DAT HOAN TAT. Nhan dup START.bat de mo TaskFlow AI.
pause
exit /b 0

:failed
echo.
echo CAI DAT CHUA HOAN TAT. Xem loi phia tren va thu lai.
pause
exit /b 1
