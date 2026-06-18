"""Provider interface for password hashing - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """Abstraction over the password hashing algorithm (e.g. bcrypt, argon2)."""

    @abstractmethod
    def hash(self, plaintext: str) -> str:
        """Return a secure hash of the plaintext password."""
        pass

    @abstractmethod
    def verify(self, plaintext: str, password_hash: str) -> bool:
        """Return True if the plaintext matches the stored hash."""
        pass
