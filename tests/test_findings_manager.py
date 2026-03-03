"""Unit tests for the findings manager and service.

These tests exercise the core reporting, acknowledgment and approval
logic. An in-memory SQLite database is used to avoid touching the
real workspace data.
"""

import os
import importlib
from datetime import datetime

# Force an in-memory database before any module that reads AppConfig is imported
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import config
import core.database

# reload to ensure new settings take effect
importlib.reload(config)
importlib.reload(core.database)

from core.database import init_db, get_session
from core.models import Customer, Vehicle, Process, ProcessLog
from services.findings_service import report_finding as svc_report
from core.findings_manager import (
    report_finding as mgr_report,
    acknowledge_finding,
    approve_finding,
    reject_finding,
    get_findings_for_vehicle,
    list_pending_findings_for_insurer,
)


def setup_module(module):
    """Create schema and seed a minimal vehicle/process for testing."""
    init_db()
    with get_session() as session:
        cust = Customer(full_name="Test User", phone_whatsapp="+10000000000")
        session.add(cust)
        session.flush()
        veh = Vehicle(
            license_plate="TEST-1",
            make="Make",
            model="Model",
            customer_id=cust.id,
            current_status="reception",
        )
        session.add(veh)
        session.flush()
        pr = Process(name="Reception", sequence_order=1, max_capacity=1)
        session.add(pr)
        session.flush()
        log = ProcessLog(
            vehicle_id=veh.id,
            process_id=pr.id,
            checkin_time=datetime.utcnow(),
            status="in_progress",
        )
        session.add(log)
        session.flush()
        module.vehicle_id = veh.id
        module.process_log_id = log.id
        module.insurer_id = None  # vehicle has no insurer yet


def test_report_and_acknowledge_flow():
    # reporting via manager
    f = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Scratch on bumper",
        additional_cost=150.0,
    )
    assert f.id is not None
    assert f.status == "pending"

    # acknowledge
    f2 = acknowledge_finding(f.id)
    assert f2.status == "acknowledged"
    assert f2.insurance_acknowledged_at is not None

    # approve
    f3 = approve_finding(f.id, approved_by_name="Inspector A")
    assert f3.status == "approved"
    assert f3.approved_by == "Inspector A"

    # retrieval
    all_for_veh = get_findings_for_vehicle(vehicle_id)
    assert len(all_for_veh) == 1


def test_service_notification_shortcircuit(monkeypatch):
    # monkeypatch notification to avoid external dependencies
    sent = {}

    def fake_notify(vehicle_id, plate, customer_phone):
        sent['called'] = True

    monkeypatch.setattr('services.findings_service.notify_finding', fake_notify)

    f = svc_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Another issue",
        additional_cost=75.0,
    )
    assert sent.get('called', False) is True


def test_pending_list_returns_empty_for_no_insurer():
    # since vehicle has no insurer, list should be empty
    results = list_pending_findings_for_insurer(insurance_company_id=0)
    assert isinstance(results, list)
    assert len(results) == 0

def test_pending_list_with_matching_insurer():
    # create an insurance company and associate to vehicle
    with get_session() as session:
        from core.models import InsuranceCompany
        ins = InsuranceCompany(name="TestIns")
        session.add(ins)
        session.flush()
        veh = session.query(Vehicle).get(vehicle_id)
        veh.insurance_company_id = ins.id
        session.flush()

    # report a new finding
    f = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Insurer test",
        additional_cost=20.0,
    )
    # now list pending for that insurer via the manager helper
    results = list_pending_findings_for_insurer(ins.id)
    # there may be other pending findings from earlier tests; ensure ours is included
    assert any(item.id == f.id for item in results)
    assert len(results) >= 1
