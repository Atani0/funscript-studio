# Security Policy

Funscript Studio is a local desktop application with a local Python backend.

## Local backend

- The backend must bind to `127.0.0.1` by default.
- Do not expose the backend to public networks.
- Do not run the backend behind a public reverse proxy.
- Treat all media files as untrusted input.

## Data that should not be committed

Do not commit:

- videos
- funscript files
- generated perception output
- training datasets
- generated scripts
- `.env` files
- API keys, tokens, or credentials
- local absolute paths such as `C:\Users\...`

## Device control safety

T-Code / OSR2 / SR6 output is experimental.

- Configure physical limits before connecting a device.
- Start with preview/simulation and low amplitude.
- Verify scripts manually before playback.
- The project cannot guarantee external device safety.

## Electron security notes

The app uses:

- `contextIsolation: true`
- `nodeIntegration: false`
- a preload bridge with explicit APIs
- local files or localhost development URLs only

Avoid adding generic filesystem APIs to the renderer. Add narrowly scoped IPC methods instead.

## CORS and local HTTP

The backend should only allow local development origins such as:

- `http://localhost:*`
- `http://127.0.0.1:*`
- `file://`
- `null` origins from packaged local files when required

Do not set permissive CORS for remote origins.

## FFmpeg and untrusted media

FFmpeg is used for local media probing, extraction, and preview conversion.
Malformed or untrusted media files can trigger decoder bugs in third-party libraries.
Keep dependencies updated and avoid processing files from untrusted sources.

## Reporting security issues

This is an Alpha project. If you find a security issue, please open a private report if the repository supports it,
or contact the maintainer directly before publishing exploit details.

Include:

- affected version
- operating system
- reproduction steps
- whether the issue requires a crafted media file, local file access, or device access

## Known security considerations

- Local file access is required for video and funscript import.
- The Python backend is local HTTP and should remain loopback-only.
- CORS is restricted to local origins.
- Electron IPC must remain narrowly scoped.
- Third-party dependencies, FFmpeg, and media decoders should be updated regularly.
