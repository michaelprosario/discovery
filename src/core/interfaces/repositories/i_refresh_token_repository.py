"""Repository interface for RefreshToken entity - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...entities.refresh_token import RefreshToken
from ...results.result import Result


class IRefreshTokenRepository(ABC):
    """Repository interface for refresh-token persistence and revocation."""

    @abstractmethod
    def add(self, token: RefreshToken) -> Result[RefreshToken]:
        """Persist a newly issued refresh token (stored hashed)."""
        pass

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> Result[Optional[RefreshToken]]:
        """Look up a refresh token by its SHA-256 hash (None if not found)."""
        pass

    @abstractmethod
    def update(self, token: RefreshToken) -> Result[RefreshToken]:
        """Persist changes to an existing refresh token (e.g. revocation/rotation)."""
        pass

    @abstractmethod
    def revoke_all_for_user(self, user_id: UUID) -> Result[None]:
        """Revoke every active refresh token belonging to a user."""
        pass
