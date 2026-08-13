#!/bin/sh
cd "$(dirname "$0")"
echo "Starting AL Planner (no Python)..."
exec node scripts/preview.js
