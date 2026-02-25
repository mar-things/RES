"""
RES — core/capacity_tracker.py
================================
Bay capacity tracking for each repair process.

Tracks how many vehicles are currently active in each process bay
and determines whether a waiting vehicle is blocked by capacity
(bay is full) or by a staff delay (bay has space but vehicle not moved).

This data drives:
  - Dashboard occupancy indicators (e.g. "Painting: 2/3 bays used")
  - ProcessTransition.delay_reason ('capacity' | 'staff')
  - Future workshop layout optimisation reports
"""

from typing import Dict, Optional

from core.database import get_session
from core.models import Process, ProcessLog


class CapacityTracker:
    """
    Tracks current bay occupancy for each repair process.

    Usage:
        tracker = CapacityTracker()
        tracker.refresh()
        info = tracker.get_bay_info(process_id=5)
        # {'name': 'Painting', 'current': 1, 'max': 1, 'is_full': True}
    """

    def __init__(self) -> None:
        """
        Initialise the tracker.

        Call refresh() after construction to load current data from DB.
        """
        # Maps process_id → {'name', 'current', 'max', 'is_full'}
        self._bay_info: Dict[int, dict] = {}

    def refresh(self) -> None:
        """
        Reload current occupancy counts from the database.

        Call this every time a vehicle checks in or out, or on the
        dashboard auto-refresh cycle (every 30 seconds).
        """
        with get_session() as session:
            processes = session.query(Process).filter_by(is_active=True).all()

            for proc in processes:
                # Count vehicles currently 'in_progress' or 'waiting' in this bay
                active_count = (
                    session.query(ProcessLog)
                    .filter_by(process_id=proc.id)
                    .filter(ProcessLog.status.in_(["in_progress", "waiting"]))
                    .count()
                )
                self._bay_info[proc.id] = {
                    "process_id": proc.id,
                    "name": proc.name,
                    "current": active_count,
                    "max": proc.max_capacity,
                    "is_full": active_count >= proc.max_capacity,
                }

    def get_bay_info(self, process_id: int) -> Optional[dict]:
        """
        Return occupancy information for a single process bay.

        Args:
            process_id: The ID of the process/bay to query.

        Returns:
            A dict with keys: process_id, name, current, max, is_full.
            Returns None if the process_id is not tracked.
        """
        return self._bay_info.get(process_id)

    def is_full(self, process_id: int) -> bool:
        """
        Check whether a process bay is currently at full capacity.

        Args:
            process_id: The ID of the process/bay.

        Returns:
            True if no more vehicles can enter this bay.
            Returns True defensively if the process_id is unknown.
        """
        info = self._bay_info.get(process_id)
        if info is None:
            return True   # Unknown bay — deny entry defensively
        return info["is_full"]

    def has_space(self, process_id: int) -> bool:
        """
        Check whether a process bay has space for another vehicle.

        Args:
            process_id: The ID of the process/bay.

        Returns:
            True if the bay can accept another vehicle.
        """
        return not self.is_full(process_id)

    def all_bays(self) -> list[dict]:
        """
        Return occupancy info for all tracked process bays.

        Returns:
            A list of bay info dicts, sorted by sequence order.
        """
        return sorted(self._bay_info.values(), key=lambda b: b["process_id"])

    def determine_delay_reason(self, next_process_id: int) -> Optional[str]:
        """
        Determine why a vehicle is not moving to the next process.

        Used when recording ProcessTransition.delay_reason.

        Args:
            next_process_id: The process the vehicle wants to move to.

        Returns:
            'capacity' if the next bay is full.
            'staff'    if the next bay has space (staff delay).
            None       if the transition happened immediately (no delay).
        """
        if self.is_full(next_process_id):
            return "capacity"
        return "staff"
