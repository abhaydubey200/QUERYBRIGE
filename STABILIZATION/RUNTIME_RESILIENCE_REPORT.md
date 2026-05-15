# RUNTIME_RESILIENCE_REPORT - QueryBridge Enterprise

## 1. System Robustness
QueryBridge is designed to maintain operational integrity in degraded infrastructure states.

## 2. Resilience Controls
- **Connector Isolation**: Failure in one database connector does not impact the availability of other registered connections.
- **Pool Eviction**: Stale or broken connections are automatically detected and evicted from the `ConnectorFactory` registry.
- **Stateless API**: Any API instance can handle any WebSocket stream (pinned by `client_id` for the session duration), facilitating horizontal scaling.

## 3. Degraded Mode Operations
- **Offline Mode**: If a database is unreachable, the Catalog Explorer serves the last cached metadata with a "Stale" indicator.
- **AI Fallback**: If LLM services are unavailable, the system permits manual SQL input through the standard query grid.

## 4. Recovery Time Objective (RTO)
- **API Instance**: < 5 seconds.
- **Database Connector**: < 2 seconds (re-acquisition).
- **Notebook Sandbox**: < 1 second (spawn).

---
**Verified by**: Senior Infrastructure Reliability Engineer
**Date**: 2026-05-13
