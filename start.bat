@echo off
setlocal
cd /d "%~dp0"
title IntlTrade Platform Launcher
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and check "Add to PATH".
    echo         Then run this file again.
    pause
    exit /b 1
)
python launcher.py
if errorlevel 1 pause
