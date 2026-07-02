# Build notes

Source build:

```bash
npm run compile
```

Python backend binary:

```bash
pyinstaller build/pyinstaller.spec
```

Electron packages:

```bash
npm run pack
npm run build:win
npm run build:mac
```

The installer output is written to `release/`. Keeping Electron Builder output separate from the Vite renderer output `dist/` prevents recursive/self-including package output.
