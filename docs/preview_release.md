# Preview release guide

This document is for local personal preview builds.

## 1. Start from source

```powershell
.\install.bat
.\start.bat
```

Or:

```powershell
pnpm install
pnpm run dev
```

## 2. Build a Windows preview package

```powershell
.\build-preview.bat
```

The portable build is written to:

```text
outputs/FunscriptStudio-Portable-Preview/
```

The zip is written to:

```text
outputs/FunscriptStudio-Portable-Windows-Preview.zip
```

## 3. Clean old builds

Remove generated output before publishing source:

```powershell
Remove-Item dist, dist-electron, outputs, build\pyinstaller -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item *.tsbuildinfo -Force -ErrorAction SilentlyContinue
```

Do not delete source folders such as `src/`, `electron/`, `backend/`, `docs/`, or `scripts/`.

## 4. Confirm Python backend starts

```powershell
.\.venv\Scripts\python.exe backend\main.py --host 127.0.0.1 --port 0 --ffmpeg node_modules\ffmpeg-static\ffmpeg.exe
```

Expected output:

```json
{"endpoint":"http://127.0.0.1:<port>","port":<port>,"ws":null}
```

## 5. Confirm Electron connects to backend

Start the app:

```powershell
pnpm run dev
```

Then use the app status bar or generation/perception actions to confirm backend calls return successfully.

## 6. Check generator functionality

- import a local video
- run fast generation
- run perception analysis
- run hybrid generation
- verify generated actions appear on the timeline
- export a funscript to the video folder

Do not include the test video or generated script in the repository.

## 7. Check persistent device limits

- open the device panel
- change axis min/max limits
- close the app
- reopen the app
- confirm limits are restored

Limits are stored in local browser storage, not in the repository.

## 8. Check packaged output excludes personal data

Before sharing a preview package, verify:

- no `data/training_datasets`
- no `perception_outputs`
- no user videos
- no user funscripts
- no `.env`
- no local absolute paths in docs or generated files

## 9. Common packaging failures

### Python not found

Install Python 3.10+ and enable "Add Python to PATH", then rerun `install.bat`.

### PyInstaller not found

Install backend requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### FFmpeg missing

Run `pnpm install`. The app uses `ffmpeg-static` for packaged preview builds.

### Electron build fails

Run:

```powershell
pnpm run typecheck
pnpm run build
```

Fix TypeScript errors before packaging.
