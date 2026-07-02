# Legacy notes

The repository previously contained an experimental duplicate structure under the root `app/` directory.

Current active entry points are:

- `src/` for the React renderer
- `electron/` for Electron main/preload code
- `backend/` for the Python backend
- `scripts/` for install/start/package helpers

The old root `app/` directory duplicated earlier backend and Electron files and is not used by the current build,
development start command, or portable packaging workflow. It should not be restored unless a migration plan
explicitly references it.
