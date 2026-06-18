"""In-memory implementation of IRefreshTokenRepository for testing and development."""
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from copy import deepcopy

from ...core.entities.refresh_token import RefreshToken
from ...core.interfaces.repositories.i_refresh_token_repository import IRefreshTokenRepository
from ...core.results.result import Result


class InMemoryRefreshTokenRepository(IRefreshTokenRepository):
    """In-memory IRefreshTokenRepository. Suitable for tests/dev, not production."""

    def __init__(self):
        self._storage: Dict[UUID, RefreshToken] = {}

    def add(self, token: RefreshToken) -> Result[RefreshToken]:
        self._storage[token.id] = deepcopy(token)
        return Result.success(deepcopy(token))

    def get_by_hash(self, token_hash: str) -> Result[Optional[RefreshToken]]:
        for token in self._storage.values():
            if token.token_hash == token_hash:
                return Result.success(deepcopy(token))
        return Result.success(None)

    def update(self, token: RefreshToken) -> Result[RefreshToken]:
        if token.id not in self._storage:
            return Result.failure(f"Refresh token {token.id} not found")
        self._storage[token.id] = deepcopy(token)
        return Result.success(deepcopy(token))

    def revoke_all_for_user(self, user_id: UUID) -> Result[None]:
        now = datetime.utcnow()
        for token in self._storage.values():
            if token.user_id == user_id and token.revoked_at is None:
                token.revoked_at = now
        return Result.success(None)

    def clear(self) -> None:
        """Clear all tokens (useful for testing)."""
        self._storage.clear()
