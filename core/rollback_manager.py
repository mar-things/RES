"""
RES — core/rollback_manager.py
================================
Business logic for rolling back a vehicle to a prior process.

Provides the ability to send a vehicle back (e.g., from QA back to
Painting, or Assembly back to Mechanic) due to rework or a failed
quality inspection. 

Rollbacks preserve the full audit trail: the current process log is 
marked as "rolled_back", a ProcessRollback record is inserted with the 
mandatory reason and approver ID, and a new ProcessLog is started at the 
target bay.
"""

from datetime import datetime

from core.database import get_session
from core.models import Process, ProcessLog, ProcessRollback, ProcessTransition, User, Vehicle
from core.process_engine import CapacityFullError


def _append_note(existing_notes: str | None, note: str) -> str:
    """Append an audit note without discarding existing operator notes."""
    return f"{existing_notes}\n{note}" if existing_notes else note


def _validate_approver(session, approved_by_id: int) -> User:
    """
    Load and validate the user approving a rollback.

    Args:
        session: Active SQLAlchemy session.
        approved_by_id: User ID supplied by the UI/service layer.

    Returns:
        The approving User object.

    Raises:
        PermissionError: If the user is missing, inactive, or not a manager/admin.
    """
    user = session.get(User, approved_by_id)
    if not user or not user.is_active or user.role not in ("manager", "admin"):
        raise PermissionError("Rollback approval requires an active manager or admin.")
    return user


def _active_log_query(session, vehicle_id: int):
    """Return the query used to find a vehicle's current active process log."""
    return (
        session.query(ProcessLog)
        .filter_by(vehicle_id=vehicle_id)
        .filter(ProcessLog.checkout_time.is_(None))
        .filter(ProcessLog.status.in_(["in_progress", "waiting"]))
        .order_by(ProcessLog.checkin_time.desc())
    )


def _ensure_target_has_capacity(session, process: Process) -> None:
    """
    Raise if the target process bay cannot accept another vehicle.

    Args:
        session: Active SQLAlchemy session.
        process: Target process.

    Raises:
        CapacityFullError: If active occupancy is at or above max_capacity.
    """
    active_count = (
        session.query(ProcessLog)
        .filter_by(process_id=process.id)
        .filter(ProcessLog.checkout_time.is_(None))
        .filter(ProcessLog.status.in_(["in_progress", "waiting"]))
        .count()
    )
    if active_count >= process.max_capacity:
        raise CapacityFullError(
            f"Process '{process.name}' is at full capacity "
            f"({process.max_capacity} vehicle(s) max)."
        )


def list_rollback_targets(vehicle_id: int) -> list[Process]:
    """
    Return prior, severity-applicable processes available for rollback.

    Args:
        vehicle_id: Vehicle whose active process determines the source point.

    Returns:
        Active processes earlier than the current process, ordered by sequence.

    Raises:
        ValueError: If the vehicle is not active in a process.
    """
    with get_session() as session:
        active_log = _active_log_query(session, vehicle_id).first()
        if not active_log:
            raise ValueError(f"Vehicle {vehicle_id} is not currently active in any process.")

        vehicle = session.get(Vehicle, vehicle_id)
        current_process = session.get(Process, active_log.process_id)
        if not vehicle or not current_process:
            raise ValueError("Vehicle or current process could not be loaded.")

        query = (
            session.query(Process)
            .filter_by(is_active=True)
            .filter(Process.sequence_order < current_process.sequence_order)
        )
        if vehicle.crash_severity.upper() == "LOW":
            query = query.filter(Process.required_severity.is_(None))
        return query.order_by(Process.sequence_order).all()


def rollback_vehicle(
    vehicle_id: int,
    to_process_id: int,
    reason: str,
    approved_by_id: int,
) -> ProcessRollback:
    """
    Roll back a vehicle from its current process to a prior process.

    This operation:
      1. Finds the currently active process log for the vehicle.
      2. Checks the vehicle out of that process with status='rolled_back'.
      3. Records a ProcessRollback entry for the audit trail.
      4. Checks the vehicle into the target process bay.

    Args:
        vehicle_id: ID of the vehicle being rolled back.
        to_process_id: ID of the repair process the vehicle is returning to.
        reason: Mandatory explanation of why the rollback is occurring.
        approved_by_id: ID of the User (manager/admin) authorizing this action.

    Returns:
        The newly created ProcessRollback ORM object.

    Raises:
        PermissionError: If the approver is not an active manager/admin.
        CapacityFullError: If the target process bay is full.
        ValueError: If the vehicle is not active, the target process does not
            exist, or the target is not a prior applicable process.
    """
    if not reason or not reason.strip():
        raise ValueError("A rollback reason must be provided.")

    with get_session() as session:
        approver = _validate_approver(session, approved_by_id)
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle or vehicle.is_deleted:
            raise ValueError(f"Vehicle {vehicle_id} does not exist or is deleted.")

        active_log = _active_log_query(session, vehicle_id).first()
        if not active_log:
            raise ValueError(f"Vehicle {vehicle_id} is not currently active in any process.")

        source_process = session.get(Process, active_log.process_id)
        target_process = session.query(Process).filter_by(
            id=to_process_id, is_active=True
        ).first()
        if not target_process:
            raise ValueError(f"Target process {to_process_id} does not exist or is inactive.")
        if not source_process:
            raise ValueError("Current process does not exist.")
        if target_process.sequence_order >= source_process.sequence_order:
            raise ValueError("Rollback target must be a prior process.")
        if (
            target_process.required_severity
            and target_process.required_severity.upper() != vehicle.crash_severity.upper()
        ):
            raise ValueError(
                f"Process '{target_process.name}' does not apply to "
                f"{vehicle.crash_severity.upper()} severity vehicles."
            )

        _ensure_target_has_capacity(session, target_process)

        now = datetime.utcnow()
        note_reason = reason.strip()

        active_log.checkout_time = now
        active_log.actual_hours = (now - active_log.checkin_time).total_seconds() / 3600.0
        active_log.status = "rolled_back"
        active_log.notes = _append_note(
            active_log.notes,
            f"[Rollback] Sent to {target_process.name}. Reason: {note_reason}",
        )

        rollback_record = ProcessRollback(
            vehicle_id=vehicle_id,
            from_process_id=source_process.id,
            to_process_id=to_process_id,
            reason=note_reason,
            approved_by_id=approver.id,
            approved_at=now,
        )
        session.add(rollback_record)

        target_log = ProcessLog(
            vehicle_id=vehicle_id,
            process_id=to_process_id,
            assigned_user_id=approver.id,
            checkin_time=now,
            estimated_hours=target_process.std_hours_estimate,
            status="in_progress",
            notes=f"Arrived via rollback from {source_process.name}.",
        )
        session.add(target_log)
        session.flush()

        transition = ProcessTransition(
            vehicle_id=vehicle_id,
            from_process_log_id=active_log.id,
            to_process_log_id=target_log.id,
            transit_minutes=0.0,
            delay_reason=None,
            recorded_at=now,
        )
        session.add(transition)

        return rollback_record
