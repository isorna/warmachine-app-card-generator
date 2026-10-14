@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1" --doctor %*
set "result=%ERRORLEVEL%"
pause
exit /b %result%
