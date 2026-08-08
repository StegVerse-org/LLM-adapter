@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\hil_submit_client.py
) else (
  python scripts\hil_submit_client.py
)
if errorlevel 1 pause
endlocal
