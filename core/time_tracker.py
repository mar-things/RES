"""
RES — core/time_tracker.py
============================
Time tracking calculations for vehicle repair processes.

Provides:
  - Elapsed time since a vehicle checked in to a process
  - Remaining time estimate (standard estimate minus elapsed)
  - Total elapsed time across all active/completed process logs
  - Transit time between process checkout and next process checkin
  - Variance: actual hours vs. estimated hours (positive = overrun)

All durations are returned in minutes (float) for consistency.
The UI layer is responsible for formatting (e.g. "2h 30m").
"""

from datetime import datetime
from typing import Optional

from core.models import ProcessLog, ProcessTransition, Vehicle


# ---------------------------------------------------------------------------
# Single process log
# ---------------------------------------------------------------------------

def elapsed_minutes(log: ProcessLog) -> float:
    """
    Calculate how many minutes have elapsed since a vehicle checked in
    to a process.

    If the vehicle has already checked out, returns the actual duration.
    If still in progress, returns time from checkin to now (UTC).

    Args:
        log: A ProcessLog ORM object.

    Returns:
        Elapsed time in minutes (float).
    """
    end = log.checkout_time if log.checkout_time else datetime.utcnow()
    delta = end - log.checkin_time
    return delta.total_seconds() / 60.0


def remaining_minutes(log: ProcessLog) -> Optional[float]:
    """
    Estimate remaining time in minutes for an in-progress process.

    Based on: (estimated_hours × 60) − elapsed_minutes.
    Returns None if no estimate is available or the process is complete.

    Args:
        log: A ProcessLog ORM object.

    Returns:
        Estimated remaining minutes, or None if not calculable.
        Negative value means the vehicle is overdue.
    """
    if log.checkout_time is not None:
        return None   # Already completed
    if log.estimated_hours is None:
        return None   # No estimate available

    estimated_minutes = log.estimated_hours * 60.0
    elapsed = elapsed_minutes(log)
    return estimated_minutes - elapsed


def variance_minutes(log: ProcessLog) -> Optional[float]:
    """
    Calculate the time variance for a completed process log.

    Variance = actual_hours × 60 − estimated_hours × 60.
    Positive = ran over estimate (cost overrun risk).
    Negative = finished under estimate (efficiency gain).

    Args:
        log: A completed ProcessLog ORM object.

    Returns:
        Variance in minutes, or None if data is incomplete.
    """
    if log.actual_hours is None or log.estimated_hours is None:
        return None
    return (log.actual_hours - log.estimated_hours) * 60.0


# ---------------------------------------------------------------------------
# Vehicle totals
# ---------------------------------------------------------------------------

def total_elapsed_minutes(vehicle: Vehicle) -> float:
    """
    Sum elapsed time across all active and completed process logs
    for a vehicle.

    Args:
        vehicle: A Vehicle ORM object with process_logs loaded.

    Returns:
        Total elapsed repair time in minutes.
    """
    return sum(elapsed_minutes(log) for log in vehicle.process_logs)


def total_remaining_minutes(vehicle: Vehicle) -> Optional[float]:
    """
    Estimate the total remaining repair time for a vehicle.

    Sums remaining time from all currently in-progress process logs.
    Does not include future processes that have not yet started.

    Args:
        vehicle: A Vehicle ORM object with process_logs loaded.

    Returns:
        Total estimated remaining minutes, or None if no estimate exists
        for any active process.
    """
    total = 0.0
    any_estimate = False

    for log in vehicle.process_logs:
        rem = remaining_minutes(log)
        if rem is not None:
            total += rem
            any_estimate = True

    return total if any_estimate else None


# ---------------------------------------------------------------------------
# Transit time
# ---------------------------------------------------------------------------

def compute_transit_minutes(
    from_log: ProcessLog, to_log: ProcessLog
) -> float:
    """
    Compute the transit time in minutes between checkout of one process
    and checkin to the next.

    This is the "hand-off time" between bays — a key metric for
    workshop layout optimisation.

    Args:
        from_log: The completed ProcessLog (the process the vehicle left).
        to_log:   The new ProcessLog (the process the vehicle entered).

    Returns:
        Transit time in minutes.

    Raises:
        ValueError: If from_log has no checkout_time.
    """
    if from_log.checkout_time is None:
        raise ValueError(
            f"ProcessLog {from_log.id} has no checkout_time — "
            "cannot compute transit time."
        )
    delta = to_log.checkin_time - from_log.checkout_time
    return delta.total_seconds() / 60.0


# ---------------------------------------------------------------------------
# Formatting helpers (for UI display)
# ---------------------------------------------------------------------------

def format_duration(minutes: float) -> str:
    """
    Format a duration in minutes as a human-readable string.

    Args:
        minutes: Duration in minutes.

    Returns:
        Formatted string, e.g. "2h 30m", "45m", "0m".

    Examples:
        format_duration(150.0)  → "2h 30m"
        format_duration(45.3)   → "45m"
        format_duration(0.0)    → "0m"
    """
    total_minutes = max(0, int(minutes))
    hours, mins = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def status_color(log: ProcessLog) -> str:
    """
    Return a color code for a process log based on its remaining time.

    Used by the dashboard and kiosk to colour-code vehicle cards:
        'green'  — On time (> 20% of estimate remaining).
        'amber'  — Near deadline (0–20% remaining or slightly overdue).
        'red'    — Overdue (negative remaining time).

    Args:
        log: An in-progress ProcessLog ORM object.

    Returns:
        String color code: 'green', 'amber', or 'red'.
    """
    rem = remaining_minutes(log)
    if rem is None:
        return "green"   # No estimate = no colour warning
    if rem < 0:
        return "red"
    # Fraction of estimated time remaining
    if log.estimated_hours:
        fraction = rem / (log.estimated_hours * 60.0)
        if fraction > 0.2:
            return "green"
    return "amber"
