"""
RES — core/process_engine.py
==============================
Core business logic for vehicle process pipeline management.

Handles:
  - Vehicle check-in to a repair process
  - Vehicle check-out from a repair process
  - Severity-based routing (LOW → skip Mechanic; HIGH → Mechanic → Straightening)
  - Capacity enforcement (raises CapacityFullError if bay is full)
  - Process transition recording (transit time between bays)
  - ProcessLog status management

This module is the heart of the RES system. All check-in/out operations
pass through here to ensure consistent state, audit trail, and KPI data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import joinedload

from core.database import get_session
from core.models import (
    Process, ProcessLog, ProcessTransition, Vehicle
)
from core.capacity_tracker import CapacityTracker
from core import time_tracker


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class CapacityFullError(Exception):
    """Raised when attempting to check a vehicle in to a full bay."""
    pass


class VehicleAlreadyActiveError(Exception):
    """Raised when a vehicle is already active (in_progress/waiting) in a process."""
    pass


class ProcessNotFoundError(Exception):
    """Raised when a process_id does not exist or is not active."""
    pass


# Module-level capacity tracker instance (refreshed before each operation)
_capacity_tracker = CapacityTracker()


# ---------------------------------------------------------------------------
# Pipeline query helpers
# ---------------------------------------------------------------------------

def get_active_processes() -> list[Process]:
    """
    Return all active repair processes, sorted by sequence_order.

    Returns:
        List of Process ORM objects ordered by sequence_order ascending.
    """
    with get_session() as session:
        return (
            session.query(Process)
            .filter_by(is_active=True)
            .order_by(Process.sequence_order)
            .all()
        )


def get_applicable_processes(crash_severity: str) -> list[Process]:
    """
    Return the repair processes applicable to a vehicle based on crash severity.

    LOW severity  → all processes where required_severity is None
    HIGH severity → all processes (None OR 'HIGH')

    Args:
        crash_severity: 'LOW' or 'HIGH'

    Returns:
        List of applicable Process objects, sorted by sequence_order.
    """
    with get_session() as session:
        query = session.query(Process).filter_by(is_active=True)
        if crash_severity.upper() == "LOW":
            query = query.filter(Process.required_severity.is_(None))
        return query.order_by(Process.sequence_order).all()


def get_process_by_id(process_id: int) -> Optional[Process]:
    """
    Fetch a single active Process by its primary key.

    Args:
        process_id: The process ID to look up.

    Returns:
        The Process ORM object, or None if not found.
    """
    with get_session() as session:
        return session.query(Process).filter_by(
            id=process_id, is_active=True
        ).first()


# ---------------------------------------------------------------------------
# Active log helpers
# ---------------------------------------------------------------------------

def get_active_log(vehicle_id: int, process_id: int) -> Optional[ProcessLog]:
    """
    Find an open (not yet checked-out) ProcessLog for a vehicle and process.

    Args:
        vehicle_id: Vehicle primary key.
        process_id: Process primary key.

    Returns:
        The matching open ProcessLog, or None if not found.
    """
    with get_session() as session:
        return (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id, process_id=process_id)
            .filter(ProcessLog.checkout_time.is_(None))
            .first()
        )


def get_last_completed_log(vehicle_id: int) -> Optional[ProcessLog]:
    """
    Return the most recently completed ProcessLog for a vehicle.

    Used to record transit time when the vehicle moves to the next process.

    Args:
        vehicle_id: Vehicle primary key.

    Returns:
        The most recently checked-out ProcessLog, or None.
    """
    with get_session() as session:
        return (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id)
            .filter(ProcessLog.checkout_time.isnot(None))
            .order_by(ProcessLog.checkout_time.desc())
            .first()
        )


# ---------------------------------------------------------------------------
# Check-in
# ---------------------------------------------------------------------------

def checkin(
    vehicle_id: int,
    process_id: int,
    user_id: Optional[int] = None,
    estimated_hours: Optional[float] = None,
    notes: Optional[str] = None,
) -> ProcessLog:
    """
    Record a vehicle checking in to a repair process.

    Creates a new ProcessLog with checkin_time = now (UTC).
    Also records a ProcessTransition if the vehicle previously completed
    another process (to track transit/hand-off time between bays).

    Args:
        vehicle_id:       ID of the vehicle entering the process.
        process_id:       ID of the target repair process.
        user_id:          ID of the staff member performing the check-in (optional).
        estimated_hours:  Expected hours to complete this process. If None,
                          falls back to the process's std_hours_estimate.
        notes:            Optional notes from the operator.

    Returns:
        The newly created and persisted ProcessLog ORM object.

    Raises:
        ProcessNotFoundError:     If the requested process does not exist.
        VehicleAlreadyActiveError: If the vehicle is already active in this process.
        CapacityFullError:        If the target bay is at full capacity.
    """
    # Refresh capacity data before making a decision
    _capacity_tracker.refresh()

    with get_session() as session:
        # Validate process exists
        process = session.query(Process).filter_by(
            id=process_id, is_active=True
        ).first()
        if not process:
            raise ProcessNotFoundError(f"No active process with id={process_id}")

        # Check for duplicate active log
        existing = (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id, process_id=process_id)
            .filter(ProcessLog.checkout_time.is_(None))
            .first()
        )
        if existing:
            raise VehicleAlreadyActiveError(
                f"Vehicle {vehicle_id} is already active in process {process_id}"
            )

        # Enforce capacity
        if _capacity_tracker.is_full(process_id):
            raise CapacityFullError(
                f"Process '{process.name}' is at full capacity "
                f"({process.max_capacity} vehicle(s) max)."
            )

        # Use process default estimate if none provided
        est = estimated_hours if estimated_hours is not None else process.std_hours_estimate

        now = datetime.utcnow()

        # Create the check-in log
        log = ProcessLog(
            vehicle_id=vehicle_id,
            process_id=process_id,
            assigned_user_id=user_id,
            checkin_time=now,
            estimated_hours=est,
            status="in_progress",
            notes=notes,
        )
        session.add(log)
        session.flush()  # Populate log.id before recording transition

        # Record transit time from the last completed process (if any)
        last_log = (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id)
            .filter(
                ProcessLog.checkout_time.isnot(None),
                ProcessLog.id != log.id,
            )
            .order_by(ProcessLog.checkout_time.desc())
            .first()
        )

        if last_log and last_log.checkout_time:
            transit_mins = (now - last_log.checkout_time).total_seconds() / 60.0
            delay_reason = _capacity_tracker.determine_delay_reason(process_id)

            transition = ProcessTransition(
                vehicle_id=vehicle_id,
                from_process_log_id=last_log.id,
                to_process_log_id=log.id,
                transit_minutes=transit_mins,
                delay_reason=delay_reason,
            )
            session.add(transition)

        return log


# ---------------------------------------------------------------------------
# Check-out
# ---------------------------------------------------------------------------

def checkout(
    vehicle_id: int,
    process_id: int,
    notes: Optional[str] = None,
) -> ProcessLog:
    """
    Record a vehicle checking out of a repair process.

    Updates the open ProcessLog: sets checkout_time = now and calculates
    actual_hours. Sets status to 'completed'.

    Args:
        vehicle_id: ID of the vehicle leaving the process.
        process_id: ID of the repair process being completed.
        notes:      Optional completion notes from the operator.

    Returns:
        The updated ProcessLog ORM object.

    Raises:
        ValueError: If no active (open) ProcessLog is found for this
                    vehicle and process combination.
    """
    with get_session() as session:
        log = (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id, process_id=process_id)
            .filter(ProcessLog.checkout_time.is_(None))
            .first()
        )

        if not log:
            raise ValueError(
                f"No active check-in found for vehicle {vehicle_id} "
                f"in process {process_id}."
            )

        now = datetime.utcnow()
        log.checkout_time = now
        log.actual_hours = (now - log.checkin_time).total_seconds() / 3600.0
        log.status = "completed"
        if notes:
            log.notes = (log.notes or "") + f"\n[Checkout] {notes}"

        return log


# ---------------------------------------------------------------------------
# Dashboard data query
# ---------------------------------------------------------------------------

def get_all_active_vehicle_logs() -> list[dict]:
    """
    Return a snapshot of all vehicles currently in a repair process.

    Used by the Workshop Dashboard to populate the Kanban board.
    Each entry contains vehicle info, the active process log, and
    display values calculated by time_tracker.

    Returns:
        List of dicts with keys:
            vehicle_id, plate, make, model, process_id, process_name,
            checkin_time, elapsed_minutes, remaining_minutes, status, color.
    """
    results = []
    with get_session() as session:
        logs = (
            session.query(ProcessLog)
            .options(
                joinedload(ProcessLog.vehicle),
                joinedload(ProcessLog.process),
            )
            .filter(ProcessLog.checkout_time.is_(None))
            .filter(ProcessLog.status.in_(["in_progress", "waiting"]))
            .all()
        )

        for log in logs:
            elapsed = time_tracker.elapsed_minutes(log)
            remaining = time_tracker.remaining_minutes(log)
            color = time_tracker.status_color(log)

            results.append({
                "vehicle_id": log.vehicle_id,
                "plate": log.vehicle.license_plate if log.vehicle else "?",
                "make": log.vehicle.make if log.vehicle else "",
                "model": log.vehicle.model if log.vehicle else "",
                "process_id": log.process_id,
                "process_name": log.process.name if log.process else "?",
                "checkin_time": log.checkin_time,
                "elapsed_minutes": elapsed,
                "remaining_minutes": remaining,
                "status": log.status,
                "color": color,
            })

    return results
