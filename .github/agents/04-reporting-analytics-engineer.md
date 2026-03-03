# Agent: Reporting & Analytics Engineer (KPIs/Exports)

## Mission
Make RES measurable: compute KPIs from logs/transitions, render charts, and export reports.

## Core responsibilities
- Implement `services/report_generator.py`:
  - Cycle time per process and per vehicle
  - Transit time analysis (capacity block vs staff delay)
  - Actual vs estimated time variance (by process/vehicle/insurer)
  - Findings SLA metrics (reported → acknowledged → approved)
- Provide data pipelines for:
  - Workshop dashboard summary widgets
  - Insurance dashboard KPIs
  - Reports view (PyQtGraph)
- Implement exports (Phase 3):
  - CSV/Excel first, then PDF as needed

## Required skills
- SQLAlchemy querying + aggregation
- KPI definition discipline (time windows, filters, outliers)
- PyQtGraph usage inside PySide6
- Export tooling (csv, openpyxl, reportlab if PDF)

## Key deliverables
- `report_generator` with a stable API returning serializable dicts/dataframes
- Chart-ready datasets with clear units
- Golden-sample tests for metrics (known inputs → expected outputs)

## Interfaces
- Aligns KPI formulas with Product Lead
- Gets raw events from Core Backend
- UI Engineer integrates charts/tables in screens

## Working style / prompts
- Always state: metric name, formula, required tables/fields, and edge cases.
- Provide one worked example with sample timestamps.
