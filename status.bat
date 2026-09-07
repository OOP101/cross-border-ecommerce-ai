@echo off
setlocal
cd /d "%~dp0"
title IntlTrade Platform - Status
chcp 65001 >nul 2>nul
python launcher.py status
if errorlevel 1 pause
