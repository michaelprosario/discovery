"""PyJWT implementation of ITokenService (stateless access tokens)."""
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID, uuid4

import jwt

from ...core.interfaces.providers.i_token_service import ITokenService
from ...core.results.result import Result

_ACCESS_TOKEN_TYPE = "access"


class JwtTokenService(ITokenService):
    """Signs and verifies short-lived access tokens as JWTs."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
    ):
        if not secret_key:
            raise ValueError("JWT secret key must not be empty")
        self._secret = secret_key
        self._algorithm = algorithm
        self._expire_minutes = access_token_expire_minutes

    @property
    def access_token_expires_seconds(self) -> int:
        return self._expire_minutes * 60

    def create_access_token(self, user_id: UUID, email: str, roles: List[str]) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "email": email,
            "roles": roles,
            "type": _ACCESS_TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> Result[dict]:
        try:
            claims = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            return Result.failure("Token has expired")
        except jwt.InvalidTokenError as exc:
            return Result.failure(f"Invalid token: {exc}")

        if claims.get("type") != _ACCESS_TOKEN_TYPE:
            return Result.failure("Not an access token")
        if not claims.get("email"):
            return Result.failure("Token missing email claim")
        return Result.success(claims)
