# RES Development Status

This document tracks the current implementation focus after the graph-assisted
project review. It is intentionally practical: it records what is stable, what
is risky, and which development lane should own the next work.

## Current Focus

The project is past the initial MVP scaffold and is now in the workflow
completion stage. The highest priority is to make the repair lifecycle correct
and enforce role boundaries before adding reporting, parts, production
messaging, kiosk mode, or AI cost estimation.

## Development Lanes

### Backend Workflow

Owns `core/process_engine.py`, `core/capacity_tracker.py`,
`core/time_tracker.py`, and `core/rollback_manager.py`.

Completed in the latest batch:
- Made rollback atomic across audit creation, source checkout, target check-in,
  and transition creation.
- Added manager/admin approval validation inside the rollback core.
- Restricted rollback targets to prior, active, severity-applicable processes.
- Blocked rollback into a full target bay before any mutation occurs.
- Added focused rollback regression tests.

Next work:
- Enforce one open `ProcessLog` per vehicle.
- Enforce legal process routing from the seeded process sequence.
- Align capacity behavior with the planned waiting states.
- Add tests for process, capacity, and time invariants.

### Insurance And Findings

Owns `core/findings_manager.py`, `services/findings_service.py`, and
`ui/insurance_dashboard.py`.

Completed in the current batch:
- Fixed the service wrapper for insurer finding queues.
- Kept acknowledged findings visible until they are approved or rejected.
- Added insurer-scoped acknowledge, approve, and reject APIs.
- Updated the insurance dashboard to use scoped mutations.
- Added regression tests for cross-insurer mutation protection.

Next work:
- Add UI-level tests for insurance dashboard behavior.
- Add notification tests proving only customers receive WhatsApp/SMS messages.
- Replace legacy `Query.get()` calls with `Session.get()` during the next
  SQLAlchemy cleanup pass.

### Desktop UI

Owns `ui/main_window.py`, dashboard wiring, and missing views/dialogs.

Completed in the current batch:
- Changed the main window to build protected pages only when the role can
  access them.
- Prevented insurance viewers from landing on the workshop dashboard.
- Added page-level navigation guards instead of relying only on hidden buttons.

Completed in the latest batch:
- Added `ui/dialogs/rollback_dialog.py`.
- Wired the dashboard rollback action to the correct dialog path.
- Hid rollback actions from non-manager/admin users.

Next work:
- Add `ui/vehicle_detail_view.py` as the workflow hub for process history,
  findings, rollback history, and role-specific actions.
- Move more action entry points from vehicle cards into the detail view.

### Testing And Release Readiness

Owns test coverage, CI gates, and packaging readiness.

Current state:
- Focused findings and rollback tests pass.
- Ruff passes for files touched in the findings and rollback stabilization
  batches.

Next work:
- Add tests for process engine, capacity tracker, time tracker, auth, and role
  isolation.
- Keep `mypy` non-blocking until current errors are triaged, then make it a
  blocking CI gate.
- Add coverage, i18n string, docstring, and packaging gates after core
  workflow tests are in place.

## Deferrals

Defer these until workflow correctness and role isolation are stable:
- AI cost estimator implementation.
- Parts inventory and supplier workflows.
- PDF/Excel exports.
- Kiosk display.
- Twilio production messaging.
- PyInstaller release packaging.
