"""PostgreSQL implementation of IOutputRepository."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func

from ...core.entities.output import Output
from ...core.interfaces.repositories.i_output_repository import IOutputRepository
from ...core.results.result import Result
from ...core.queries.output_queries import (
    ListOutputsByNotebookQuery,
    ListAllOutputsQuery,
    SearchOutputsQuery
)
from ...core.value_objects.enums import SortOption, SortOrder
from ..database.models import OutputModel


class PostgresOutputRepository(IOutputRepository):
    """
    PostgreSQL implementation of IOutputRepository using SQLAlchemy.

    This implementation stores outputs in a PostgreSQL database.
    Follows the Dependency Inversion Principle: defined in Core, implemented in Infrastructure.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self._session = session

    def _model_to_entity(self, model: OutputModel) -> Output:
        """
        Convert database model to domain entity.

        Args:
            model: OutputModel from database

        Returns:
            Output: Domain entity
        """
        return Output(
            id=model.id,
            notebook_id=model.notebook_id,
            title=model.title,
            content=model.content,
            output_type=model.output_type,
            status=model.status,
            prompt=model.prompt,
            template_name=model.template_name,
            metadata=dict(model.output_metadata) if model.output_metadata else {},
            source_references=list(model.source_references) if model.source_references else [],
            word_count=model.word_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at
        )

    def _entity_to_model(self, entity: Output) -> OutputModel:
        """
        Convert domain entity to database model.

        Args:
            entity: Output domain entity

        Returns:
            OutputModel: Database model
        """
        return OutputModel(
            id=entity.id,
            notebook_id=entity.notebook_id,
            title=entity.title,
            content=entity.content,
            output_type=entity.output_type.value,
            status=entity.status.value,
            prompt=entity.prompt,
            template_name=entity.template_name,
            output_metadata=entity.metadata,
            source_references=entity.source_references,
            word_count=entity.word_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            completed_at=entity.completed_at
        )

    def add(self, output: Output) -> Result[Output]:
        """
        Add a new output to the repository.

        Args:
            output: The output entity to add

        Returns:
            Result[Output]: Success with the added output or failure
        """
        try:
            # Check if output already exists
            existing = self._session.query(OutputModel).filter_by(id=output.id).first()
            if existing:
                return Result.failure(f"Output with ID {output.id} already exists")

            # Convert entity to model and add to database
            model = self._entity_to_model(output)
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

    def update(self, output: Output) -> Result[Output]:
        """
        Update an existing output in the repository.

        Args:
            output: The output entity to update

        Returns:
            Result[Output]: Success with the updated output or failure
        """
        try:
            # Find existing output
            model = self._session.query(OutputModel).filter_by(id=output.id).first()
            if not model:
                return Result.failure(f"Output with ID {output.id} not found")

            # Update fields
            model.title = output.title
            model.content = output.content
            model.output_type = output.output_type.value
            model.status = output.status.value
            model.prompt = output.prompt
            model.template_name = output.template_name
            model.output_metadata = output.metadata
            model.source_references = output.source_references
            model.word_count = output.word_count
            model.updated_at = output.updated_at
            model.completed_at = output.completed_at

            self._session.commit()
            self._session.refresh(model)

            return Result.success(self._model_to_entity(model))

        except IntegrityError as e:
            self._session.rollback()
            return Result.failure(f"Database integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def upsert(self, output: Output) -> Result[Output]:
        """
        Add or update an output (insert if doesn't exist, update if exists).

        Args:
            output: The output entity to upsert

        Returns:
            Result[Output]: Success with the upserted output or failure
        """
        try:
            # Check if output exists
            model = self._session.query(OutputModel).filter_by(id=output.id).first()

            if model:
                # Update existing
                model.title = output.title
                model.content = output.content
                model.output_type = output.output_type.value
                model.status = output.status.value
                model.prompt = output.prompt
                model.template_name = output.template_name
                model.output_metadata = output.metadata
                model.source_references = output.source_references
                model.word_count = output.word_count
                model.updated_at = output.updated_at
                model.completed_at = output.completed_at
            else:
                # Insert new
                model = self._entity_to_model(output)
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

    def get_by_id(self, output_id: UUID) -> Result[Optional[Output]]:
        """
        Get an output by its ID.

        Args:
            output_id: The UUID of the output

        Returns:
            Result[Optional[Output]]: Success with output if found, None if not found, or failure
        """
        try:
            model = self._session.query(OutputModel).filter_by(id=output_id).first()
            
            if model:
                return Result.success(self._model_to_entity(model))
            else:
                return Result.success(None)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def exists(self, output_id: UUID) -> Result[bool]:
        """
        Check if an output exists by its ID.

        Args:
            output_id: The UUID of the output

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        try:
            exists = self._session.query(
                self._session.query(OutputModel).filter_by(id=output_id).exists()
            ).scalar()
            
            return Result.success(exists)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def delete(self, output_id: UUID) -> Result[None]:
        """
        Delete an output by its ID.

        Args:
            output_id: The UUID of the output to delete

        Returns:
            Result[None]: Success or failure
        """
        try:
            # Find and delete the output
            deleted_count = self._session.query(OutputModel).filter_by(id=output_id).delete()
            
            if deleted_count == 0:
                return Result.failure(f"Output with ID {output_id} not found")
            
            self._session.commit()
            return Result.success(None)

        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def get_by_notebook(self, query: ListOutputsByNotebookQuery) -> Result[List[Output]]:
        """
        Get all outputs for a specific notebook with optional filtering and sorting.

        Args:
            query: Query parameters for filtering and sorting

        Returns:
            Result[List[Output]]: Success with list of outputs or failure
        """
        try:
            # Start with base query
            db_query = self._session.query(OutputModel).filter_by(notebook_id=query.notebook_id)

            # Apply filters
            if query.output_type:
                db_query = db_query.filter(OutputModel.output_type == query.output_type.value)
            
            if query.status:
                db_query = db_query.filter(OutputModel.status == query.status.value)

            # Apply sorting
            db_query = self._apply_sorting(db_query, query.sort_by, query.sort_order)

            # Apply pagination
            if query.offset > 0:
                db_query = db_query.offset(query.offset)
            
            if query.limit:
                db_query = db_query.limit(query.limit)

            # Execute query
            models = db_query.all()
            outputs = [self._model_to_entity(model) for model in models]
            
            return Result.success(outputs)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def get_all(self, query: Optional[ListAllOutputsQuery] = None) -> Result[List[Output]]:
        """
        Get all outputs with optional filtering and sorting.

        Args:
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Output]]: Success with list of outputs or failure
        """
        try:
            # Start with base query
            db_query = self._session.query(OutputModel)

            if query:
                # Apply filters
                if query.output_type:
                    db_query = db_query.filter(OutputModel.output_type == query.output_type.value)
                
                if query.status:
                    db_query = db_query.filter(OutputModel.status == query.status.value)
                
                if query.notebook_ids:
                    db_query = db_query.filter(OutputModel.notebook_id.in_(query.notebook_ids))
                
                if query.created_after:
                    db_query = db_query.filter(OutputModel.created_at >= query.created_after)
                
                if query.created_before:
                    db_query = db_query.filter(OutputModel.created_at <= query.created_before)

                # Apply sorting
                db_query = self._apply_sorting(db_query, query.sort_by, query.sort_order)

                # Apply pagination
                if query.offset > 0:
                    db_query = db_query.offset(query.offset)
                
                if query.limit:
                    db_query = db_query.limit(query.limit)
            else:
                # Default sorting
                db_query = db_query.order_by(desc(OutputModel.updated_at))

            # Execute query
            models = db_query.all()
            outputs = [self._model_to_entity(model) for model in models]
            
            return Result.success(outputs)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def search(self, query: SearchOutputsQuery) -> Result[List[Output]]:
        """
        Search outputs by content or title.

        Args:
            query: Search query parameters

        Returns:
            Result[List[Output]]: Success with list of matching outputs or failure
        """
        try:
            # Start with base query
            db_query = self._session.query(OutputModel)

            # Apply search filter (case-insensitive search in title and content)
            search_filter = or_(
                OutputModel.title.ilike(f'%{query.search_term}%'),
                OutputModel.content.ilike(f'%{query.search_term}%')
            )
            db_query = db_query.filter(search_filter)

            # Apply additional filters
            if query.notebook_id:
                db_query = db_query.filter(OutputModel.notebook_id == query.notebook_id)
            
            if query.output_type:
                db_query = db_query.filter(OutputModel.output_type == query.output_type.value)
            
            if query.status:
                db_query = db_query.filter(OutputModel.status == query.status.value)

            # Apply sorting
            db_query = self._apply_sorting(db_query, query.sort_by, query.sort_order)

            # Apply pagination
            if query.offset > 0:
                db_query = db_query.offset(query.offset)
            
            if query.limit:
                db_query = db_query.limit(query.limit)

            # Execute query
            models = db_query.all()
            outputs = [self._model_to_entity(model) for model in models]
            
            return Result.success(outputs)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def count_by_notebook(self, notebook_id: UUID) -> Result[int]:
        """
        Get the count of outputs for a specific notebook.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[int]: Success with count or failure
        """
        try:
            count = self._session.query(OutputModel).filter_by(notebook_id=notebook_id).count()
            return Result.success(count)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def count(self, query: Optional[ListAllOutputsQuery] = None) -> Result[int]:
        """
        Get the total count of outputs.

        Args:
            query: Optional query parameters for filtering

        Returns:
            Result[int]: Success with count or failure
        """
        try:
            # Start with base query
            db_query = self._session.query(OutputModel)

            if query:
                # Apply same filters as get_all but without pagination
                if query.output_type:
                    db_query = db_query.filter(OutputModel.output_type == query.output_type.value)
                
                if query.status:
                    db_query = db_query.filter(OutputModel.status == query.status.value)
                
                if query.notebook_ids:
                    db_query = db_query.filter(OutputModel.notebook_id.in_(query.notebook_ids))
                
                if query.created_after:
                    db_query = db_query.filter(OutputModel.created_at >= query.created_after)
                
                if query.created_before:
                    db_query = db_query.filter(OutputModel.created_at <= query.created_before)

            count = db_query.count()
            return Result.success(count)

        except SQLAlchemyError as e:
            return Result.failure(f"Database error: {str(e)}")

    def delete_by_notebook(self, notebook_id: UUID) -> Result[None]:
        """
        Delete all outputs for a specific notebook.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[None]: Success or failure
        """
        try:
            # Delete all outputs for the notebook
            self._session.query(OutputModel).filter_by(notebook_id=notebook_id).delete()
            self._session.commit()
            return Result.success(None)

        except SQLAlchemyError as e:
            self._session.rollback()
            return Result.failure(f"Database error: {str(e)}")

    def _apply_sorting(self, query, sort_by: SortOption, sort_order: SortOrder):
        """
        Apply sorting to the query.

        Args:
            query: SQLAlchemy query object
            sort_by: Sort field
            sort_order: Sort direction

        Returns:
            Modified query with sorting applied
        """
        # Map sort options to model fields
        sort_fields = {
            SortOption.NAME: OutputModel.title,  # Use title for name sorting
            SortOption.CREATED_AT: OutputModel.created_at,
            SortOption.UPDATED_AT: OutputModel.updated_at,
            # Add other sort options as needed
        }

        field = sort_fields.get(sort_by, OutputModel.updated_at)
        
        if sort_order == SortOrder.ASC:
            return query.order_by(asc(field))
        else:
            return query.order_by(desc(field))