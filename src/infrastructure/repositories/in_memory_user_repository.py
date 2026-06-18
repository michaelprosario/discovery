"""In-memory implementation of IUserRepository for testing and development."""
from typing import Optional, Dict
from uuid import UUID
from copy import deepcopy

from ...core.entities.user import User
from ...core.interfaces.repositories.i_user_repository import IUserRepository
from ...core.results.result import Result


class InMemoryUserRepository(IUserRepository):
    """In-memory IUserRepository. Suitable for tests/dev, not production."""

    def __init__(self):
        self._storage: Dict[UUID, User] = {}

    def add(self, user: User) -> Result[User]:
        if self.exists_by_email(user.email).value:
            return Result.failure(f"A user with email '{user.email}' already exists")
        self._storage[user.id] = deepcopy(user)
        return Result.success(deepcopy(user))

    def update(self, user: User) -> Result[User]:
        if user.id not in self._storage:
            return Result.failure(f"User with ID {user.id} not found")
        self._storage[user.id] = deepcopy(user)
        return Result.success(deepcopy(user))

    def get_by_id(self, user_id: UUID) -> Result[Optional[User]]:
        user = self._storage.get(user_id)
        return Result.success(deepcopy(user) if user else None)

    def get_by_email(self, email: str) -> Result[Optional[User]]:
        normalized = User.normalize_email(email)
        for user in self._storage.values():
            if user.email == normalized:
                return Result.success(deepcopy(user))
        return Result.success(None)

    def exists_by_email(self, email: str) -> Result[bool]:
        normalized = User.normalize_email(email)
        return Result.success(any(u.email == normalized for u in self._storage.values()))

    def clear(self) -> None:
        """Clear all users (useful for testing)."""
        self._storage.clear()
