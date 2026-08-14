@echo off
REM Double-click this file to start DairyOS (backend + frontend) and open
REM the dashboard in your browser. See scripts\start_dairyos.ps1 for what
REM it actually does.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_dairyos.ps1"
pause
