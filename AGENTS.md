# AGENTS.md

Operational guide for AI agents working in the QueryBridge repo. Commands and
workflows below are grounded in scripts and configs actually present in the
repository.

## Repo Layout (top level)

- `backend/` — primary Python FastAPI service (`app/main.py`) plus a TypeScript
  Fastify sub-service under `backend/src/` (separate `package.json`).
- `frontend/` — Vite + React 18 UI.
- `desktop/` — Tauri-based desktop shell (`desktop/src-tauri/`) and Python
  orchestrators (`local_service_orchestrator.py`, `runtime_watchdog.py`).
- `infra/` — nginx config and observability stack (`prometheus.yml`).
- `scripts/` — system-level helpers (e.g. `validate-system.py`).
- `STABILIZATION/` — stabilization / certification reports. Read-only for
  context; do not regenerate.
- `docs/` — guides and audits. `LOCAL_SETUP_GUIDE.md` at repo root is the
  canonical setup doc.

## Full-stack workflows

Start everything (Linux/macOS):

```bash
docker-compose up -d --build
```

Start everything (Windows, recommended — handles `.env` bootstrap and port
checks):

```powershell
./start-querybridge.ps1
```

Stop everything:

```bash
docker-compose down            # Linux/macOS
./stop-querybridge.ps1         # Windows
```

Dev compose overlay (when present): `docker-compose -f docker-compose.yml -f
docker-compose.dev.yml up -d --build`. Prod overlay:
`docker-compose.prod.yml`.

System / toolchain sanity check:

```bash
python scripts/validate-system.py
```

Default service URLs (from `docker-compose.yml`):

- UI: http://localhost:3000
- API: http://localhost:8000 (docs at `/docs`, metrics at `/metrics`)
- Nginx gateway: http://localhost:8080
- Postgres: `localhost:5444` (container `querybridge_db`)
- Redis: `localhost:6380`
- MySQL: `localhost:3307`, MSSQL: `localhost:1434`, Oracle: `localhost:1522`
- Prometheus: `localhost:9090`, Grafana: `localhost:3001`

## Backend — Python (FastAPI)

From `backend/`:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The container entrypoint runs `alembic upgrade head` before launching uvicorn
with 4 workers — match that ordering when reproducing prod locally.

Tests (pytest, with markers registered in `backend/tests/conftest.py`):

```bash
cd backend
pytest                              # all tests
pytest -m unit                      # unit only
pytest -m security                  # security only
pytest tests/unit/test_pii_detector.py
```

Registered markers: `unit`, `integration`, `security`, `load`, `slow`,
`postgres`, `mysql`, `mssql`, `oracle`, `snowflake`.

Operational / runtime validation suite (requires running stack; resilience
tests need Docker access):

```bash
cd backend
python scripts/validation/run_all_tests.py
```

Individual validators live in `backend/scripts/validation/`
(`real_db_validation.py`, `concurrency_validation.py`, `memory_validation.py`,
`resilience_validation.py`).

## Backend — TypeScript (Fastify) sub-service

From `backend/` (this `package.json` is separate from the Python app):

```bash
npm install
npm run dev     # ts-node-dev on backend/src/index.ts
npm run build   # tsc -> backend/dist
npm start       # node dist/index.js
```

## Frontend

From `frontend/`:

```bash
npm install
npm run dev      # vite on 0.0.0.0:3000
npm run build    # tsc && vite build
npm run preview  # serve the built bundle on 3000
```

## Environment / secrets

- Copy `.env.example` → `.env` before first run.
- Required keys: `JWT_SECRET`, `ENCRYPTION_KEY` (32-byte base64),
  `NVIDIA_API_KEY`. `start-querybridge.ps1` auto-generates `JWT_SECRET` /
  `ENCRYPTION_KEY` when it sees the example placeholders.
- Port overrides honored by compose and the PowerShell starter: `UI_PORT`,
  `API_PORT`.

## Conventions for agents

- Do not edit files under `STABILIZATION/` or `docs/audit/` — they are
  historical reports.
- Do not commit generated artifacts: `backend/dist/`, `frontend/dist/`,
  `**/node_modules/`, `**/__pycache__/`.
- Prefer editing the Python backend (`backend/app/`) for API/runtime changes;
  the TS service under `backend/src/` is a separate surface.
- TODO: confirm canonical lint/format commands — none are wired into
  `package.json` scripts or `requirements.txt` at time of writing.
