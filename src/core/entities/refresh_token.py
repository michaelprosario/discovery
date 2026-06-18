"""Refresh token domain entity."""
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field


@dataclass
class RefreshToken:
    """
    A persisted, revocable handle used to mint new access tokens.

    Only the SHA-256 hash of the opaque token value is stored (``token_hash``);
    the raw token is returned to the client once and never persisted. Rotation
    is modeled with ``replaced_by`` so a replayed (already-rotated) token can be
    detected and the whole chain revoked.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = None
    token_hash: str = ""
    expires_at: datetime = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    replaced_by: Optional[UUID] = None

    @property
    def is_active(self) -> bool:
        """True if the token has not been revoked and has not expired."""
        return not self.is_revoked and not self.is_expired

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.utcnow() >= self.expires_at

    def revoke(self, replaced_by: Optional[UUID] = None) -> None:
        """Mark this token revoked, optionally recording the rotation successor."""
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
        if replaced_by is not None:
            self.replaced_by = replaced_by
