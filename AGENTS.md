# AGENTS.md

Operational reference for coding agents working on this repository. Commands
below are grounded in scripts and configs present in the repo. Keep this file
short; prefer linking to existing docs over duplicating them.

## Repo Layout

- `backend/` – FastAPI (Python) service. Also contains a separate Node/TS
  scaffold (`package.json`) with `dev`/`build`/`start` scripts.
- `frontend/` – Vite + React + TypeScript app.
- `desktop/` – Tauri shell plus `local_service_orchestrator.py` and
  `runtime_watchdog.py`.
- `infra/` – `nginx` proxy and `observability/prometheus.yml` configs.
- `scripts/` – Operational scripts (validation, backup/restore).
- `STABILIZATION/` – Generated stabilization/audit reports. Treat as
  read-only; do not hand-edit.
- `docs/` – Installation, security, performance, and audit docs.

## Bring-Up

- One-command (Linux/macOS): `docker-compose up -d --build`
- Windows orchestrator: `./start-querybridge.ps1` (auto-generates `JWT_SECRET`
  / `ENCRYPTION_KEY` into `.env`, port-checks 3000/8000/5444/6380/9090, then
  runs `docker-compose up -d --build`).
- Shutdown (Windows): `./stop-querybridge.ps1` (runs `docker-compose down`,
  preserves volumes).
- Plain install: `./install.sh` (Linux) or `./install.ps1` (Windows) –
  thin wrappers around `docker-compose -f docker-compose.yml up -d`.
- Python bootstrap: `python bootstrap.py` (equivalent to the install
  scripts).
- Compose overlays: `docker-compose.dev.yml` mounts source and runs
  `uvicorn --reload` + `npm run dev`; `docker-compose.prod.yml` runs
  `gunicorn -w 4 -k uvicorn.workers.UvicornWorker` + `npm run preview`.

## Service Map (from `LOCAL_SETUP_GUIDE.md`)

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Nginx proxy | http://localhost |
| API docs | http://localhost:8000/docs |
| Metrics | http://localhost:8000/metrics |
| Grafana | http://localhost:3001 |

## Backend (Python / FastAPI)

- Install: `pip install -r backend/requirements.txt`
- Dev: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  (run from `backend/`)
- Prod: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000`
- Tests: `pytest` from `backend/` (shared fixtures in
  `backend/tests/conftest.py`; uses in-memory `sqlite+aiosqlite`).
- Migrations: `alembic` from `backend/` (config: `backend/alembic.ini`,
  versions under `backend/alembic/versions/`).

## Backend (Node / TypeScript scaffold)

`backend/package.json` exposes:
- `npm run dev` – `ts-node-dev` on `src/index.ts`
- `npm run build` – `tsc`
- `npm start` – `node dist/index.js`

TODO: confirm whether this Node scaffold is active in production or
superseded by the FastAPI app; both currently coexist in `backend/`.

## Frontend (Vite + React)

From `frontend/`:
- `npm install`
- `npm run dev` – Vite on port 3000, host `0.0.0.0`
- `npm run build` – `tsc && vite build`
- `npm run preview` – Vite preview server on port 3000

## Operations

- System validation: `python scripts/validate-system.py` – checks for
  required tools (docker, docker-compose, python, node, npm) and verifies
  ports 3000 / 8000 / 5432 / 6379 are free.
- Logs: `docker-compose logs -f <service>`
- Recover a service: `docker-compose restart <service>`
- Metadata backup: `scripts/backup/backup_metadata.sh` – runs
  `pg_dump` inside the `querybridge_db` container to
  `/backups/metadata_backup.dump`.
- Metadata restore: `scripts/backup/restore_metadata.sh` – `pg_restore`
  in a single transaction (`-1`) from the same dump.

## Environment

- Copy `.env.example` → `.env`. Required keys: `JWT_SECRET`,
  `ENCRYPTION_KEY` (32-byte base64), `NVIDIA_API_KEY`.
- `start-querybridge.ps1` will auto-generate `JWT_SECRET` and
  `ENCRYPTION_KEY` if their placeholder values are still present.

## Agent Conventions

- Branch prefix: `tembo/` for any agent-authored branches.
- Default base/target branch: `main` (per repo configuration).
- Do not hand-edit files under `STABILIZATION/` – they are generated
  audit/report artifacts.
