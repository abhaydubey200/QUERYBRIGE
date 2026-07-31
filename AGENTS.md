# AGENTS.md

Guidance for AI agents working in the QueryBridge repository.
All commands below are grounded in the actual repo files (package.json,
requirements.txt, Dockerfiles, docker-compose, scripts, alembic.ini, conftest.py).

## Project Overview

QueryBridge is an enterprise AI analytics platform that turns natural language
into validated SQL, executes it against enterprise databases, and visualizes
results. The repo contains a full-stack app plus Docker orchestration.

## Tech Stack

- **Backend (primary, Python):** FastAPI app at `backend/app/main.py` (`app.main:app`),
  Python 3.11+, SQLAlchemy 2.0 (async), Pydantic 2, Alembic migrations, asyncpg,
  Redis, Prometheus client. See `backend/requirements.txt`.
- **Backend (secondary, Node.js):** Fastify app at `backend/src/index.ts` with its
  own `backend/package.json`. The Docker stack runs the Python app; the Node stack
  is an alternative runtime. See `backend/package.json`.
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS, React Query, Zustand,
  Recharts, Radix UI. See `frontend/package.json`.
- **Desktop:** Tauri shell in `desktop/src-tauri/` with Python orchestrator/watchdog
  (`desktop/local_service_orchestrator.py`, `desktop/runtime_watchdog.py`).
- **Infra:** Docker Compose, PostgreSQL 15, Redis 7, MySQL 8, MSSQL 2022, Oracle Free,
  Nginx, Prometheus, Grafana.

## Commands

Run from the directory noted for each component.

### Backend (Python) — run from `backend/`

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Run (dev) | `uvicorn app.main:app --reload` |
| Run (prod) | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000` |
| Apply DB migrations | `alembic upgrade head` |
| Create migration | `alembic revision -m "description"` |
| Run tests | `pytest` |
| Run operational validation suite | `python scripts/validation/run_all_tests.py` |

> TODO: `pytest`, `pytest-asyncio`, and `aiosqlite` are used by `tests/conftest.py`
> but are NOT declared in `requirements.txt`. Install them separately to run tests:
> `pip install pytest pytest-asyncio aiosqlite`. A dev-requirements file should be added.

Tests use custom markers (see `backend/tests/conftest.py`):
`unit`, `integration`, `security`, `load`, `slow`, `postgres`, `mysql`, `mssql`,
`oracle`, `snowflake`. Example: `pytest -m unit` or `pytest -m "not slow"`.
`conftest.py` provides in-memory SQLite fixtures via `sqlite+aiosqlite:///:memory:`.

### Backend (Node.js) — run from `backend/`

| Task | Command |
|------|---------|
| Install deps | `npm install` |
| Dev | `npm run dev` (`ts-node-dev --respawn --transpile-only src/index.ts`) |
| Build | `npm run build` (`tsc`) |
| Start (built) | `npm start` (`node dist/index.js`) |

### Frontend — run from `frontend/`

| Task | Command |
|------|---------|
| Install deps | `npm install` |
| Dev | `npm run dev` (Vite on port 3000) |
| Build | `npm run build` (`tsc && vite build`) |
| Preview build | `npm run preview` (Vite preview on port 3000) |

Path alias: `@` -> `frontend/src` (see `vite.config.ts`).
No ESLint/Prettier config is present; there is no `npm run lint` or typecheck script.

### Docker (run from repo root)

| Task | Command |
|------|---------|
| Full stack up | `docker compose up -d --build` |
| Dev override (hot reload) | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` |
| Prod override (gunicorn/preview) | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` |
| Bootstrap (alias) | `python bootstrap.py` (runs `docker-compose up -d`) |
| View logs | `docker compose logs -f <service>` |
| Restart a service | `docker compose restart <service>` |

The `api` service runs `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.

### Scripts (run from repo root)

| Task | Command |
|------|---------|
| Validate system (tools/ports/.env) | `python scripts/validate-system.py` |
| Backup PostgreSQL metadata | `bash scripts/backup/backup_metadata.sh` |
| Restore PostgreSQL metadata | `bash scripts/backup/restore_metadata.sh` |

## Services & Ports (docker-compose.yml)

| Service | Host port | Container port | Notes |
|---------|-----------|----------------|-------|
| Frontend (ui) | 3000 | 3000 | React dashboard |
| API | 8000 | 8000 | FastAPI; docs at `/docs` |
| Nginx | 8080 | 80 | Unified gateway |
| PostgreSQL | 5444 | 5432 | db `querybridge`, user `admin` |
| Redis | 6380 | 6379 | |
| MySQL | 3307 | 3306 | db `querybridge_test` |
| MSSQL | 1434 | 1433 | |
| Oracle | 1522 | 1521 | |
| Prometheus | 9090 | 9090 | scrapes `backend:8000/metrics` |
| Grafana | 3001 | 3000 | |

## Environment Setup

1. Copy `.env.example` to `.env` at repo root.
2. Required keys: `JWT_SECRET`, `ENCRYPTION_KEY` (32-byte base64 for AES-256),
   `NVIDIA_API_KEY` (AI runtime), `DATABASE_URL`, `REDIS_URL`.
3. `start-querybridge.ps1` auto-generates secure keys on Windows if placeholders exist.

## API Entry Point & Key Routes

- ASGI app: `app.main:app` (FastAPI v2.1.0). Health: `GET /api/v1/health/`.
- Metrics: `GET /metrics` (Prometheus). Root: `GET /`.
- Routers registered under `/api/v1/*`: `auth`, `connections`, `ai`, `ai_schema`,
  `catalog`, `dashboards`, `semantic`, `notebooks`, `governance`, `monitoring`,
  `workspaces`, `plugins`, `websocket` (`/api/v1/ws`), `storage`, `health`.
- On startup, `app/main.py` creates missing tables via `Base.metadata.create_all`
  as a safety net (migrations via Alembic are the primary path).

## Database Migrations

Alembic config in `backend/alembic.ini`; versions in `backend/alembic/versions/`.
Existing migrations: `001_initial_schema`, `002_add_security_infrastructure`,
`002b_catalog_repair`, `003_metadata_intelligence`, `004_lineage_governance`.

## Layout

```
backend/        Python FastAPI app (app/), Node Fastify app (src/), tests/, alembic/
frontend/       React + Vite app (src/)
desktop/        Tauri shell (src-tauri/) + Python orchestrator
infra/          nginx.conf, prometheus.yml, observability/
scripts/        validate-system.py, backup/{backup,restore}_metadata.sh
configs/        env templates and runtime/secrets templates
docs/           setup + audit docs
STABILIZATION/  runtime/stabilization reports (generated; do not edit)
scratch/        repro/stress/verify scripts (experimental)
docker-compose.yml, docker-compose.dev.yml, docker-compose.prod.yml
```

## Conventions

- Keep changes minimal and grounded in existing patterns.
- No code comments unless explicitly requested.
- `STABILIZATION/` and `backend/dist/`, `backend/node_modules/`, `frontend/dist/`
  are generated artifacts — do not hand-edit.
- TODO: no `.gitignore` was found at repo root; build artifacts (node_modules,
  dist, __pycache__) should be ignored. Add a `.gitignore` if touching tracked artifacts.
