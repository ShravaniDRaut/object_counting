@echo off
title AI-Powered Real-Time Object Counting System
cd /d "%~dp0"

echo ============================================================
echo Starting AI Real-Time Object Counting System
echo ============================================================

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py %*
) else (
    python main.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with code %ERRORLEVEL%
    pause
)
