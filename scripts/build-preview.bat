@echo off
setlocal
cd /d "%~dp0\.."
echo [Funscript Studio] Build Windows preview package
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

echo [INFO] Cleaning old preview build output...
if exist "dist" rmdir /s /q "dist"
if exist "dist-electron" rmdir /s /q "dist-electron"
if exist "outputs\FunscriptStudio-Portable-Preview" rmdir /s /q "outputs\FunscriptStudio-Portable-Preview"
if exist "outputs\FunscriptStudio-Portable-Windows-Preview.zip" del /q "outputs\FunscriptStudio-Portable-Windows-Preview.zip"

echo [INFO] Running TypeScript and frontend build...
call npm.cmd run build
if errorlevel 1 (
  echo [ERROR] Frontend/Electron build failed.
  pause
  exit /b 1
)

echo [INFO] Building Python backend executable...
call .venv\Scripts\python.exe -m PyInstaller build\pyinstaller.spec --noconfirm --clean
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed.
  pause
  exit /b 1
)

echo [INFO] Creating portable preview folder...
set PORTABLE_NAME=FunscriptStudio-Portable-Preview
node scripts\package-portable.cjs
if errorlevel 1 (
  echo [ERROR] Portable package creation failed.
  pause
  exit /b 1
)
set PORTABLE_NAME=

echo [INFO] Checking package for excluded user-data folders...
if exist "outputs\FunscriptStudio-Portable-Preview\resources\app\data" (
  echo [ERROR] Package unexpectedly contains data directory.
  pause
  exit /b 1
)

echo [INFO] Creating zip...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'outputs\FunscriptStudio-Portable-Preview\*' -DestinationPath 'outputs\FunscriptStudio-Portable-Windows-Preview.zip' -CompressionLevel Optimal -Force"
if errorlevel 1 (
  echo [ERROR] Zip creation failed.
  pause
  exit /b 1
)

echo.
echo [OK] Preview build complete:
echo   outputs\FunscriptStudio-Portable-Preview
echo   outputs\FunscriptStudio-Portable-Windows-Preview.zip
pause
