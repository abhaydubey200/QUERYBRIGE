# RESOURCE_GOVERNOR_REPORT - QueryBridge Enterprise

## 1. Governance Policy
QueryBridge Enterprise enforces strict resource limits on data extraction and code execution to protect system availability.

## 2. Enforced Limits

### 2.1 Data Retrieval Limits
- **Notebook SQL Cells**: Hard limit of **1000 rows** per execution to prevent UI and memory crashes.
- **WebSocket Streams**: Configurable batching (50-500 rows) with backpressure to protect browser memory.
- **Catalog Refresh**: Chunked schema discovery to prevent database lock contention.

### 2.2 Execution Limits
- **Notebook Cells (Python)**: **30 second** wall-clock timeout.
- **Memory Ceiling**: 512MB per sandbox instance (configured in `NotebookKernel`).

### 2.3 Connection Governance
- **Pool Sizing**: Managed via `ConnectionConfig.pool_size` per database.
- **Cleanup**: Automatic eviction of stale connectors via `ConnectorFactory.cleanup()`.

## 3. Violation Handling
- **Overflow**: Truncated with "Limit Reached" notification.
- **Timeout**: Process termination with `HTTP 408` or equivalent error payload.

---
**Certified by**: Senior Platform Reliability Engineer
**Date**: 2026-05-13
