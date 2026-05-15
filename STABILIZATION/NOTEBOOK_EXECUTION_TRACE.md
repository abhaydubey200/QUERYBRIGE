# NOTEBOOK_EXECUTION_TRACE - QueryBridge Enterprise

## 1. Trace Overview
This document traces the execution of Python and SQL code cells within the isolated QueryBridge Notebook Runtime.

## 2. Request Lifecycle
| Layer | Component | Logic | Async State |
| :--- | :--- | :--- | :--- |
| **Frontend** | `NotebookCell.tsx` | POST /execute/{notebook_id} | **Async** |
| **API** | `notebooks.py` | Calls kernel.execute() | **Async** |
| **Kernel** | `NotebookKernel` | Orchestrates Python/SQL routing | **Async** |
| **Isolation** | `NotebookSandbox` | fresh `multiprocessing.Process` | **Async (Monitor)** |
| **Execution** | `exec()` / `driver` | Runs code in sub-process | **Sync (Internal)** |
| **Result** | `Queue` | Collects stdout/stderr/data | **Async (Collect)** |
| **UI** | `Renderer` | Displays results in cell output | **Async** |

## 3. Runtime Boundaries
- **Process Boundary**: Hard separation between API (Parent) and Sandbox (Child).
- **Network Boundary**: Sandbox has restricted network access (unless explicitly enabled for connectors).
- **Governance Boundary**: SQL execution via kernel follows the 1,000 row hard limit.

## 4. Verification Results
- **Async Execution**: API is non-blocking while waiting for results due to `await asyncio.sleep(0.1)` in the monitor loop.
- **Process Cleanup**: `finally` block in `sandbox.py` ensures processes are terminated even on error.
- **Timeout**: Verified 30s wall-clock termination.

---
**Verified by**: Principal Distributed Systems Engineer
**Date**: 2026-05-13
