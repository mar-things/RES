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
from core.models import Process, ProcessLog, ProcessRollback, Vehicle
from core.process_engine import checkin, checkout


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
        ValueError: If the vehicle is not currently active in any process, 
                    or if the target process does not exist.
    """
    if not reason or not reason.strip():
        raise ValueError("A rollback reason must be provided.")

    with get_session() as session:
        # Find the active process log
        active_log = (
            session.query(ProcessLog)
            .filter_by(vehicle_id=vehicle_id)
            .filter(ProcessLog.checkout_time.is_(None))
            .first()
        )

        if not active_log:
            raise ValueError(f"Vehicle {vehicle_id} is not currently active in any process.")

        from_process_id = active_log.process_id

        # Verify target process exists
        target_process = session.query(Process).filter_by(id=to_process_id, is_active=True).first()
        if not target_process:
            raise ValueError(f"Target process {to_process_id} does not exist or is inactive.")

        # 1. Create the rollback audit record
        rollback_record = ProcessRollback(
            vehicle_id=vehicle_id,
            from_process_id=from_process_id,
            to_process_id=to_process_id,
            reason=reason.strip(),
            approved_by_id=approved_by_id,
            approved_at=datetime.utcnow()
        )
        session.add(rollback_record)
        session.flush()

    # The rest happens outside the specific session scope to utilize existing functions
    # 2. Check out of current process, marking as rolled_back
    checkout(
        vehicle_id=vehicle_id, 
        process_id=from_process_id, 
        notes=f"Rolled back to {target_process.name}. Reason: {reason.strip()}",
        status="rolled_back"
    )

    # 3. Check into target process
    checkin(
        vehicle_id=vehicle_id,
        process_id=to_process_id,
        user_id=approved_by_id,
        notes=f"Arrived via rollback from Process ID: {from_process_id}."
    )

    # Return the rollback record (fetching fresh from DB if needed, though we already have it in local var)
    with get_session() as session:
        return session.query(ProcessRollback).get(rollback_record.id)
