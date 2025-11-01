"""Unit tests for SourceIngestionService."""
import pytest
from uuid import uuid4
from unittest.mock import Mock

from src.core.services.source_ingestion_service import SourceIngestionService
from src.core.commands.source_commands import (
    ImportFileSourceCommand,
    ImportUrlSourceCommand,
    DeleteSourceCommand,
    RestoreSourceCommand,
    RenameSourceCommand,
    ExtractContentCommand
)
from src.core.queries.source_queries import (
    GetSourceByIdQuery,
    ListSourcesQuery,
    CheckSourceExistsQuery,
    CheckDuplicateSourceQuery,
    GetSourceCountQuery
)
from src.core.value_objects.enums import FileType, SourceType, SortOption, SortOrder
from src.core.entities.notebook import Notebook
from src.core.interfaces.providers.i_web_fetch_provider import WebContent
from src.core.results.result import Result
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.infrastructure.repositories.in_memory_source_repository import InMemorySourceRepository


@pytest.fixture
def notebook_repository():
    """Fixture to provide a fresh notebook repository."""
    return InMemoryNotebookRepository()


@pytest.fixture
def source_repository():
    """Fixture to provide a fresh source repository."""
    return InMemorySourceRepository()


@pytest.fixture
def file_storage_provider():
    """Mock file storage provider."""
    provider = Mock()
    provider.store_file.return_value = Result.success("stored/path/file.pdf")
    provider.delete_file.return_value = Result.success(None)
    return provider


@pytest.fixture
def content_extraction_provider():
    """Mock content extraction provider."""
    provider = Mock()
    provider.extract_text.return_value = Result.success("Extracted text content from file")
    return provider


@pytest.fixture
def web_fetch_provider():
    """Mock web fetch provider."""
    provider = Mock()
    web_content = WebContent(
        url="https://example.com",
        title="Example Page",
        html="<html>...</html>",
        text="Main content from the web page",
        metadata={"author": "John Doe"}
    )
    provider.fetch_url.return_value = Result.success(web_content)
    return provider


@pytest.fixture
def service(notebook_repository, source_repository, file_storage_provider,
            content_extraction_provider, web_fetch_provider):
    """Fixture to provide a service instance with dependencies."""
    return SourceIngestionService(
        source_repository=source_repository,
        notebook_repository=notebook_repository,
        file_storage_provider=file_storage_provider,
        content_extraction_provider=content_extraction_provider,
        web_fetch_provider=web_fetch_provider
    )


@pytest.fixture
def test_notebook(notebook_repository):
    """Create a test notebook."""
    notebook = Notebook.create(name="Test Notebook", description="For testing").value
    notebook_repository.add(notebook)
    return notebook


class TestImportFileSource:
    """Tests for importing file sources."""

    def test_import_file_source_success(self, service, test_notebook):
        """Test successful file source import."""
        command = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test Document.pdf",
            file_type=FileType.PDF,
            file_content=b"PDF content here",
            metadata={"pages": 10}
        )

        result = service.import_file_source(command)

        assert result.is_success
        assert result.value.name == "Test Document.pdf"
        assert result.value.file_type == FileType.PDF
        assert result.value.source_type == SourceType.FILE
        assert result.value.notebook_id == test_notebook.id
        assert result.value.extracted_text == "Extracted text content from file"

    def test_import_file_source_notebook_not_found(self, service):
        """Test importing to non-existent notebook fails."""
        command = ImportFileSourceCommand(
            notebook_id=uuid4(),
            file_name="Test.pdf",
            file_type=FileType.PDF,
            file_content=b"content"
        )

        result = service.import_file_source(command)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_import_file_source_file_too_large(self, service, test_notebook):
        """Test importing file that exceeds size limit fails."""
        # Create content larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)

        command = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Large File.pdf",
            file_type=FileType.PDF,
            file_content=large_content
        )

        result = service.import_file_source(command)

        assert result.is_failure
        assert result.validation_errors is not None
        assert any("size" in err.message.lower() for err in result.validation_errors)

    def test_import_file_source_duplicate_content(self, service, test_notebook):
        """Test importing duplicate content is rejected."""
        content = b"Same content"
        command1 = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="File 1.txt",
            file_type=FileType.TXT,
            file_content=content
        )

        # First import should succeed
        result1 = service.import_file_source(command1)
        assert result1.is_success

        # Second import with same content should fail
        command2 = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="File 2.txt",
            file_type=FileType.TXT,
            file_content=content
        )

        result2 = service.import_file_source(command2)
        assert result2.is_failure
        assert "duplicate" in result2.error.lower()

    def test_import_file_source_empty_name(self, service, test_notebook):
        """Test importing with empty name fails."""
        command = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="",
            file_type=FileType.PDF,
            file_content=b"content"
        )

        result = service.import_file_source(command)

        assert result.is_failure
        assert result.validation_errors is not None


class TestImportUrlSource:
    """Tests for importing URL sources."""

    def test_import_url_source_success(self, service, test_notebook):
        """Test successful URL source import."""
        command = ImportUrlSourceCommand(
            notebook_id=test_notebook.id,
            url="https://example.com/article",
            title="Example Article"
        )

        result = service.import_url_source(command)

        assert result.is_success
        assert result.value.name == "Example Article"
        assert result.value.url == "https://example.com/article"
        assert result.value.source_type == SourceType.URL
        assert result.value.extracted_text == "Main content from the web page"

    def test_import_url_source_without_title(self, service, test_notebook):
        """Test URL import uses fetched title when not provided."""
        command = ImportUrlSourceCommand(
            notebook_id=test_notebook.id,
            url="https://example.com/article"
        )

        result = service.import_url_source(command)

        assert result.is_success
        assert result.value.name == "Example Page"  # From mocked WebContent

    def test_import_url_source_notebook_not_found(self, service):
        """Test importing to non-existent notebook fails."""
        command = ImportUrlSourceCommand(
            notebook_id=uuid4(),
            url="https://example.com"
        )

        result = service.import_url_source(command)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_import_url_source_fetch_failure(self, service, test_notebook, web_fetch_provider):
        """Test import fails when URL fetch fails."""
        web_fetch_provider.fetch_url.return_value = Result.failure("Network error")

        command = ImportUrlSourceCommand(
            notebook_id=test_notebook.id,
            url="https://example.com"
        )

        result = service.import_url_source(command)

        assert result.is_failure
        assert "fetch" in result.error.lower()

    def test_import_url_source_duplicate_content(self, service, test_notebook):
        """Test importing duplicate URL content is rejected."""
        command1 = ImportUrlSourceCommand(
            notebook_id=test_notebook.id,
            url="https://example.com/page1"
        )

        # First import should succeed
        result1 = service.import_url_source(command1)
        assert result1.is_success

        # Second import with same content should fail (same mock content)
        command2 = ImportUrlSourceCommand(
            notebook_id=test_notebook.id,
            url="https://example.com/page2"
        )

        result2 = service.import_url_source(command2)
        assert result2.is_failure
        assert "duplicate" in result2.error.lower()


class TestDeleteSource:
    """Tests for deleting sources."""

    def test_delete_source_success(self, service, test_notebook):
        """Test successful source deletion."""
        # Create a source first
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Delete the source
        delete_cmd = DeleteSourceCommand(
            source_id=source_id,
            notebook_id=test_notebook.id
        )
        result = service.delete_source(delete_cmd)

        assert result.is_success

        # Verify source is soft-deleted
        get_query = GetSourceByIdQuery(source_id=source_id, include_deleted=False)
        get_result = service.get_source_by_id(get_query)
        assert get_result.is_failure

        # Verify it exists with include_deleted=True
        get_query_with_deleted = GetSourceByIdQuery(source_id=source_id, include_deleted=True)
        get_result_with_deleted = service.get_source_by_id(get_query_with_deleted)
        assert get_result_with_deleted.is_success

    def test_delete_source_not_found(self, service, test_notebook):
        """Test deleting non-existent source fails."""
        delete_cmd = DeleteSourceCommand(
            source_id=uuid4(),
            notebook_id=test_notebook.id
        )
        result = service.delete_source(delete_cmd)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_delete_source_wrong_notebook(self, service, test_notebook, notebook_repository):
        """Test deleting source from wrong notebook fails."""
        # Create another notebook
        other_notebook = Notebook.create(name="Other Notebook").value
        notebook_repository.add(other_notebook)

        # Create source in first notebook
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Try to delete from wrong notebook
        delete_cmd = DeleteSourceCommand(
            source_id=source_id,
            notebook_id=other_notebook.id
        )
        result = service.delete_source(delete_cmd)

        assert result.is_failure
        assert "does not belong" in result.error.lower()


class TestRestoreSource:
    """Tests for restoring deleted sources."""

    def test_restore_source_success(self, service, test_notebook):
        """Test successful source restoration."""
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        delete_cmd = DeleteSourceCommand(source_id=source_id, notebook_id=test_notebook.id)
        service.delete_source(delete_cmd)

        # Restore the source
        restore_cmd = RestoreSourceCommand(
            source_id=source_id,
            notebook_id=test_notebook.id
        )
        result = service.restore_source(restore_cmd)

        assert result.is_success

        # Verify source is accessible again
        get_query = GetSourceByIdQuery(source_id=source_id)
        get_result = service.get_source_by_id(get_query)
        assert get_result.is_success

    def test_restore_source_not_deleted(self, service, test_notebook):
        """Test restoring non-deleted source fails."""
        # Create a source (not deleted)
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Try to restore
        restore_cmd = RestoreSourceCommand(
            source_id=source_id,
            notebook_id=test_notebook.id
        )
        result = service.restore_source(restore_cmd)

        assert result.is_failure
        assert "not deleted" in result.error.lower()


class TestRenameSource:
    """Tests for renaming sources."""

    def test_rename_source_success(self, service, test_notebook):
        """Test successful source rename."""
        # Create a source
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Original Name.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Rename the source
        rename_cmd = RenameSourceCommand(
            source_id=source_id,
            notebook_id=test_notebook.id,
            new_name="New Name.txt"
        )
        result = service.rename_source(rename_cmd)

        assert result.is_success
        assert result.value.name == "New Name.txt"

    def test_rename_source_empty_name(self, service, test_notebook):
        """Test renaming with empty name fails."""
        # Create a source
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Try to rename with empty name
        rename_cmd = RenameSourceCommand(
            source_id=source_id,
            notebook_id=test_notebook.id,
            new_name=""
        )
        result = service.rename_source(rename_cmd)

        assert result.is_failure


class TestExtractContent:
    """Tests for content extraction."""

    def test_extract_content_success(self, service, test_notebook):
        """Test successful content extraction."""
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.pdf",
            file_type=FileType.PDF,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Extract content
        extract_cmd = ExtractContentCommand(
            source_id=source_id,
            notebook_id=test_notebook.id
        )
        result = service.extract_content(extract_cmd)

        assert result.is_success
        assert result.value.id == source_id
        assert len(result.value.extracted_text) > 0

    def test_extract_content_already_extracted(self, service, test_notebook):
        """Test that already extracted content is returned without re-extraction."""
        # Create a source (auto-extracts on import)
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.pdf",
            file_type=FileType.PDF,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        # Extract content (should return cached)
        extract_cmd = ExtractContentCommand(
            source_id=source_id,
            notebook_id=test_notebook.id,
            force_reextract=False
        )
        result = service.extract_content(extract_cmd)

        assert result.is_success
        assert result.value.id == source_id


class TestListSources:
    """Tests for listing sources."""

    def test_list_sources_empty(self, service, test_notebook):
        """Test listing when no sources exist."""
        query = ListSourcesQuery(notebook_id=test_notebook.id)
        result = service.list_sources(query)

        assert result.is_success
        assert len(result.value) == 0

    def test_list_sources_multiple(self, service, test_notebook):
        """Test listing multiple sources."""
        # Import multiple sources
        for i in range(3):
            cmd = ImportFileSourceCommand(
                notebook_id=test_notebook.id,
                file_name=f"File {i}.txt",
                file_type=FileType.TXT,
                file_content=f"content{i}".encode()
            )
            service.import_file_source(cmd)

        query = ListSourcesQuery(notebook_id=test_notebook.id)
        result = service.list_sources(query)

        assert result.is_success
        assert len(result.value) == 3

    def test_list_sources_sorted_by_name(self, service, test_notebook):
        """Test listing sources sorted by name."""
        # Import sources in non-alphabetical order
        names = ["Charlie", "Alpha", "Bravo"]
        for name in names:
            cmd = ImportFileSourceCommand(
                notebook_id=test_notebook.id,
                file_name=f"{name}.txt",
                file_type=FileType.TXT,
                file_content=name.encode()
            )
            service.import_file_source(cmd)

        query = ListSourcesQuery(
            notebook_id=test_notebook.id,
            sort_by=SortOption.NAME,
            sort_order=SortOrder.ASC
        )
        result = service.list_sources(query)

        assert result.is_success
        names = [src.name for src in result.value]
        assert names == ["Alpha.txt", "Bravo.txt", "Charlie.txt"]

    def test_list_sources_exclude_deleted(self, service, test_notebook):
        """Test listing excludes deleted sources by default."""
        # Import sources
        cmd1 = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="File 1.txt",
            file_type=FileType.TXT,
            file_content=b"content1"
        )
        result1 = service.import_file_source(cmd1)

        cmd2 = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="File 2.txt",
            file_type=FileType.TXT,
            file_content=b"content2"
        )
        service.import_file_source(cmd2)

        # Delete first source
        delete_cmd = DeleteSourceCommand(
            source_id=result1.value.id,
            notebook_id=test_notebook.id
        )
        service.delete_source(delete_cmd)

        # List without deleted
        query = ListSourcesQuery(notebook_id=test_notebook.id, include_deleted=False)
        result = service.list_sources(query)

        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0].name == "File 2.txt"


class TestCheckOperations:
    """Tests for check operations."""

    def test_check_exists_true(self, service, test_notebook):
        """Test checking if source exists (true case)."""
        # Create a source
        import_cmd = ImportFileSourceCommand(
            notebook_id=test_notebook.id,
            file_name="Test.txt",
            file_type=FileType.TXT,
            file_content=b"content"
        )
        import_result = service.import_file_source(import_cmd)
        source_id = import_result.value.id

        query = CheckSourceExistsQuery(source_id=source_id)
        result = service.check_exists(query)

        assert result.is_success
        assert result.value is True

    def test_check_exists_false(self, service):
        """Test checking if source exists (false case)."""
        query = CheckSourceExistsQuery(source_id=uuid4())
        result = service.check_exists(query)

        assert result.is_success
        assert result.value is False

    def test_get_count(self, service, test_notebook):
        """Test getting source count."""
        # Import sources
        for i in range(3):
            cmd = ImportFileSourceCommand(
                notebook_id=test_notebook.id,
                file_name=f"File {i}.txt",
                file_type=FileType.TXT,
                file_content=f"content{i}".encode()
            )
            service.import_file_source(cmd)

        query = GetSourceCountQuery(notebook_id=test_notebook.id)
        result = service.get_count(query)

        assert result.is_success
        assert result.value == 3
