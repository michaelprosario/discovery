"""PostgreSQL implementation of INotebookRepository."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ...core.entities.notebook import Notebook
from ...core.interfaces.repositories.i_notebook_repository import INotebookRepository
from ...core.results.result import Result
from ...core.queries.notebook_queries import ListNotebooksQuery
from ...core.value_objects.enums import SortOption, SortOrder
from ..database.models import NotebookModel


class PostgresNotebookRepository(INotebookRepository):
    """
    PostgreSQL implementation of INotebookRepository using SQLAlchemy.

    This implementation stores notebooks in a PostgreSQL database.
    Follows the Dependency Inversion Principle: defined in Core, implemented in Infrastructure.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session

    def _model_to_entity(self, model: NotebookModel) -> Notebook:
        """
        Convert database model to domain entity.

        Args:
            model: NotebookModel from database

        Returns:
            Notebook: Domain entity
        """
        return Notebook(
            id=model.id,
            name=model.name,
            description=model.description,
            tags=list(model.tags) if model.tags else [],
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            source_count=model.source_count,
            output_count=model.output_count
        )

    def _entity_to_model(self, entity: Notebook) -> NotebookModel:
        """
        Convert domain entity to database model.

        Args:
            entity: Notebook domain entity

        Returns:
            NotebookModel: Database model
        """
        return NotebookModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            tags=entity.tags,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            source_count=entity.source_count,
            output_count=entity.output_count
        )

    def add(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add a new notebook to the repository.

        Args:
            notebook: The notebook entity to add

        Returns:
            Result[Notebook]: Success with the added notebook or failure
        """
        try:
            # Check if notebook already exists
            existing = self._session.query(NotebookModel).filter_by(id=notebook.id).first()
            if existing:
                return Result.failure(f"Notebook with ID {notebook.id} already exists")

            # Convert entity to model and add to database
            model = self._entity_to_model(notebook)
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

    def update(self, notebook: Notebook) -> Result[Notebook]:
        """
        Update an existing notebook in the repository.

        Args:
            notebook: The notebook entity to update

        Returns:
            Result[Notebook]: Success with the updated notebook or failure
        """
        try:
            # Find existing notebook
            model = self._session.query(NotebookModel).filter_by(id=notebook.id).first()
            if not model:
                return Result.failure(f"Notebook with ID {notebook.id} not found")

            # Update fields
            model.name = notebook.name
            model.description = notebook.description
            model.tags = notebook.tags
            model.updated_at = notebook.updated_at
            model.source_count = notebook.source_count
            model.output_count = notebook.output_count

            self._session.commit()
            self._session.refresh(model)

            return Result.success(self._model_to_entity(model))

        except IntegrityError as e:
            self._session.rollback()
            return Result.failure(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def upsert(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add or update a notebook (insert if doesn't exist, update if exists).

        Args:
            notebook: The notebook entity to upsert

        Returns:
            Result[Notebook]: Success with the upserted notebook or failure
        """
        try:
            # Check if notebook exists
            model = self._session.query(NotebookModel).filter_by(id=notebook.id).first()

            if model:
                # Update existing
                model.name = notebook.name
                model.description = notebook.description
                model.tags = notebook.tags
                model.updated_at = notebook.updated_at
                model.source_count = notebook.source_count
                model.output_count = notebook.output_count
            else:
                # Insert new
                model = self._entity_to_model(notebook)
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

    def get_by_id(self, notebook_id: UUID) -> Result[Optional[Notebook]]:
        """
        Get a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[Optional[Notebook]]: Success with notebook if found, None if not found, or failure
        """
        try:
            model = self._session.query(NotebookModel).filter_by(id=notebook_id).first()

            if model is None:
                return Result.success(None)

            return Result.success(self._model_to_entity(model))

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def exists(self, notebook_id: UUID) -> Result[bool]:
        """
        Check if a notebook exists by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        try:
            exists = self._session.query(NotebookModel).filter_by(id=notebook_id).first() is not None
            return Result.success(exists)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> Result[bool]:
        """
        Check if a notebook with the given name exists.

        Args:
            name: The notebook name to check (case-insensitive comparison)
            exclude_id: Optional ID to exclude from the check (for updates)

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        try:
            normalized_name = name.strip().lower()

            query = self._session.query(NotebookModel)

            # Case-insensitive comparison
            query = query.filter(NotebookModel.name.ilike(normalized_name))

            # Exclude specific ID if provided
            if exclude_id:
                query = query.filter(NotebookModel.id != exclude_id)

            exists = query.first() is not None
            return Result.success(exists)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def delete(self, notebook_id: UUID) -> Result[None]:
        """
        Delete a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook to delete

        Returns:
            Result[None]: Success or failure
        """
        try:
            model = self._session.query(NotebookModel).filter_by(id=notebook_id).first()

            if not model:
                return Result.failure(f"Notebook with ID {notebook_id} not found")

            self._session.delete(model)
            self._session.commit()

            return Result.success(None)

        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def get_all(self, query: Optional[ListNotebooksQuery] = None) -> Result[List[Notebook]]:
        """
        Get all notebooks with optional filtering and sorting.

        Args:
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Notebook]]: Success with list of notebooks or failure
        """
        try:
            db_query = self._session.query(NotebookModel)

            # Apply filters if query provided
            if query:
                # Filter by tags
                if query.tags:
                    # Filter notebooks that have any of the requested tags
                    # This works for both PostgreSQL ARRAY and SQLite JSON
                    from sqlalchemy import or_, func
                    tag_filters = []
                    for tag in query.tags:
                        # For PostgreSQL, use the ANY operator; for SQLite, use JSON contains
                        if self._session.bind.dialect.name == 'postgresql':
                            tag_filters.append(NotebookModel.tags.any(tag))
                        else:
                            # For SQLite with JSON, check if tag is in the JSON array
                            tag_filters.append(NotebookModel.tags.contains(tag))
                    if tag_filters:
                        db_query = db_query.filter(or_(*tag_filters))

                # Filter by date range
                if query.date_from:
                    db_query = db_query.filter(NotebookModel.created_at >= query.date_from)

                if query.date_to:
                    db_query = db_query.filter(NotebookModel.created_at <= query.date_to)

                # Sort notebooks
                if query.sort_by == SortOption.NAME:
                    order_field = NotebookModel.name
                elif query.sort_by == SortOption.CREATED_AT:
                    order_field = NotebookModel.created_at
                elif query.sort_by == SortOption.UPDATED_AT:
                    order_field = NotebookModel.updated_at
                elif query.sort_by == SortOption.SOURCE_COUNT:
                    order_field = NotebookModel.source_count
                else:
                    order_field = NotebookModel.created_at

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
            notebooks = [self._model_to_entity(model) for model in models]

            return Result.success(notebooks)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def count(self, query: Optional[ListNotebooksQuery] = None) -> Result[int]:
        """
        Get the total count of notebooks, with optional filtering.

        Args:
            query: Optional query parameters for filtering

        Returns:
            Result[int]: Success with count or failure
        """
        try:
            db_query = self._session.query(NotebookModel)

            if query:
                # Filter by tags
                if query.tags:
                    from sqlalchemy import or_
                    tag_filters = []
                    for tag in query.tags:
                        if self._session.bind.dialect.name == 'postgresql':
                            tag_filters.append(NotebookModel.tags.any(tag))
                        else:
                            tag_filters.append(NotebookModel.tags.contains(tag))
                    if tag_filters:
                        db_query = db_query.filter(or_(*tag_filters))

                # Filter by date range
                if query.date_from:
                    db_query = db_query.filter(NotebookModel.created_at >= query.date_from)

                if query.date_to:
                    db_query = db_query.filter(NotebookModel.created_at <= query.date_to)

            count = db_query.count()
            return Result.success(count)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")
