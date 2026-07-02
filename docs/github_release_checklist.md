# GitHub release checklist

Before publishing a public Alpha repository:

- [ ] Delete build artifacts
- [ ] Delete `node_modules/`
- [ ] Delete `.venv/`
- [ ] Delete `dist/`
- [ ] Delete `dist-electron/`
- [ ] Delete `outputs/`
- [ ] Delete `release/` and `out/`
- [ ] Delete `build/pyinstaller/`
- [ ] Delete `__pycache__/` and `*.pyc`
- [ ] Delete `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- [ ] Delete `.env` and local config files
- [ ] Delete training datasets
- [ ] Delete generated perception outputs
- [ ] Delete generated scripts
- [ ] Delete video samples
- [ ] Delete funscript samples unless synthetic and documented
- [ ] Search for `C:\Users` or other personal paths
- [ ] Search for API keys, tokens, secrets, and credentials
- [ ] Run `pnpm run typecheck`
- [ ] Run `pnpm run build`
- [ ] Run `python -m pytest tests`
- [ ] Run `npm audit --omit=dev` or `pnpm audit --prod`
- [ ] Review `README.md`
- [ ] Review `LICENSE`
- [ ] Review `SECURITY.md`
- [ ] Review `CONTRIBUTING.md`
- [ ] Review `.gitignore`
- [ ] Confirm backend binds to `127.0.0.1` by default
- [ ] Confirm CORS is not open to remote origins
- [ ] Confirm Electron uses `contextIsolation: true`
- [ ] Confirm Electron uses `nodeIntegration: false`
- [ ] Confirm preload exposes only required APIs
- [ ] Confirm packaged output does not include user data
- [ ] Confirm no large binary artifacts are committed
- [ ] Confirm docs state Alpha / Preview status
