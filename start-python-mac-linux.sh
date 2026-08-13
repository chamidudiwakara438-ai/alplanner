#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "============================================"
echo "  AL PLANNER - Python edition"
echo "============================================"
echo
PY=python3
if ! command -v $PY >/dev/null 2>&1; then
  echo "Python 3 is not installed!"
  echo "Mac:   brew install python3   (or python.org)"
  echo "Linux: sudo apt install python3 python3-pip"
  exit 1
fi
if ! $PY -c "import flask" 2>/dev/null; then
  echo "First time setup - installing Flask..."
  $PY -m pip install flask || $PY -m pip install --user flask || $PY -m pip install --break-system-packages flask
fi
echo
echo "Open your browser and go to:  http://localhost:3000"
echo
echo "Login:  student@alplanner.lk / student123"
echo "Admin:  admin@alplanner.lk   / admin123"
echo
echo "(Keep this terminal open. Ctrl+C to stop.)"
echo "============================================"
$PY server.py
