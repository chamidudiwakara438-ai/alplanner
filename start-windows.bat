@echo off
title AL Planner
echo ============================================
echo   AL PLANNER - starting the website...
echo ============================================
echo.
where node >nul 2>nul
if %errorlevel% neq 0 (
  echo Node.js is not installed!
  echo 1. Go to https://nodejs.org
  echo 2. Download the LTS version and install it
  echo 3. Run this file again
  echo.
  pause
  exit /b
)
if not exist node_modules (
  echo First time setup - installing dependencies...
  call npm install
)
echo.
echo Website starting... Open your browser and go to:
echo.
echo      http://localhost:3000
echo.
echo Login:  student@alplanner.lk / student123
echo Admin:  admin@alplanner.lk   / admin123
echo.
echo (Keep this window open while using the site.
echo  Close it or press Ctrl+C to stop the website.)
echo ============================================
node server.js
pause
