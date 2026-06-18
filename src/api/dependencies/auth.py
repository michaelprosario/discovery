"""Dependency wiring for the authentication system."""
from functools import lru_cache
from typing import Generator

from fastapi import Depends

from ...core.interfaces.providers.i_password_hasher import IPasswordHasher
from ...core.interfaces.providers.i_token_service import ITokenService
from ...core.services.auth_service import AuthService
from ...infrastructure.providers.bcrypt_password_hasher import BcryptPasswordHasher
from ...infrastructure.providers.jwt_token_service import JwtTokenService
from ...infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from ...infrastructure.repositories.postgres_refresh_token_repository import (
    PostgresRefreshTokenRepository,
)
from ..auth.config import get_auth_settings


@lru_cache()
def get_password_hasher() -> IPasswordHasher:
    """Cached singleton password hasher."""
    return BcryptPasswordHasher()


@lru_cache()
def get_token_service() -> ITokenService:
    """Cached singleton JWT token service built from auth settings."""
    settings = get_auth_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


def get_auth_service(
    hasher: IPasswordHasher = Depends(get_password_hasher),
    token_service: ITokenService = Depends(get_token_service),
) -> Generator[AuthService, None, None]:
    """Build an AuthService bound to a request-scoped database session."""
    from ...infrastructure.database.connection import get_db

    settings = get_auth_settings()
    db = next(get_db())
    try:
        yield AuthService(
            user_repository=PostgresUserRepository(db),
            refresh_token_repository=PostgresRefreshTokenRepository(db),
            password_hasher=hasher,
            token_service=token_service,
            refresh_token_ttl_days=settings.refresh_token_expire_days,
        )
    finally:
        db.close()
