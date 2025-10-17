"""PostgreSQL implementation of ISourceRepository."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_

from ...core.entities.source import Source
from ...core.interfaces.repositories.i_source_repository import ISourceRepository
from ...core.results.result import Result
from ...core.queries.source_queries import ListSourcesQuery
from ...core.value_objects.enums import SourceType, FileType, SortOption, SortOrder
from ..database.models import SourceModel


class PostgresSourceRepository(ISourceRepository):
    """
    PostgreSQL implementation of ISourceRepository using SQLAlchemy.

    This implementation stores sources in a PostgreSQL database.
    Follows the Dependency Inversion Principle: defined in Core, implemented in Infrastructure.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session

    def _model_to_entity(self, model: SourceModel) -> Source:
        """
        Convert database model to domain entity.

        Args:
            model: SourceModel from database

        Returns:
            Source: Domain entity
        """
        # Convert string to enum
        source_type = SourceType(model.source_type)
        file_type = FileType(model.file_type) if model.file_type else None

        return Source(
            id=model.id,
            notebook_id=model.notebook_id,
            name=model.name,
            source_type=source_type,
            file_type=file_type,
            url=model.url,
            file_path=model.file_path,
            file_size=model.file_size,
            content_hash=model.content_hash,
            extracted_text=model.extracted_text,
            metadata=dict(model.source_metadata) if model.source_metadata else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at
        )

    def _entity_to_model(self, entity: Source) -> SourceModel:
        """
        Convert domain entity to database model.

        Args:
            entity: Source domain entity

        Returns:
            SourceModel: Database model
        """
        return SourceModel(
            id=entity.id,
            notebook_id=entity.notebook_id,
            name=entity.name,
            source_type=entity.source_type.value,
            file_type=entity.file_type.value if entity.file_type else None,
            url=entity.url,
            file_path=entity.file_path,
            file_size=entity.file_size,
            content_hash=entity.content_hash,
            extracted_text=entity.extracted_text,
            source_metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at
        )

    def add(self, source: Source) -> Result[Source]:
        """
        Add a new source to the repository.

        Args:
            source: The source entity to add

        Returns:
            Result[Source]: Success with the added source or failure
        """
        try:
            # Check if source already exists
            existing = self._session.query(SourceModel).filter_by(id=source.id).first()
            if existing:
                return Result.failure(f"Source with ID {source.id} already exists")

            # Convert entity to model and add to database
            model = self._entity_to_model(source)
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)

            # Convert back to entity and return
            return Result.success(self._model_to_entity(model))

        except IntegrityError as e:
            self._session.rollback()
            return Result.failure(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def update(self, source: Source) -> Result[Source]:
        """
        Update an existing source in the repository.

        Args:
            source: The source entity to update

        Returns:
            Result[Source]: Success with the updated source or failure
        """
        try:
            # Find existing source
            model = self._session.query(SourceModel).filter_by(id=source.id).first()
            if not model:
                return Result.failure(f"Source with ID {source.id} not found")

            # Update fields
            model.notebook_id = source.notebook_id
            model.name = source.name
            model.source_type = source.source_type.value
            model.file_type = source.file_type.value if source.file_type else None
            model.url = source.url
            model.file_path = source.file_path
            model.file_size = source.file_size
            model.content_hash = source.content_hash
            model.extracted_text = source.extracted_text
            model.source_metadata = source.metadata
            model.updated_at = source.updated_at
            model.deleted_at = source.deleted_at

            self._session.commit()
            self._session.refresh(model)

            return Result.success(self._model_to_entity(model))

        except IntegrityError as e:
            self._session.rollback()
            return Result.failure(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def upsert(self, source: Source) -> Result[Source]:
        """
        Add or update a source (insert if doesn't exist, update if exists).

        Args:
            source: The source entity to upsert

        Returns:
            Result[Source]: Success with the upserted source or failure
        """
        try:
            # Check if source exists
            model = self._session.query(SourceModel).filter_by(id=source.id).first()

            if model:
                # Update existing
                model.notebook_id = source.notebook_id
                model.name = source.name
                model.source_type = source.source_type.value
                model.file_type = source.file_type.value if source.file_type else None
                model.url = source.url
                model.file_path = source.file_path
                model.file_size = source.file_size
                model.content_hash = source.content_hash
                model.extracted_text = source.extracted_text
                model.source_metadata = source.metadata
                model.updated_at = source.updated_at
                model.deleted_at = source.deleted_at
            else:
                # Insert new
                model = self._entity_to_model(source)
                self._session.add(model)

            self._session.commit()
            self._session.refresh(model)

            return Result.success(self._model_to_entity(model))

        except IntegrityError as e:
            self._session.rollback()
            return Result.failure(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def get_by_id(self, source_id: UUID, include_deleted: bool = False) -> Result[Optional[Source]]:
        """
        Get a source by its ID.

        Args:
            source_id: The UUID of the source
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[Optional[Source]]: Success with source if found, None if not found, or failure
        """
        try:
            query = self._session.query(SourceModel).filter_by(id=source_id)

            if not include_deleted:
                query = query.filter(SourceModel.deleted_at.is_(None))

            model = query.first()

            if model is None:
                return Result.success(None)

            return Result.success(self._model_to_entity(model))

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def exists(self, source_id: UUID, include_deleted: bool = False) -> Result[bool]:
        """
        Check if a source exists by its ID.

        Args:
            source_id: The UUID of the source
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        try:
            query = self._session.query(SourceModel).filter_by(id=source_id)

            if not include_deleted:
                query = query.filter(SourceModel.deleted_at.is_(None))

            exists = query.first() is not None
            return Result.success(exists)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def get_by_notebook(self, notebook_id: UUID, query: Optional[ListSourcesQuery] = None) -> Result[List[Source]]:
        """
        Get all sources for a notebook with optional filtering and sorting.

        Args:
            notebook_id: The UUID of the notebook
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Source]]: Success with list of sources or failure
        """
        try:
            db_query = self._session.query(SourceModel).filter_by(notebook_id=notebook_id)

            # By default, exclude deleted sources unless specified
            if not query or not query.include_deleted:
                db_query = db_query.filter(SourceModel.deleted_at.is_(None))

            # Apply filters if query provided
            if query:
                # Filter by source types
                if query.source_types:
                    source_type_values = [st.value for st in query.source_types]
                    db_query = db_query.filter(SourceModel.source_type.in_(source_type_values))

                # Filter by file types
                if query.file_types:
                    file_type_values = [ft.value for ft in query.file_types]
                    db_query = db_query.filter(SourceModel.file_type.in_(file_type_values))

                # Sort sources
                if query.sort_by == SortOption.NAME:
                    order_field = SourceModel.name
                elif query.sort_by == SortOption.CREATED_AT:
                    order_field = SourceModel.created_at
                elif query.sort_by == SortOption.UPDATED_AT:
                    order_field = SourceModel.updated_at
                else:
                    order_field = SourceModel.created_at

                if query.sort_order == SortOrder.DESC:
                    db_query = db_query.order_by(order_field.desc())
                else:
                    db_query = db_query.order_by(order_field.asc())

                # Apply pagination
                if query.offset:
                    db_query = db_query.offset(query.offset)

                if query.limit:
                    db_query = db_query.limit(query.limit)

            # Execute query
            models = db_query.all()

            # Convert models to entities
            sources = [self._model_to_entity(model) for model in models]

            return Result.success(sources)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def get_by_content_hash(self, notebook_id: UUID, content_hash: str) -> Result[Optional[Source]]:
        """
        Get a source by its content hash within a notebook (for duplicate detection).

        Args:
            notebook_id: The UUID of the notebook
            content_hash: The SHA256 hash of the content

        Returns:
            Result[Optional[Source]]: Success with source if found, None if not found, or failure
        """
        try:
            model = self._session.query(SourceModel).filter(
                and_(
                    SourceModel.notebook_id == notebook_id,
                    SourceModel.content_hash == content_hash,
                    SourceModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return Result.success(None)

            return Result.success(self._model_to_entity(model))

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def soft_delete(self, source_id: UUID) -> Result[None]:
        """
        Soft delete a source by setting its deleted_at timestamp.

        Args:
            source_id: The UUID of the source to soft delete

        Returns:
            Result[None]: Success or failure
        """
        try:
            from datetime import datetime

            model = self._session.query(SourceModel).filter_by(id=source_id).first()

            if not model:
                return Result.failure(f"Source with ID {source_id} not found")

            if model.deleted_at is not None:
                return Result.failure(f"Source with ID {source_id} is already deleted")

            model.deleted_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()

            self._session.commit()

            return Result.success(None)

        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def delete(self, source_id: UUID) -> Result[None]:
        """
        Permanently delete a source from the repository.

        Args:
            source_id: The UUID of the source to delete

        Returns:
            Result[None]: Success or failure
        """
        try:
            model = self._session.query(SourceModel).filter_by(id=source_id).first()

            if not model:
                return Result.failure(f"Source with ID {source_id} not found")

            self._session.delete(model)
            self._session.commit()

            return Result.success(None)

        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def count(self, notebook_id: UUID, include_deleted: bool = False) -> Result[int]:
        """
        Get the count of sources in a notebook.

        Args:
            notebook_id: The UUID of the notebook
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[int]: Success with count or failure
        """
        try:
            query = self._session.query(SourceModel).filter_by(notebook_id=notebook_id)

            if not include_deleted:
                query = query.filter(SourceModel.deleted_at.is_(None))

            count = query.count()
            return Result.success(count)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")
