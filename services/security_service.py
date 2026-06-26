"""
RES - services/security_service.py
==================================
Security posture checks for local deployments.

These checks are intentionally read-only. They help administrators verify
that production configuration avoids common deployment mistakes.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import AppConfig
from core.database import get_session
from core.models import User


@dataclass(frozen=True)
class SecurityFinding:
    """One security audit finding."""

    code: str
    severity: str
    message: str


def run_security_audit() -> list[SecurityFinding]:
    """
    Run local security configuration checks.

    Returns:
        List of findings. An empty list means no checked issues were found.
    """
    findings: list[SecurityFinding] = []
    if AppConfig.IS_PROD and AppConfig.SECRET_KEY in {"", "dev-insecure-key", "change-me"}:
        findings.append(SecurityFinding(
            code="weak-secret-key",
            severity="high",
            message="Production SECRET_KEY must be a strong random value.",
        ))
    if AppConfig.IS_PROD and AppConfig.DATABASE_URL.startswith("sqlite"):
        findings.append(SecurityFinding(
            code="sqlite-production",
            severity="medium",
            message="Production should use PostgreSQL rather than SQLite.",
        ))
    if AppConfig.USE_TWILIO and not AppConfig.TWILIO_AUTH_TOKEN:
        findings.append(SecurityFinding(
            code="twilio-token-missing",
            severity="high",
            message="Twilio is enabled but TWILIO_AUTH_TOKEN is missing.",
        ))

    with get_session() as session:
        active_admins = (
            session.query(User)
            .filter_by(role="admin", is_active=True)
            .count()
        )
        if active_admins == 0:
            findings.append(SecurityFinding(
                code="no-active-admin",
                severity="high",
                message="At least one active admin account is required.",
            ))
        default_admin = (
            session.query(User)
            .filter_by(username="admin", is_active=True)
            .first()
        )
        if default_admin:
            findings.append(SecurityFinding(
                code="default-admin-present",
                severity="medium",
                message="Rename or disable the default admin account after setup.",
            ))

    return findings
