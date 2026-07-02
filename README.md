# Funscript Studio

Funscript Studio is a local-first desktop funscript editor and video/audio perception generation tool.
It combines an Electron + React + TypeScript UI with a local Python backend for media analysis,
script generation, editing, export, and optional T-Code device preview.

Current version: **0.1.0-alpha.1**

## Alpha / Preview status

This project is currently an **Alpha / Preview** build.

- It is intended for personal research, local script editing, and local generation experiments.
- Generated scripts still require human review and manual refinement.
- It is not guaranteed to be production-ready.
- Device-control related features must be used carefully with user-defined safety limits.
- No sample videos, user funscripts, generated datasets, or private training data are included.

## Features

- Local video import and playback
- Timeline editor with zoom, playhead sync, keyframe editing, smoothing, and amplitude adjustment
- Funscript import/export
- Same-name multi-axis funscript auto-import
- Fast beat-based generation
- Perception-based generation
- Hybrid learned generation
- Training dataset import
- Learned profile fitting
- Similar segment matching
- Quality metrics
- Multi-axis support
- Local Python backend
- Optional OSR2/SR6 T-Code serial output with persistent axis limits
- Windowed/fullscreen muted preview mirror
- Windows preview build

## Architecture

```text
Video + Audio
  -> Python Perception Engine
  -> Hybrid Generator / Learning Module
  -> React Timeline Editor
  -> Exported Funscript
  -> Optional local T-Code device bridge
```

Main layers:

- `electron/` - Electron main process and preload bridge
- `src/` - React + TypeScript renderer UI
- `backend/` - local Python HTTP backend
- `backend/perception/` - perception timeline generation
- `backend/generation/` - event extraction, motion planning, action synthesis, quality metrics
- `backend/learning/` - training datasets, learned profiles, similarity index
- `scripts/` - install, start, and preview packaging helpers

## Installation

Recommended development environment:

- Windows 10/11
- Node.js 18+
- pnpm
- Python 3.10+
- FFmpeg, or the bundled `ffmpeg-static` dependency

Install dependencies:

```powershell
pnpm install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Or use the Windows helper:

```powershell
.\install.bat
```

## Development

Run the development build:

```powershell
pnpm run dev
```

Run checks:

```powershell
pnpm run typecheck
pnpm run build
python -m pytest tests
```

## One-click preview usage

For local preview builds on Windows:

```powershell
.\install.bat
.\start.bat
```

The legacy `start-app.bat` wrapper is also kept for compatibility.

To build a portable preview package:

```powershell
.\build-preview.bat
```

The preview build output is written under `outputs/`.

## Build

Build frontend and Electron code:

```powershell
pnpm run build
```

Build Windows packages with Electron Builder:

```powershell
pnpm run build:win
```

Create an unpacked Electron package:

```powershell
pnpm run pack
```

Build the Python backend executable:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller build\pyinstaller.spec --noconfirm --clean
```

## Data privacy

- The software is local-first by default.
- It does not automatically upload videos, funscripts, training datasets, learned profiles, or generated outputs.
- User data directories must not be committed to GitHub.
- If future API integrations are added, users must explicitly configure them and understand the privacy risks.

## Safety note for device control

Device output is experimental and should be used carefully.

- Set amplitude, position, speed, and frequency limits before testing with physical devices.
- Verify scripts in preview mode first.
- The project is not responsible for risks caused by external devices or unsafe limits.
- Default axis limits are intentionally conservative and can be adjusted in the device panel.

## Development status

Status: **Alpha**

Known limitations:

- Generated script quality can be unstable.
- Perception accuracy varies across live-action, 3D animation, 2D animation, and edited videos.
- Training currently uses parameter fitting and similar-segment matching rather than a built-in deep learning model.
- No default sample dataset is included.
- Device support depends on browser serial API availability and user hardware.
- Some media formats are converted to temporary local MP4 previews using FFmpeg.

Roadmap:

- Better perception feature validation tools
- More robust hybrid generation profiles
- Safer device simulation and calibration workflows
- Cleaner model/plugin extension points
- Optional future deep model integration without changing the local-first default

## Security

Read [SECURITY.md](SECURITY.md) before exposing the backend or using device-control features.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening issues or pull requests.

## License

MIT. See [LICENSE](LICENSE).
