
# RES Contracts (Source of Truth)

This document defines stable interfaces between modules so multiple agents can work without collisions.

## Folder ownership
- `app/` — Desktop UI (PySide6)
- `core/` — Domain + service layer
- `data/` — SQLAlchemy models, migrations, persistence
- `reports/` — KPI computations, export pipelines
- `ai/` — AI cost estimator module
- `integrations/` — notifications (Twilio/email), external APIs
- `tests/` — test infrastructure, fixtures, regression suite

> Rule: if you change an interface here, update this file in the same PR.

---

## Service layer contract (core -> app)

### Naming
- Services are pure Python classes/functions that do **not** import UI code.
- UI calls services; services call data layer + integrations.

### Example shape
- `core/services/auth.py`
  - `login(username: str, password: str) -> Session`
  - `logout(session_id: str) -> None`
- `core/services/process.py`
  - `create_process(dto) -> Process`
  - `update_process(process_id, dto) -> Process`
  - `get_dashboard_summary(filters) -> DashboardDTO`

### Error handling
- Services raise typed exceptions:
  - `ValidationError`
  - `AuthError`
  - `NotFoundError`
  - `ConflictError`
UI maps these to user-facing messages.

---

## Data layer contract (data -> core)
- SQLAlchemy models live in `data/models.py` (or `data/models/` package).
- DB session management is centralized (single factory).
- Transactions: service boundary owns commit/rollback.

---

## Integrations contract (integrations -> core)
Provide a small adapter interface, e.g.:
- `send_sms(to: str, message: str) -> MessageResult`
- `send_email(to: str, subject: str, body: str) -> MessageResult`

Core code must not depend on vendor SDK specifics.

---

## Reporting contract (reports -> core/app)
- A report is a function:
  - `build_kpi_snapshot(start: date, end: date, filters: dict) -> KPISnapshot`
- Exports:
  - `export_csv(snapshot, path) -> path`
  - `export_excel(snapshot, path) -> path`
  - `export_pdf(snapshot, path) -> path`

---

## AI module contract (ai -> core/app)
- Inference API:
  - `estimate_cost(input: EstimatorInput) -> EstimatorOutput`
- Must be deterministic for a given input unless explicitly flagged stochastic.
- Provide an evaluation harness in `ai/eval/` and unit tests with frozen fixtures.

---

## KPI definitions (fill in)
Add a table of KPIs with:
- Name
- Formula
- Data source tables/fields
- Refresh cadence
- Edge cases
