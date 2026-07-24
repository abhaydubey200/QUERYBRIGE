# AGENTS.md

Guidance for AI coding agents working in the QueryBridge repository.

## Project Overview

QueryBridge is an enterprise AI-native data intelligence platform. It has a
Python/FastAPI backend (primary), a React/TypeScript/Vite frontend, a
secondary TypeScript/Fastify backend (`backend/src/`), and a Tauri desktop
app (`desktop/`). All services are orchestrated via Docker Compose.

## Repository Layout

```
backend/app/          # Python FastAPI application (primary backend)
backend/src/          # TypeScript Fastify backend (secondary)
backend/alembic/      # Database migrations
backend/tests/        # pytest test suite (unit, security)
frontend/src/         # React + Vite frontend
desktop/              # Tauri desktop app + local orchestrator
infra/                # Nginx config, Prometheus config
scripts/              # System validation, backup/restore scripts
scratch/              # Ad-hoc stress & isolation test scripts
configs/              # Environment templates
docs/                 # Installation & setup docs
STABILIZATION/        # Runtime/concurrency/audit reports (reference only)
```

## Environment Setup

1. Copy `.env.example` to `.env` at the repo root.
2. Required variables (validated on startup by `app/core/env_validator.py`):
   - `DATABASE_URL` — PostgreSQL async connection string
   - `REDIS_URL` — Redis connection string
   - `JWT_SECRET` — Session signing secret
   - `ENCRYPTION_KEY` — AES-256 key for data-source credential encryption
   - `NVIDIA_API_KEY` — Key for the AI intelligence runtime
3. Optional: `SNOWFLAKE_*` variables for external Snowflake validation.

## Common Commands

### Backend (Python / FastAPI — primary)

All commands run from `backend/`.

| Task | Command |
| :--- | :--- |
| Install deps | `pip install -r requirements.txt` |
| Dev server | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Production | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000` |
| Run migrations | `alembic upgrade head` |
| Type/env check | `python -m app.core.env_validator` |

The FastAPI app entry point is `app.main:app`. API routes are registered under
the `/api/v1` prefix (auth, connections, ai, ai_schema, catalog, dashboards,
semantic, notebooks, governance, monitoring, workspaces, plugins, websocket,
storage, health). A `/metrics` endpoint serves Prometheus metrics.

### Backend (TypeScript / Fastify — secondary)

All commands run from `backend/`.

| Task | Command |
| :--- | :--- |
| Install deps | `npm install` |
| Dev server | `npm run dev` (ts-node-dev, port 8000) |
| Build | `npm run build` (tsc → `dist/`) |
| Start | `npm start` (`node dist/index.js`) |

TypeScript config: `backend/tsconfig.json` (target ES2022, CommonJS, strict).

### Frontend (React / Vite)

All commands run from `frontend/`.

| Task | Command |
| :--- | :--- |
| Install deps | `npm install` |
| Dev server | `npm run dev` (Vite, port 3000) |
| Build | `npm run build` (`tsc && vite build`) |
| Preview | `npm run preview` (port 3000) |

Path alias: `@/` maps to `src/` (configured in `tsconfig.json` and
`vite.config.ts`).

### Docker Compose

| Task | Command |
| :--- | :--- |
| Start all services | `docker-compose up -d --build` |
| Dev overrides | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up` |
| Prod overrides | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up` |
| Stop | `docker-compose down` |

Services: postgres (5444), redis (6380), mysql (3307), mssql (1434),
oracle (1522), api (8000), ui (3000), nginx (8080), prometheus (9090),
grafana (3001).

### Utility Scripts

| Task | Command |
| :--- | :--- |
| System validation | `python scripts/validate-system.py` |
| Backup metadata | `bash scripts/backup/backup_metadata.sh` |
| Restore metadata | `bash scripts/backup/restore_metadata.sh` |
| Operational cert suite | `cd backend && python -m scripts.validation.run_all_tests` |
| Stress test | `python scratch/stress_test.py` |

## Testing

Tests use **pytest** with async support. The test config lives in
`backend/tests/conftest.py`.

| Task | Command |
| :--- | :--- |
| Run all tests | `cd backend && pytest` |
| Unit tests only | `cd backend && pytest tests/unit -m unit` |
| Security tests | `cd backend && pytest tests/security -m security` |

Custom pytest markers (defined in `conftest.py`): `unit`, `integration`,
`security`, `load`, `slow`, `postgres`, `mysql`, `mssql`, `oracle`,
`snowflake`.

Tests use an in-memory SQLite database via `aiosqlite` + `StaticPool`.

## Linting & Type Checking

- **Frontend / TS backend**: `npm run build` runs `tsc` which enforces strict
  TypeScript. No standalone linter is configured in this repo.
- **Python backend**: No linter/formatter config (no ruff, flake8, or black
  config files). Verify changes by running the test suite and `tsc` where
  applicable.
- TODO: Consider adding `ruff` or `flake8` config for the Python backend and
  `eslint` for the frontend to formalize linting.

## Database Migrations

Alembic is configured in `backend/alembic.ini` with scripts in
`backend/alembic/`.

| Task | Command |
| :--- | :--- |
| Apply migrations | `cd backend && alembic upgrade head` |
| Create migration | `cd backend && alembic revision --autogenerate -m "description"` |

On startup, `app/main.py` also calls `Base.metadata.create_all` as a safety
net for missing tables.

## Key Conventions

- **Backend Python**: async-first (asyncpg, aiomysql, aioodbc). Modules under
  `app/` use the `app.*` import namespace. Logging via `loguru`. Settings
  validated via `pydantic-settings`.
- **Backend TS**: Fastify with `pino` logging. Routes registered with
  `/api/v1` prefix.
- **Frontend**: React 18 with TanStack Query for data fetching, Zustand for
  state, Radix UI + Tailwind CSS for components, React Router for navigation.
- **Connectors**: Database connectors in `app/connectors/` support PostgreSQL,
  MySQL, MSSQL, Oracle, Snowflake, and file-based sources. All extend
  `base_connector.py` and are created via `connector_factory.py`.
- **Docker Compose**: The API service runs `alembic upgrade head` before
  starting uvicorn. The frontend Dockerfile runs `npm run dev`.

## Service URLs (local)

| Service | URL |
| :--- | :--- |
| Frontend | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Metrics | http://localhost:8000/metrics |
| Nginx gateway | http://localhost:8080 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
