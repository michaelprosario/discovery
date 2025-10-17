"""Unit tests for PostgresSourceRepository."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.core.entities.source import Source
from src.core.value_objects.enums import SourceType, FileType
from src.infrastructure.repositories.postgres_source_repository import PostgresSourceRepository
from src.infrastructure.database.models import Base, NotebookModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(session):
    """Create a PostgresSourceRepository instance with the test session."""
    return PostgresSourceRepository(session)


@pytest.fixture
def notebook_id(session):
    """Create a test notebook and return its ID."""
    notebook = NotebookModel(
        id=uuid4(),
        name="Test Notebook",
        description="A test notebook",
        tags=["test"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        source_count=0,
        output_count=0
    )
    session.add(notebook)
    session.commit()
    return notebook.id


@pytest.fixture
def sample_file_source(notebook_id):
    """Create a sample file source entity."""
    return Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Test PDF",
        source_type=SourceType.FILE,
        file_type=FileType.PDF,
        file_path="/path/to/test.pdf",
        file_size=1024,
        content_hash="abc123hash",
        extracted_text="Sample extracted text",
        metadata={"author": "Test Author", "pages": 10}
    )


@pytest.fixture
def sample_url_source(notebook_id):
    """Create a sample URL source entity."""
    return Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Test Website",
        source_type=SourceType.URL,
        url="https://example.com/article",
        content_hash="def456hash",
        extracted_text="Website content",
        metadata={"title": "Example Article", "date": "2024-01-01"}
    )


# Test add() method
def test_add_file_source_success(repository, sample_file_source):
    """Test successfully adding a file source."""
    result = repository.add(sample_file_source)

    assert result.is_success
    assert result.value is not None
    assert result.value.id == sample_file_source.id
    assert result.value.name == sample_file_source.name
    assert result.value.source_type == SourceType.FILE
    assert result.value.file_type == FileType.PDF


def test_add_url_source_success(repository, sample_url_source):
    """Test successfully adding a URL source."""
    result = repository.add(sample_url_source)

    assert result.is_success
    assert result.value is not None
    assert result.value.id == sample_url_source.id
    assert result.value.source_type == SourceType.URL
    assert result.value.url == sample_url_source.url


def test_add_duplicate_source_fails(repository, sample_file_source):
    """Test that adding a source with duplicate ID fails."""
    # Add source first time
    result1 = repository.add(sample_file_source)
    assert result1.is_success

    # Try to add again with same ID
    result2 = repository.add(sample_file_source)
    assert result2.is_failure
    assert "already exists" in result2.error.lower()


# Test get_by_id() method
def test_get_by_id_existing_source(repository, sample_file_source):
    """Test retrieving an existing source by ID."""
    # Add source
    repository.add(sample_file_source)

    # Retrieve it
    result = repository.get_by_id(sample_file_source.id)

    assert result.is_success
    assert result.value is not None
    assert result.value.id == sample_file_source.id
    assert result.value.name == sample_file_source.name


def test_get_by_id_nonexistent_source(repository):
    """Test retrieving a non-existent source returns None."""
    nonexistent_id = uuid4()
    result = repository.get_by_id(nonexistent_id)

    assert result.is_success
    assert result.value is None


def test_get_by_id_excludes_deleted_by_default(repository, sample_file_source):
    """Test that soft-deleted sources are excluded by default."""
    # Add and soft-delete source
    repository.add(sample_file_source)
    sample_file_source.soft_delete()
    repository.update(sample_file_source)

    # Try to retrieve without include_deleted
    result = repository.get_by_id(sample_file_source.id)
    assert result.is_success
    assert result.value is None

    # Try with include_deleted=True
    result_with_deleted = repository.get_by_id(sample_file_source.id, include_deleted=True)
    assert result_with_deleted.is_success
    assert result_with_deleted.value is not None
    assert result_with_deleted.value.deleted_at is not None


# Test update() method
def test_update_existing_source(repository, sample_file_source):
    """Test updating an existing source."""
    # Add source
    repository.add(sample_file_source)

    # Modify it
    sample_file_source.rename("Updated Name")

    # Update in repository
    result = repository.update(sample_file_source)

    assert result.is_success
    assert result.value.name == "Updated Name"


def test_update_nonexistent_source_fails(repository, sample_file_source):
    """Test updating a non-existent source fails."""
    result = repository.update(sample_file_source)

    assert result.is_failure
    assert "not found" in result.error.lower()


# Test upsert() method
def test_upsert_new_source(repository, sample_file_source):
    """Test upsert creates a new source if it doesn't exist."""
    result = repository.upsert(sample_file_source)

    assert result.is_success
    assert result.value.id == sample_file_source.id


def test_upsert_existing_source(repository, sample_file_source):
    """Test upsert updates existing source."""
    # Add source first
    repository.add(sample_file_source)

    # Modify and upsert
    sample_file_source.rename("Upserted Name")
    result = repository.upsert(sample_file_source)

    assert result.is_success
    assert result.value.name == "Upserted Name"


# Test get_by_notebook() method
def test_get_by_notebook_empty(repository, notebook_id):
    """Test getting sources for a notebook with no sources."""
    result = repository.get_by_notebook(notebook_id)

    assert result.is_success
    assert len(result.value) == 0


def test_get_by_notebook_multiple_sources(repository, notebook_id):
    """Test getting multiple sources for a notebook."""
    # Create and add multiple sources
    source1 = Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Source 1",
        source_type=SourceType.FILE,
        file_type=FileType.PDF,
        file_path="/path1.pdf",
        file_size=1024,
        content_hash="hash1",
        extracted_text="Text 1"
    )
    source2 = Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Source 2",
        source_type=SourceType.URL,
        url="https://example.com",
        content_hash="hash2",
        extracted_text="Text 2"
    )

    repository.add(source1)
    repository.add(source2)

    # Retrieve all
    result = repository.get_by_notebook(notebook_id)

    assert result.is_success
    assert len(result.value) == 2


def test_get_by_notebook_excludes_deleted(repository, notebook_id, sample_file_source):
    """Test that soft-deleted sources are excluded by default."""
    # Add source
    repository.add(sample_file_source)

    # Soft delete it
    repository.soft_delete(sample_file_source.id)

    # Query should not return it
    result = repository.get_by_notebook(notebook_id)
    assert result.is_success
    assert len(result.value) == 0


# Test get_by_content_hash() method
def test_get_by_content_hash_found(repository, sample_file_source):
    """Test finding a source by content hash."""
    # Add source
    repository.add(sample_file_source)

    # Search by hash
    result = repository.get_by_content_hash(
        sample_file_source.notebook_id,
        sample_file_source.content_hash
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.id == sample_file_source.id


def test_get_by_content_hash_not_found(repository, notebook_id):
    """Test searching for non-existent hash returns None."""
    result = repository.get_by_content_hash(notebook_id, "nonexistent_hash")

    assert result.is_success
    assert result.value is None


def test_get_by_content_hash_excludes_deleted(repository, sample_file_source):
    """Test that soft-deleted sources are not found by hash."""
    # Add and soft-delete
    repository.add(sample_file_source)
    repository.soft_delete(sample_file_source.id)

    # Search should not find it
    result = repository.get_by_content_hash(
        sample_file_source.notebook_id,
        sample_file_source.content_hash
    )
    assert result.is_success
    assert result.value is None


# Test soft_delete() method
def test_soft_delete_existing_source(repository, sample_file_source):
    """Test soft deleting an existing source."""
    # Add source
    repository.add(sample_file_source)

    # Soft delete
    result = repository.soft_delete(sample_file_source.id)

    assert result.is_success

    # Verify it's marked as deleted
    source_result = repository.get_by_id(sample_file_source.id, include_deleted=True)
    assert source_result.value.deleted_at is not None


def test_soft_delete_nonexistent_source(repository):
    """Test soft deleting a non-existent source fails."""
    result = repository.soft_delete(uuid4())

    assert result.is_failure
    assert "not found" in result.error.lower()


# Test delete() (permanent delete) method
def test_delete_existing_source(repository, sample_file_source):
    """Test permanently deleting a source."""
    # Add source
    repository.add(sample_file_source)

    # Delete permanently
    result = repository.delete(sample_file_source.id)

    assert result.is_success

    # Verify it's gone
    source_result = repository.get_by_id(sample_file_source.id, include_deleted=True)
    assert source_result.value is None


def test_delete_nonexistent_source(repository):
    """Test deleting a non-existent source fails."""
    result = repository.delete(uuid4())

    assert result.is_failure


# Test count() method
def test_count_empty_notebook(repository, notebook_id):
    """Test counting sources in empty notebook."""
    result = repository.count(notebook_id)

    assert result.is_success
    assert result.value == 0


def test_count_multiple_sources(repository, notebook_id):
    """Test counting multiple sources."""
    # Add two sources
    source1 = Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Source 1",
        source_type=SourceType.FILE,
        file_type=FileType.PDF,
        file_path="/path1.pdf",
        file_size=1024,
        content_hash="hash1",
        extracted_text="Text 1"
    )
    source2 = Source(
        id=uuid4(),
        notebook_id=notebook_id,
        name="Source 2",
        source_type=SourceType.URL,
        url="https://example.com",
        content_hash="hash2",
        extracted_text="Text 2"
    )

    repository.add(source1)
    repository.add(source2)

    # Count
    result = repository.count(notebook_id)

    assert result.is_success
    assert result.value == 2


def test_count_excludes_deleted_by_default(repository, notebook_id, sample_file_source):
    """Test that count excludes soft-deleted sources by default."""
    # Add and soft-delete
    repository.add(sample_file_source)
    repository.soft_delete(sample_file_source.id)

    # Count should be 0
    result = repository.count(notebook_id)
    assert result.is_success
    assert result.value == 0

    # Count with include_deleted should be 1
    result_with_deleted = repository.count(notebook_id, include_deleted=True)
    assert result_with_deleted.is_success
    assert result_with_deleted.value == 1


# Test exists() method
def test_exists_true(repository, sample_file_source):
    """Test exists returns True for existing source."""
    repository.add(sample_file_source)

    result = repository.exists(sample_file_source.id)

    assert result.is_success
    assert result.value is True


def test_exists_false(repository):
    """Test exists returns False for non-existent source."""
    result = repository.exists(uuid4())

    assert result.is_success
    assert result.value is False


def test_exists_excludes_deleted_by_default(repository, sample_file_source):
    """Test exists excludes soft-deleted sources by default."""
    # Add and soft-delete
    repository.add(sample_file_source)
    repository.soft_delete(sample_file_source.id)

    # Should not exist
    result = repository.exists(sample_file_source.id)
    assert result.is_success
    assert result.value is False

    # Should exist with include_deleted
    result_with_deleted = repository.exists(sample_file_source.id, include_deleted=True)
    assert result_with_deleted.is_success
    assert result_with_deleted.value is True
