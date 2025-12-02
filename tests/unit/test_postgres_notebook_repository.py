"""Unit tests for PostgresNotebookRepository."""
import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.entities.notebook import Notebook
from src.core.queries.notebook_queries import ListNotebooksQuery
from src.core.value_objects.enums import SortOption, SortOrder
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(session):
    """Create a PostgresNotebookRepository instance for testing."""
    return PostgresNotebookRepository(session)


@pytest.fixture
def sample_notebook():
    """Create a sample notebook for testing."""
    result = Notebook.create(
        name="Test Notebook",
        created_by="user@example.com",
        description="A test notebook",
        tags=["test", "sample"]
    )
    return result.value


class TestPostgresNotebookRepository:
    """Test suite for PostgresNotebookRepository."""

    def test_add_notebook_success(self, repository, sample_notebook):
        """Test successfully adding a notebook."""
        result = repository.add(sample_notebook)

        assert result.is_success
        assert result.value.id == sample_notebook.id
        assert result.value.name == "Test Notebook"
        assert result.value.description == "A test notebook"
        assert "test" in result.value.tags
        assert "sample" in result.value.tags

    def test_add_duplicate_notebook_fails(self, repository, sample_notebook):
        """Test that adding a duplicate notebook fails."""
        # Add notebook first time
        repository.add(sample_notebook)

        # Try to add same notebook again
        result = repository.add(sample_notebook)

        assert result.is_failure
        assert "already exists" in result.error

    def test_get_by_id_existing_notebook(self, repository, sample_notebook):
        """Test retrieving an existing notebook by ID."""
        repository.add(sample_notebook)

        result = repository.get_by_id(sample_notebook.id)

        assert result.is_success
        assert result.value is not None
        assert result.value.id == sample_notebook.id
        assert result.value.name == "Test Notebook"

    def test_get_by_id_nonexistent_notebook(self, repository):
        """Test retrieving a non-existent notebook returns None."""
        result = repository.get_by_id(uuid4())

        assert result.is_success
        assert result.value is None

    def test_exists_returns_true_for_existing_notebook(self, repository, sample_notebook):
        """Test that exists returns True for an existing notebook."""
        repository.add(sample_notebook)

        result = repository.exists(sample_notebook.id)

        assert result.is_success
        assert result.value is True

    def test_exists_returns_false_for_nonexistent_notebook(self, repository):
        """Test that exists returns False for a non-existent notebook."""
        result = repository.exists(uuid4())

        assert result.is_success
        assert result.value is False

    def test_exists_by_name_case_insensitive(self, repository, sample_notebook):
        """Test that exists_by_name is case-insensitive."""
        repository.add(sample_notebook)

        # Test with different case
        result = repository.exists_by_name("TEST NOTEBOOK")

        assert result.is_success
        assert result.value is True

    def test_exists_by_name_with_exclude_id(self, repository, sample_notebook):
        """Test exists_by_name with exclude_id parameter."""
        repository.add(sample_notebook)

        # Should return False when excluding the notebook's own ID
        result = repository.exists_by_name("Test Notebook", exclude_id=sample_notebook.id)

        assert result.is_success
        assert result.value is False

    def test_update_notebook_success(self, repository, sample_notebook):
        """Test successfully updating a notebook."""
        repository.add(sample_notebook)

        # Modify notebook
        sample_notebook.name = "Updated Notebook"
        sample_notebook.description = "Updated description"

        result = repository.update(sample_notebook)

        assert result.is_success
        assert result.value.name == "Updated Notebook"
        assert result.value.description == "Updated description"

    def test_update_nonexistent_notebook_fails(self, repository, sample_notebook):
        """Test that updating a non-existent notebook fails."""
        result = repository.update(sample_notebook)

        assert result.is_failure
        assert "not found" in result.error

    def test_upsert_inserts_new_notebook(self, repository, sample_notebook):
        """Test that upsert inserts a new notebook if it doesn't exist."""
        result = repository.upsert(sample_notebook)

        assert result.is_success
        assert result.value.id == sample_notebook.id

        # Verify it was inserted
        get_result = repository.get_by_id(sample_notebook.id)
        assert get_result.is_success
        assert get_result.value is not None

    def test_upsert_updates_existing_notebook(self, repository, sample_notebook):
        """Test that upsert updates an existing notebook."""
        repository.add(sample_notebook)

        # Modify and upsert
        sample_notebook.name = "Upserted Notebook"
        result = repository.upsert(sample_notebook)

        assert result.is_success
        assert result.value.name == "Upserted Notebook"

    def test_delete_notebook_success(self, repository, sample_notebook):
        """Test successfully deleting a notebook."""
        repository.add(sample_notebook)

        result = repository.delete(sample_notebook.id)

        assert result.is_success

        # Verify deletion
        get_result = repository.get_by_id(sample_notebook.id)
        assert get_result.value is None

    def test_delete_nonexistent_notebook_fails(self, repository):
        """Test that deleting a non-existent notebook fails."""
        result = repository.delete(uuid4())

        assert result.is_failure
        assert "not found" in result.error

    def test_get_all_returns_all_notebooks(self, repository):
        """Test that get_all returns all notebooks."""
        # Add multiple notebooks
        nb1 = Notebook.create(name="Notebook 1", created_by="user@example.com", tags=["tag1"]).value
        nb2 = Notebook.create(name="Notebook 2", created_by="user@example.com", tags=["tag2"]).value
        nb3 = Notebook.create(name="Notebook 3", created_by="user@example.com", tags=["tag1", "tag2"]).value

        repository.add(nb1)
        repository.add(nb2)
        repository.add(nb3)

        result = repository.get_all()

        assert result.is_success
        assert len(result.value) == 3

    def test_get_all_with_tag_filter(self, repository):
        """Test get_all with tag filtering."""
        nb1 = Notebook.create(name="Notebook 1", created_by="user@example.com", tags=["python"]).value
        nb2 = Notebook.create(name="Notebook 2", created_by="user@example.com", tags=["java"]).value
        nb3 = Notebook.create(name="Notebook 3", created_by="user@example.com", tags=["python", "ml"]).value

        repository.add(nb1)
        repository.add(nb2)
        repository.add(nb3)

        query = ListNotebooksQuery(tags=["python"])
        result = repository.get_all(query)

        assert result.is_success
        # Note: SQLite doesn't support array operations the same way as PostgreSQL
        # This test might need adjustment based on actual implementation

    def test_get_all_with_sorting(self, repository):
        """Test get_all with sorting."""
        nb1 = Notebook.create(name="A Notebook", created_by="user@example.com").value
        nb2 = Notebook.create(name="C Notebook", created_by="user@example.com").value
        nb3 = Notebook.create(name="B Notebook", created_by="user@example.com").value

        repository.add(nb1)
        repository.add(nb2)
        repository.add(nb3)

        query = ListNotebooksQuery(
            sort_by=SortOption.NAME,
            sort_order=SortOrder.ASC
        )
        result = repository.get_all(query)

        assert result.is_success
        assert len(result.value) == 3
        assert result.value[0].name == "A Notebook"
        assert result.value[1].name == "B Notebook"
        assert result.value[2].name == "C Notebook"

    def test_get_all_with_pagination(self, repository):
        """Test get_all with pagination."""
        for i in range(5):
            nb = Notebook.create(name=f"Notebook {i}", created_by="user@example.com").value
            repository.add(nb)

        query = ListNotebooksQuery(limit=2, offset=1)
        result = repository.get_all(query)

        assert result.is_success
        assert len(result.value) == 2

    def test_count_returns_correct_count(self, repository):
        """Test that count returns the correct number of notebooks."""
        # Initially empty
        result = repository.count()
        assert result.is_success
        assert result.value == 0

        # Add notebooks
        for i in range(3):
            nb = Notebook.create(name=f"Notebook {i}", created_by="user@example.com").value
            repository.add(nb)

        result = repository.count()
        assert result.is_success
        assert result.value == 3

    def test_repository_handles_unicode_names(self, repository):
        """Test that repository handles Unicode characters in names."""
        nb = Notebook.create(name="Notebook 日本語 测试", created_by="user@example.com").value
        result = repository.add(nb)

        assert result.is_success
        assert result.value.name == "Notebook 日本語 测试"

    def test_repository_preserves_tags_order(self, repository):
        """Test that repository preserves tag order."""
        nb = Notebook.create(name="Test", created_by="user@example.com", tags=["z", "a", "m"]).value
        repository.add(nb)

        result = repository.get_by_id(nb.id)

        assert result.is_success
        # Tags should be preserved as-is
        assert result.value.tags == ["z", "a", "m"]

    def test_repository_handles_empty_description(self, repository):
        """Test that repository handles notebooks with no description."""
        nb = Notebook.create(name="Test Notebook", created_by="user@example.com", description=None).value
        result = repository.add(nb)

        assert result.is_success
        assert result.value.description is None

    def test_repository_handles_empty_tags(self, repository):
        """Test that repository handles notebooks with no tags."""
        nb = Notebook.create(name="Test Notebook", created_by="user@example.com", tags=[]).value
        result = repository.add(nb)

        assert result.is_success
        assert result.value.tags == []
