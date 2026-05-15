# API_CONVERGENCE_REPORT - QueryBridge Enterprise

## 1. Router Mounting Status
All core modules are correctly mounted in `main.py`.

| Router | Prefix | Status |
| :--- | :--- | :--- |
| `auth` | `/api/v1/auth` | **MOUNTED** |
| `connections` | `/api/v1/connections` | **MOUNTED** |
| `ai` | `/api/v1/ai` | **MOUNTED** |
| `catalog` | `/api/v1/catalog` | **MOUNTED** |
| `semantic` | `/api/v1/semantic` | **MOUNTED** |
| `notebooks` | `/api/v1/notebooks` | **MOUNTED** |
| `websocket` | `/api/v1/ws` | **MOUNTED** |

## 2. API Integrity Issues
- **Semantic Endpoint**: Returns full list of metrics via sync session.
- **Workspaces/Plugins**: Currently use sync database queries in the route handler.
- **Response Models**: Inconsistent usage of Pydantic models across secondary routers (Plugins/Workspaces).

## 3. Recommended Actions
1.  **Refactor Routers**: Convert all `db.query` calls to `await db.execute(select(...))` using `AsyncSession`.
2.  **Standardize Responses**: Enforce a unified `APIResponse` envelope for all endpoints.

---
**Auditor**: Senior Platform Engineer
**Date**: 2026-05-13
