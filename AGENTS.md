# AGENTS.md

Operational notes for AI/automation agents working in this repository.
Keep this file grounded in real, in-repo workflows. When a command is unverified,
mark it with a TODO rather than inventing details.

## Repository layout

- `backend/` — Python FastAPI app (`app/`, `requirements.txt`, `alembic/`) plus a
  TypeScript Fastify service (`src/`, `package.json`, `tsconfig.json`).
- `frontend/` — Vite + React + TypeScript app (`package.json`, `vite.config.ts`).
- `desktop/`, `marketplace/`, `infra/`, `configs/` — supporting components and
  templates.
- `docs/` — user-facing guides (installation, security, Docker).
- `STABILIZATION/` — stabilization and validation reports (treat as read-only
  historical artifacts).
- `scripts/` — top-level utility scripts (`validate-system.py`, `backup/`).
- `bootstrap.py`, `setup_infra.py`, `install.sh`, `install.ps1` — convenience
  entry points that wrap `docker-compose`.

## Local startup

The canonical local workflow is Docker Compose. See `LOCAL_SETUP_GUIDE.md` and
`docs/DOCKER_SETUP_GUIDE.md` for details.

- Linux / macOS: `docker-compose up -d --build`
- Windows: `./start-querybridge.ps1` (stop with `./stop-querybridge.ps1`)
- Minimal install: `./install.sh` or `python bootstrap.py` (both wrap
  `docker-compose -f docker-compose.yml up -d`).
- Compose variants: `docker-compose.yml` (base), `docker-compose.dev.yml`
  (adds `--reload`, mounts source, `npm run dev`), `docker-compose.prod.yml`
  (gunicorn + uvicorn workers, `npm run preview`).

Environment configuration: copy `.env.example` to `.env` and set `JWT_SECRET`,
`ENCRYPTION_KEY`, and `NVIDIA_API_KEY` before starting. `start-querybridge.ps1`
auto-generates `JWT_SECRET` / `ENCRYPTION_KEY` if placeholder values are
detected.

## Service endpoints (default ports from `docker-compose.yml`)

| Service       | Host port | URL                                |
| ------------- | --------- | ---------------------------------- |
| Frontend (UI) | 3000      | http://localhost:3000              |
| API           | 8000      | http://localhost:8000/docs         |
| Metrics       | 8000      | http://localhost:8000/metrics      |
| Nginx gateway | 8080      | http://localhost:8080              |
| Grafana       | 3001      | http://localhost:3001              |
| Prometheus    | 9090      | http://localhost:9090              |
| Postgres      | 5444      | localhost:5444 → 5432 (container)  |
| Redis         | 6380      | localhost:6380 → 6379 (container)  |
| MySQL         | 3307      | localhost:3307 → 3306 (container)  |
| MSSQL         | 1434      | localhost:1434 → 1433 (container)  |
| Oracle Free   | 1522      | localhost:1522 → 1521 (container)  |

Health probe used by the API container: `GET /api/v1/health/`.

## Backend (Python / FastAPI)

- Dependencies: `pip install -r backend/requirements.txt`.
- App entry: `backend/app/main.py` (`app.main:app`).
- Container start command (`docker-compose.yml`):
  `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
  (executed with `backend/` mounted at `/app`).
- Dev override (`docker-compose.dev.yml`):
  `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- Prod override (`docker-compose.prod.yml`):
  `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000`.
- Migrations: Alembic, configured in `backend/alembic.ini` with versions under
  `backend/alembic/versions/`. Invoke as `alembic upgrade head` from the
  `backend/` directory (matches the compose command).
- Tests: `backend/tests/` with `conftest.py` and pytest-style files under
  `unit/` and `security/` (e.g. `test_pii_detector.py`,
  `test_pii_masking.py`, `test_file_connector.py`).
  - TODO: confirm the canonical pytest command (no `pytest.ini` /
    `pyproject.toml` is present at the repo root).
- Validation scripts: `backend/scripts/validation/run_all_tests.py` orchestrates
  `real_db_validation.py`, `concurrency_validation.py`, `memory_validation.py`,
  and `resilience_validation.py` (the last requires Docker access).

## Backend (Node / TypeScript)

`backend/package.json` scripts (Fastify-based service under `backend/src/`):

- `npm run dev` — `ts-node-dev --respawn --transpile-only src/index.ts`.
- `npm run build` — `tsc`.
- `npm start` — `node dist/index.js`.

## Frontend

`frontend/package.json` scripts:

- `npm run dev` — `vite --port 3000 --host 0.0.0.0`.
- `npm run build` — `tsc && vite build`.
- `npm run preview` — `vite preview --port 3000 --host 0.0.0.0`.

## Diagnostics & troubleshooting

- `python scripts/validate-system.py` — checks for required tools
  (`docker`, `docker-compose`, `python`, `node`, `npm`), port availability
  (3000, 8000, 5432, 6379), and `.env` presence.
- `docker-compose logs -f <service>` — tail logs for a specific service
  (e.g. `api`, `ui`, `postgres`, `redis`, `nginx`).
- `docker-compose restart <service>` — recover a single service.
- Metadata backup / restore:
  `scripts/backup/backup_metadata.sh` runs `pg_dump` inside `querybridge_db`
  to `/backups/metadata_backup.dump`;
  `scripts/backup/restore_metadata.sh` runs the matching `pg_restore`.

## Conventions for agents

- Place scratch / temporary files in `/tmp`, never inside the repo (the
  platform auto-opens a PR on any in-repo change).
- Do not modify `STABILIZATION/` reports or other historical artifacts unless
  the task explicitly says so.
- Prefer adding a TODO with a short note over guessing when a workflow is
  unclear.
