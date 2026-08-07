# AGENTS.md

Operational reference for coding agents working on this repository. Commands
below are grounded in scripts and configs present in the repo. Keep this file
short; prefer linking to existing docs over duplicating them.

## Repo Layout

- `backend/` – FastAPI (Python) service (`app/`, `requirements.txt`,
  `alembic/`, `tests/`). Also contains a separate Node/TS scaffold
  (`src/`, `package.json`) with `dev`/`build`/`start` scripts.
- `frontend/` – Vite + React + TypeScript app.
- `desktop/` – Tauri shell plus `local_service_orchestrator.py` and
  `runtime_watchdog.py`.
- `infra/` – `nginx/` proxy and `observability/` (prometheus, loki, tempo).
- `configs/` – Environment templates (`.env.example`, `.env.production`,
  `secrets.template`, `runtime.template.json`).
- `scripts/` – Operational scripts (`validate-system.py`, `backup/`).
- `docs/` – Installation, security, Docker, and audit docs.
- `STABILIZATION/` – Generated stabilization/audit reports. Treat as
  read-only; do not hand-edit.
- `marketplace/` – Plugin registry (`registry.json`).

## Bring-Up

- One-command (Linux/macOS): `docker-compose up -d --build`
- Windows orchestrator: `./start-querybridge.ps1` (auto-generates
  `JWT_SECRET`/`ENCRYPTION_KEY` into `.env` if placeholders are present,
  port-checks 3000/8000/5444/6380/9090, then runs
  `docker-compose up -d --build`).
- Shutdown (Windows): `./stop-querybridge.ps1` (runs `docker-compose down`,
  preserves volumes).
- Plain install: `./install.sh` (Linux) or `./install.ps1` (Windows) –
  thin wrappers around `docker-compose -f docker-compose.yml up -d`.
- Python bootstrap: `python bootstrap.py` (equivalent to the install
  scripts).
- Compose overlays: `docker-compose.dev.yml` mounts source and runs
  `uvicorn --reload` + `npm run dev`; `docker-compose.prod.yml` runs
  `gunicorn -w 4 -k uvicorn.workers.UvicornWorker` + `npm run preview`.

## Service Map (ports from `docker-compose.yml`)

| Service    | Host port | URL / note                     |
| ---------- | --------- | ------------------------------ |
| Frontend   | 3000      | http://localhost:3000          |
| API        | 8000      | http://localhost:8000/docs     |
| Metrics    | 8000      | http://localhost:8000/metrics  |
| Nginx      | 8080      | http://localhost:8080          |
| Grafana    | 3001      | http://localhost:3001          |
| Prometheus | 9090      | http://localhost:9090          |
| Postgres   | 5444      | maps to 5432 in container      |
| Redis      | 6380      | maps to 6379 in container      |
| MySQL      | 3307      | maps to 3306 in container      |
| MSSQL      | 1434      | maps to 1433 in container      |
| Oracle     | 1522      | maps to 1521 in container      |

## Backend (Python / FastAPI)

- Install: `pip install -r backend/requirements.txt`
- Dev: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  (run from `backend/`)
- Prod: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  app.main:app -b 0.0.0.0:8000`
- Tests: `pytest` from `backend/` (shared fixtures in
  `backend/tests/conftest.py`; uses in-memory `sqlite+aiosqlite`).
  Markers: `unit`, `integration`, `security`, `load`, `slow`, `postgres`,
  `mysql`, `mssql`, `oracle`, `snowflake`.
- Migrations: `alembic upgrade head` from `backend/` (config:
  `backend/alembic.ini`, versions under `backend/alembic/versions/`).
- Operational validation suite: `python -m
  scripts.validation.run_all_tests` from `backend/` (runs DB, concurrency,
  memory, and resilience checks).
- API entry point: `backend/app/main.py` — routes under `/api/v1/`
  (auth, connections, ai, ai_schema, catalog, dashboards, semantic,
  notebooks, governance, monitoring, workspaces, plugins, websocket,
  storage, health).
- Env validation: `app/core/env_validator.py` blocks startup if
  `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, or
  `NVIDIA_API_KEY` are missing; warns on placeholder values in production.

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
  ports 3000/8000/5432/6379 are free.
  TODO: port list in `validate-system.py` (5432, 6379) does not match
  `docker-compose.yml` host ports (5444, 6380).
- Logs: `docker-compose logs -f <service>`
- Recover a service: `docker-compose restart <service>`
- Metadata backup: `scripts/backup/backup_metadata.sh` – runs
  `pg_dump` inside the `querybridge_db` container to
  `/backups/metadata_backup.dump`.
- Metadata restore: `scripts/backup/restore_metadata.sh` – `pg_restore`
  in a single transaction (`-1`) from the same dump.

## Environment

- Copy `.env.example` → `.env`. Required keys: `DATABASE_URL`,
  `REDIS_URL`, `JWT_SECRET`, `ENCRYPTION_KEY` (32-byte base64),
  `NVIDIA_API_KEY`. Optional overrides: `ENV` (default `production`),
  `LOG_LEVEL`, `POSTGRES_USER`/`POSTGRES_PASSWORD`, `UI_PORT`,
  `API_PORT`.
- `start-querybridge.ps1` will auto-generate `JWT_SECRET` and
  `ENCRYPTION_KEY` if their placeholder values are still present.
- Generate a JWT secret: `openssl rand -base64 32`.

## Conventions for Agents

- Do not modify `STABILIZATION/` reports or other historical artifacts
  unless the task explicitly says so.
- Prefer adding a TODO with a short note over guessing when a workflow is
  unclear.
- Keep edits minimal and grounded in actual repo usage.
