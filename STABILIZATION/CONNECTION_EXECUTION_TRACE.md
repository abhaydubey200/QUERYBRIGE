# CONNECTION EXECUTION TRACE

## 1. Overview
This document traces the end-to-end execution flow of connection management in QueryBridge, from the React frontend to the Python backend runtime and database connectors.

## 2. Component Flow Map

### Frontend Layer
- **ConnectionDashboard.tsx**: Initial entry point. Triggers `fetchConnections()` on mount.
- **ConnectionWizard.tsx**: multi-step form for creating and testing connections.
- **connectionStore.ts**: Zustand store for state management.
- **API Client**: standard `fetch` calls to `${API_URL}/connections`.

### API Layer (FastAPI)
- **main.py**: entry point, middleware stack (CORS, Metrics, Security), router registration.
- **api/endpoints/connections.py**: Route handlers for LIST, CREATE, TEST, DELETE.
- **db/session.py**: Async database session management (`get_db`).

### Service Layer
- **services/connection_manager.py**: Core business logic. Handles encryption/decryption, workspace isolation, and metadata discovery.
- **connectors/connector_factory.py**: singleton factory for connector instantiation and pool caching.

### Connector Layer
- **base_connector.py**: Abstract base class defining the connector contract.
- **postgres_connector.py**: asyncpg-based PostgreSQL driver.
- **mysql_connector.py**: aiomysql-based MySQL driver.
- **mssql_connector.py**: aioodbc-based MSSQL driver.
- **oracle_connector.py**: oracledb-based Oracle driver (Thin mode).
- **snowflake_connector.py**: snowflake-connector-python wrapper.
- **file_connector.py**: DuckDB/Pandas-based file processor.

## 3. Detailed Execution Traces

### Trace A: List Connections (`GET /api/v1/connections`)
1. **Frontend**: `ConnectionDashboard` calls `fetch('/api/v1/connections/')`.
2. **Backend**: `MetricsMiddleware` starts timer.
3. **Backend**: `list_connections` endpoint is invoked.
4. **Backend**: `AsyncSession` is yielded from `get_db`.
5. **Backend**: `select(DBConnection)` is executed.
6. **Backend**: Pydantic validates `DBConnection` objects into `ConnectionResponse`.
7. **Potential Failure**: Lazy-loading of relationships (`workspace`, `ssl_config`) during serialization in an async session context.

### Trace B: Test Connection (`POST /api/v1/connections/test`)
1. **Frontend**: `ConnectionWizard` calls `handleTest()`.
2. **Backend**: `test_connection` endpoint receives payload.
3. **Backend**: `ConnectionManager.test_connection` is called.
4. **Backend**: `ConnectorFactory.get_connector` returns a transient instance.
5. **Connector**: `connector.test_connection()` is awaited.
6. **Connector**: Driver attempts network handshake and simple query (`SELECT 1` or version).
7. **Potential Failure**: Driver-level crash (segfault) in `pyodbc` or `oracledb` if dependencies are missing, or unhandled async timeout.

### Trace C: Create Connection (`POST /api/v1/connections/`)
1. **Frontend**: `ConnectionWizard` calls `handleSave()`.
2. **Backend**: `create_connection` endpoint receives payload.
3. **Backend**: `ConnectionManager.create_connection` is called.
4. **Service**: Password is encrypted via `encryption_service`.
5. **Service**: Workspace check/creation logic runs.
6. **Service**: `DBConnection` is added to session and committed.
7. **Potential Failure**: Encryption key mismatch or database constraint violation.

## 4. Runtime Observability
- **Logs**: Handled by `loguru`.
- **Metrics**: Exported to Prometheus via `MetricsMiddleware`.
- **Audit**: Logged to `audit_logs` table via `ConnectionManager`.
