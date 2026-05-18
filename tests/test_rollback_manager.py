"""Unit tests for rollback workflow invariants.

The rollback flow is intentionally tested at the core/service boundary
with an in-memory SQLite database. These tests verify the audit trail,
role requirements, target validation, and atomic failure behavior.
"""

import os
from datetime import datetime

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.database import Base, engine, get_session, init_db  # noqa: E402
from core.models import Customer, Process, ProcessLog, ProcessRollback, User, Vehicle  # noqa: E402
from core.process_engine import CapacityFullError  # noqa: E402
from core.rollback_manager import list_rollback_targets, rollback_vehicle  # noqa: E402
from services.rollback_service import rollback_vehicle as svc_rollback_vehicle  # noqa: E402


def _seed_base():
    """Create a vehicle, process pipeline, users, and an active QA log."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    with get_session() as session:
        customer = Customer(full_name="Rollback Customer", phone_whatsapp="+15550000000")
        session.add(customer)
        session.flush()

        vehicle = Vehicle(
            license_plate="ROLL-1",
            make="Toyota",
            model="Corolla",
            customer_id=customer.id,
            crash_severity="LOW",
            current_status="in_repair",
        )
        session.add(vehicle)

        reception = Process(
            name="Vehicle Reception",
            sequence_order=1,
            std_hours_estimate=1.0,
            max_capacity=2,
        )
        mechanic = Process(
            name="Mechanic Work",
            sequence_order=2,
            std_hours_estimate=4.0,
            max_capacity=1,
            required_severity="HIGH",
        )
        painting = Process(
            name="Painting",
            sequence_order=3,
            std_hours_estimate=5.0,
            max_capacity=2,
        )
        qa = Process(
            name="Quality Assurance",
            sequence_order=4,
            std_hours_estimate=2.0,
            max_capacity=1,
        )
        session.add_all([reception, mechanic, painting, qa])

        manager = User(
            full_name="Manager",
            username="manager",
            password_hash="hash",
            role="manager",
            is_active=True,
        )
        admin = User(
            full_name="Admin",
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=True,
        )
        mechanic_user = User(
            full_name="Mechanic",
            username="mechanic",
            password_hash="hash",
            role="mechanic",
            is_active=True,
        )
        session.add_all([manager, admin, mechanic_user])
        session.flush()

        active_log = ProcessLog(
            vehicle_id=vehicle.id,
            process_id=qa.id,
            checkin_time=datetime.utcnow(),
            estimated_hours=qa.std_hours_estimate,
            status="in_progress",
        )
        session.add(active_log)
        session.flush()

        return {
            "vehicle_id": vehicle.id,
            "reception_id": reception.id,
            "mechanic_id": mechanic.id,
            "painting_id": painting.id,
            "qa_id": qa.id,
            "manager_id": manager.id,
            "admin_id": admin.id,
            "mechanic_user_id": mechanic_user.id,
            "active_log_id": active_log.id,
        }


@pytest.fixture()
def seeded_ids():
    """Provide IDs for the common rollback scenario."""
    return _seed_base()


def test_rollback_happy_path_creates_audit_and_new_log(seeded_ids):
    """A valid rollback preserves old history and starts the target process."""
    rollback = rollback_vehicle(
        vehicle_id=seeded_ids["vehicle_id"],
        to_process_id=seeded_ids["painting_id"],
        reason="  QA paint defect  ",
        approved_by_id=seeded_ids["manager_id"],
    )

    assert rollback.id is not None
    assert rollback.from_process_id == seeded_ids["qa_id"]
    assert rollback.to_process_id == seeded_ids["painting_id"]
    assert rollback.reason == "QA paint defect"
    assert rollback.approved_by_id == seeded_ids["manager_id"]
    assert rollback.approved_at is not None

    with get_session() as session:
        old_log = session.get(ProcessLog, seeded_ids["active_log_id"])
        assert old_log.status == "rolled_back"
        assert old_log.checkout_time is not None
        assert old_log.actual_hours is not None
        assert "QA paint defect" in old_log.notes

        new_log = (
            session.query(ProcessLog)
            .filter_by(
                vehicle_id=seeded_ids["vehicle_id"],
                process_id=seeded_ids["painting_id"],
                status="in_progress",
            )
            .filter(ProcessLog.checkout_time.is_(None))
            .one()
        )
        assert new_log.assigned_user_id == seeded_ids["manager_id"]


def test_service_rollback_wrapper_executes_core_flow(seeded_ids):
    """The service layer exposes rollback execution for UI code."""
    rollback = svc_rollback_vehicle(
        vehicle_id=seeded_ids["vehicle_id"],
        to_process_id=seeded_ids["painting_id"],
        reason="Manager approved rework",
        approved_by_id=seeded_ids["admin_id"],
    )

    assert rollback.to_process_id == seeded_ids["painting_id"]
    assert rollback.approved_by_id == seeded_ids["admin_id"]


def test_list_rollback_targets_returns_prior_applicable_processes(seeded_ids):
    """LOW-severity vehicles exclude prior HIGH-only process targets."""
    targets = list_rollback_targets(seeded_ids["vehicle_id"])
    target_ids = {target.id for target in targets}

    assert seeded_ids["reception_id"] in target_ids
    assert seeded_ids["painting_id"] in target_ids
    assert seeded_ids["mechanic_id"] not in target_ids
    assert seeded_ids["qa_id"] not in target_ids


def test_rollback_rejects_blank_reason_without_mutation(seeded_ids):
    """A blank reason leaves audit and process logs unchanged."""
    with pytest.raises(ValueError):
        rollback_vehicle(
            vehicle_id=seeded_ids["vehicle_id"],
            to_process_id=seeded_ids["painting_id"],
            reason="   ",
            approved_by_id=seeded_ids["manager_id"],
        )

    with get_session() as session:
        assert session.query(ProcessRollback).count() == 0
        old_log = session.get(ProcessLog, seeded_ids["active_log_id"])
        assert old_log.checkout_time is None
        assert old_log.status == "in_progress"


def test_rollback_requires_manager_or_admin_approval(seeded_ids):
    """Mechanics cannot authorize rollback records."""
    with pytest.raises(PermissionError):
        rollback_vehicle(
            vehicle_id=seeded_ids["vehicle_id"],
            to_process_id=seeded_ids["painting_id"],
            reason="Needs rework",
            approved_by_id=seeded_ids["mechanic_user_id"],
        )

    with get_session() as session:
        assert session.query(ProcessRollback).count() == 0


@pytest.mark.parametrize("target_key", ["qa_id"])
def test_rollback_rejects_current_or_forward_target(seeded_ids, target_key):
    """Rollback targets must be earlier than the active process."""
    with pytest.raises(ValueError, match="prior process"):
        rollback_vehicle(
            vehicle_id=seeded_ids["vehicle_id"],
            to_process_id=seeded_ids[target_key],
            reason="Invalid target",
            approved_by_id=seeded_ids["manager_id"],
        )


def test_rollback_rejects_high_only_target_for_low_severity(seeded_ids):
    """Severity routing rules still apply to rollback target choices."""
    with pytest.raises(ValueError, match="does not apply"):
        rollback_vehicle(
            vehicle_id=seeded_ids["vehicle_id"],
            to_process_id=seeded_ids["mechanic_id"],
            reason="Invalid severity target",
            approved_by_id=seeded_ids["manager_id"],
        )


def test_rollback_is_atomic_when_target_capacity_is_full(seeded_ids):
    """Capacity failures leave no partial audit row or checked-out source log."""
    with get_session() as session:
        painting = session.get(Process, seeded_ids["painting_id"])
        painting.max_capacity = 1

        blocker = Vehicle(
            license_plate="BLOCK-1",
            make="Honda",
            model="Civic",
            customer_id=session.query(Customer).first().id,
            crash_severity="LOW",
            current_status="in_repair",
        )
        session.add(blocker)
        session.flush()

        session.add(
            ProcessLog(
                vehicle_id=blocker.id,
                process_id=painting.id,
                checkin_time=datetime.utcnow(),
                status="in_progress",
            )
        )

    with pytest.raises(CapacityFullError):
        rollback_vehicle(
            vehicle_id=seeded_ids["vehicle_id"],
            to_process_id=seeded_ids["painting_id"],
            reason="Target is full",
            approved_by_id=seeded_ids["manager_id"],
        )

    with get_session() as session:
        assert session.query(ProcessRollback).count() == 0
        old_log = session.get(ProcessLog, seeded_ids["active_log_id"])
        assert old_log.checkout_time is None
        assert old_log.status == "in_progress"
        target_open_count = (
            session.query(ProcessLog)
            .filter_by(
                vehicle_id=seeded_ids["vehicle_id"],
                process_id=seeded_ids["painting_id"],
            )
            .filter(ProcessLog.checkout_time.is_(None))
            .count()
        )
        assert target_open_count == 0
