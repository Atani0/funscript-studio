@echo off
setlocal
cd /d "%~dp0\.."
echo [Funscript Studio] Start development preview
echo.

if not exist "node_modules" (
  echo [ERROR] node_modules not found. Run install.bat first.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Python virtual environment not found. Run install.bat first.
  pause
  exit /b 1
)

node scripts\start-app.cjs
if errorlevel 1 (
  echo.
  echo [ERROR] App start failed. See logs above.
  pause
  exit /b 1
)

pause
