"""Tests for time and capacity helpers."""

import os
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.capacity_tracker import CapacityTracker  # noqa: E402
from core.database import Base, engine, get_session, init_db  # noqa: E402
from core.models import Customer, Process, ProcessLog, Vehicle  # noqa: E402
from core.time_tracker import elapsed_minutes, format_duration, remaining_minutes, variance_minutes  # noqa: E402


def _seed_capacity():
    """Create one bay with one active and one waiting vehicle."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    with get_session() as session:
        customer = Customer(full_name="Capacity Customer", phone_whatsapp="+15550000003")
        process = Process(name="Paint", sequence_order=1, std_hours_estimate=2.0, max_capacity=1)
        session.add_all([customer, process])
        session.flush()
        active_vehicle = Vehicle(
            license_plate="ACT-1",
            make="Toyota",
            model="Corolla",
            customer_id=customer.id,
        )
        waiting_vehicle = Vehicle(
            license_plate="WAIT-1",
            make="Honda",
            model="Civic",
            customer_id=customer.id,
        )
        session.add_all([active_vehicle, waiting_vehicle])
        session.flush()
        session.add_all([
            ProcessLog(
                vehicle_id=active_vehicle.id,
                process_id=process.id,
                status="in_progress",
                checkin_time=datetime.utcnow() - timedelta(minutes=30),
                estimated_hours=2.0,
            ),
            ProcessLog(
                vehicle_id=waiting_vehicle.id,
                process_id=process.id,
                status="waiting",
                checkin_time=datetime.utcnow() - timedelta(minutes=5),
                estimated_hours=2.0,
            ),
        ])
        return process.id


def test_capacity_counts_only_in_progress_bay_occupancy():
    """Waiting vehicles do not count as physically occupying a bay."""
    process_id = _seed_capacity()
    tracker = CapacityTracker()
    tracker.refresh()
    info = tracker.get_bay_info(process_id)
    assert info["current"] == 1
    assert info["is_full"] is True


def test_time_tracker_duration_remaining_and_variance():
    """Time helper calculations remain deterministic for completed logs."""
    now = datetime.utcnow()
    log = ProcessLog(
        vehicle_id=1,
        process_id=1,
        checkin_time=now - timedelta(hours=2),
        checkout_time=now - timedelta(hours=1),
        estimated_hours=0.5,
        actual_hours=1.0,
    )
    assert round(elapsed_minutes(log)) == 60
    assert remaining_minutes(log) is None
    assert variance_minutes(log) == 30.0
    assert format_duration(125.0) == "2h 5m"
