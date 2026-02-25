"""
RES — core/seeds.py
=====================
Database seed data.

Populates the database with the default repair pipeline processes
and a default admin user on first run.

Run this once after init_db():
    from core.seeds import seed_all
    seed_all()
"""

from core.database import get_session
from core.models import Process, User
from services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Default repair pipeline
# ---------------------------------------------------------------------------

DEFAULT_PROCESSES = [
    # (name, sequence_order, std_hours_estimate, max_capacity, required_severity)
    ("Vehicle Reception",      1, 1.0,  1, None),
    ("Mechanic Work",          2, 4.0,  2, "HIGH"),   # High severity only
    ("Straightening",          3, 6.0,  2, None),
    ("Preparation to Paint",   4, 3.0,  2, None),
    ("Painting",               5, 5.0,  1, None),
    ("Assembly",               6, 3.0,  2, None),
    ("Polishing",              7, 2.0,  2, None),
    ("Quality Assurance",      8, 2.0,  1, None),
]


def seed_processes(session) -> int:
    """
    Insert the default repair pipeline processes if not already present.

    Existing processes are not modified — this is safe to run repeatedly.

    Args:
        session: An active SQLAlchemy session.

    Returns:
        Number of new processes inserted.
    """
    inserted = 0
    for name, order, hours, capacity, severity in DEFAULT_PROCESSES:
        exists = session.query(Process).filter_by(sequence_order=order).first()
        if not exists:
            session.add(Process(
                name=name,
                sequence_order=order,
                std_hours_estimate=hours,
                max_capacity=capacity,
                required_severity=severity,
                is_active=True,
            ))
            inserted += 1
    return inserted


def seed_admin_user(session) -> bool:
    """
    Create a default admin user if no users exist yet.

    IMPORTANT: Change the default password immediately after first login.

    Args:
        session: An active SQLAlchemy session.

    Returns:
        True if the admin user was created, False if users already exist.
    """
    if session.query(User).count() > 0:
        return False

    session.add(User(
        full_name="System Administrator",
        username="admin",
        password_hash=hash_password("admin1234"),  # Change on first login!
        role="admin",
        is_active=True,
    ))
    return True


def seed_all() -> None:
    """
    Run all seed functions in a single transaction.

    Safe to call on every startup — existing data is never overwritten.
    Prints a summary of what was inserted.
    """
    with get_session() as session:
        procs = seed_processes(session)
        admin = seed_admin_user(session)

    if procs:
        print(f"[Seed] Inserted {procs} default process(es).")
    if admin:
        print("[Seed] Created default admin user (username: admin, password: admin1234).")
        print("[Seed] ⚠  Change the admin password immediately after first login!")
