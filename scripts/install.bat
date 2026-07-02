@echo off
setlocal
cd /d "%~dp0\.."
echo [Funscript Studio] Install dependencies
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install Node.js 18+ from https://nodejs.org/
  pause
  exit /b 1
)

where pnpm >nul 2>nul
if errorlevel 1 (
  echo [INFO] pnpm was not found. Installing pnpm globally...
  call npm.cmd install -g pnpm
  if errorlevel 1 (
    echo [ERROR] Failed to install pnpm.
    pause
    exit /b 1
  )
)

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.10+ and enable Add Python to PATH.
    pause
    exit /b 1
  )
)

echo [INFO] Installing Node/Electron dependencies...
call pnpm.cmd install
if errorlevel 1 (
  echo [ERROR] pnpm install failed.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [INFO] Creating Python virtual environment...
  python -m venv .venv 2>nul || py -3 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create Python virtual environment.
    pause
    exit /b 1
  )
)

echo [INFO] Installing Python backend dependencies...
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip.
  pause
  exit /b 1
)
call .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] Failed to install backend requirements.
  pause
  exit /b 1
)

if exist "node_modules\ffmpeg-static\ffmpeg.exe" (
  echo [INFO] FFmpeg static binary found.
) else (
  echo [WARN] FFmpeg static binary was not found in node_modules. Re-run pnpm install if media analysis fails.
)

echo.
echo [OK] Install complete.
echo Next steps:
echo   start.bat
echo   build-preview.bat
pause
