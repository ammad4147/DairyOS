@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\Start-DairyOS-Web.ps1"
if errorlevel 1 (
  echo.
  pause
)
endlocal
