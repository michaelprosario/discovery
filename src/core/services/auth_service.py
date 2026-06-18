"""Authentication service - registration, login, refresh-token rotation, logout."""
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ..entities.user import User
from ..entities.refresh_token import RefreshToken
from ..commands.auth_commands import (
    RegisterUserCommand,
    LoginCommand,
    RefreshCommand,
    LogoutCommand,
    ChangePasswordCommand,
)
from ..interfaces.repositories.i_user_repository import IUserRepository
from ..interfaces.repositories.i_refresh_token_repository import IRefreshTokenRepository
from ..interfaces.providers.i_password_hasher import IPasswordHasher
from ..interfaces.providers.i_token_service import ITokenService
from ..results.result import Result
from ..results.validation_error import ValidationError

# Generic message returned for any login failure so we never reveal whether an
# email exists (account-enumeration defense).
_INVALID_CREDENTIALS = "Invalid email or password"


@dataclass
class AuthTokens:
    """A freshly issued access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthService:
    """
    Domain service for authentication.

    Orchestrates the user and refresh-token repositories together with the
    password hasher and token service (all abstractions, per DIP). Business
    failures are returned as ``Result`` values rather than raised.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        refresh_token_repository: IRefreshTokenRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        refresh_token_ttl_days: int = 14,
    ):
        self._users = user_repository
        self._refresh_tokens = refresh_token_repository
        self._hasher = password_hasher
        self._tokens = token_service
        self._refresh_ttl_days = refresh_token_ttl_days

    # -- Registration ---------------------------------------------------------
    def register(self, command: RegisterUserCommand) -> Result[User]:
        """Register a new user. Fails on weak password or duplicate email."""
        password_check = User.validate_password(command.password)
        if password_check.is_failure:
            return password_check

        email = User.normalize_email(command.email)
        exists_result = self._users.exists_by_email(email)
        if exists_result.is_failure:
            return Result.failure(f"Failed to check email uniqueness: {exists_result.error}")
        if exists_result.value:
            return Result.validation_failure([
                ValidationError(
                    field="email",
                    message="An account with this email already exists",
                    code="DUPLICATE_EMAIL",
                )
            ])

        password_hash = self._hasher.hash(command.password)
        create_result = User.create(
            email=email,
            password_hash=password_hash,
            display_name=command.display_name,
            roles=command.roles,
        )
        if create_result.is_failure:
            return create_result

        return self._users.add(create_result.value)

    # -- Login ----------------------------------------------------------------
    def authenticate(self, command: LoginCommand) -> Result[AuthTokens]:
        """Verify credentials and issue an access + refresh token pair."""
        user_result = self._users.get_by_email(command.email)
        if user_result.is_failure:
            return Result.failure(f"Failed to load user: {user_result.error}")

        user = user_result.value
        # Verify the password even when the user is missing to keep timing
        # roughly constant, then return the same generic error.
        if user is None:
            self._hasher.verify(command.password, _DUMMY_HASH)
            return Result.failure(_INVALID_CREDENTIALS)

        if not self._hasher.verify(command.password, user.password_hash):
            return Result.failure(_INVALID_CREDENTIALS)

        if not user.is_active:
            return Result.failure("Account is disabled")

        return self._issue_tokens(user)

    # -- Refresh (rotation + reuse detection) ---------------------------------
    def refresh(self, command: RefreshCommand) -> Result[AuthTokens]:
        """Exchange a valid refresh token for a new token pair, rotating it."""
        token_hash = _hash_refresh_token(command.refresh_token)
        lookup = self._refresh_tokens.get_by_hash(token_hash)
        if lookup.is_failure:
            return Result.failure(f"Failed to load refresh token: {lookup.error}")

        token = lookup.value
        if token is None:
            return Result.failure("Invalid refresh token")

        # Reuse detection: a token that was already rotated/revoked is being
        # replayed -> assume compromise and revoke the user's entire chain.
        if token.is_revoked:
            self._refresh_tokens.revoke_all_for_user(token.user_id)
            return Result.failure("Refresh token has been revoked")

        if token.is_expired:
            return Result.failure("Refresh token has expired")

        user_result = self._users.get_by_id(token.user_id)
        if user_result.is_failure:
            return Result.failure(f"Failed to load user: {user_result.error}")
        user = user_result.value
        if user is None or not user.is_active:
            return Result.failure("Account is no longer active")

        issue_result = self._issue_tokens(user)
        if issue_result.is_failure:
            return issue_result

        # Rotate: revoke the presented token, pointing at its successor.
        new_hash = _hash_refresh_token(issue_result.value.refresh_token)
        successor = self._refresh_tokens.get_by_hash(new_hash).value
        token.revoke(replaced_by=successor.id if successor else None)
        self._refresh_tokens.update(token)

        return issue_result

    # -- Logout ---------------------------------------------------------------
    def logout(self, command: LogoutCommand) -> Result[None]:
        """Revoke a refresh token (idempotent)."""
        token_hash = _hash_refresh_token(command.refresh_token)
        lookup = self._refresh_tokens.get_by_hash(token_hash)
        if lookup.is_failure:
            return Result.failure(f"Failed to load refresh token: {lookup.error}")

        token = lookup.value
        if token is not None and not token.is_revoked:
            token.revoke()
            update_result = self._refresh_tokens.update(token)
            if update_result.is_failure:
                return Result.failure(f"Failed to revoke token: {update_result.error}")

        return Result.success(None)

    # -- Change password ------------------------------------------------------
    def change_password(self, command: ChangePasswordCommand) -> Result[None]:
        """Change a user's password; revokes all existing refresh tokens."""
        user_result = self._users.get_by_email(command.email)
        if user_result.is_failure:
            return Result.failure(f"Failed to load user: {user_result.error}")
        user = user_result.value
        if user is None or not self._hasher.verify(command.old_password, user.password_hash):
            return Result.failure(_INVALID_CREDENTIALS)

        password_check = User.validate_password(command.new_password)
        if password_check.is_failure:
            return password_check

        user.set_password_hash(self._hasher.hash(command.new_password))
        update_result = self._users.update(user)
        if update_result.is_failure:
            return Result.failure(f"Failed to update password: {update_result.error}")

        # Force re-login everywhere.
        self._refresh_tokens.revoke_all_for_user(user.id)
        return Result.success(None)

    # -- Read-through helper --------------------------------------------------
    def get_user_by_email(self, email: str) -> Result[Optional[User]]:
        """Convenience passthrough for the /me endpoint."""
        return self._users.get_by_email(email)

    # -- Internals ------------------------------------------------------------
    def _issue_tokens(self, user: User) -> Result[AuthTokens]:
        access_token = self._tokens.create_access_token(user.id, user.email, user.roles)

        raw_refresh = secrets.token_urlsafe(48)
        refresh_entity = RefreshToken(
            user_id=user.id,
            token_hash=_hash_refresh_token(raw_refresh),
            expires_at=datetime.utcnow() + timedelta(days=self._refresh_ttl_days),
        )
        add_result = self._refresh_tokens.add(refresh_entity)
        if add_result.is_failure:
            return Result.failure(f"Failed to persist refresh token: {add_result.error}")

        return Result.success(AuthTokens(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=self._tokens.access_token_expires_seconds,
        ))


def _hash_refresh_token(raw: str) -> str:
    """SHA-256 of the opaque refresh token (high-entropy → fast hash is fine)."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# Pre-computed bcrypt-style placeholder used to equalize timing on unknown
# emails. Any well-formed hash works; verification simply returns False.
_DUMMY_HASH = "$2b$12$0000000000000000000000000000000000000000000000000000a"
