# Domain Model

This document defines the domain entities and services for the Discovery application, following Clean Architecture principles where the Core contains business logic independent of infrastructure concerns.

## Rules for repositories that do CRUD
- provide a way to add domain entity
- provide a way to update domain entity
- provide a way to upsert domain entity
- provide a way to get entity by Id(Guid)
- provide a way to check if entity exists by Id(Guid)


## Domain Entities

Domain entities represent the core business objects with identity, behavior, and business rules. They reside in the **Core** layer.

---

### 1. Notebook

**Description:** A collection container for organizing related sources and outputs around a specific research topic or project.

**Properties:**
- `id: UUID` - Unique identifier
- `name: string` - Notebook name (required, max 255 chars)
- `description: string?` - Optional description (max 2000 chars)
- `tags: List<string>` - Categorization tags
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last modification timestamp
- `sources: List<Source>` - Collection of sources (1:many relationship)
- `outputs: List<OutputFile>` - Collection of generated outputs (1:many relationship)

**Business Rules:**
- Name must be non-empty and trimmed
- Name must be unique per user
- Tags are normalized (lowercase, trimmed)
- Cannot be deleted if it contains sources or outputs without cascade
- Updated timestamp changes on any modification to notebook or its children

**Domain Methods:**
```python
add_source(source: Source) -> Result
remove_source(source_id: UUID) -> Result
add_output(output: OutputFile) -> Result
rename(new_name: string) -> Result
add_tags(tags: List<string>) -> Result
remove_tags(tags: List<string>) -> Result
get_source_count() -> int
get_total_size() -> int  # Total size in bytes
```

---

### 2. Source

**Description:** A research material imported into a notebook (file or URL).

**Properties:**
- `id: UUID` - Unique identifier
- `notebook_id: UUID` - Parent notebook reference
- `name: string` - Display name (required)
- `source_type: SourceType` - Enum: FILE, URL
- `file_type: FileType?` - Enum: PDF, DOCX, DOC, TXT, MD (for FILE type)
- `url: string?` - Source URL (for URL type)
- `file_path: string?` - Local file path (for FILE type)
- `file_size: int?` - Size in bytes
- `content_hash: string` - SHA256 hash of content
- `extracted_text: string` - Extracted text content
- `metadata: dict` - Additional metadata (author, page count, etc.)
- `created_at: datetime` - Import timestamp
- `updated_at: datetime` - Last modification timestamp
- `deleted_at: datetime?` - Soft delete timestamp

**Business Rules:**
- Either file_path or url must be set based on source_type
- File size must be positive and within limits (e.g., max 50MB)
- Content hash used for duplicate detection
- Name defaults to filename or page title if not provided
- Soft delete: deleted_at set instead of physical deletion
- Cannot modify extracted_text directly (regenerate from source)

**Domain Methods:**
```python
rename(new_name: string) -> Result
extract_content() -> Result<string>
is_deleted() -> bool
soft_delete() -> Result
restore() -> Result
get_preview(length: int = 500) -> string
validate_file_type() -> Result
```

---

### 3. OutputFile

**Description:** A generated document synthesized from notebook sources using templates and prompts.

**Properties:**
- `id: UUID` - Unique identifier
- `notebook_id: UUID` - Parent notebook reference
- `title: string` - Output title (required)
- `content: string` - Generated content (markdown format)
- `template_id: UUID?` - Reference to template used (optional)
- `custom_prompt: string?` - User-provided prompt
- `output_type: OutputType` - Enum: SUMMARY, BLOG_POST, BRIEFING, REPORT, ESSAY, CUSTOM
- `parameters: dict` - Generation parameters (length, tone, style, etc.)
- `source_ids: List<UUID>` - Sources used in generation
- `version: int` - Version number for tracking regenerations
- `status: OutputStatus` - Enum: DRAFT, GENERATING, COMPLETED, FAILED
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last modification timestamp
- `generated_at: datetime?` - Completion timestamp
- `deleted_at: datetime?` - Soft delete timestamp

**Business Rules:**
- Title must be non-empty
- Content must be valid markdown
- Version increments on regeneration
- Status transitions: DRAFT -> GENERATING -> COMPLETED/FAILED
- Source IDs must reference valid sources in the notebook
- Cannot delete if status is GENERATING
- Soft delete: deleted_at set instead of physical deletion

**Domain Methods:**
```python
update_content(content: string) -> Result
mark_as_generating() -> Result
mark_as_completed() -> Result
mark_as_failed(error: string) -> Result
regenerate(prompt: string?, template_id: UUID?) -> Result
soft_delete() -> Result
restore() -> Result
get_source_citations() -> List<Source>
increment_version() -> int
```

---

### 4. OutputFileTemplate

**Description:** A reusable structure/format definition for generating outputs with consistent sections and formatting.

**Properties:**
- `id: UUID` - Unique identifier
- `name: string` - Template name (required, unique)
- `description: string` - Template description
- `output_type: OutputType` - Associated output type
- `sections: List<TemplateSection>` - Ordered list of sections
- `system_prompt: string` - Base prompt for LLM
- `default_parameters: dict` - Default generation parameters
- `is_system: bool` - System template (cannot be deleted/modified)
- `is_active: bool` - Active/archived status
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last modification timestamp

**Business Rules:**
- Name must be unique
- System templates cannot be modified or deleted
- At least one section required
- Sections must be ordered (have sequence numbers)
- Default parameters must be valid JSON

**Domain Methods:**
```python
add_section(section: TemplateSection) -> Result
remove_section(section_id: UUID) -> Result
reorder_sections(section_order: List<UUID>) -> Result
update_prompt(prompt: string) -> Result
clone(new_name: string) -> OutputFileTemplate
validate_structure() -> Result
```

---

### 5. TemplateSection

**Description:** A section definition within an output template.

**Properties:**
- `id: UUID` - Unique identifier
- `template_id: UUID` - Parent template reference
- `name: string` - Section name (e.g., "Introduction", "Key Findings")
- `description: string` - What this section should contain
- `prompt_instructions: string` - Specific instructions for LLM
- `sequence: int` - Order within template
- `is_required: bool` - Whether section must be included
- `min_length: int?` - Minimum word count
- `max_length: int?` - Maximum word count

**Business Rules:**
- Section name required within template
- Sequence must be positive
- Length constraints: min_length < max_length if both set
- Required sections cannot be removed

**Domain Methods:**
```python
update_instructions(instructions: string) -> Result
set_length_constraints(min: int?, max: int?) -> Result
```

---

## Value Objects

Value objects are immutable objects defined by their attributes rather than identity.

### SourceType (Enum)
```python
FILE = "file"
URL = "url"
```

### FileType (Enum)
```python
PDF = "pdf"
DOCX = "docx"
DOC = "doc"
TXT = "txt"
MD = "md"
```

### OutputType (Enum)
```python
SUMMARY = "summary"
BLOG_POST = "blog_post"
BRIEFING = "briefing"
REPORT = "report"
ESSAY = "essay"
FAQ = "faq"
MEETING_NOTES = "meeting_notes"
COMPARATIVE_ANALYSIS = "comparative_analysis"
CUSTOM = "custom"
```

### OutputStatus (Enum)
```python
DRAFT = "draft"
GENERATING = "generating"
COMPLETED = "completed"
FAILED = "failed"
```

### GenerationParameters (Value Object)
```python
class GenerationParameters:
    length: LengthOption  # SHORT, MEDIUM, LONG
    tone: ToneOption  # FORMAL, CASUAL, ACADEMIC, CONVERSATIONAL
    style: string?  # Additional style guidance
    include_citations: bool
    max_tokens: int?
```

---

## Domain Services

Domain services contain business logic that doesn't naturally fit within a single entity. They orchestrate operations across entities and depend on interfaces (abstractions) defined in Core.

---

### 1. NotebookManagementService

**Purpose:** Manages notebook lifecycle operations and enforces business rules across notebooks.

**Dependencies (Interfaces):**
- `INotebookRepository` - Persistence abstraction
- `ISourceRepository` - Source persistence abstraction
- `IOutputRepository` - Output persistence abstraction

**Methods:**

#### CreateNotebook
```python
def create_notebook(command: CreateNotebookCommand) -> Result<Notebook>
```
**Business Logic:**
- Validates notebook name uniqueness
- Normalizes tags
- Generates UUID and timestamps
- Creates notebook entity
- Persists via repository

**Returns:** `Result<Notebook>` with success/failure status

---

#### DeleteNotebook
```python
def delete_notebook(command: DeleteNotebookCommand) -> Result
```
**Business Logic:**
- Validates notebook exists
- Checks if notebook has sources/outputs
- If cascade flag set: soft delete all children
- If not cascade: return failure with validation message
- Soft deletes notebook

**Returns:** `Result` with success/failure status

---

#### RenameNotebook
```python
def rename_notebook(command: RenameNotebookCommand) -> Result<Notebook>
```
**Business Logic:**
- Validates new name not empty
- Checks name uniqueness
- Updates notebook name and timestamp
- Persists changes

**Returns:** `Result<Notebook>` with updated notebook

---

#### ListNotebooks
```python
def list_notebooks(query: ListNotebooksQuery) -> Result<List<NotebookSummary>>
```
**Business Logic:**
- Applies filters (tags, date range)
- Applies sorting (name, date, source count)
- Returns notebook summaries with metadata

**Returns:** `Result<List<NotebookSummary>>`

---

### 2. SourceIngestionService

**Purpose:** Handles importing and processing sources from various origins.

**Dependencies (Interfaces):**
- `ISourceRepository` - Source persistence
- `IFileStorageProvider` - File system abstraction
- `IContentExtractionProvider` - Text extraction abstraction
- `IWebFetchProvider` - URL fetching abstraction
- `INotebookRepository` - Notebook validation

**Methods:**

#### ImportFileSource
```python
def import_file_source(command: ImportFileSourceCommand) -> Result<Source>
```
**Business Logic:**
- Validates notebook exists
- Validates file type supported
- Validates file size within limits
- Calculates content hash
- Checks for duplicates (same hash in notebook)
- Stores original file via IFileStorageProvider
- Extracts text via IContentExtractionProvider
- Creates Source entity
- Persists via repository

**Returns:** `Result<Source>` with created source

---

#### ImportUrlSource
```python
def import_url_source(command: ImportUrlSourceCommand) -> Result<Source>
```
**Business Logic:**
- Validates notebook exists
- Validates URL format
- Fetches content via IWebFetchProvider
- Extracts main content (remove ads/navigation)
- Calculates content hash
- Checks for duplicates
- Creates Source entity with URL metadata
- Persists via repository

**Returns:** `Result<Source>` with created source

---

#### DeleteSource
```python
def delete_source(command: DeleteSourceCommand) -> Result
```
**Business Logic:**
- Validates source exists
- Checks if used in active output generation
- Soft deletes source
- Updates notebook's updated_at timestamp

**Returns:** `Result` with success/failure status

---

#### ExtractContentFromSource
```python
def extract_content(command: ExtractContentCommand) -> Result<string>
```
**Business Logic:**
- Validates source exists
- Determines extraction strategy based on file type
- Delegates to IContentExtractionProvider
- Updates source extracted_text
- Handles extraction failures gracefully

**Returns:** `Result<string>` with extracted text

---

### 3. OutputGenerationService

**Purpose:** Orchestrates AI-powered output generation from notebook sources.

**Dependencies (Interfaces):**
- `IOutputRepository` - Output persistence
- `ISourceRepository` - Source retrieval
- `ITemplateRepository` - Template retrieval
- `ILlmProvider` - LLM API abstraction
- `INotebookRepository` - Notebook validation

**Methods:**

#### GenerateSummary
```python
def generate_summary(command: GenerateSummaryCommand) -> Result<OutputFile>
```
**Business Logic:**
- Validates sources exist and belong to notebook
- Retrieves source content
- Concatenates with delimiters
- Validates total token count within limits
- Constructs prompt based on length parameter
- Calls ILlmProvider for generation
- Creates OutputFile entity (type: SUMMARY)
- Persists via repository
- Handles API failures and retries

**Returns:** `Result<OutputFile>` with generated summary

---

#### GenerateOutputFromTemplate
```python
def generate_output(command: GenerateOutputCommand) -> Result<OutputFile>
```
**Business Logic:**
- Validates notebook exists and has sources
- Retrieves template if template_id provided
- Validates custom_prompt if provided
- Determines sources to include (all or selected)
- Retrieves source content
- Constructs multi-part prompt:
  - Template system prompt
  - Section instructions
  - Custom user prompt
  - Source content
- Validates total token count
- Creates OutputFile entity with status GENERATING
- Calls ILlmProvider with streaming
- Updates OutputFile with generated content
- Marks as COMPLETED or FAILED
- Persists via repository

**Returns:** `Result<OutputFile>` with generated output

---

#### RegenerateOutput
```python
def regenerate_output(command: RegenerateOutputCommand) -> Result<OutputFile>
```
**Business Logic:**
- Validates output exists
- Increments version number
- Uses original parameters unless overridden
- Calls generate_output with updated parameters
- Maintains history of previous versions

**Returns:** `Result<OutputFile>` with regenerated output

---

#### DeleteOutput
```python
def delete_output(command: DeleteOutputCommand) -> Result
```
**Business Logic:**
- Validates output exists
- Checks status not GENERATING
- Soft deletes output
- Updates notebook's updated_at timestamp

**Returns:** `Result` with success/failure status

---

### 4. TemplateManagementService

**Purpose:** Manages output template lifecycle and customization.

**Dependencies (Interfaces):**
- `ITemplateRepository` - Template persistence

**Methods:**

#### CreateTemplate
```python
def create_template(command: CreateTemplateCommand) -> Result<OutputFileTemplate>
```
**Business Logic:**
- Validates name uniqueness
- Validates at least one section provided
- Validates section sequence numbers
- Creates OutputFileTemplate entity
- Creates TemplateSection entities
- Persists via repository

**Returns:** `Result<OutputFileTemplate>`

---

#### UpdateTemplate
```python
def update_template(command: UpdateTemplateCommand) -> Result<OutputFileTemplate>
```
**Business Logic:**
- Validates template exists
- Checks not system template (is_system = false)
- Updates allowed fields
- Validates structure after update
- Persists changes

**Returns:** `Result<OutputFileTemplate>`

---

#### CloneTemplate
```python
def clone_template(command: CloneTemplateCommand) -> Result<OutputFileTemplate>
```
**Business Logic:**
- Validates source template exists
- Creates deep copy with new name
- Sets is_system = false
- Persists new template

**Returns:** `Result<OutputFileTemplate>`

---

#### ListTemplates
```python
def list_templates(query: ListTemplatesQuery) -> Result<List<OutputFileTemplate>>
```
**Business Logic:**
- Filters by output_type if specified
- Filters by is_active
- Returns all matching templates

**Returns:** `Result<List<OutputFileTemplate>>`

---

### 5. SearchService

**Purpose:** Provides cross-notebook search functionality.

**Dependencies (Interfaces):**
- `ISearchProvider` - Full-text search abstraction
- `INotebookRepository` - Notebook access
- `ISourceRepository` - Source access
- `IOutputRepository` - Output access

**Methods:**

#### SearchAll
```python
def search_all(query: SearchQuery) -> Result<SearchResults>
```
**Business Logic:**
- Validates search term not empty
- Delegates to ISearchProvider
- Applies filters (type, date range, tags)
- Returns unified results with relevance ranking
- Includes preview snippets with highlighted terms

**Returns:** `Result<SearchResults>` containing notebooks, sources, and outputs

---

#### IndexContent
```python
def index_content(command: IndexContentCommand) -> Result
```
**Business Logic:**
- Determines entity type (notebook, source, output)
- Extracts indexable content
- Delegates to ISearchProvider for indexing
- Handles indexing failures

**Returns:** `Result` with success/failure status

---

## Command and Query Objects (CQRS Pattern)

Following Clean Architecture, all service methods accept Command or Query objects as inputs.

### Sample Commands

```python
class CreateNotebookCommand:
    name: string
    description: string?
    tags: List<string>

class ImportFileSourceCommand:
    notebook_id: UUID
    file_path: string
    file_name: string
    file_type: FileType

class GenerateOutputCommand:
    notebook_id: UUID
    template_id: UUID?
    custom_prompt: string?
    source_ids: List<UUID>?  # None = use all sources
    parameters: GenerationParameters
```

### Sample Queries

```python
class ListNotebooksQuery:
    tags: List<string>?
    date_from: datetime?
    date_to: datetime?
    sort_by: SortOption
    sort_order: SortOrder

class SearchQuery:
    search_term: string
    entity_types: List<EntityType>?  # None = all types
    tags: List<string>?
    date_from: datetime?
    date_to: datetime?
    max_results: int = 100
```

---

## Result Pattern

All domain service methods return a `Result<T>` object for consistent error handling:

```python
class Result<T>:
    is_success: bool
    is_failure: bool
    value: T?
    error: string?
    validation_errors: List<ValidationError>?

    @staticmethod
    def success(value: T) -> Result<T>

    @staticmethod
    def failure(error: string) -> Result<T>

    @staticmethod
    def validation_failure(errors: List<ValidationError>) -> Result<T>
```

**Benefits:**
- No exceptions for business rule violations
- Explicit success/failure handling
- Rich error information for UI display
- Consistent API across all services

---

## Repository Interfaces (Abstractions)

These interfaces are **defined in Core** but **implemented in Infrastructure**.

```python
class INotebookRepository:
    def get_by_id(id: UUID) -> Notebook?
    def get_all() -> List<Notebook>
    def add(notebook: Notebook) -> Result
    def update(notebook: Notebook) -> Result
    def delete(id: UUID) -> Result
    def exists_by_name(name: string) -> bool

class ISourceRepository:
    def get_by_id(id: UUID) -> Source?
    def get_by_notebook(notebook_id: UUID) -> List<Source>
    def add(source: Source) -> Result
    def update(source: Source) -> Result
    def soft_delete(id: UUID) -> Result

class IOutputRepository:
    def get_by_id(id: UUID) -> OutputFile?
    def get_by_notebook(notebook_id: UUID) -> List<OutputFile>
    def add(output: OutputFile) -> Result
    def update(output: OutputFile) -> Result
    def soft_delete(id: UUID) -> Result

class ITemplateRepository:
    def get_by_id(id: UUID) -> OutputFileTemplate?
    def get_all_active() -> List<OutputFileTemplate>
    def add(template: OutputFileTemplate) -> Result
    def update(template: OutputFileTemplate) -> Result
    def delete(id: UUID) -> Result
```

---

## Provider Interfaces (Abstractions)

These interfaces abstract external dependencies and are **defined in Core**, **implemented in Infrastructure**.

```python
class IFileStorageProvider:
    def store_file(source_path: string, destination: string) -> Result<string>
    def retrieve_file(path: string) -> Result<bytes>
    def delete_file(path: string) -> Result
    def get_file_size(path: string) -> Result<int>

class IContentExtractionProvider:
    def extract_text_from_pdf(file_path: string) -> Result<string>
    def extract_text_from_docx(file_path: string) -> Result<string>
    def extract_text_from_txt(file_path: string) -> Result<string>

class IWebFetchProvider:
    def fetch_url(url: string) -> Result<WebContent>
    def extract_main_content(html: string) -> Result<string>

class ILlmProvider:
    def generate(prompt: string, parameters: dict) -> Result<string>
    def generate_stream(prompt: string, parameters: dict) -> IAsyncIterator<string>
    def count_tokens(text: string) -> int

class ISearchProvider:
    def index_document(id: UUID, content: string, metadata: dict) -> Result
    def search(query: string, filters: dict) -> Result<List<SearchHit>>
    def delete_document(id: UUID) -> Result
```

---

## Domain Architecture Summary

**Core Project Structure:**
```
/core
  /entities
    - notebook.py
    - source.py
    - output_file.py
    - output_file_template.py
    - template_section.py
  /value_objects
    - enums.py
    - generation_parameters.py
  /services
    - notebook_management_service.py
    - source_ingestion_service.py
    - output_generation_service.py
    - template_management_service.py
    - search_service.py
  /interfaces
    /repositories
      - i_notebook_repository.py
      - i_source_repository.py
      - i_output_repository.py
      - i_template_repository.py
    /providers
      - i_file_storage_provider.py
      - i_content_extraction_provider.py
      - i_web_fetch_provider.py
      - i_llm_provider.py
      - i_search_provider.py
  /commands
    - notebook_commands.py
    - source_commands.py
    - output_commands.py
  /queries
    - notebook_queries.py
    - search_queries.py
  /results
    - result.py
    - validation_error.py
```

**Key Principles Applied:**
- ✅ Core has minimal external dependencies
- ✅ All business logic in entities and services
- ✅ Services use Command/Query objects as inputs
- ✅ Services return Result objects
- ✅ Interfaces defined in Core, implemented in Infrastructure
- ✅ Dependency inversion: Core defines abstractions
- ✅ Highly testable: services can be unit tested with mocks
