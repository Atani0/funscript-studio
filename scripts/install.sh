#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[Funscript Studio] macOS/Linux installer"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Please install Node.js 20+ from https://nodejs.org/"
  exit 1
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "Installing pnpm..."
  npm install -g pnpm
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then PYTHON_BIN=python3; elif command -v python >/dev/null 2>&1; then PYTHON_BIN=python; fi
fi
if [ -z "$PYTHON_BIN" ]; then
  echo "Python not found. Please install Python 3.9+."
  exit 1
fi

pnpm install

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt

echo "Optional packages are listed in backend/requirements-optional.txt."
echo "The app can run without them by using FFmpeg fallback."

echo "Install complete. Run ./start-app.sh"
