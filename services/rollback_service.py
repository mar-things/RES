"""
RES - services/rollback_service.py
===================================
Service boundary for process rollback workflows.

UI code calls this module instead of reaching directly into
core.rollback_manager. Keeping the boundary small makes rollback behavior
consistent across dialogs, future vehicle detail views, and tests.
"""

from core.models import Process, ProcessRollback
from core.rollback_manager import (
    list_rollback_targets as _list_rollback_targets,
    rollback_vehicle as _rollback_vehicle,
)


def list_rollback_targets(vehicle_id: int) -> list[Process]:
    """
    Return valid rollback targets for a vehicle's current active process.

    Args:
        vehicle_id: Vehicle whose active process should be inspected.

    Returns:
        Prior, active, severity-applicable processes ordered by sequence.
    """
    return _list_rollback_targets(vehicle_id)


def rollback_vehicle(
    vehicle_id: int,
    to_process_id: int,
    reason: str,
    approved_by_id: int,
) -> ProcessRollback:
    """
    Roll back a vehicle with manager/admin approval.

    Args:
        vehicle_id: Vehicle being rolled back.
        to_process_id: Prior process to return the vehicle to.
        reason: Mandatory written reason.
        approved_by_id: Active manager/admin user approving the rollback.

    Returns:
        The created rollback audit record.
    """
    return _rollback_vehicle(
        vehicle_id=vehicle_id,
        to_process_id=to_process_id,
        reason=reason,
        approved_by_id=approved_by_id,
    )
