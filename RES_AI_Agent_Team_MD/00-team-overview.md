# RES AI Agent Team Overview

Project: **RES — Repair Execution System** (Python + PySide6 + SQLAlchemy)

This team is sized to cover:
- Core process tracking + audit trails
- Multi-role desktop UI (workshop, insurance, kiosk)
- Notifications (MVP local, prod Twilio)
- Reporting/KPIs + exports
- Security + packaging + deployment
- Tests/QA
- Future AI Cost Estimator subproject

## Recommended team size: **7 AI agents**

1. **Product & Domain Lead (PM/BA)**
2. **Core Backend Engineer (Process/DB)**
3. **Desktop UI Engineer (PySide6/Qt)**
4. **Reporting & Analytics Engineer (KPIs/Exports)**
5. **Security & Release Engineer (Hardening/Packaging/Deploy)**
6. **QA & Test Automation Engineer**
7. **AI Cost Estimator Engineer (Vision/ML integration; Phase 6)**

## Coordination rules
- Single source of truth: `implementation_plan.md` and the repo.
- Every PR/change must include: docstrings, type hints where useful, and tests for new core logic.
- All UI strings must be translatable (Qt i18n).
- No data deletion; use soft deletes/audit tables per plan.

## Definition of Done (DoD)
- Feature works end-to-end in the desktop app.
- DB migrations/seeds updated if schema changed.
- Unit tests added/updated and passing.
- Logs/audit trails recorded where applicable.
- UI text is i18n-ready.
- Short developer note in `walkthrough.md` or module docstring.
