"""
RES — core/database.py
========================
Database connection and session management.

Uses SQLAlchemy 2.x with a session factory pattern.
The database engine is configured once from AppConfig.DATABASE_URL.
To switch from SQLite to PostgreSQL, change DATABASE_URL in .env —
no other code changes are required.

Usage example:
    from core.database import get_session

    with get_session() as session:
        vehicles = session.query(Vehicle).all()
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool

from config import AppConfig


# ---------------------------------------------------------------------------
# ORM Base
# ---------------------------------------------------------------------------

if "Base" not in globals():
    class Base(DeclarativeBase):
        """
        Declarative base class for all ORM models.

        All models in models.py inherit from this class so SQLAlchemy
        can discover and manage them as a unified schema.
        """
        pass


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _create_engine():
    """
    Create and configure the SQLAlchemy engine from AppConfig.

    For SQLite, enables WAL mode (Write-Ahead Logging) for better
    concurrent read performance on the workshop floor displays.

    Returns:
        A configured SQLAlchemy Engine instance.
    """
    engine_kwargs = {
        "echo": AppConfig.IS_DEV,   # Log SQL in development; silent in production
        "future": True,
    }
    if AppConfig.DATABASE_URL == "sqlite:///:memory:":
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        })

    engine = create_engine(AppConfig.DATABASE_URL, **engine_kwargs)

    # Enable WAL mode for SQLite (ignored silently for PostgreSQL)
    if "sqlite" in AppConfig.DATABASE_URL:
        @event.listens_for(engine, "connect")
        def set_sqlite_wal(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


# Module-level engine and session factory (singletons).
engine = _create_engine()
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional database session as a context manager.

    Automatically commits on success and rolls back on any exception,
    then closes the session to return the connection to the pool.

    Yields:
        An active SQLAlchemy Session.

    Raises:
        Re-raises any exception after rolling back the transaction.

    Example:
        with get_session() as session:
            session.add(some_object)
            # commit happens automatically on __exit__
    """
    session: Session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Create all tables defined in models.py if they do not already exist.

    This is called once at application startup. It is safe to call
    multiple times — existing tables are never dropped or modified.
    Safe for both SQLite (dev) and PostgreSQL (production).
    """
    # Import models here to ensure they are registered with Base before
    # create_all is called. The import is intentional.
    import core.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
