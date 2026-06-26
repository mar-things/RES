"""
RES - services/report_service.py
================================
Reporting and export helpers for time, cost, and operational KPIs.

This module keeps report generation outside the UI so dashboards, exports,
and tests all use the same SQLAlchemy-backed calculations.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.database import get_session
from core.models import Finding, Process, ProcessLog, ProcessTransition, Vehicle


@dataclass(frozen=True)
class TransitSummary:
    """Aggregated transit-time metrics grouped by destination process."""

    process_name: str
    transition_count: int
    average_minutes: float
    capacity_delay_count: int
    staff_delay_count: int


@dataclass(frozen=True)
class ProcessVarianceSummary:
    """Actual-vs-estimated time metrics grouped by process."""

    process_name: str
    completed_count: int
    estimated_hours: float
    actual_hours: float
    variance_hours: float


@dataclass(frozen=True)
class VehicleCostSummary:
    """Cost rollup for one vehicle."""

    vehicle_id: int
    plate: str
    findings_cost: float
    parts_cost: float
    approved_budget: float
    total_cost: float
    budget_remaining: float


@dataclass(frozen=True)
class KpiSnapshot:
    """Top-level operational KPI snapshot for the Reports view."""

    active_vehicle_count: int
    open_finding_count: int
    average_transit_minutes: float
    total_estimated_hours: float
    total_actual_hours: float
    total_variance_hours: float
    approved_budget_total: float
    actual_cost_total: float


def transit_time_report() -> list[TransitSummary]:
    """
    Aggregate transit times by destination process.

    Returns:
        Summaries ordered by process sequence.
    """
    with get_session() as session:
        transitions = session.query(ProcessTransition).all()
        grouped: dict[int, list[ProcessTransition]] = {}
        for transition in transitions:
            to_log = session.get(ProcessLog, transition.to_process_log_id)
            if to_log:
                grouped.setdefault(to_log.process_id, []).append(transition)

        rows = []
        for process_id, items in grouped.items():
            process = session.get(Process, process_id)
            minutes = [item.transit_minutes or 0.0 for item in items]
            rows.append((
                process.sequence_order if process else 0,
                TransitSummary(
                    process_name=process.name if process else f"Process {process_id}",
                    transition_count=len(items),
                    average_minutes=sum(minutes) / len(minutes) if minutes else 0.0,
                    capacity_delay_count=sum(1 for item in items if item.delay_reason == "capacity"),
                    staff_delay_count=sum(1 for item in items if item.delay_reason == "staff"),
                ),
            ))
        return [summary for _, summary in sorted(rows, key=lambda item: item[0])]


def process_variance_report() -> list[ProcessVarianceSummary]:
    """
    Aggregate completed actual-vs-estimated time by process.

    Returns:
        Process variance summaries ordered by sequence.
    """
    with get_session() as session:
        processes = session.query(Process).filter_by(is_active=True).order_by(Process.sequence_order)
        summaries = []
        for process in processes:
            logs = (
                session.query(ProcessLog)
                .filter_by(process_id=process.id)
                .filter(ProcessLog.checkout_time.isnot(None))
                .all()
            )
            estimated = sum(log.estimated_hours or 0.0 for log in logs)
            actual = sum(log.actual_hours or 0.0 for log in logs)
            summaries.append(ProcessVarianceSummary(
                process_name=process.name,
                completed_count=len(logs),
                estimated_hours=estimated,
                actual_hours=actual,
                variance_hours=actual - estimated,
            ))
        return summaries


def vehicle_cost_report() -> list[VehicleCostSummary]:
    """
    Build total cost summaries for all non-deleted vehicles.

    Returns:
        Vehicle cost summaries ordered by newest reception first.
    """
    with get_session() as session:
        vehicles = (
            session.query(Vehicle)
            .filter_by(is_deleted=False)
            .order_by(Vehicle.reception_date.desc())
            .all()
        )
        rows = []
        for vehicle in vehicles:
            findings_cost = sum(item.additional_cost for item in vehicle.findings)
            parts_cost = sum(item.total_cost for item in vehicle.parts_used)
            approved_budget = vehicle.approved_budget or vehicle.estimated_total_cost or 0.0
            total_cost = findings_cost + parts_cost
            rows.append(VehicleCostSummary(
                vehicle_id=vehicle.id,
                plate=vehicle.license_plate,
                findings_cost=findings_cost,
                parts_cost=parts_cost,
                approved_budget=approved_budget,
                total_cost=total_cost,
                budget_remaining=approved_budget - total_cost,
            ))
        return rows


def build_kpi_snapshot() -> KpiSnapshot:
    """
    Build the top-level KPI snapshot used by reporting dashboards.

    Returns:
        A KpiSnapshot with active queue, findings, time, and cost totals.
    """
    variances = process_variance_report()
    costs = vehicle_cost_report()
    with get_session() as session:
        active_vehicle_count = (
            session.query(ProcessLog.vehicle_id)
            .filter(ProcessLog.checkout_time.is_(None))
            .distinct()
            .count()
        )
        open_finding_count = (
            session.query(Finding)
            .filter(Finding.status.in_(["pending", "acknowledged"]))
            .count()
        )
        transit_values = [
            value for (value,) in session.query(ProcessTransition.transit_minutes).all()
            if value is not None
        ]

    estimated = sum(row.estimated_hours for row in variances)
    actual = sum(row.actual_hours for row in variances)
    return KpiSnapshot(
        active_vehicle_count=active_vehicle_count,
        open_finding_count=open_finding_count,
        average_transit_minutes=(
            sum(transit_values) / len(transit_values) if transit_values else 0.0
        ),
        total_estimated_hours=estimated,
        total_actual_hours=actual,
        total_variance_hours=actual - estimated,
        approved_budget_total=sum(row.approved_budget for row in costs),
        actual_cost_total=sum(row.total_cost for row in costs),
    )


def export_csv(path: str | Path) -> Path:
    """
    Export all report tables as one CSV file.

    Args:
        path: Destination path.

    Returns:
        The written path.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["RES Report Export", datetime.utcnow().isoformat()])
        writer.writerow([])
        writer.writerow(["Transit Time"])
        writer.writerow(["Process", "Count", "Average Minutes", "Capacity Delays", "Staff Delays"])
        for row in transit_time_report():
            writer.writerow([
                row.process_name,
                row.transition_count,
                f"{row.average_minutes:.2f}",
                row.capacity_delay_count,
                row.staff_delay_count,
            ])
        writer.writerow([])
        writer.writerow(["Actual vs Estimated"])
        writer.writerow(["Process", "Completed", "Estimated Hours", "Actual Hours", "Variance Hours"])
        for row in process_variance_report():
            writer.writerow([
                row.process_name,
                row.completed_count,
                f"{row.estimated_hours:.2f}",
                f"{row.actual_hours:.2f}",
                f"{row.variance_hours:.2f}",
            ])
        writer.writerow([])
        writer.writerow(["Vehicle Costs"])
        writer.writerow(["Plate", "Findings", "Parts", "Budget", "Total", "Budget Remaining"])
        for row in vehicle_cost_report():
            writer.writerow([
                row.plate,
                f"{row.findings_cost:.2f}",
                f"{row.parts_cost:.2f}",
                f"{row.approved_budget:.2f}",
                f"{row.total_cost:.2f}",
                f"{row.budget_remaining:.2f}",
            ])
    return output


def export_excel(path: str | Path) -> Path:
    """
    Export a spreadsheet-compatible CSV file.

    The project avoids a hard Excel writer dependency in the desktop MVP;
    Excel opens the generated CSV directly.
    """
    return export_csv(path)


def export_pdf(path: str | Path) -> Path:
    """
    Export a compact text-based PDF report without third-party dependencies.

    Args:
        path: Destination path.

    Returns:
        The written path.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_kpi_snapshot()
    lines = [
        "RES KPI Report",
        f"Generated UTC: {datetime.utcnow().isoformat()}",
        f"Active vehicles: {snapshot.active_vehicle_count}",
        f"Open findings: {snapshot.open_finding_count}",
        f"Average transit minutes: {snapshot.average_transit_minutes:.2f}",
        f"Time variance hours: {snapshot.total_variance_hours:.2f}",
        f"Approved budget total: {snapshot.approved_budget_total:.2f}",
        f"Actual cost total: {snapshot.actual_cost_total:.2f}",
    ]
    content = "\\n".join(lines)
    stream = f"BT /F1 12 Tf 50 760 Td ({content}) Tj ET"
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "trailer << /Root 1 0 R /Size 6 >>\nstartxref\n0\n%%EOF\n"
    )
    output.write_text(pdf, encoding="latin-1")
    return output
