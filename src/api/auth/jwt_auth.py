"""JWT authentication dependencies for FastAPI.

Routers depend on ``get_current_user_email`` / ``get_current_user_email_with_api_key``
and receive the authenticated user's email — the same contract the rest of the app
(``created_by`` ownership) already relies on. The email is sourced from a verified
internal access token (JWT) issued by the auth router.
"""
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ...core.interfaces.providers.i_token_service import ITokenService
from ..dependencies.auth import get_token_service
from .authorization import SYSTEM_USER_EMAIL  # re-exported for routers that import it

__all__ = [
    "oauth2_scheme",
    "get_token_claims",
    "get_current_user_email",
    "get_current_user_email_with_api_key",
    "get_current_user_roles",
    "SYSTEM_USER_EMAIL",
]

# tokenUrl points at the OAuth2 password-grant endpoint (see auth_router).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_token_claims(
    token: str = Depends(oauth2_scheme),
    token_service: ITokenService = Depends(get_token_service),
) -> dict:
    """Verify the bearer access token and return its claims, or raise 401."""
    result = token_service.decode_access_token(token)
    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result.value


async def get_current_user_email(claims: dict = Depends(get_token_claims)) -> str:
    """Return the authenticated user's email from a verified access token."""
    email = claims.get("email")
    if not email:
        raise _CREDENTIALS_EXCEPTION
    return email


async def get_current_user_email_with_api_key(
    claims: dict = Depends(get_token_claims),
) -> str:
    """
    Back-compat alias for the dependency every router already imports.

    The former dual token-or-API-key flow collapses to "valid JWT" now.
    Kept as a distinct name so routers stay unchanged.
    """
    email = claims.get("email")
    if not email:
        raise _CREDENTIALS_EXCEPTION
    return email


async def get_current_user_roles(claims: dict = Depends(get_token_claims)) -> List[str]:
    """Return the authenticated user's roles from the access token."""
    roles = claims.get("roles")
    return roles if isinstance(roles, list) else []
