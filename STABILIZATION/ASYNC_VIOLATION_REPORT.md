# ASYNC_VIOLATION_REPORT - QueryBridge Enterprise

## 1. Critical Violations
The following files contain blocking code that will freeze the FastAPI event loop under load.

| Location | Code Pattern | Risk |
| :--- | :--- | :--- |
| `semantic/metric_registry.py` | `self.db.query(...)` | Database I/O on Event Loop |
| `api/endpoints/semantic.py` | `db.query(...)` | Database I/O on Event Loop |
| `services/lineage_engine.py` | `self.db.query(...)` | Database I/O on Event Loop |
| `notebook/kernel.py` | `time.sleep` (potential) | Thread-blocking latency |

## 2. Event Loop Safety Audit
- **LLM Calls**: Currently non-blocking via `httpx`.
- **Database (Core)**: `AsyncSession` is implemented for `connections` and `auth`, but secondary tables are still using legacy sync patterns.
- **WebSocket**: Streaming is async-native, but row masking (`PIIDetector`) must be verified for performance.

## 3. Remediation Plan
- **MANDATORY**: Replace all `db.query` with `AsyncSession.execute`.
- **MANDATORY**: Ensure all service methods are `async def`.

---
**Auditor**: Senior Async Systems Engineer
**Date**: 2026-05-13
