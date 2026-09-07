@echo off
setlocal
cd /d "%~dp0"
title IntlTrade Platform - Stop
chcp 65001 >nul 2>nul
python launcher.py stop
if errorlevel 1 pause
