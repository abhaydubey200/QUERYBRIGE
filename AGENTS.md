# AGENTS.md

> Living guide for humans and agents working in the QueryBridge repository.
> Captures the real, repo-grounded workflows and commands. Maintained by the
> "Auto AGENTS.md maintainer" scheduled task.
> Last updated: 2026-07-17

## Project overview

QueryBridge is an "Enterprise Analytics Operating System" — a Python/FastAPI
backend with a React/Vite frontend, orchestrated by Docker Compose, with an
optional Tauri desktop shell. It connects to multiple databases, exposes an nVIDIA-based AI intelligence
layer (`NVIDIA_API_KEY`, models `meta/llama-3-70b-instruct` and
`nvidia/nv-embed-v1`), and ships an observability stack.

## Repository layout

```
backend/        # Canonical runtime: Python FastAPI app (app/, uvicorn app.main:app)
  app/          # FastAPI app — endpoints, services, connectors, models, core
  src/          # Secondary/legacy TypeScript Fastify app (see "Known issues / TODOs")
  alembic/      # DB migrations (versions 001–004 + 002b catalog repair)
  tests/        # pytest suite (unit/, security/) + conftest.py
  scripts/validation/  # Operational certification suite (run_all_tests.py)
  sdk/          # connector_base.py
  requirements.txt      # Python deps (FastAPI/uvicorn/sqlalchemy/asyncpg/...)
  package.json          # Node/TS app scripts (secondary, see TODOs)
frontend/       # React 18 + Vite 5 + TS + Tailwind + Radix + zustand + react-query
desktop/        # Tauri shell (src-tauri/) + local_service_orchestrator.py, runtime_watchdog.py
infra/          # nginx.conf, observability/{prometheus,loki,tempo}.yml
scripts/        # validate-system.py, backup/{backup,restore}_metadata.sh
configs/        # env/secret/runtime templates
marketplace/    # registry.json (semantic plugin packs, e.g. fmcg-pack-01)
scratch/        # repro_runtime.py, stress_test.py, verify_isolation.py
STABILIZATION/  # Remediation/certification reports (markdown only)
docs/           # Setup/security guides + audit/PHASE7 reports
docker-compose.yml          # Base stack (services: api, ui, nginx + DBs + observability)
docker-compose.dev.yml      # Dev overrides (see TODOs — service names mismatched)
docker-compose.prod.yml     # Prod overrides (gunicorn / vite preview)
setup_infra.py  # Generator script that wrote the compose/infra files
bootstrap.py, install.sh, install.ps1  # Thin wrappers around `docker-compose up -d`
start-querybridge.ps1  # Windows startup orchestrator (key gen, port checks, compose up)
```

## Prerequisites

- Docker Desktop (with `docker` + `docker-compose`)
- Python 3.11 (backend image is `python:3.11-slim-bookworm`)
- Node 20 (frontend image is `node:20-alpine`)
- `loguru` is used by `scripts/validate-system.py`

## Environment setup

1. `cp .env.example .env`
2. Set the required keys (the app validates these at startup via
   `app.core.env_validator.validate_environment`):
   - `JWT_SECRET` — session signing (`openssl rand -base64 32`)
   - `ENCRYPTION_KEY` — AES-256 key for data-source credentials (32-byte base64)
   - `NVIDIA_API_KEY` — required by the AI runtime
   - `DATABASE_URL`, `REDIS_URL` — point at the compose service hostnames
     (`postgres:5432`, `redis:6379`) when running in Docker

## Common commands

### Run the whole stack (primary workflow)

```bash
docker-compose up -d --build          # build + start all services (per LOCAL_SETUP_GUIDE)
python bootstrap.py                   # equivalent: docker-compose -f docker-compose.yml up -d
./install.sh                          # same, shell wrapper
./start-querybridge.ps1               # Windows: checks deps, generates secure keys, compose up
python scripts/validate-system.py     # pre-flight: toolchain + port + .env checks
```

### Operate the stack

```bash
docker-compose logs -f <service>      # tail logs
docker-compose restart <service>      # restart one service
docker-compose down                   # stop everything
```

Valid `<service>` names from `docker-compose.yml`: `postgres`, `redis`, `mysql`,
`mssql`, `oracle`, `api`, `ui`, `nginx`, `prometheus`, `grafana`.

### Backend (Python — canonical runtime)

The Dockerized backend runs migrations then serves:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Local/backend commands (run from `backend/`):

```bash
pip install -r requirements.txt                # install Python deps
uvicorn app.main:app --reload --port 8000      # local dev server
alembic upgrade head                           # apply migrations
alembic revision --autogenerate -m "msg"       # create a new migration
alembic downgrade -1                           # roll back one revision
```

### Backend tests (run from `backend/`)

```bash
pytest                       # run the suite (tests/unit, tests/security)
pytest -m unit               # by marker
pytest -m security
```

Registered markers (from `tests/conftest.py`): `unit`, `integration`, `security`,
`load`, `slow`, `postgres`, `mysql`, `mssql`, `oracle`, `snowflake`.

Operational certification suite (run from `backend/`):

```bash
python scripts/validation/run_all_tests.py
# runs: real_db_validation, concurrency_validation, memory_validation, resilience_validation
```

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev        # vite --port 3000 --host 0.0.0.0  (path alias "@" -> frontend/src)
npm run build      # tsc && vite build
npm run preview    # vite preview --port 3000 --host 0.0.0.0
```

### Metadata backup / restore

```bash
bash scripts/backup/backup_metadata.sh    # pg_dump -> /backups/metadata_backup.dump (in querybridge_db)
bash scripts/backup/restore_metadata.sh   # pg_restore from that dump
```

## Services & ports (from `docker-compose.yml`)

| Service    | Container           | Host port → container | Notes |
|------------|---------------------|------------------------|-------|
| postgres   | querybridge_db      | 5444 → 5432            | DB `querybridge`, user `admin` |
| redis      | querybridge_cache   | 6380 → 6379            | AOF enabled |
| mysql      | querybridge_mysql   | 3307 → 3306             | |
| mssql      | querybridge_mssql   | 1434 → 1433             | msodbcsql18, EULA accepted |
| oracle     | querybridge_oracle  | 1522 → 1521             | gvenzl/oracle-free |
| api        | querybridge_api     | 8000 → 8000             | runs `alembic upgrade head` first |
| ui         | querybridge_ui      | 3000 → 3000             | Vite dev server |
| nginx      | querybridge_nginx   | 8080 → 80               | gateway |
| prometheus | querybridge_prometheus | 9090 → 9090          | |
| grafana    | querybridge_grafana | 3001 → 3000             | |

> Note: `LOCAL_SETUP_GUIDE.md` lists nginx on port 80 and uses the internal
> container ports for postgres/redis; the compose file maps nginx to **8080**
> and exposes postgres/redis on **5444/6380**. Prefer the compose values above.

## API surface (all routes under `/api/v1`)

Routers registered in `backend/app/main.py`:

- `/api/v1/auth`, `/connections`, `/ai`, `/catalog`, `/dashboards`, `/semantic`,
  `/notebooks`, `/governance`, `/monitoring`, `/workspaces`, `/plugins`,
  `/ws` (websocket), `/storage`, `/health`
- `ai_schema` router is mounted with prefix `/api/v1` (tags only in `include_router`)
- FastAPI docs: `http://localhost:8000/docs`
- Prometheus metrics: `GET /metrics` (registered at app root in `main.py`)
- Health: `GET /api/v1/health/` and `GET /api/v1/health/deep`

## Connectors (`backend/app/connectors/`)

`postgres`, `mysql`, `mssql`, `oracle`, `snowflake`, `file` — created via
`connector_factory.py`; base class in `base_connector.py` / `sdk/connector_base.py`.

## Conventions

- API responses follow the `{ success, data, error }` envelope (see the global
  exception handler in `app/main.py`, which attaches an `X-Trace-ID`).
- Logging via `loguru` (backend) and `pino`/`pino-pretty` (Node backend).
- Frontend state via `zustand`; data fetching via `@tanstack/react-query`.
- All compose services are on the `querybridge_network` bridge network.

## Known issues / TODOs

Things that look off but were not changed (kept out of scope per minimal-edit
constraint). Verify before acting.

- **TODO:** `docker-compose.dev.yml` and `docker-compose.prod.yml` define
  services named `backend` and `frontend`, but the base compose names them
  `api` and `ui`. The overrides therefore do not apply to the real services —
  the documented `docker-compose -f docker-compose.yml -f docker-compose.dev.yml`
  dev/prod workflow is currently a no-op for hot-reload/gunicorn.
- **TODO:** `pytest`, `pytest-asyncio`, and `aiosqlite` (used by
  `tests/conftest.py` for the in-memory `sqlite+aiosqlite` fixture and async
  fixtures) are **not** in `backend/requirements.txt`. Running tests requires
  installing them separately, and an `asyncio_mode` config is not set.
- **TODO:** A second backend exists in `backend/src/` (TypeScript/Fastify via
  `backend/package.json`: `npm run dev|build|start`). It is **not** used by the
  Docker runtime (Dockerfile runs `uvicorn app.main:app`). Relationship to the
  Python app and whether it is still maintained is unclear.
- **TODO:** `node_modules/` and `dist/` appear to be tracked in git (commit
  `b30df631` claims they were removed, but `.gitignore` is absent and
  `git ls-files` lists ~25k `node_modules` entries). Confirm intended state.
- **TODO:** `scripts/validate-system.py` checks host ports 5432/6379, but the
  compose stack exposes postgres/redis on 5444/6380 — the check may report false
  port conflicts/availability against the wrong ports.
