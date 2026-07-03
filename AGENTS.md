# AGENTS.md — QueryBridge

Quick reference for agents working in this repository.

## Project Overview

QueryBridge is an enterprise analytics platform with a dual-backend (FastAPI + Fastify), React/Vite frontend, and Tauri desktop wrapper. All services are Docker-first.

## Repository Layout

| Path | Purpose |
|------|---------|
| `backend/` | Python FastAPI (primary) + TypeScript Fastify (secondary) |
| `frontend/` | React 18 + Vite + TypeScript + TailwindCSS |
| `desktop/` | Tauri desktop app (Rust + Python services) |
| `infra/` | Nginx, Prometheus, Loki, Tempo configs |
| `configs/` | Environment templates and runtime limits |
| `scripts/` | System validation, backup/restore |
| `scratch/` | Debug, stress-test, reproduction scripts |
| `marketplace/` | Plugin registry (JSON) |
| `docs/` | Installation, security, audit reports |
| `STABILIZATION/` | 44 certification/convergence reports |

## Commands

### Docker (Primary Workflow)

```bash
# Start all services (production)
docker-compose up -d --build

# Start with dev overrides (volume mounts, reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start with production overrides (gunicorn, preview)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop (preserves volumes)
docker-compose down

# View logs
docker-compose logs -f <service>

# Restart a service
docker-compose restart <service>
```

### Backend (Python / FastAPI)

```bash
# Run locally (dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run locally (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000

# Run tests
pytest backend/tests/

# Run specific test markers
pytest backend/tests/ -m unit
pytest backend/tests/ -m integration
pytest backend/tests/ -m security

# Database migrations
alembic upgrade head

# Validation scripts (operational)
python backend/scripts/validation/run_all_tests.py
python backend/scripts/validation/real_db_validation.py
python backend/scripts/validation/concurrency_validation.py
python backend/scripts/validation/memory_validation.py
python backend/scripts/validation/resilience_validation.py
```

### Backend (TypeScript / Fastify)

```bash
# Run dev server (from backend/)
npm run dev

# Build (from backend/)
npm run build
```

### Frontend

```bash
# Run dev server (from frontend/)
npm run dev          # vite --port 3000 --host 0.0.0.0

# Build
npm run build       # tsc && vite build

# Preview production build
npm run preview     # vite preview --port 3000 --host 0.0.0.0
```

### Desktop (Tauri)

```bash
# Dev (from desktop/)
tauri dev           # launches npm run dev, connects to localhost:5173

# Build
tauri build         # runs npm run build, packages from ../dist
```

### Operational Scripts

```bash
# Validate system prerequisites (docker, python, node, ports, .env)
python scripts/validate-system.py

# Backup metadata
bash scripts/backup/backup_metadata.sh

# Restore metadata
bash scripts/restore/restore_metadata.sh
```

## Docker Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| `postgres` | querybridge_db | 5444→5432 | Primary database |
| `redis` | querybridge_cache | 6380→6379 | Cache/session store |
| `mysql` | querybridge_mysql | 3307→3306 | MySQL test target |
| `mssql` | querybridge_mssql | 1434→1433 | MSSQL test target |
| `oracle` | querybridge_oracle | 1522→1521 | Oracle test target |
| `api` | querybridge_api | 8000→8000 | FastAPI backend |
| `ui` | querybridge_ui | 3000→3000 | React frontend |
| `nginx` | querybridge_nginx | 8080→80 | Reverse proxy |
| `prometheus` | querybridge_prometheus | 9090→9090 | Metrics |
| `grafana` | querybridge_grafana | 3001→3000 | Dashboards |

Additional services via `setup_infra.py`: `migration_runner`, `loki` (3100), `tempo` (3200), `node_exporter` (9100).

## Key URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Nginx proxy | http://localhost:8080 |
| API docs (Swagger) | http://localhost:8000/docs |
| Prometheus metrics | http://localhost:8000/metrics |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

## Environment Setup

1. Copy `configs/.env.example` to `.env` at repo root
2. Set required variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `JWT_SECRET`, `ENCRYPTION_KEY`, `NVIDIA_API_KEY`
3. Windows: `./start-querybridge.ps1` auto-generates keys and checks ports

## Testing

- **Framework**: pytest + pytest-asyncio (Python only)
- **Test DB**: In-memory SQLite with async sessions
- **Custom markers**: `unit`, `integration`, `security`, `load`, `slow`, `postgres`, `mysql`, `mssql`, `oracle`, `snowflake`
- **No frontend test setup** exists yet (TODO: add vitest + testing-library)
- **No linting/formatting config** exists yet (TODO: add ruff for Python, eslint for TS)

## Database Migrations

Alembic migrations are in `backend/alembic/versions/`. They run automatically at API container startup. Run manually with `alembic upgrade head` from the `backend/` directory.

## Architecture Patterns

- **Connector Factory**: Thread-safe factory with instance caching and cache invalidation for 8 connector types
- **Process Isolation**: `run_in_subprocess()` wraps crash-prone operations (pyodbc, oracledb) in separate processes
- **Enterprise Startup Validation**: Pydantic Settings enforces required env vars before app start
- **Observability**: Full LGTM stack — Loki, Grafana, Tempo, Prometheus
- **PII Detection**: Multi-method consensus (regex + naming + entropy)
- **Plugin SDK**: `QueryBridgeConnector` abstract base class for third-party connectors
