"""
RES - cost_estimator/db_writer.py
=================================
Persistence bridge from estimator output to the RES database.
"""

from core.findings_manager import report_finding
from core.models import Finding
from cost_estimator.cost_model import CostEstimate


def write_estimate_to_finding(
    vehicle_id: int,
    process_log_id: int,
    estimate: CostEstimate,
    photo_path: str,
    description: str,
) -> Finding:
    """
    Store an estimator result as a normal RES finding.

    Args:
        vehicle_id: Vehicle primary key.
        process_log_id: Active process log primary key.
        estimate: Cost estimate produced by the estimator.
        photo_path: Stored photo path.
        description: Operator/AI description.

    Returns:
        The created Finding.
    """
    estimator_ref = f"ai:{estimate.severity}:{estimate.confidence:.2f}"
    return report_finding(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description=(
            f"{description}\n"
            f"Estimator: {estimate.severity} damage, "
            f"${estimate.low:.2f}-${estimate.high:.2f}. {estimate.rationale}"
        ).strip(),
        additional_cost=estimate.recommended,
        photo_path=photo_path,
        cost_estimator_ref=estimator_ref,
    )
