# SQL_EXECUTION_TRACE - QueryBridge Enterprise

## 1. Trace Overview
This document traces the complete execution lifecycle of a SQL query from the Frontend UI to the Database and back through the Real-Time Streaming Engine.

## 2. Request Lifecycle
| Layer | Component | Logic | Async State |
| :--- | :--- | :--- | :--- |
| **Frontend** | `QueryGrid.tsx` | Dispatches query via WebSocket | **Async** |
| **Transport** | `WebSocket` | JSON Payload over secure socket | **Async** |
| **API** | `websocket.py` | Receives query, validates session | **Async** |
| **Orchestration**| `ConnectionManager` | Loads config, checks read-only | **Async** |
| **Connector** | `ConnectorFactory` | Acquires async-native driver | **Async** |
| **Database** | `asyncpg/aioodbc` | Executes query on remote server | **Async** |
| **Streaming** | `AsyncGenerator` | Yields rows as they arrive | **Async** |
| **Transport** | `WebSocketManager`| Batches rows and pushes to UI | **Async** |

## 3. Runtime Boundaries
- **API Boundary**: FastAPI endpoint maintains the connection.
- **Driver Boundary**: `asyncpg` manages the low-level socket to Postgres.
- **Governance Boundary**: `PIIDetector` applies masking in-stream before rows leave the backend.

## 4. Verification Results
- **Async Ownership**: Fully non-blocking. No `time.sleep` or sync drivers detected in the path.
- **Stream Chunking**: Adaptive batching (50-500 rows) is active.
- **Cancellation**: WS disconnect successfully triggers `task.cancel()` in the streaming generator.

---
**Verified by**: Enterprise Runtime Validation Architect
**Date**: 2026-05-13
