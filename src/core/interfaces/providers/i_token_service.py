"""Provider interface for access-token (JWT) handling - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from ...results.result import Result


class ITokenService(ABC):
    """
    Abstraction over signed access-token creation and verification.

    Access tokens are stateless (JWT in the default implementation); refresh
    tokens are opaque random values managed by the AuthService/repository, not
    here.
    """

    @abstractmethod
    def create_access_token(self, user_id: UUID, email: str, roles: List[str]) -> str:
        """Create a signed, short-lived access token for the given principal."""
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> Result[dict]:
        """
        Verify and decode an access token.

        Returns Result.success(claims) on a valid, unexpired access token, or
        Result.failure(reason) otherwise. Never raises for invalid tokens.
        """
        pass

    @property
    @abstractmethod
    def access_token_expires_seconds(self) -> int:
        """Lifetime of an access token in seconds (for the ``expires_in`` field)."""
        pass
