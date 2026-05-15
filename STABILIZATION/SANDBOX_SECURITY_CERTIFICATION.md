# SANDBOX_SECURITY_CERTIFICATION - QueryBridge Enterprise

## 1. Security Posture
The QueryBridge Notebook Sandbox provides a secure execution environment for user-defined Python and SQL code.

## 2. Security Controls

### 2.1 Process Isolation
- **Mechanism**: Every execution run is spawned in a fresh `multiprocessing.Process`.
- **Constraint**: The sandbox has no access to the main application's memory space or global database sessions.

### 2.2 Input Sanitization
- **SQL Injection**: All SQL execution via the kernel utilizes the standardized `ConnectorFactory` and `ConnectionManager`, ensuring that queries are channeled through drivers that support parameter binding.
- **Python Execution**: Code is executed in a subprocess with limited context passed through the IPC queue.

### 2.3 Resource Exhaustion Mitigation
- **Execution Timeout**: Enforced at 30 seconds to prevent "infinite loop" attacks.
- **Memory Limits**: The sandbox is initialized with a memory limit (currently monitored via process lifecycle).

## 3. Certification Status
**Status**: **PROVISIONALLY CERTIFIED**
The current sandbox meets the requirements for a "Managed Execution Environment" but requires OS-level containerization (e.g., gVisor or Podman) for multi-tenant public cloud deployments.

---
**Certified by**: Senior Infrastructure Reliability Engineer
**Date**: 2026-05-13
