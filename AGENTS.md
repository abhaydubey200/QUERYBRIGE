# AGENTS.md

Operational notes for AI/automation agents working in this repository.
Keep this file grounded in real, in-repo workflows. When a command is unverified,
mark it with a TODO rather than inventing details.

## Repository layout

- `backend/` — Python FastAPI app (`app/`, `requirements.txt`, `alembic/`) plus a
  TypeScript service (`src/`, `package.json`, `tsconfig.json`).
- `frontend/` — Vite + React + TypeScript app (`package.json`, `vite.config.ts`).
- `desktop/`, `marketplace/`, `infra/`, `configs/` — supporting components and
  templates.
- `docs/` — user-facing guides (installation, security, Docker).
- `STABILIZATION/` — stabilization and validation reports (treat as read-only
  historical artifacts).
- `scripts/` — top-level utility scripts (e.g. `validate-system.py`, `backup/`).
- `bootstrap.py`, `setup_infra.py`, `install.sh`, `install.ps1` — convenience
  entry points that wrap `docker-compose`.

## Local startup

The canonical local workflow is Docker Compose. See `LOCAL_SETUP_GUIDE.md` and
`docs/DOCKER_SETUP_GUIDE.md` for details.

- Linux / macOS: `docker-compose up -d --build`
- Windows: `./start-querybridge.ps1` (stop with `./stop-querybridge.ps1`)
- Minimal install: `./install.sh` or `python bootstrap.py`
- Compose variants: `docker-compose.dev.yml`, `docker-compose.prod.yml`,
  `docker-compose.yml` (default).

Environment configuration: copy `.env.example` to `.env` and set `JWT_SECRET`,
`ENCRYPTION_KEY`, and `NVIDIA_API_KEY` before starting.

## Service endpoints (default ports)

| Service       | URL                                              |
| ------------- | ------------------------------------------------ |
| Frontend      | http://localhost:3000                            |
| Nginx gateway | http://localhost                                 |
| API docs      | http://localhost:8000/docs                       |
| Metrics       | http://localhost:8000/metrics                    |
| Grafana       | http://localhost:3001                            |
| Postgres      | localhost:5444 (host) → 5432 (container)         |

## Backend (Python)

- Dependencies: `pip install -r backend/requirements.txt`
- App package: `backend/app/` (FastAPI + SQLAlchemy + asyncpg + Redis).
- Migrations: Alembic, configured in `backend/alembic.ini` with versions under
  `backend/alembic/versions/`.
  - TODO: confirm the exact `alembic` invocation used in CI / Compose; the
    standard form is `alembic -c backend/alembic.ini upgrade head`.
- Tests: `backend/tests/` with `conftest.py`; appears to use pytest.
  - TODO: confirm the canonical test command (no `pytest.ini` / `pyproject.toml`
    is present at the repo root).
- Validation scripts: `backend/scripts/validation/run_all_tests.py` plus
  focused checks (`concurrency_validation.py`, `memory_validation.py`,
  `real_db_validation.py`, `resilience_validation.py`).

## Backend (Node / TypeScript)

`backend/package.json` scripts:

- `npm run dev` — `ts-node-dev` against `src/index.ts`.
- `npm run build` — `tsc`.
- `npm start` — `node dist/index.js`.

## Frontend

`frontend/package.json` scripts:

- `npm run dev` — Vite dev server on port 3000.
- `npm run build` — `tsc && vite build`.
- `npm run preview` — Vite preview server on port 3000.

## Diagnostics & troubleshooting

- `python scripts/validate-system.py` — system / port-conflict check referenced
  by the setup guide.
- `docker-compose logs -f <service>` — tail logs for a specific service.
- `docker-compose restart <service>` — recover a single service.

## Conventions for agents

- Place scratch / temporary files in `/tmp`, never inside the repo (the
  platform auto-opens a PR on any in-repo change).
- Do not modify `STABILIZATION/` reports or other historical artifacts unless
  the task explicitly says so.
- Prefer adding a TODO with a short note over guessing when a workflow is
  unclear.
