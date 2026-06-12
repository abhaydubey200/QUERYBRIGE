# AGENTS.md

Operational notes for coding agents working in this repository. Keep entries grounded in actual repo files and verified usage. See `LOCAL_SETUP_GUIDE.md` and `docs/` for user-facing setup docs.

## Repository layout

- `backend/` — Fastify (TypeScript) service plus a Python `app/` package and Alembic migrations.
  - `backend/src/` — TypeScript entrypoint compiled to `backend/dist/` (`tsc`).
  - `backend/app/` — Python application package referenced by tests (`from app.models`, `from app.db.session`).
  - `backend/alembic/` — database migrations (`alembic.ini` at `backend/alembic.ini`, `script_location = alembic`).
  - `backend/tests/` — `pytest` suites (`unit/`, `security/`) with shared async fixtures in `backend/tests/conftest.py`.
- `frontend/` — Vite + React + TypeScript (Tailwind, Radix UI, React Query, Zustand).
- `desktop/` — Tauri shell (`desktop/src-tauri/`) plus Python orchestrator/watchdog scripts.
- `marketplace/registry.json` — connector/plugin registry.
- `infra/`, `configs/`, `docker-compose*.yml` — deployment + service composition.
- `scripts/validate-system.py` — pre-flight check for required tools and ports.
- `STABILIZATION/` — historical stabilization reports; treat as read-only reference.

## Common workflows

### Start / stop the full stack
- Linux/macOS: `docker-compose up -d --build` (or `./install.sh` for a minimal bring-up).
- Windows: `./start-querybridge.ps1` (auto-generates `.env` keys); `./stop-querybridge.ps1` for shutdown.
- Compose variants: `docker-compose.yml` (default), `docker-compose.dev.yml`, `docker-compose.prod.yml`.
- Python helper: `python bootstrap.py` wraps `docker-compose up -d`.

### Validate environment
- `python scripts/validate-system.py` — checks for `docker`, `docker-compose`, `python`, `node`, `npm` and that ports `3000, 8000, 5432, 6379` are free.

### Backend (Node/TypeScript service)
From `backend/`:
- `npm run dev` — `ts-node-dev` against `src/index.ts`.
- `npm run build` — `tsc` to `dist/`.
- `npm start` — runs the compiled `dist/index.js`.

### Backend (Python app + tests)
- Tests: `pytest backend/tests` (uses async fixtures; `conftest.py` constructs an in-memory SQLAlchemy engine and imports from `app.*`, so run with `backend/` on `PYTHONPATH`, e.g. `cd backend && pytest tests`).
- Dependencies: `pip install -r backend/requirements.txt`.
- Migrations: `cd backend && alembic upgrade head` (config in `backend/alembic.ini`).

### Frontend
From `frontend/`:
- `npm run dev` — Vite dev server on `:3000` (host `0.0.0.0`).
- `npm run build` — `tsc && vite build`.
- `npm run preview` — preview the built bundle on `:3000`.

### Service URLs (local)
| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Nginx gateway | http://localhost |
| Backend API docs | http://localhost:8000/docs |
| Metrics | http://localhost:8000/metrics |
| Grafana | http://localhost:3001 |

## Environment

`.env` is required at the repo root. Copy from `.env.example` and set at minimum:
- `JWT_SECRET` — session signing.
- `ENCRYPTION_KEY` — 32-byte base64 key for credential encryption.
- `NVIDIA_API_KEY` — required for AI runtime features.

`start-querybridge.ps1` will auto-generate `JWT_SECRET` / `ENCRYPTION_KEY` when placeholders are detected.

## Conventions for agents

- Treat files under `STABILIZATION/` as point-in-time reports — do not rewrite them as part of unrelated changes.
- Prefer editing existing modules over adding new top-level directories; the layout above is load-bearing for imports (`app.*`, `src/*`).
- Scratch/output files belong in `/tmp` or `scratch/`, never committed.
- TODO: add lint / format commands once a canonical toolchain is wired up (no `lint` or `format` script is defined in `backend/package.json` or `frontend/package.json` at present).
- TODO: document end-to-end / integration test entrypoint — current `pytest` suites cover unit and security only.
