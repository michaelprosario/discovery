"""Auth configuration loaded from environment variables."""
import os
import secrets
import warnings
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class AuthSettings:
    """Resolved settings for the internal OAuth2 + JWT auth system."""

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    allow_registration: bool


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@lru_cache()
def get_auth_settings() -> AuthSettings:
    """
    Build AuthSettings from the environment (cached).

    If ``JWT_SECRET_KEY`` is unset, an ephemeral secret is generated and a loud
    warning is emitted: tokens then survive only until the process restarts.
    Production deployments MUST set a stable ``JWT_SECRET_KEY``.
    """
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not secret:
        secret = secrets.token_urlsafe(48)
        warnings.warn(
            "JWT_SECRET_KEY is not set — generated an ephemeral secret. "
            "Tokens will be invalidated on restart. Set JWT_SECRET_KEY for production.",
            RuntimeWarning,
            stacklevel=2,
        )

    return AuthSettings(
        jwt_secret_key=secret,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256",
        access_token_expire_minutes=_get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15),
        refresh_token_expire_days=_get_int("REFRESH_TOKEN_EXPIRE_DAYS", 14),
        allow_registration=_get_bool("ALLOW_REGISTRATION", True),
    )
