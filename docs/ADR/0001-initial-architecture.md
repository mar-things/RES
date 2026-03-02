
# ADR 0001: Initial architecture

## Status
Accepted

## Context
RES is a desktop-first application with role-based access, dashboards, reporting, and an AI cost estimator module.

## Decision
- Use a monorepo with clear module boundaries: `app/`, `core/`, `data/`, `reports/`, `ai/`, `integrations/`.
- Desktop UI is PySide6 (Qt Widgets).
- Start with SQLite for local-first deployment; keep a clean path to Postgres for later.
- Service-layer architecture: UI calls `core/services/*`, which own transactions and call data/integrations.

## Consequences
- Faster development and offline capability now.
- Requires discipline on service boundaries and contracts to avoid tight coupling.
