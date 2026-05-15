# STREAMING_LIFECYCLE_REPORT - QueryBridge Enterprise

## 1. Lifecycle States
1.  **INITIATED**: WS handshake complete, query payload received.
2.  **PRE-FLIGHT**: Connection config loaded, PII detector initialized.
3.  **EXECUTING**: Query dispatched to database driver.
4.  **STREAMING**: `AsyncGenerator` yielding rows; `WebSocketManager` batching.
5.  **COMPLETED**: All rows sent, stream stats broadcast.
6.  **DISCONNECTED**: Resource cleanup performed.

## 2. Resource Management
- **Memory Pressure**: Row batches are cleared immediately after `send_json`, preventing heap accumulation.
- **Connection Health**: Database pools are managed by `ConnectorFactory`; connections are returned to the pool immediately after the generator exhausts.
- **Backpressure**: `asyncio.sleep(0.01)` between batches ensures the event loop remains responsive to other clients.

## 3. Failure Conditions Verified
- **Slow Client**: WS buffers handle small delays; persistent slow consumers are disconnected to prevent backend memory leaks.
- **Database Timeout**: `ConnectionManager` enforces a strict timeout, raising `TimeoutError` and closing the stream gracefully.
- **Interruption**: Browser refresh triggers `WebSocketDisconnect`, which cancels the backend streaming task.

---
**Verified by**: Real-Time Systems Reliability Engineer
**Date**: 2026-05-13
