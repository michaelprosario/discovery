"""Value object enums for the Discovery application."""
from enum import Enum


class SourceType(str, Enum):
    """Type of source material."""
    FILE = "file"
    URL = "url"
    TEXT = "text"


class FileType(str, Enum):
    """Supported file types for file sources."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"


class OutputType(str, Enum):
    """Type of generated output."""
    SUMMARY = "summary"
    BLOG_POST = "blog_post"
    BRIEFING = "briefing"
    REPORT = "report"
    ESSAY = "essay"
    FAQ = "faq"
    MEETING_NOTES = "meeting_notes"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    CUSTOM = "custom"


class OutputStatus(str, Enum):
    """Status of output file generation."""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class SortOption(str, Enum):
    """Sort options for listings."""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SOURCE_COUNT = "source_count"


class SortOrder(str, Enum):
    """Sort order direction."""
    ASC = "asc"
    DESC = "desc"
