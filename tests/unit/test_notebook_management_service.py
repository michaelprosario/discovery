"""Unit tests for NotebookManagementService."""
import pytest
from uuid import uuid4
from datetime import datetime

from src.core.services.notebook_management_service import NotebookManagementService
from src.core.commands.notebook_commands import (
    CreateNotebookCommand,
    UpdateNotebookCommand,
    RenameNotebookCommand,
    DeleteNotebookCommand,
    AddTagsCommand,
    RemoveTagsCommand
)
from src.core.queries.notebook_queries import (
    GetNotebookByIdQuery,
    ListNotebooksQuery,
    CheckNotebookExistsQuery,
    CheckNotebookNameExistsQuery
)
from src.core.value_objects.enums import SortOption, SortOrder
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository


@pytest.fixture
def repository():
    """Fixture to provide a fresh repository for each test."""
    return InMemoryNotebookRepository()


@pytest.fixture
def service(repository):
    """Fixture to provide a service instance with repository."""
    return NotebookManagementService(repository)


class TestCreateNotebook:
    """Tests for creating notebooks."""

    def test_create_notebook_success(self, service):
        """Test successful notebook creation."""
        command = CreateNotebookCommand(
            name="Research Project",
            created_by="user@example.com",
            description="My research notes",
            tags=["research", "science"]
        )

        result = service.create_notebook(command)

        assert result.is_success
        assert result.value.name == "Research Project"
        assert result.value.description == "My research notes"
        assert set(result.value.tags) == {"research", "science"}
        assert result.value.created_by == "user@example.com"
        assert result.value.id is not None

    def test_create_notebook_with_minimal_data(self, service):
        """Test creating notebook with only required fields."""
        command = CreateNotebookCommand(name="Minimal Notebook", created_by="user@example.com")

        result = service.create_notebook(command)

        assert result.is_success
        assert result.value.name == "Minimal Notebook"
        assert result.value.description is None
        assert result.value.tags == []
        assert result.value.created_by == "user@example.com"

    def test_create_notebook_duplicate_name(self, service):
        """Test that duplicate names are rejected."""
        command1 = CreateNotebookCommand(name="Duplicate Test", created_by="user@example.com")
        service.create_notebook(command1)

        command2 = CreateNotebookCommand(name="Duplicate Test", created_by="user@example.com")
        result = service.create_notebook(command2)


        assert result.is_failure
        assert "already exists" in result.error.lower()

    def test_create_notebook_duplicate_name_case_insensitive(self, service):
        """Test that duplicate names are rejected (case-insensitive)."""
        command1 = CreateNotebookCommand(name="Test Notebook", created_by="user@example.com")
        service.create_notebook(command1)

        command2 = CreateNotebookCommand(name="test notebook", created_by="user@example.com")
        result = service.create_notebook(command2)

        assert result.is_failure
        assert "already exists" in result.error.lower()

    def test_create_notebook_empty_name(self, service):
        """Test that empty names are rejected."""
        command = CreateNotebookCommand(name="", created_by="user@example.com")

        result = service.create_notebook(command)

        assert result.is_failure
        assert result.validation_errors is not None
        assert any("name" in err.field.lower() for err in result.validation_errors)

    def test_create_notebook_whitespace_only_name(self, service):
        """Test that whitespace-only names are rejected."""
        command = CreateNotebookCommand(name="   ", created_by="user@example.com")

        result = service.create_notebook(command)

        assert result.is_failure

    def test_create_notebook_name_too_long(self, service):
        """Test that names exceeding max length are rejected."""
        command = CreateNotebookCommand(name="x" * 256, created_by="user@example.com")

        result = service.create_notebook(command)

        assert result.is_failure
        assert result.validation_errors is not None

    def test_create_notebook_tags_normalized(self, service):
        """Test that tags are normalized (lowercase, trimmed)."""
        command = CreateNotebookCommand(
            name="Tag Test",
            created_by="user@example.com",
            tags=["Research", " SCIENCE ", "data"]
        )

        result = service.create_notebook(command)

        assert result.is_success
        assert set(result.value.tags) == {"research", "science", "data"}

    def test_create_notebook_without_created_by(self, service):
        """Test that creating notebook without created_by fails."""
        command = CreateNotebookCommand(name="Test Notebook", created_by="")

        result = service.create_notebook(command)

        assert result.is_failure
        assert result.validation_errors is not None
        assert any("created_by" in err.field.lower() for err in result.validation_errors)

    def test_create_notebook_with_invalid_email(self, service):
        """Test that creating notebook with invalid email fails."""
        command = CreateNotebookCommand(name="Test Notebook", created_by="not-an-email")

        result = service.create_notebook(command)

        assert result.is_failure
        assert result.validation_errors is not None
        assert any(err.code == "INVALID_FORMAT" for err in result.validation_errors)


class TestGetNotebook:
    """Tests for retrieving notebooks."""

    def test_get_notebook_by_id_success(self, service):
        """Test successfully retrieving a notebook by ID."""
        create_cmd = CreateNotebookCommand(name="Test Notebook", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        query = GetNotebookByIdQuery(notebook_id=notebook_id)
        result = service.get_notebook_by_id(query)

        assert result.is_success
        assert result.value.id == notebook_id
        assert result.value.name == "Test Notebook"

    def test_get_notebook_by_id_not_found(self, service):
        """Test retrieving non-existent notebook."""
        query = GetNotebookByIdQuery(notebook_id=uuid4())
        result = service.get_notebook_by_id(query)

        assert result.is_failure
        assert "not found" in result.error.lower()


class TestUpdateNotebook:
    """Tests for updating notebooks."""

    def test_update_notebook_name(self, service):
        """Test updating notebook name."""
        create_cmd = CreateNotebookCommand(name="Original Name", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        update_cmd = UpdateNotebookCommand(
            notebook_id=notebook_id,
            name="Updated Name"
        )
        result = service.update_notebook(update_cmd)

        assert result.is_success
        assert result.value.name == "Updated Name"

    def test_update_notebook_description(self, service):
        """Test updating notebook description."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        update_cmd = UpdateNotebookCommand(
            notebook_id=notebook_id,
            description="New description"
        )
        result = service.update_notebook(update_cmd)

        assert result.is_success
        assert result.value.description == "New description"

    def test_update_notebook_tags(self, service):
        """Test updating notebook tags."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com", tags=["old"])
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        update_cmd = UpdateNotebookCommand(
            notebook_id=notebook_id,
            tags=["new", "tags"]
        )
        result = service.update_notebook(update_cmd)

        assert result.is_success
        assert set(result.value.tags) == {"new", "tags"}

    def test_update_notebook_not_found(self, service):
        """Test updating non-existent notebook."""
        update_cmd = UpdateNotebookCommand(
            notebook_id=uuid4(),
            name="New Name"
        )
        result = service.update_notebook(update_cmd)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_update_notebook_duplicate_name(self, service):
        """Test that updating to duplicate name is rejected."""
        service.create_notebook(CreateNotebookCommand(name="Notebook 1", created_by="user@example.com"))
        create_result = service.create_notebook(CreateNotebookCommand(name="Notebook 2", created_by="user@example.com"))
        notebook_id = create_result.value.id

        update_cmd = UpdateNotebookCommand(
            notebook_id=notebook_id,
            name="Notebook 1"
        )
        result = service.update_notebook(update_cmd)

        assert result.is_failure
        assert "already exists" in result.error.lower()


class TestRenameNotebook:
    """Tests for renaming notebooks."""

    def test_rename_notebook_success(self, service):
        """Test successful notebook rename."""
        create_cmd = CreateNotebookCommand(name="Old Name", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        rename_cmd = RenameNotebookCommand(
            notebook_id=notebook_id,
            new_name="New Name"
        )
        result = service.rename_notebook(rename_cmd)

        assert result.is_success
        assert result.value.name == "New Name"

    def test_rename_notebook_duplicate_name(self, service):
        """Test that renaming to duplicate name is rejected."""
        service.create_notebook(CreateNotebookCommand(name="Existing Name", created_by="user@example.com"))
        create_result = service.create_notebook(CreateNotebookCommand(name="To Rename", created_by="user@example.com"))
        notebook_id = create_result.value.id

        rename_cmd = RenameNotebookCommand(
            notebook_id=notebook_id,
            new_name="Existing Name"
        )
        result = service.rename_notebook(rename_cmd)

        assert result.is_failure
        assert "already exists" in result.error.lower()

    def test_rename_notebook_not_found(self, service):
        """Test renaming non-existent notebook."""
        rename_cmd = RenameNotebookCommand(
            notebook_id=uuid4(),
            new_name="New Name"
        )
        result = service.rename_notebook(rename_cmd)

        assert result.is_failure
        assert "not found" in result.error.lower()


class TestDeleteNotebook:
    """Tests for deleting notebooks."""

    def test_delete_empty_notebook(self, service):
        """Test deleting an empty notebook."""
        create_cmd = CreateNotebookCommand(name="To Delete", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        delete_cmd = DeleteNotebookCommand(notebook_id=notebook_id)
        result = service.delete_notebook(delete_cmd)

        assert result.is_success

        # Verify it's deleted
        query = GetNotebookByIdQuery(notebook_id=notebook_id)
        get_result = service.get_notebook_by_id(query)
        assert get_result.is_failure

    def test_delete_notebook_with_sources_without_cascade(self, service, repository):
        """Test that deleting notebook with sources requires cascade."""
        create_cmd = CreateNotebookCommand(name="With Sources", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook = create_result.value

        # Simulate having sources
        notebook.source_count = 2
        repository.update(notebook)

        delete_cmd = DeleteNotebookCommand(notebook_id=notebook.id, cascade=False)
        result = service.delete_notebook(delete_cmd)

        assert result.is_failure
        assert "cascade" in result.error.lower()

    def test_delete_notebook_not_found(self, service):
        """Test deleting non-existent notebook."""
        delete_cmd = DeleteNotebookCommand(notebook_id=uuid4())
        result = service.delete_notebook(delete_cmd)

        assert result.is_failure
        assert "not found" in result.error.lower()


class TestListNotebooks:
    """Tests for listing notebooks."""

    def test_list_notebooks_empty(self, service):
        """Test listing when no notebooks exist."""
        query = ListNotebooksQuery()
        result = service.list_notebooks(query)

        assert result.is_success
        assert len(result.value) == 0

    def test_list_notebooks_multiple(self, service):
        """Test listing multiple notebooks."""
        service.create_notebook(CreateNotebookCommand(name="Notebook 1", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Notebook 2", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Notebook 3", created_by="user@example.com"))

        query = ListNotebooksQuery()
        result = service.list_notebooks(query)

        assert result.is_success
        assert len(result.value) == 3

    def test_list_notebooks_sorted_by_name_asc(self, service):
        """Test listing notebooks sorted by name ascending."""
        service.create_notebook(CreateNotebookCommand(name="Charlie", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Alpha", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Bravo", created_by="user@example.com"))

        query = ListNotebooksQuery(sort_by=SortOption.NAME, sort_order=SortOrder.ASC)
        result = service.list_notebooks(query)

        assert result.is_success
        names = [nb.name for nb in result.value]
        assert names == ["Alpha", "Bravo", "Charlie"]

    def test_list_notebooks_sorted_by_name_desc(self, service):
        """Test listing notebooks sorted by name descending."""
        service.create_notebook(CreateNotebookCommand(name="Charlie", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Alpha", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="Bravo", created_by="user@example.com"))

        query = ListNotebooksQuery(sort_by=SortOption.NAME, sort_order=SortOrder.DESC)
        result = service.list_notebooks(query)

        assert result.is_success
        names = [nb.name for nb in result.value]
        assert names == ["Charlie", "Bravo", "Alpha"]

    def test_list_notebooks_filtered_by_tags(self, service):
        """Test listing notebooks filtered by tags."""
        service.create_notebook(CreateNotebookCommand(name="NB1", created_by="user@example.com", tags=["python"]))
        service.create_notebook(CreateNotebookCommand(name="NB2", created_by="user@example.com", tags=["javascript"]))
        service.create_notebook(CreateNotebookCommand(name="NB3", created_by="user@example.com", tags=["python", "data"]))

        query = ListNotebooksQuery(tags=["python"])
        result = service.list_notebooks(query)

        assert result.is_success
        assert len(result.value) == 2
        names = {nb.name for nb in result.value}
        assert names == {"NB1", "NB3"}

    def test_list_notebooks_with_pagination(self, service):
        """Test listing notebooks with pagination."""
        for i in range(10):
            service.create_notebook(CreateNotebookCommand(name=f"Notebook {i}", created_by="user@example.com"))

        query = ListNotebooksQuery(limit=5, offset=0)
        result = service.list_notebooks(query)

        assert result.is_success
        assert len(result.value) == 5


class TestTagOperations:
    """Tests for tag operations."""

    def test_add_tags(self, service):
        """Test adding tags to a notebook."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com", tags=["existing"])
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        add_cmd = AddTagsCommand(notebook_id=notebook_id, tags=["new", "tags"])
        result = service.add_tags(add_cmd)

        assert result.is_success
        assert set(result.value.tags) == {"existing", "new", "tags"}

    def test_add_tags_duplicates_ignored(self, service):
        """Test that duplicate tags are not added."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com", tags=["existing"])
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        add_cmd = AddTagsCommand(notebook_id=notebook_id, tags=["existing", "new"])
        result = service.add_tags(add_cmd)

        assert result.is_success
        assert set(result.value.tags) == {"existing", "new"}

    def test_remove_tags(self, service):
        """Test removing tags from a notebook."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com", tags=["tag1", "tag2", "tag3"])
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        remove_cmd = RemoveTagsCommand(notebook_id=notebook_id, tags=["tag2"])
        result = service.remove_tags(remove_cmd)

        assert result.is_success
        assert set(result.value.tags) == {"tag1", "tag3"}

    def test_remove_nonexistent_tags(self, service):
        """Test removing tags that don't exist (should succeed)."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com", tags=["tag1"])
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        remove_cmd = RemoveTagsCommand(notebook_id=notebook_id, tags=["nonexistent"])
        result = service.remove_tags(remove_cmd)

        assert result.is_success
        assert result.value.tags == ["tag1"]


class TestCheckExistence:
    """Tests for existence checking."""

    def test_check_exists_true(self, service):
        """Test checking if notebook exists (true case)."""
        create_cmd = CreateNotebookCommand(name="Test", created_by="user@example.com")
        create_result = service.create_notebook(create_cmd)
        notebook_id = create_result.value.id

        query = CheckNotebookExistsQuery(notebook_id=notebook_id)
        result = service.check_exists(query)

        assert result.is_success
        assert result.value is True

    def test_check_exists_false(self, service):
        """Test checking if notebook exists (false case)."""
        query = CheckNotebookExistsQuery(notebook_id=uuid4())
        result = service.check_exists(query)

        assert result.is_success
        assert result.value is False

    def test_check_name_exists_true(self, service):
        """Test checking if notebook name exists (true case)."""
        service.create_notebook(CreateNotebookCommand(name="Existing", created_by="user@example.com"))

        query = CheckNotebookNameExistsQuery(name="Existing")
        result = service.check_name_exists(query)

        assert result.is_success
        assert result.value is True

    def test_check_name_exists_false(self, service):
        """Test checking if notebook name exists (false case)."""
        query = CheckNotebookNameExistsQuery(name="Nonexistent")
        result = service.check_name_exists(query)

        assert result.is_success
        assert result.value is False

    def test_check_name_exists_with_exclusion(self, service):
        """Test checking name existence with ID exclusion."""
        create_result = service.create_notebook(CreateNotebookCommand(name="Test", created_by="user@example.com"))
        notebook_id = create_result.value.id

        query = CheckNotebookNameExistsQuery(name="Test", exclude_id=notebook_id)
        result = service.check_name_exists(query)

        assert result.is_success
        assert result.value is False


class TestGetCount:
    """Tests for getting notebook count."""

    def test_get_count_empty(self, service):
        """Test getting count when no notebooks exist."""
        result = service.get_count()

        assert result.is_success
        assert result.value == 0

    def test_get_count_multiple(self, service):
        """Test getting count with multiple notebooks."""
        service.create_notebook(CreateNotebookCommand(name="NB1", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="NB2", created_by="user@example.com"))
        service.create_notebook(CreateNotebookCommand(name="NB3", created_by="user@example.com"))

        result = service.get_count()

        assert result.is_success
        assert result.value == 3
