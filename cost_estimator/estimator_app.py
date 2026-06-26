"""
RES - cost_estimator/estimator_app.py
=====================================
Convenience workflow for one-shot estimator usage.
"""

from pathlib import Path

from core.models import Finding
from cost_estimator.ai_engine import estimate_from_photo
from cost_estimator.db_writer import write_estimate_to_finding


def estimate_and_record(
    vehicle_id: int,
    process_log_id: int,
    photo_path: str | Path,
    description: str,
) -> Finding:
    """
    Estimate a photo and write the result into RES findings.

    Args:
        vehicle_id: Vehicle primary key.
        process_log_id: Active process log primary key.
        photo_path: Source image path.
        description: Operator description.

    Returns:
        Created Finding.
    """
    stored, estimate = estimate_from_photo(photo_path, description)
    return write_estimate_to_finding(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        estimate=estimate,
        photo_path=str(stored),
        description=description,
    )
