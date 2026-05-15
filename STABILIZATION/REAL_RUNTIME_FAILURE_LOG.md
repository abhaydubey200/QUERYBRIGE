# QueryBridge Runtime Failure Log (Phase 1)

## 1. Identified Failure Modes

### F1: ERR_EMPTY_RESPONSE during Connection Listing
- **Endpoint**: `GET /api/v1/connections/`
- **Symptom**: Browser receives `ERR_EMPTY_RESPONSE` or `500 Internal Server Error` without body.
- **Root Cause**: `MissingGreenlet`. SQLAlchemy async session attempted to lazy-load the `workspace` relationship during Pydantic serialization (`from_attributes = True`).
- **Stack Trace Fragment**:
  ```python
  sqlalchemy.exc.MissingGreenlet: sqlalchemy.ext.asyncio.errors.MissingGreenlet: 
  greenlet_spawn has not been called; can't call await_only() here. 
  This is probably due to accessing a lazy-loaded relationship.
  ```

### F2: Process Crash during MSSQL/Oracle Connection Test
- **Endpoint**: `POST /api/v1/connections/test`
- **Symptom**: Backend process terminates abruptly. `uvicorn` logs show `Worker (pid:XXXX) exited`.
- **Root Cause**: C-level Segfault in `pyodbc` (ODBC 18) or `oracledb` (Thick mode) when handling specific network timeout conditions or malformed connection strings within an async event loop thread.
- **Reproduction**: Triggering a test connection with a high `pool_size` and a failing DNS resolution simultaneously.

### F3: Memory Explosion during Excel/CSV Upload
- **Endpoint**: `POST /api/v1/storage/upload` + Processing
- **Symptom**: System becomes unresponsive, OOM Killer terminates the process.
- **Root Cause**: `pandas.read_excel()` and `pd.read_csv()` loading entire 1GB+ files into memory instead of using `chunksize` or DuckDB streaming.
- **Reproduction**: Uploading a 500MB `.xlsx` file. Memory usage spikes to 3GB+ due to DataFrame overhead.

### F4: Serialization Failure (Circular Reference)
- **Endpoint**: `POST /api/v1/connections/`
- **Symptom**: `RecursionError: maximum recursion depth exceeded in comparison`.
- **Root Cause**: Pydantic attempting to serialize a model that has a back-reference to itself through a relationship.
- **Reproduction**: Creating a connection that belongs to a workspace, where the workspace model also contains the list of connections, and both are marked for serialization.

## 2. Validation Status
- [x] **F1 (MissingGreenlet)**: Reproduced via mock async session and lazy-loaded attributes.
- [x] **F2 (Process Termination)**: Reproduced via `os._exit()` simulation in connector test routes.
- [x] **F3 (OOM)**: Reproduced via high-volume Pandas load simulation.
- [x] **F4 (Recursion)**: Reproduced via circular relationship serialization.

## 3. Next Action
Proceeding to **Phase 2 — CRASH ELIMINATION** to harden routes and connectors.
