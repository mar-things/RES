"""
RES — services/auth_service.py
================================
Authentication and role-based access control.

Provides password hashing/verification and session management.
Passwords are stored as bcrypt hashes — never in plaintext.

Roles and their permissions:
    mechanic         — Check in/out vehicles; report findings.
    manager          — All mechanic rights + approve rollbacks.
    admin            — Full access including user management.
    insurance-viewer — Read-only view of their own company's videos.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bcrypt

from core.database import get_session
from core.models import User


@dataclass
class AuthUser:
    """
    A lightweight snapshot of a logged-in user's data.

    Stored in memory for the application session. Uses a plain dataclass
    instead of a live ORM object to avoid DetachedInstanceError when
    accessing attributes outside a database session.
    """
    id: int
    full_name: str
    username: str
    role: str
    insurance_company_id: Optional[int]
    is_active: bool


# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Uses bcrypt with the default work factor (12 rounds).
    The resulting hash is safe to store in the database.

    Args:
        plain: The plaintext password to hash.

    Returns:
        A bcrypt hash string (prefixed with $2b$).
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain:  The plaintext password entered by the user.
        hashed: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# Session / Login
# ---------------------------------------------------------------------------

# In-memory session: holds the currently logged-in user for this process.
# For a multi-user server architecture this would be replaced by
# token-based sessions. For the desktop MVP, one user is logged in per app.
_current_user: Optional[AuthUser] = None


def login(username: str, password: str) -> Optional[AuthUser]:
    """
    Authenticate a user by username and password.

    Stamps last_login on success. Returns None if credentials are wrong
    or the account is inactive.

    Args:
        username: The username entered at the login screen.
        password: The plaintext password entered at the login screen.

    Returns:
        An AuthUser snapshot on success, or None if authentication fails.
    """
    global _current_user

    with get_session() as session:
        user = session.query(User).filter_by(
            username=username, is_active=True
        ).first()

        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            # Copy fields into a plain dataclass — safe to use outside the session
            auth_user = AuthUser(
                id=user.id,
                full_name=user.full_name,
                username=user.username,
                role=user.role,
                insurance_company_id=user.insurance_company_id,
                is_active=user.is_active,
            )
            _current_user = auth_user
            return auth_user

    _current_user = None
    return None


def logout() -> None:
    """Clear the current in-memory session."""
    global _current_user
    _current_user = None


def get_current_user() -> Optional[AuthUser]:
    """
    Return the currently logged-in user.

    Returns:
        The current AuthUser snapshot, or None if nobody is logged in.
    """
    return _current_user


def is_logged_in() -> bool:
    """Return True if a user is currently logged in."""
    return _current_user is not None


# ---------------------------------------------------------------------------
# Role checks
# ---------------------------------------------------------------------------

def has_role(*roles: str) -> bool:
    """
    Check whether the current user has one of the specified roles.

    Args:
        *roles: One or more role strings to check against.

    Returns:
        True if the current user's role is in the provided list.

    Example:
        if has_role("manager", "admin"):
            show_rollback_button()
    """
    user = get_current_user()
    return user is not None and user.role in roles


def require_role(*roles: str) -> None:
    """
    Raise PermissionError if the current user does not have the required role.

    Args:
        *roles: One or more acceptable roles.

    Raises:
        PermissionError: If no user is logged in or role does not match.
    """
    if not has_role(*roles):
        raise PermissionError(
            f"Action requires one of the following roles: {', '.join(roles)}"
        )
