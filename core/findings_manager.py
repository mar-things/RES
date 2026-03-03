"""
RES — core/findings_manager.py
================================
Business logic for managing unexpected damage findings.

Handles reporting discoveries, insurance acknowledgment, and budget
approvals. All actions are timestamped to measure SLAs.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import joinedload

from core.database import get_session
from core.models import Finding, Vehicle, ProcessLog


def report_finding(
    vehicle_id: int,
    process_log_id: int,
    description: str,
    additional_cost: float = 0.0,
    photo_path: Optional[str] = None,
    cost_estimator_ref: Optional[str] = None,
) -> Finding:
    """
    Record a new damage finding from the workshop floor.

    Args:
        vehicle_id: ID of the vehicle.
        process_log_id: ID of the active repair process log where it was found.
        description: Details of the damage.
        additional_cost: Estimated extra cost (manual initially).
        photo_path: Optional path to an uploaded photo.
        cost_estimator_ref: Hook for Phase 7 AI integration.

    Returns:
        The newly created Finding ORM object.
    """
    with get_session() as session:
        finding = Finding(
            vehicle_id=vehicle_id,
            process_log_id=process_log_id,
            description=description,
            additional_cost=additional_cost,
            photo_path=photo_path,
            cost_estimator_ref=cost_estimator_ref,
            reported_at=datetime.utcnow(),
            status="pending",
        )
        session.add(finding)
        return finding


def acknowledge_finding(finding_id: int) -> Finding:
    """
    Record that an insurance company has seen the finding.

    This completes the first step of the SLA (Time to Acknowledge).
    """
    with get_session() as session:
        finding = session.query(Finding).get(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        if finding.status == "pending":
            finding.status = "acknowledged"
            finding.insurance_acknowledged_at = datetime.utcnow()
        
        return finding


def approve_finding(finding_id: int, approved_by_name: str) -> Finding:
    """
    Record that an insurance company has approved the additional budget.

    This completes the second step of the SLA (Time to Approve) and updates
    the vehicle's authorized constraints.
    """
    with get_session() as session:
        finding = session.query(Finding).get(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        # Update finding
        finding.status = "approved"
        finding.approved_at = datetime.utcnow()
        finding.approved_by = approved_by_name

        # Update vehicle total approved budget
        vehicle = session.query(Vehicle).get(finding.vehicle_id)
        if vehicle:
            current_budget = vehicle.approved_budget or 0.0
            vehicle.approved_budget = current_budget + finding.additional_cost

        return finding


def reject_finding(finding_id: int, rejected_by_name: str) -> Finding:
    """Record that an insurance company rejected the finding."""
    with get_session() as session:
        finding = session.query(Finding).get(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        finding.status = "rejected"
        finding.approved_at = datetime.utcnow()  # Reusing datetime as resolution time
        finding.approved_by = rejected_by_name

        return finding


def get_findings_for_vehicle(vehicle_id: int) -> list[Finding]:
    """Retrieve all findings for a specific vehicle."""
    with get_session() as session:
        return (
            session.query(Finding)
            .filter_by(vehicle_id=vehicle_id)
            .order_by(Finding.reported_at.desc())
            .all()
        )


def list_pending_findings_for_insurer(insurance_company_id: int) -> list[Finding]:
    """Return all currently pending findings for a given insurer.

    The returned Finding objects include the related Vehicle and
    ProcessLog/process so the UI can display identifying information
    without additional queries.
    """
    with get_session() as session:
        return (
            session.query(Finding)
            .join(Vehicle)
            .options(
                joinedload(Finding.vehicle),
                joinedload(Finding.process_log).joinedload(ProcessLog.process),
            )
            .filter(Vehicle.insurance_company_id == insurance_company_id)
            .filter(Finding.status == "pending")
            .order_by(Finding.reported_at.desc())
            .all()
        )
