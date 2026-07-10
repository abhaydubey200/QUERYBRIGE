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

- Copy `.env.example` → `.env`. Required keys:
  `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`,
  `ENCRYPTION_KEY` (32-byte base64), `NVIDIA_API_KEY`.
  Optional overrides: `ENV` (default `production`), `LOG_LEVEL`,
  `POSTGRES_USER`/`POSTGRES_PASSWORD`, `UI_PORT`, `API_PORT`.
- `start-querybridge.ps1` will auto-generate `JWT_SECRET` and
  `ENCRYPTION_KEY` if their placeholder values are still present.
- Env validation blocks startup if required keys are missing
  (`app/core/env_validator.py`); warns on placeholder values in
  production mode.

## API Routes (from `backend/app/main.py`)

All under `/api/v1/`:

| Prefix | Tag | Key Purpose |
| --- | --- | --- |
| `/auth` | Security | JWT auth, LDAP |
| `/connections` | Infrastructure | DB connection CRUD |
| `/ai` | Intelligence | AI SQL generation |
| `/ai-schema` | AI Schema & Search | Schema discovery + semantic search |
| `/catalog` | Data Catalog | Table/column metadata |
| `/dashboards` | Analytics | Dashboard management |
| `/semantic` | Semantic Layer | Metric registry, semantic resolver |
| `/notebooks` | Data Science | Sandbox notebook execution |
| `/governance` | Compliance | PII detection, masking, policies |
| `/monitoring` | Observability | Deep health probes |
| `/workspaces` | Tenancy | Multi-workspace isolation |
| `/plugins` | Extensions | Plugin marketplace |
| `/ws` | Streaming | WebSocket real-time events |
| `/storage` | Storage | File upload/storage |
| `/health` | Lifecycle | Liveness (`/`) + deep health (`/deep`) |
| `/metrics` | — | Prometheus metrics (not under `/api/v1`) |

## Database Connectors

`ConnectorFactory` (`backend/app/connectors/connector_factory.py`) supports:

| Type key(s) | Connector | Docker-mapped port |
| --- | --- | --- |
| `postgres`, `postgresql` | PostgresConnector | 5444 |
| `mysql` | MySQLConnector | 3307 |
| `mssql`, `sqlserver` | MSSQLConnector | 1434 |
| `oracle` | OracleConnector | 1522 |
| `snowflake` | SnowflakeConnector | Cloud |
| `csv`, `excel`, `file` | FileConnector | — |

Register custom connectors at runtime:
`ConnectorFactory.register_connector(type_name, connector_class)`.

## Observability Stack

- **Prometheus** scrapes `backend:8000` and `node_exporter:9100` (port 9090).
- **Grafana** on port 3001 (default admin password: `admin`).
- **Loki** log aggregation on port 3100 (`infra/observability/loki.yml`).
- **Tempo** distributed tracing on port 3200 (`infra/observability/tempo.yml`).
- Custom Prometheus metrics defined in `backend/app/core/metrics.py`:
  `querybridge_http_requests_total`, `querybridge_http_request_duration_seconds`,
  `querybridge_query_duration_seconds`, `querybridge_ai_failures_total`,
  `querybridge_semantic_resolution_seconds`, `querybridge_connection_health`,
  `querybridge_connection_latency_seconds`.

## Alembic Migrations

Four migration versions in `backend/alembic/versions/`:
1. `001_initial_schema` — core tables
2. `002_add_security_infrastructure` — auth/security
3. `002b_catalog_repair` — catalog fixes
4. `003_metadata_intelligence` — metadata AI
5. `004_lineage_governance` — lineage & governance

Auto-run on API container startup (`alembic upgrade head`).

## Test Markers

`pytest` markers registered in `conftest.py`:
`unit`, `integration`, `security`, `load`, `slow`,
`postgres`, `mysql`, `mssql`, `oracle`, `snowflake`.

Run security tests: `pytest -m security`. Skip slow: `pytest -m "not slow"`.

## Architecture Notes

- Backend is dual-stack: Python FastAPI (primary, `app/`) + Node.js Fastify
  (`src/`, `package.json`). Both coexist; see TODO above.
- Connector instances are cached by `ConnectorFactory` with
  signature-based invalidation; config changes replace cached instances.
- Notebook execution runs in a sandboxed process
  (`app/notebook_runtime/sandbox_executor.py`).
- Startup sequence: env validation (`app/core/env_validator.py`) →
  DB migrations (`alembic upgrade head`) → dependency bootstrap
  (`app/dependency_bootstrapper.py`) → health probes.
- `setup_infra.py` is a **code generator** — it writes docker-compose,
  configs, scripts, and docs. Re-running it may overwrite edits to those
  files.
- `scratch/` contains ad-hoc scripts (stress testing, isolation
  verification) — not production code.
- `marketplace/registry.json` defines installable plugin packs
  (e.g. FMCG Analytics Pack with `inventory_turnover`, `shelf_velocity`,
  `out_of_stock_rate` metrics).

## Agent Conventions

- Branch prefix: `tembo/` for any agent-authored branches.
- Default base/target branch: `main` (per repo configuration).
- Do not hand-edit files under `STABILIZATION/` – they are generated
  audit/report artifacts.
