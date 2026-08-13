@echo off
title AL Planner (Python edition)
cd /d "%~dp0"
echo.
echo   ==========================================
echo     AL PLANNER - starting the website...
echo          build 2026-08-13w
echo   ==========================================
echo.
echo   Closing any OLD AL Planner window that is
echo   still holding port 3000 (this was hiding the
echo   new lessons!)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul
)
echo.

set "PYCMD="

rem 1) Try the "py" launcher (installed by most Python installers)
where py >nul 2>nul
if %errorlevel%==0 set "PYCMD=py"

rem 2) Look for the new Python install-manager location
if not defined PYCMD (
  for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do (
    if not defined PYCMD ( if exist "%%D\python.exe" set "PYCMD=%%D\python.exe" )
  )
)

rem 3) Look for the classic python.org location
if not defined PYCMD (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if not defined PYCMD ( if exist "%%D\python.exe" set "PYCMD=%%D\python.exe" )
  )
)

if not defined PYCMD (
  echo   Python was not found on this PC.
  echo   Install it from https://www.python.org/downloads/
  echo   IMPORTANT: tick the box "Add python.exe to PATH" while installing.
  pause
  exit /b 1
)

echo   Using Python: %PYCMD%
"%PYCMD%" -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo   Installing Flask...
  "%PYCMD%" -m pip install flask
)

echo.
echo   Website address: http://localhost:3000
echo   Keep this window OPEN while you use the website.
echo   Press Ctrl+C inside this window to stop.
echo.
ping 127.0.0.1 -n 4 >nul
start "" http://localhost:3000
"%PYCMD%" server.py
pause
