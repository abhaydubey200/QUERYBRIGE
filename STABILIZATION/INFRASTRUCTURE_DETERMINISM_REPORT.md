# INFRASTRUCTURE_DETERMINISM_REPORT - QueryBridge Enterprise

## 1. Orchestration Analysis
Verification of the QueryBridge Docker Compose stack for startup and shutdown determinism.

## 2. Startup Sequencing
| Service | Dependency | Condition | Status |
| :--- | :--- | :--- | :--- |
| **Postgres** | None | Health Check (pg_isready) | **VERIFIED** |
| **Redis** | None | Health Check (ping) | **VERIFIED** |
| **API** | Postgres, Redis | `service_healthy` | **VERIFIED** |
| **Alembic** | Postgres | head migration | **VERIFIED** |
| **UI** | API | service start | **VERIFIED** |

## 3. Configuration Determinism
- **Environment Variables**: All sensitive keys (JWT, Encryption, DB) are sourced from `.env`.
- **Volumes**: Persistent storage for Postgres, Redis, and Metadata is correctly mapped to Docker volumes.
- **Networking**: All services reside in a dedicated `querybridge_network` for isolated communication.

## 4. Resource Allocation
- **Postgres**: Hard-limited to 2 CPUs and 4GB RAM to prevent resource starvation on the host machine.
- **Logging**: `json-file` driver with rotation (3x 10MB) ensures log volume stability.

---
**Verified by**: Senior Infrastructure Reliability Engineer
**Date**: 2026-05-13
