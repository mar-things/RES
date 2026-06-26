"""Tests for inventory, cost, and reporting services."""

import os
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.database import Base, engine, get_session, init_db  # noqa: E402
from core.models import Customer, Finding, Process, ProcessLog, ProcessTransition, Vehicle  # noqa: E402
from services.parts_service import create_part, create_supplier, record_part_used, vehicle_parts_cost  # noqa: E402
from services.report_service import (  # noqa: E402
    build_kpi_snapshot,
    export_csv,
    export_pdf,
    process_variance_report,
    transit_time_report,
    vehicle_cost_report,
)


def _seed_reporting_data():
    """Create a completed process, transition, finding, and vehicle."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    with get_session() as session:
        customer = Customer(full_name="Report Customer", phone_whatsapp="+15550000001")
        session.add(customer)
        session.flush()
        vehicle = Vehicle(
            license_plate="RPT-1",
            make="Toyota",
            model="Corolla",
            customer_id=customer.id,
            crash_severity="LOW",
            approved_budget=1000.0,
        )
        process_a = Process(name="Reception", sequence_order=1, std_hours_estimate=1.0)
        process_b = Process(name="Paint", sequence_order=2, std_hours_estimate=2.0)
        session.add_all([vehicle, process_a, process_b])
        session.flush()
        log_a = ProcessLog(
            vehicle_id=vehicle.id,
            process_id=process_a.id,
            checkin_time=datetime.utcnow() - timedelta(hours=2),
            checkout_time=datetime.utcnow() - timedelta(hours=1),
            estimated_hours=1.0,
            actual_hours=1.0,
            status="completed",
        )
        log_b = ProcessLog(
            vehicle_id=vehicle.id,
            process_id=process_b.id,
            checkin_time=datetime.utcnow(),
            estimated_hours=2.0,
            status="in_progress",
        )
        session.add_all([log_a, log_b])
        session.flush()
        session.add(ProcessTransition(
            vehicle_id=vehicle.id,
            from_process_log_id=log_a.id,
            to_process_log_id=log_b.id,
            transit_minutes=30.0,
            delay_reason="staff",
        ))
        session.add(Finding(
            vehicle_id=vehicle.id,
            process_log_id=log_b.id,
            description="Bumper damage",
            additional_cost=250.0,
            status="pending",
        ))
        return vehicle.id


def test_parts_usage_decrements_stock_and_rolls_up_cost():
    """Recording parts used updates inventory and vehicle cost summary."""
    vehicle_id = _seed_reporting_data()
    supplier = create_supplier("Parts Co")
    part = create_part("Bumper", unit_cost=120.0, stock_quantity=3, supplier_id=supplier.id)

    used = record_part_used(vehicle_id, part.id, quantity=2)
    summary = vehicle_parts_cost(vehicle_id)

    assert used.total_cost == 240.0
    assert summary.total_parts_cost == 240.0
    assert summary.line_count == 1
    with get_session() as session:
        assert session.get(type(part), part.id).stock_quantity == 1


def test_reports_include_time_transit_cost_and_exports(tmp_path):
    """Report services aggregate seeded operational data and write exports."""
    vehicle_id = _seed_reporting_data()
    part = create_part("Clip", unit_cost=10.0, stock_quantity=5)
    record_part_used(vehicle_id, part.id, quantity=2)

    transit = transit_time_report()
    variance = process_variance_report()
    costs = vehicle_cost_report()
    snapshot = build_kpi_snapshot()

    assert transit[0].average_minutes == 30.0
    assert any(row.completed_count == 1 for row in variance)
    assert costs[0].total_cost == 270.0
    assert snapshot.open_finding_count == 1

    csv_path = export_csv(tmp_path / "report.csv")
    pdf_path = export_pdf(tmp_path / "report.pdf")
    assert csv_path.exists()
    assert pdf_path.exists()
