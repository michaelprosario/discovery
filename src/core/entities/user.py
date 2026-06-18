"""User domain entity."""
import re
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from ..results.result import Result
from ..results.validation_error import ValidationError

# Minimal email format check; mirrors the lightweight "@" check used elsewhere
# (Notebook.created_by) but a little stricter for the authoritative user record.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Roles
ROLE_USER = "user"
ROLE_ADMIN = "admin"

# Minimum password length enforced at registration.
MIN_PASSWORD_LENGTH = 8


@dataclass
class User:
    """
    An authenticated principal of the system.

    The ``email`` is the stable identity used as ``created_by`` on every owned
    resource (notebooks, sources, outputs). ``password_hash`` is always a hash —
    plaintext passwords never live on the entity.
    """

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    display_name: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: [ROLE_USER])
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Normalize data after initialization."""
        if self.email:
            self.email = self.email.strip().lower()
        if self.display_name:
            self.display_name = self.display_name.strip()
        if not self.roles:
            self.roles = [ROLE_USER]

    @staticmethod
    def normalize_email(email: str) -> str:
        """Canonical form of an email for storage and lookup."""
        return email.strip().lower() if email else ""

    @staticmethod
    def validate_password(password: str) -> Result[None]:
        """
        Validate a plaintext password against the password policy.

        Kept separate from ``create`` because the plaintext is hashed by the
        service before the entity is constructed — the entity never sees it.
        """
        errors = []
        if not password:
            errors.append(ValidationError(
                field="password", message="Password is required", code="REQUIRED"
            ))
        elif len(password) < MIN_PASSWORD_LENGTH:
            errors.append(ValidationError(
                field="password",
                message=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
                code="MIN_LENGTH"
            ))
        elif len(password) > 128:
            errors.append(ValidationError(
                field="password",
                message="Password cannot exceed 128 characters",
                code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)
        return Result.success(None)

    @staticmethod
    def create(
        email: str,
        password_hash: str,
        display_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
    ) -> Result['User']:
        """
        Factory method to create a new user with validation.

        Args:
            email: Login email (required, unique, normalized to lowercase)
            password_hash: Pre-hashed password (the service hashes plaintext)
            display_name: Optional human-friendly name (max 255 chars)
            roles: Optional roles, defaults to ["user"]

        Returns:
            Result[User]: Success with user or failure with validation errors
        """
        errors = []

        email = User.normalize_email(email)
        if not email:
            errors.append(ValidationError(
                field="email", message="Email is required", code="REQUIRED"
            ))
        elif not _EMAIL_RE.match(email):
            errors.append(ValidationError(
                field="email", message="Email must be a valid email address", code="INVALID_FORMAT"
            ))
        elif len(email) > 255:
            errors.append(ValidationError(
                field="email", message="Email cannot exceed 255 characters", code="MAX_LENGTH"
            ))

        if not password_hash:
            errors.append(ValidationError(
                field="password_hash", message="Password hash is required", code="REQUIRED"
            ))

        if display_name and len(display_name) > 255:
            errors.append(ValidationError(
                field="display_name", message="Display name cannot exceed 255 characters", code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)

        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            roles=roles or [ROLE_USER],
        )
        return Result.success(user)

    @property
    def is_admin(self) -> bool:
        """True if the user holds the admin role (full visibility)."""
        return ROLE_ADMIN in self.roles

    def set_password_hash(self, password_hash: str) -> None:
        """Replace the stored password hash and bump the timestamp."""
        self.password_hash = password_hash
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Soft-disable the account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        return f"User(id={self.id}, email='{self.email}')"

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}', roles={self.roles}, active={self.is_active})"
