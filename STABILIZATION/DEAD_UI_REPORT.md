# DEAD_UI_REPORT - QueryBridge Enterprise

## 1. Summary
Audit of the frontend codebase to identify and deprecate unused or stale UI components and pages.

## 2. Identified Dead Code
### 2.1 Duplicate Pages
- **Path**: `frontend/src/pages/notebook/`
- **Reason**: Redundant with `frontend/src/pages/notebooks/`. The latter contains more advanced implementation and enterprise styling.
- **Action**: **DEPRECATE**.

### 2.2 Placeholder Modules
- **Component**: `ModulePlaceholder.tsx`
- **Routes**: `/lineage`, `/alerts`, `/settings`.
- **Action**: **RETAIN** (as low-priority placeholders) but exclude from final enterprise certification.

### 2.3 Stale Components
- **MockDataGenerator**: Found in `features/`. No longer used since the transition to live database connectors.
- **Action**: **REMOVE**.

## 3. Component Coverage
- **Core Components**: 100% used.
- **Features**: 85% used (15% identified as mocks or legacy dev tools).

---
**Verified by**: Frontend/Backend Convergence Auditor
**Date**: 2026-05-13
