"""Unit tests for the findings manager and service.

These tests exercise the core reporting, acknowledgment and approval
logic. An in-memory SQLite database is used to avoid touching the
real workspace data.
"""

import os
from datetime import datetime

# Force an in-memory database before any module that reads AppConfig is imported
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.database import init_db, get_session  # noqa: E402
from core.models import Customer, Vehicle, Process, ProcessLog  # noqa: E402
from services.findings_service import (  # noqa: E402
    report_finding as svc_report,
    list_pending_for_insurer as svc_list_pending_for_insurer,
    acknowledge_finding_for_insurer as svc_ack_for_insurer,
    approve_finding_for_insurer as svc_approve_for_insurer,
    reject_finding_for_insurer as svc_reject_for_insurer,
)
from core.findings_manager import (  # noqa: E402
    report_finding as mgr_report,
    acknowledge_finding,
    approve_finding,
    get_findings_for_vehicle,
    list_pending_findings_for_insurer,
    acknowledge_finding_for_insurer,
    approve_finding_for_insurer,
    reject_finding_for_insurer,
)

vehicle_id = 0
process_log_id = 0


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

    svc_report(
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


def test_acknowledged_findings_remain_visible_until_resolution():
    """Acknowledged findings stay in the insurer queue until approved/rejected."""
    with get_session() as session:
        from core.models import InsuranceCompany
        ins = InsuranceCompany(name="AckFlowIns")
        session.add(ins)
        session.flush()
        veh = session.query(Vehicle).get(vehicle_id)
        veh.insurance_company_id = ins.id
        session.flush()
        insurer_id = ins.id

    finding = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Ack flow finding",
        additional_cost=50.0,
    )

    acknowledged = acknowledge_finding_for_insurer(finding.id, insurer_id)
    assert acknowledged.status == "acknowledged"

    unresolved = list_pending_findings_for_insurer(insurer_id)
    assert any(item.id == finding.id for item in unresolved)

    approved = approve_finding_for_insurer(finding.id, insurer_id, "Adjuster A")
    assert approved.status == "approved"

    unresolved_after_approval = list_pending_findings_for_insurer(insurer_id)
    assert all(item.id != finding.id for item in unresolved_after_approval)


def test_insurer_scoped_mutations_reject_other_insurer_findings():
    """Insurer actions cannot mutate findings for another insurer's vehicle."""
    with get_session() as session:
        from core.models import InsuranceCompany
        insurer_a = InsuranceCompany(name="Scoped A")
        insurer_b = InsuranceCompany(name="Scoped B")
        session.add_all([insurer_a, insurer_b])
        session.flush()
        veh = session.query(Vehicle).get(vehicle_id)
        veh.insurance_company_id = insurer_a.id
        session.flush()
        insurer_a_id = insurer_a.id
        insurer_b_id = insurer_b.id

    finding = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Scoped finding",
        additional_cost=30.0,
    )

    try:
        acknowledge_finding_for_insurer(finding.id, insurer_b_id)
        assert False, "cross-insurer acknowledge should fail"
    except ValueError:
        pass

    try:
        approve_finding_for_insurer(finding.id, insurer_b_id, "Wrong Adjuster")
        assert False, "cross-insurer approve should fail"
    except ValueError:
        pass

    try:
        reject_finding_for_insurer(finding.id, insurer_b_id, "Wrong Adjuster")
        assert False, "cross-insurer reject should fail"
    except ValueError:
        pass

    acknowledged = acknowledge_finding_for_insurer(finding.id, insurer_a_id)
    assert acknowledged.status == "acknowledged"


def test_service_insurer_wrappers_delegate_to_scoped_core_functions():
    """Service layer exposes the insurer-scoped queue and mutations used by UI."""
    with get_session() as session:
        from core.models import InsuranceCompany
        ins = InsuranceCompany(name="ServiceScoped")
        session.add(ins)
        session.flush()
        veh = session.query(Vehicle).get(vehicle_id)
        veh.insurance_company_id = ins.id
        session.flush()
        insurer_id = ins.id

    finding = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Service scoped finding",
        additional_cost=10.0,
    )

    service_queue = svc_list_pending_for_insurer(insurer_id)
    assert any(item.id == finding.id for item in service_queue)

    svc_ack_for_insurer(finding.id, insurer_id)
    acknowledged_queue = svc_list_pending_for_insurer(insurer_id)
    assert any(item.id == finding.id for item in acknowledged_queue)

    rejected = svc_reject_for_insurer(finding.id, insurer_id, "Adjuster B")
    assert rejected.status == "rejected"


def test_service_approve_for_insurer_updates_budget_once():
    """Insurer-scoped service approval adds the finding cost to vehicle budget."""
    with get_session() as session:
        from core.models import InsuranceCompany
        ins = InsuranceCompany(name="BudgetIns")
        session.add(ins)
        session.flush()
        veh = session.query(Vehicle).get(vehicle_id)
        veh.insurance_company_id = ins.id
        veh.approved_budget = 0.0
        session.flush()
        insurer_id = ins.id

    finding = mgr_report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description="Budget finding",
        additional_cost=125.0,
    )
    approved = svc_approve_for_insurer(finding.id, insurer_id, "Adjuster C")
    assert approved.status == "approved"
    assert approved.insurance_acknowledged_at is not None

    with get_session() as session:
        veh = session.query(Vehicle).get(vehicle_id)
        assert veh.approved_budget == 125.0
