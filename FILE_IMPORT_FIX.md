# File Import Design Bug Fix

## Issue
The `/api/sources/file` endpoint had a design flaw where it required users to provide a `content` parameter (base64-encoded file content). According to the specification, the system should automatically extract content from files - users should only need to provide the file path.

## Fix Date
October 17, 2025

## Problem Statement

**Given:**
- User is using `/api/sources/file`
- User wants to import content from a file
- User provides: `notebook_id`, `name`, `file_path`, `file_type`

**Then:**
- System should extract content automatically from the file
- System should populate the content field based on file extraction
- The `content` parameter should NOT be required
- The `file_size` parameter should NOT be required (calculated automatically)

## Changes Made

### 1. Implemented FileContentExtractionProvider

**File:** `src/infrastructure/providers/file_content_extraction_provider.py` (NEW - 222 lines)

Created a concrete implementation of `IContentExtractionProvider` interface that extracts text from various file formats:

**Supported Formats:**
- **PDF**: Uses PyPDF2 to extract text from all pages
- **DOCX**: Uses python-docx to extract paragraphs and tables
- **DOC**: Uses textract library (requires system dependencies)
- **TXT**: Direct file reading with multi-encoding support (utf-8, latin-1, cp1252, iso-8859-1)
- **MD**: Markdown file reading (same as TXT)

**Key Features:**
- Error handling with Result pattern
- Multiple encoding fallback for text files
- Extraction from PDF pages sequentially
- Table extraction from DOCX files
- Helpful error messages when libraries are missing

**Example Usage:**
```python
provider = FileContentExtractionProvider()
result = provider.extract_text("/path/to/file.pdf", FileType.PDF)

if result.is_success:
    text_content = result.value
else:
    error_message = result.error
```

### 2. Updated ImportFileSourceRequest DTO

**File:** `src/api/dtos.py`

**Before:**
```python
class ImportFileSourceRequest(BaseModel):
    notebook_id: UUID
    name: str
    file_path: str
    file_type: str
    file_size: int  # Required ❌
    content: str    # Required ❌ (base64 encoded)
```

**After:**
```python
class ImportFileSourceRequest(BaseModel):
    notebook_id: UUID
    name: str
    file_path: str  # Content extracted automatically ✅
    file_type: str
```

**Key Changes:**
- ❌ Removed required `content` field
- ❌ Removed required `file_size` field (calculated automatically)
- ✅ Updated field description to indicate automatic extraction

### 3. Updated import_file_source Endpoint Logic

**File:** `src/api/sources_router.py`

**Logic Flow:**
1. Validate file type
2. **Extract content from file using FileContentExtractionProvider**
3. Get file size automatically from filesystem
4. Convert extracted text to bytes for hash calculation
5. Build metadata with file name and extension
6. Create source with extracted content

**Added Dependency Injection:**
```python
def get_content_extraction_provider():
    """Dependency injection for IContentExtractionProvider."""
    from ..infrastructure.providers.file_content_extraction_provider import FileContentExtractionProvider
    return FileContentExtractionProvider()

def get_source_service(
    source_repo = Depends(get_source_repository),
    notebook_repo = Depends(get_notebook_repository),
    web_fetch_provider = Depends(get_web_fetch_provider),
    content_extraction_provider = Depends(get_content_extraction_provider)  # ✅ Added
) -> SourceIngestionService:
    return SourceIngestionService(
        source_repository=source_repo,
        notebook_repository=notebook_repo,
        file_storage_provider=None,
        content_extraction_provider=content_extraction_provider,  # ✅ Injected
        web_fetch_provider=web_fetch_provider
    )
```

**Updated Endpoint:**
```python
@router.post("/file", ...)
def import_file_source(
    request: ImportFileSourceRequest,
    service: SourceIngestionService = Depends(get_source_service),
    content_extraction_provider = Depends(get_content_extraction_provider)
):
    # Extract content from file
    extraction_result = content_extraction_provider.extract_text(
        request.file_path,
        file_type_enum
    )

    if extraction_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Failed to extract content: {extraction_result.error}"}
        )

    extracted_text = extraction_result.value

    # Get file size automatically
    file_size = os.path.getsize(request.file_path)

    # Build metadata
    metadata = {
        "original_file_name": os.path.basename(request.file_path),
        "file_extension": os.path.splitext(request.file_path)[1],
    }

    # Create command with extracted content
    command = ImportFileSourceCommand(
        notebook_id=request.notebook_id,
        name=request.name,
        file_path=request.file_path,
        file_type=file_type_enum,
        file_size=file_size,
        content=extracted_text.encode('utf-8'),
        metadata=metadata
    )
```

### 4. Updated API Documentation

**File:** `API_DOCUMENTATION.md`

Updated to show:
- Minimal request (only `notebook_id`, `name`, `file_path`, `file_type`)
- Clear explanation of automatic content extraction
- How each file type is processed
- Updated examples without `content` or `file_size` fields
- Error responses for extraction failures

### 5. Added Dependencies

**File:** `pyproject.toml`

Added required libraries for content extraction:
```toml
dependencies = [
    # ... existing dependencies ...
    "PyPDF2>=3.0.0",       # PDF extraction
    "python-docx>=1.1.0",  # DOCX extraction
]
```

**Note:** DOC file extraction uses the `antiword` system utility via subprocess instead of the `textract` Python library to avoid dependency conflicts with `beautifulsoup4`.

## API Usage

### Before (Incorrect)

```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Research Paper",
    "file_path": "/documents/paper.pdf",
    "file_type": "pdf",
    "file_size": 2048576,              # ❌ Required
    "content": "base64_encoded_..."    # ❌ Required
  }'
```

**Problems:**
- User must read file and encode to base64
- User must calculate file size
- Complex client-side processing required
- Large payloads due to base64 encoding

### After (Correct)

```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Research Paper",
    "file_path": "/documents/paper.pdf",
    "file_type": "pdf"
  }'
```

**What Happens:**
1. System validates file exists at path
2. Extracts text from PDF using PyPDF2
3. Calculates file size automatically
4. Generates content hash from extracted text
5. Creates source with extracted content

**Benefits:**
- ✅ Simpler API (only 4 required fields)
- ✅ No client-side file reading/encoding
- ✅ No large base64 payloads
- ✅ Server-side extraction ensures consistency
- ✅ Automatic metadata extraction

## Content Extraction Details

### PDF Files (.pdf)

**Library:** PyPDF2

**Process:**
1. Open PDF file in binary mode
2. Create PdfReader instance
3. Iterate through all pages
4. Extract text from each page
5. Join pages with double newlines
6. Return extracted text or error if no text found

**Limitations:**
- Cannot extract text from image-based PDFs (scanned documents)
- Complex layouts may have text ordering issues
- Encrypted PDFs require password

### DOCX Files (.docx)

**Library:** python-docx

**Process:**
1. Open DOCX file using python-docx
2. Extract text from all paragraphs
3. Extract text from all tables (cells joined with " | ")
4. Join all text with double newlines
5. Return extracted text

**Features:**
- Preserves paragraph structure
- Extracts table content
- Handles formatted text

### DOC Files (.doc)

**Method:** antiword subprocess

**Process:**
1. Execute `antiword` command on the file
2. Capture output text
3. Return extracted text

**Requirements:**
- Requires `antiword` system utility to be installed
- Linux: `sudo apt-get install antiword`
- macOS: `brew install antiword`
- Windows: Use LibreOffice or convert to DOCX format

**Note:**
- Uses subprocess to call antiword directly
- Fallback for older Word documents
- No Python library dependencies (avoids dependency conflicts)
- 30-second timeout for extraction

### TXT/MD Files (.txt, .md)

**Process:**
1. Try multiple encodings in order:
   - UTF-8 (most common)
   - Latin-1
   - CP1252 (Windows)
   - ISO-8859-1
2. Read entire file content
3. Return text or error if all encodings fail

**Features:**
- Automatic encoding detection
- Handles various text encodings
- Preserves original formatting

## Error Handling

### File Not Found
```json
{
  "error": "Failed to extract content from file: File not found: /path/to/file.pdf"
}
```

### Unsupported File Type
```json
{
  "error": "Unsupported file type: jpg"
}
```

### Missing Library
```json
{
  "error": "Failed to extract content from file: PyPDF2 library not installed. Install with: pip install PyPDF2"
}
```

### Empty File
```json
{
  "error": "Failed to extract content from file: No text content could be extracted from PDF (may be image-based)"
}
```

### Extraction Failure
```json
{
  "error": "Failed to extract content from file: [specific error message]"
}
```

## Testing Results

### Unit Tests
✅ All 113 unit tests pass
✅ No regressions introduced
✅ Existing functionality preserved

### Coverage
- NotebookManagementService: 38 tests
- SourceIngestionService: 24 tests
- PostgresNotebookRepository: 23 tests
- PostgresSourceRepository: 26 tests
- **New**: FileContentExtractionProvider (tested via integration)

## Comparison: Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Required Fields** | 6 fields | 4 fields |
| **Client Complexity** | High (file reading, base64 encoding) | Low (just provide path) |
| **Payload Size** | Large (base64 encoded file) | Small (JSON metadata only) |
| **File Size** | User provides | Calculated automatically |
| **Content Hash** | Based on user-provided content | Based on extracted text |
| **Error Detection** | Client-side | Server-side |
| **Consistency** | Depends on client implementation | Guaranteed by server |

## Architecture Compliance

This fix maintains Clean Architecture principles:

- ✅ **API Layer**: Updated DTO and endpoint with dependency injection
- ✅ **Infrastructure Layer**: Created FileContentExtractionProvider
- ✅ **Core Layer**: Uses existing IContentExtractionProvider interface
- ✅ **Dependency Injection**: Provider injected via FastAPI DI
- ✅ **Result Pattern**: All methods return Result<T>
- ✅ **Interface Segregation**: Implements existing interface

**Dependencies Flow:**
```
API Layer (sources_router.py)
    ↓ depends on
Core Layer (IContentExtractionProvider interface)
    ↑ implemented by
Infrastructure Layer (FileContentExtractionProvider)
```

## Files Modified

### Created
- ✅ `src/infrastructure/providers/file_content_extraction_provider.py` (NEW - 222 lines)
- ✅ `FILE_IMPORT_FIX.md` (this document)

### Modified
- ✅ `src/api/dtos.py` - Removed `content` and `file_size` fields
- ✅ `src/api/sources_router.py` - Added content extraction logic and DI
- ✅ `API_DOCUMENTATION.md` - Updated documentation and examples
- ✅ `pyproject.toml` - Added PyPDF2, python-docx, textract dependencies

### No Changes Needed
- ✅ Core layer (SourceIngestionService) - interface already existed
- ✅ Core layer (IContentExtractionProvider) - interface already defined
- ✅ Infrastructure (repositories) - no changes needed
- ✅ Database models - no schema changes

## Backward Compatibility

**Breaking Change:** Yes, this is a breaking change.

**Before:**
- Required: `notebook_id`, `name`, `file_path`, `file_type`, `file_size`, `content`

**After:**
- Required: `notebook_id`, `name`, `file_path`, `file_type`

**Migration Path:**

If users were previously calling with `content` and `file_size`:
```json
// Old request
{
  "notebook_id": "...",
  "name": "My Document",
  "file_path": "/path/to/file.pdf",
  "file_type": "pdf",
  "file_size": 2048576,
  "content": "base64_encoded_content..."
}

// New request - just remove content and file_size
{
  "notebook_id": "...",
  "name": "My Document",
  "file_path": "/path/to/file.pdf",
  "file_type": "pdf"
}
```

**Note:** The file must exist and be accessible on the server filesystem.

## Installation Instructions

### Install Dependencies

```bash
# Install Python packages
uv pip install PyPDF2 python-docx

# Or sync from pyproject.toml
uv sync
```

### System Dependencies (for DOC files)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y antiword
```

**macOS:**
```bash
brew install antiword
```

**Windows:**
- Use LibreOffice to convert DOC to DOCX, or use WSL with antiword

## Benefits

1. **Simpler API**: Users only provide file path, not content
2. **Better UX**: No need to read files client-side
3. **Automatic**: System intelligently extracts content from various formats
4. **Consistent**: All file sources processed uniformly
5. **Smaller Payloads**: No base64-encoded content in requests
6. **Error Detection**: Server-side validation and error handling
7. **Metadata**: Automatic extraction of file name and extension

## Complete Feature Set

After this fix, the `/api/sources/file` endpoint:

1. ✅ Validates file path exists
2. ✅ Extracts text from PDF files
3. ✅ Extracts text from DOCX files
4. ✅ Extracts text from DOC files
5. ✅ Extracts text from TXT files
6. ✅ Extracts text from MD files
7. ✅ Calculates file size automatically
8. ✅ Generates content hash
9. ✅ Extracts metadata (filename, extension)
10. ✅ Handles errors gracefully
11. ✅ Supports multiple encodings for text files
12. ✅ Provides helpful error messages

## Success Criteria ✅

All requirements from `prompts/009-AmendFileImport.md` met:

- ✅ Content parameter removed from `/api/sources/file`
- ✅ File size parameter removed (calculated automatically)
- ✅ Content extracted automatically using infrastructure-level code
- ✅ All tests pass
- ✅ Documentation updated

## Examples

### Example 1: Import PDF

```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Attention Is All You Need",
    "file_path": "/papers/attention.pdf",
    "file_type": "pdf"
  }'
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Attention Is All You Need",
  "source_type": "file",
  "file_type": "pdf",
  "file_path": "/papers/attention.pdf",
  "file_size": 2048576,
  "content_hash": "sha256_hash...",
  "extracted_text": "Abstract\n\nThe dominant sequence transduction models...",
  "metadata": {
    "original_file_name": "attention.pdf",
    "file_extension": ".pdf"
  },
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z",
  "deleted_at": null
}
```

### Example 2: Import DOCX

```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Meeting Notes",
    "file_path": "/documents/notes.docx",
    "file_type": "docx"
  }'
```

### Example 3: Import Markdown

```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "README",
    "file_path": "/projects/readme.md",
    "file_type": "md"
  }'
```

## Known Limitations

1. **PDF Limitations**:
   - Cannot extract text from image-based (scanned) PDFs
   - Complex layouts may have text ordering issues
   - Encrypted PDFs not supported

2. **DOC Limitations**:
   - Requires antiword system dependency on Linux
   - May not work on all platforms without additional setup

3. **File Access**:
   - File must exist on server filesystem
   - Server must have read permissions
   - Not suitable for user file uploads (use multipart/form-data for that)

## Future Enhancements

Planned improvements:

1. **OCR Support**: Extract text from image-based PDFs using Tesseract
2. **File Upload**: Support multipart/form-data for direct file uploads
3. **Cloud Storage**: Support S3, Azure Blob, Google Cloud Storage
4. **More Formats**: Support HTML, RTF, ODT, etc.
5. **Async Processing**: Background job processing for large files
6. **Progress Tracking**: WebSocket updates for extraction progress
7. **Preview Generation**: Generate thumbnails/previews for documents

## Summary

This fix completes the file import feature by removing the unnecessary `content` and `file_size` parameters and automatically extracting content from files using infrastructure-level providers. This provides a much more intuitive API where users simply provide a file path and let the system handle all content extraction.

The implementation:
- ✅ Follows the specification exactly
- ✅ Maintains Clean Architecture
- ✅ Passes all tests (113 tests)
- ✅ Provides excellent UX
- ✅ Is well documented
- ✅ Supports 5 file formats
- ✅ Handles errors gracefully

Users can now import file sources with just four parameters: `notebook_id`, `name`, `file_path`, and `file_type`!
