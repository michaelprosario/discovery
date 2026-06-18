"""PostgreSQL implementation of IRefreshTokenRepository."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...core.entities.refresh_token import RefreshToken
from ...core.interfaces.repositories.i_refresh_token_repository import IRefreshTokenRepository
from ...core.results.result import Result
from ..database.models import RefreshTokenModel


class PostgresRefreshTokenRepository(IRefreshTokenRepository):
    """PostgreSQL implementation of IRefreshTokenRepository using SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def _model_to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
            replaced_by=model.replaced_by,
        )

    def add(self, token: RefreshToken) -> Result[RefreshToken]:
        try:
            model = RefreshTokenModel(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                created_at=token.created_at,
                revoked_at=token.revoked_at,
                replaced_by=token.replaced_by,
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return Result.success(self._model_to_entity(model))
        except SQLAlchemyError as exc:
            self._session.rollback()
            return Result.failure(f"Failed to add refresh token: {exc}")

    def get_by_hash(self, token_hash: str) -> Result[Optional[RefreshToken]]:
        try:
            model = self._session.query(RefreshTokenModel).filter(
                RefreshTokenModel.token_hash == token_hash
            ).first()
            return Result.success(self._model_to_entity(model) if model else None)
        except SQLAlchemyError as exc:
            return Result.failure(f"Failed to get refresh token: {exc}")

    def update(self, token: RefreshToken) -> Result[RefreshToken]:
        try:
            model = self._session.query(RefreshTokenModel).filter(
                RefreshTokenModel.id == token.id
            ).first()
            if model is None:
                return Result.failure(f"Refresh token {token.id} not found")

            model.revoked_at = token.revoked_at
            model.replaced_by = token.replaced_by
            self._session.commit()
            self._session.refresh(model)
            return Result.success(self._model_to_entity(model))
        except SQLAlchemyError as exc:
            self._session.rollback()
            return Result.failure(f"Failed to update refresh token: {exc}")

    def revoke_all_for_user(self, user_id: UUID) -> Result[None]:
        try:
            now = datetime.utcnow()
            self._session.query(RefreshTokenModel).filter(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            ).update({RefreshTokenModel.revoked_at: now}, synchronize_session=False)
            self._session.commit()
            return Result.success(None)
        except SQLAlchemyError as exc:
            self._session.rollback()
            return Result.failure(f"Failed to revoke tokens: {exc}")
