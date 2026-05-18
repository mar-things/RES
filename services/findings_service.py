"""
RES — services/findings_service.py
====================================
Higher‑level business logic related to damage findings.

This module wraps the core/findings_manager functions and takes care
of auxiliary tasks such as notifying the vehicle owner via the
notification service.
"""

from typing import Optional

from core.findings_manager import (
    report_finding as _report,
    acknowledge_finding as _ack,
    acknowledge_finding_for_insurer as _ack_for_insurer,
    approve_finding as _approve,
    approve_finding_for_insurer as _approve_for_insurer,
    reject_finding as _reject,
    reject_finding_for_insurer as _reject_for_insurer,
    get_findings_for_vehicle as _get_for_vehicle,
    list_pending_findings_for_insurer,
)
from services.notification_service import notify_finding
from core.database import get_session
from core.models import Vehicle


# ---------------------------------------------------------------------------
# Reporting / retrieval
# ---------------------------------------------------------------------------


def report_finding(
    vehicle_id: int,
    process_log_id: int,
    description: str,
    additional_cost: float = 0.0,
    photo_path: Optional[str] = None,
    cost_estimator_ref: Optional[str] = None,
):
    """Create a new finding and notify the customer.

    Args mirror those of :func:`core.findings_manager.report_finding`.

    Returns:
        The newly-created Finding ORM object.
    """
    finding = _report(
        vehicle_id=vehicle_id,
        process_log_id=process_log_id,
        description=description,
        additional_cost=additional_cost,
        photo_path=photo_path,
        cost_estimator_ref=cost_estimator_ref,
    )

    # try to send a notification (best-effort)
    try:
        with get_session() as session:
            vehicle = session.query(Vehicle).get(vehicle_id)
            if vehicle and vehicle.customer:
                notify_finding(
                    vehicle_id=vehicle.id,
                    plate=vehicle.license_plate,
                    customer_phone=vehicle.customer.phone_whatsapp,
                )
    except Exception as exc:  # pragma: no cover - notification is optional
        print(f"[FindingsService] notification error: {exc}")

    return finding


def acknowledge_finding(finding_id: int):
    """Acknowledge a finding without insurer scoping.

    UI entry points for insurance users should prefer
    :func:`acknowledge_finding_for_insurer`.
    """
    return _ack(finding_id)


def acknowledge_finding_for_insurer(finding_id: int, insurance_company_id: int):
    """Acknowledge only if the finding belongs to the insurer."""
    return _ack_for_insurer(finding_id, insurance_company_id)


def approve_finding(finding_id: int, approved_by_name: str):
    """Approve a finding without insurer scoping.

    UI entry points for insurance users should prefer
    :func:`approve_finding_for_insurer`.
    """
    return _approve(finding_id, approved_by_name)


def approve_finding_for_insurer(
    finding_id: int, insurance_company_id: int, approved_by_name: str
):
    """Approve only if the finding belongs to the insurer."""
    return _approve_for_insurer(finding_id, insurance_company_id, approved_by_name)


def reject_finding(finding_id: int, rejected_by_name: str):
    """Reject a finding without insurer scoping.

    UI entry points for insurance users should prefer
    :func:`reject_finding_for_insurer`.
    """
    return _reject(finding_id, rejected_by_name)


def reject_finding_for_insurer(
    finding_id: int, insurance_company_id: int, rejected_by_name: str
):
    """Reject only if the finding belongs to the insurer."""
    return _reject_for_insurer(finding_id, insurance_company_id, rejected_by_name)


def get_findings_for_vehicle(vehicle_id: int):
    """Return all findings recorded for a vehicle."""
    return _get_for_vehicle(vehicle_id)


def list_pending_for_insurer(insurance_company_id: int):
    """Return unresolved findings belonging to an insurance company."""
    return list_pending_findings_for_insurer(insurance_company_id)
