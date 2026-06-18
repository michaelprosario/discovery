"""PostgreSQL implementation of IUserRepository."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ...core.entities.user import User
from ...core.interfaces.repositories.i_user_repository import IUserRepository
from ...core.results.result import Result
from ..database.models import UserModel


class PostgresUserRepository(IUserRepository):
    """PostgreSQL implementation of IUserRepository using SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def _model_to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            display_name=model.display_name,
            roles=list(model.roles) if model.roles else ["user"],
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            password_hash=entity.password_hash,
            display_name=entity.display_name,
            roles=entity.roles,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def add(self, user: User) -> Result[User]:
        try:
            model = self._entity_to_model(user)
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return Result.success(self._model_to_entity(model))
        except IntegrityError:
            self._session.rollback()
            return Result.failure(f"A user with email '{user.email}' already exists")
        except SQLAlchemyError as exc:
            self._session.rollback()
            return Result.failure(f"Failed to add user: {exc}")

    def update(self, user: User) -> Result[User]:
        try:
            model = self._session.query(UserModel).filter(UserModel.id == user.id).first()
            if model is None:
                return Result.failure(f"User with ID {user.id} not found")

            model.email = user.email
            model.password_hash = user.password_hash
            model.display_name = user.display_name
            model.roles = user.roles
            model.is_active = user.is_active
            model.updated_at = user.updated_at

            self._session.commit()
            self._session.refresh(model)
            return Result.success(self._model_to_entity(model))
        except SQLAlchemyError as exc:
            self._session.rollback()
            return Result.failure(f"Failed to update user: {exc}")

    def get_by_id(self, user_id: UUID) -> Result[Optional[User]]:
        try:
            model = self._session.query(UserModel).filter(UserModel.id == user_id).first()
            return Result.success(self._model_to_entity(model) if model else None)
        except SQLAlchemyError as exc:
            return Result.failure(f"Failed to get user: {exc}")

    def get_by_email(self, email: str) -> Result[Optional[User]]:
        try:
            normalized = User.normalize_email(email)
            model = self._session.query(UserModel).filter(UserModel.email == normalized).first()
            return Result.success(self._model_to_entity(model) if model else None)
        except SQLAlchemyError as exc:
            return Result.failure(f"Failed to get user: {exc}")

    def exists_by_email(self, email: str) -> Result[bool]:
        try:
            normalized = User.normalize_email(email)
            exists = self._session.query(UserModel.id).filter(UserModel.email == normalized).first() is not None
            return Result.success(exists)
        except SQLAlchemyError as exc:
            return Result.failure(f"Failed to check user existence: {exc}")
