@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\python-setup.ps1" %*
set "result=%ERRORLEVEL%"
pause
exit /b %result%
