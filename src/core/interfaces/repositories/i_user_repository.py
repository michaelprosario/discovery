"""Repository interface for User entity - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...entities.user import User
from ...results.result import Result


class IUserRepository(ABC):
    """
    Repository interface for User persistence operations.

    Defined in the Core layer (Dependency Inversion); Infrastructure provides
    concrete implementations.
    """

    @abstractmethod
    def add(self, user: User) -> Result[User]:
        """Add a new user. Fails if the email already exists."""
        pass

    @abstractmethod
    def update(self, user: User) -> Result[User]:
        """Update an existing user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Result[Optional[User]]:
        """Get a user by id (None if not found)."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Result[Optional[User]]:
        """Get a user by email, case-insensitive (None if not found)."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> Result[bool]:
        """Check whether a user with the given email exists."""
        pass
