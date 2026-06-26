"""Tests for notifications, security audit, and estimator fallback."""

import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.database import Base, engine, get_session, init_db  # noqa: E402
from core.models import Customer, NotificationLog, Process, ProcessLog, User, Vehicle  # noqa: E402
from cost_estimator.ai_engine import estimate_from_photo  # noqa: E402
from cost_estimator.estimator_app import estimate_and_record  # noqa: E402
from services.notification_service import send_client_message  # noqa: E402
from services.security_service import run_security_audit  # noqa: E402


def _seed_vehicle():
    """Create a vehicle and active process log."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    with get_session() as session:
        customer = Customer(full_name="Notify Customer", phone_whatsapp="+15550000002")
        admin = User(
            full_name="Admin",
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=True,
        )
        session.add_all([customer, admin])
        session.flush()
        vehicle = Vehicle(
            license_plate="AI-1",
            make="Honda",
            model="Civic",
            customer_id=customer.id,
            crash_severity="LOW",
        )
        process = Process(name="Reception", sequence_order=1, std_hours_estimate=1.0)
        session.add_all([vehicle, process])
        session.flush()
        log = ProcessLog(
            vehicle_id=vehicle.id,
            process_id=process.id,
            status="in_progress",
        )
        session.add(log)
        session.flush()
        return vehicle.id, log.id


def test_send_client_sms_logs_failed_without_credentials():
    """SMS attempts are audited even when Twilio credentials are absent."""
    vehicle_id, _ = _seed_vehicle()
    send_client_message(vehicle_id, "+15550000002", "Test", channel="sms")
    with get_session() as session:
        logs = session.query(NotificationLog).all()
    assert [(log.status, log.channel) for log in logs] == [("failed", "sms")]


def test_security_audit_reports_default_admin():
    """Security audit flags the default admin setup account."""
    _seed_vehicle()
    findings = run_security_audit()
    assert any(finding.code == "default-admin-present" for finding in findings)


def test_estimator_offline_fallback_and_db_writer(tmp_path, monkeypatch):
    """Estimator copies a photo, classifies severity, and writes a finding."""
    vehicle_id, log_id = _seed_vehicle()
    monkeypatch.setattr("config.AppConfig.PHOTO_STORAGE_PATH", tmp_path)
    photo = Path(tmp_path / "damage.jpg")
    photo.write_bytes(b"fake jpg content")

    stored, estimate = estimate_from_photo(photo, "front bumper dent")
    finding = estimate_and_record(vehicle_id, log_id, photo, "front bumper dent")

    assert stored.exists()
    assert estimate.severity == "MEDIUM"
    assert finding.cost_estimator_ref.startswith("ai:MEDIUM")
