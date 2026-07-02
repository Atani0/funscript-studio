# Dependency notes

Funscript Studio is an Alpha / Preview project. Dependency risks should be reviewed before public release.

## Main runtime dependencies

- Electron
- React
- TypeScript
- Vite
- Python standard library HTTP server
- PyInstaller
- FFmpeg / `ffmpeg-static`

## Media processing

FFmpeg processes untrusted local media files. This is powerful but carries decoder risk.

Recommendations:

- keep FFmpeg updated
- avoid processing untrusted media when possible
- do not expose backend media endpoints to public networks
- treat crash reports from media parsing as security-sensitive

## Electron

Electron must be updated carefully. Major upgrades can change preload, serial permissions, and media behavior.

Current security posture:

- `contextIsolation: true`
- `nodeIntegration: false`
- local files or local development URLs only
- explicit preload API surface

## Python packages

The backend is designed to degrade gracefully when optional perception dependencies are unavailable.
Keep optional heavy CV/pose dependencies outside mandatory install paths unless they are required for a specific workflow.

## Audit guidance

Run:

```powershell
npm audit --omit=dev
pnpm audit --prod
python -m pytest tests
```

If a dependency cannot be upgraded immediately, document:

- affected package
- advisory
- reason upgrade is deferred
- mitigation
- follow-up issue
