"""Integration tests for process-engine routing and waiting semantics."""

import os
from datetime import datetime

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.database import Base, engine, get_session, init_db  # noqa: E402
from core.models import Customer, Process, ProcessLog, Vehicle  # noqa: E402
from core.process_engine import (  # noqa: E402
    CapacityFullError,
    IllegalProcessTransitionError,
    VehicleAlreadyActiveError,
    activate_waiting,
    advance_vehicle,
    checkin,
    get_next_process,
)


def _seed_pipeline() -> dict[str, int]:
    """Reset the database and create a minimal severity-aware pipeline."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    with get_session() as session:
        customer = Customer(full_name="Process Customer", phone_whatsapp="+15551112222")
        session.add(customer)
        session.flush()

        low_vehicle = Vehicle(
            license_plate="LOW-1",
            make="Toyota",
            model="Yaris",
            customer_id=customer.id,
            crash_severity="LOW",
            current_status="reception",
        )
        high_vehicle = Vehicle(
            license_plate="HIGH-1",
            make="Ford",
            model="Focus",
            customer_id=customer.id,
            crash_severity="HIGH",
            current_status="reception",
        )
        session.add_all([low_vehicle, high_vehicle])

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
        straightening = Process(
            name="Straightening",
            sequence_order=3,
            std_hours_estimate=6.0,
            max_capacity=1,
        )
        qa = Process(
            name="Quality Assurance",
            sequence_order=4,
            std_hours_estimate=2.0,
            max_capacity=1,
        )
        session.add_all([reception, mechanic, straightening, qa])
        session.flush()

        return {
            "customer_id": customer.id,
            "low_vehicle_id": low_vehicle.id,
            "high_vehicle_id": high_vehicle.id,
            "reception_id": reception.id,
            "mechanic_id": mechanic.id,
            "straightening_id": straightening.id,
            "qa_id": qa.id,
        }


@pytest.fixture()
def ids():
    """Provide a clean process-engine scenario for each test."""
    return _seed_pipeline()


def test_checkin_rejects_second_open_log_for_same_vehicle(ids):
    """A vehicle cannot occupy or wait in two process logs at once."""
    checkin(ids["low_vehicle_id"], ids["reception_id"])

    with pytest.raises(VehicleAlreadyActiveError):
        checkin(ids["low_vehicle_id"], ids["straightening_id"])


def test_low_severity_vehicle_skips_high_only_mechanic(ids):
    """LOW severity route moves from reception directly to straightening."""
    first = get_next_process(ids["low_vehicle_id"])
    assert first.id == ids["reception_id"]

    checkin(ids["low_vehicle_id"], ids["reception_id"])
    _, next_log = advance_vehicle(ids["low_vehicle_id"], ids["reception_id"])

    assert next_log is not None
    assert next_log.process_id == ids["straightening_id"]
    assert next_log.status == "in_progress"


def test_high_severity_vehicle_routes_through_mechanic(ids):
    """HIGH severity route includes the mechanic process after reception."""
    checkin(ids["high_vehicle_id"], ids["reception_id"])
    _, next_log = advance_vehicle(ids["high_vehicle_id"], ids["reception_id"])

    assert next_log is not None
    assert next_log.process_id == ids["mechanic_id"]


def test_checkin_rejects_out_of_order_or_inapplicable_target(ids):
    """Manual check-in must follow the next legal severity route step."""
    with pytest.raises(IllegalProcessTransitionError):
        checkin(ids["low_vehicle_id"], ids["mechanic_id"])

    with pytest.raises(IllegalProcessTransitionError):
        checkin(ids["high_vehicle_id"], ids["straightening_id"])


def test_advance_creates_waiting_log_when_next_bay_is_full(ids):
    """A full next bay queues the vehicle instead of creating a second bay occupant."""
    with get_session() as session:
        blocker = Vehicle(
            license_plate="BLOCK-1",
            make="Honda",
            model="Civic",
            customer_id=ids["customer_id"],
            crash_severity="LOW",
            current_status="in_repair",
        )
        session.add(blocker)
        session.flush()
        session.add(
            ProcessLog(
                vehicle_id=blocker.id,
                process_id=ids["straightening_id"],
                checkin_time=datetime.utcnow(),
                status="in_progress",
            )
        )

    checkin(ids["low_vehicle_id"], ids["reception_id"])
    _, waiting_log = advance_vehicle(ids["low_vehicle_id"], ids["reception_id"])

    assert waiting_log is not None
    assert waiting_log.process_id == ids["straightening_id"]
    assert waiting_log.status == "waiting"

    with get_session() as session:
        occupied_count = (
            session.query(ProcessLog)
            .filter_by(process_id=ids["straightening_id"], status="in_progress")
            .filter(ProcessLog.checkout_time.is_(None))
            .count()
        )
        assert occupied_count == 1


def test_waiting_log_activation_requires_capacity(ids):
    """Waiting logs can only become in-progress after bay capacity is available."""
    with get_session() as session:
        blocker = Vehicle(
            license_plate="BLOCK-2",
            make="Honda",
            model="Civic",
            customer_id=ids["customer_id"],
            crash_severity="LOW",
            current_status="in_repair",
        )
        session.add(blocker)
        session.flush()
        blocker_log = ProcessLog(
            vehicle_id=blocker.id,
            process_id=ids["straightening_id"],
            checkin_time=datetime.utcnow(),
            status="in_progress",
        )
        session.add(blocker_log)
        session.flush()
        blocker_log_id = blocker_log.id

    checkin(ids["low_vehicle_id"], ids["reception_id"])
    _, waiting_log = advance_vehicle(ids["low_vehicle_id"], ids["reception_id"])
    assert waiting_log.status == "waiting"

    with pytest.raises(CapacityFullError):
        activate_waiting(ids["low_vehicle_id"], ids["straightening_id"])

    with get_session() as session:
        blocker_log = session.get(ProcessLog, blocker_log_id)
        blocker_log.checkout_time = datetime.utcnow()
        blocker_log.status = "completed"

    activated = activate_waiting(ids["low_vehicle_id"], ids["straightening_id"])
    assert activated.status == "in_progress"
