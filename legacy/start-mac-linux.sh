#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "============================================"
echo "  AL PLANNER - starting the website..."
echo "============================================"
echo
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed!"
  echo "1. Go to https://nodejs.org"
  echo "2. Download the LTS version and install it"
  echo "3. Run this file again"
  exit 1
fi
if [ ! -d node_modules ]; then
  echo "First time setup - installing dependencies..."
  npm install
fi
echo
echo "Website starting... Open your browser and go to:"
echo
echo "     http://localhost:3000"
echo
echo "Login:  student@alplanner.lk / student123"
echo "Admin:  admin@alplanner.lk   / admin123"
echo
echo "(Keep this terminal open while using the site."
echo " Press Ctrl+C to stop the website.)"
echo "============================================"
node server.js
