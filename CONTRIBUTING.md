# Contributing

Thanks for your interest in Funscript Studio.

This project is currently an Alpha / Preview desktop application. Contributions should focus on stability,
local-first workflows, generation quality, safety, documentation, and maintainability.

## Development setup

Requirements:

- Node.js 18+
- pnpm
- Python 3.10+
- Windows 10/11 recommended for preview packaging

Install:

```powershell
pnpm install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Or run:

```powershell
.\install.bat
```

## Run locally

```powershell
pnpm run dev
```

## Test and checks

```powershell
pnpm run typecheck
pnpm run build
python -m pytest tests
```

## Pull requests

Before opening a PR:

- keep changes scoped
- run type checks
- run relevant Python tests
- update docs if behavior changes
- avoid committing generated files

Do not commit:

- `node_modules/`
- `.venv/`
- `dist/`
- `dist-electron/`
- `outputs/`
- `build/pyinstaller/`
- media files
- user funscripts
- training datasets
- generated perception output
- `.env` or credentials

## Code style

- Prefer small, readable TypeScript and Python modules.
- Keep UI code separate from generation/perception logic.
- Keep backend APIs local-first and loopback-only.
- Add fallback behavior for optional dependencies.
- Prefer explicit error messages over silent failures.

## Issues

Useful issue reports include:

- OS and app version
- video format and codec if relevant
- whether a Python backend error appeared
- steps to reproduce
- screenshots or logs with personal paths removed

Do not attach private videos, private funscripts, training data, or device logs that include sensitive data.
