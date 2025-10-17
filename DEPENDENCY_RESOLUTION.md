# Dependency Conflict Resolution

## Issue

When implementing the file import fix, we encountered a dependency conflict:

```
textract>=1.6.5 depends on beautifulsoup4>=4.8.0,<4.9.dev0
project depends on beautifulsoup4>=4.12.0 (needed for web fetching)
```

These two requirements are incompatible - `textract` requires an older version of `beautifulsoup4` that conflicts with the newer version needed for our URL import functionality.

## Root Cause

The `textract` library (last updated in 2020) has a hard dependency on `beautifulsoup4<4.9`, which is incompatible with modern versions of BeautifulSoup4 (currently 4.12+) that we need for proper HTML parsing in the web fetch provider.

## Solution

Instead of using the `textract` Python library for DOC file extraction, we implemented a direct subprocess call to the `antiword` system utility.

### Changes Made

1. **Removed `textract` from dependencies** (`pyproject.toml`)
   - Removed: `textract>=1.6.5`
   - Kept: `PyPDF2>=3.0.0`, `python-docx>=1.1.0`, `beautifulsoup4>=4.12.0`

2. **Updated DOC extraction method** (`src/infrastructure/providers/file_content_extraction_provider.py`)
   - Changed from: `textract.process()` Python library call
   - Changed to: `subprocess.run(['antiword', file_path])` system call

3. **Updated documentation**
   - FILE_IMPORT_FIX.md
   - API_DOCUMENTATION.md
   - Added installation instructions for antiword

## Implementation Details

### Before (with textract)
```python
import textract

def extract_text_from_doc(self, file_path: str) -> Result[str]:
    extracted_bytes = textract.process(file_path)
    extracted_text = extracted_bytes.decode('utf-8')
    return Result.success(extracted_text)
```

### After (with antiword subprocess)
```python
import subprocess

def extract_text_from_doc(self, file_path: str) -> Result[str]:
    result = subprocess.run(
        ['antiword', file_path],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        return Result.success(result.stdout)
    else:
        return Result.failure(f"antiword failed: {result.stderr}")
```

## Benefits

1. **No dependency conflicts**: Avoids BeautifulSoup4 version conflict
2. **Simpler dependencies**: Fewer Python packages to install
3. **System-level**: Uses well-tested antiword utility
4. **Better error messages**: Clear installation instructions when antiword is missing
5. **Performance**: Direct system call can be faster than Python wrapper

## Installation Requirements

### Python Dependencies (via pip/uv)
```bash
uv pip install PyPDF2 python-docx beautifulsoup4
```

### System Dependencies (for DOC files)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install antiword
```

**macOS:**
```bash
brew install antiword
```

**Windows:**
- Use Windows Subsystem for Linux (WSL) with antiword, or
- Convert DOC files to DOCX format using LibreOffice, or
- Skip DOC support (DOCX is more common anyway)

## Trade-offs

### Advantages
- ✅ No Python dependency conflicts
- ✅ Simpler dependency tree
- ✅ Well-tested, mature utility (antiword)
- ✅ Clear error messages
- ✅ All other formats work without system dependencies

### Disadvantages
- ❌ Requires system-level installation of antiword for DOC support
- ❌ DOC extraction not available on Windows without WSL
- ❌ Extra setup step for users who need DOC support

### Mitigation
- Most modern documents use DOCX format (which works without system dependencies)
- DOC is a legacy format - most users won't need it
- Clear error messages guide users to install antiword if needed
- Alternative: users can convert DOC to DOCX before importing

## Testing

All 113 unit tests pass after this change:
```bash
pytest tests/unit/ -v
# ====================== 113 passed, 413 warnings in 1.18s ======================
```

No regressions introduced - the change only affects DOC file extraction implementation, not the API or other file formats.

## Alternative Solutions Considered

### 1. Use older BeautifulSoup4 (REJECTED)
- **Option**: Downgrade to beautifulsoup4<4.9 to satisfy textract
- **Reason for rejection**: Would lose important features and bug fixes in newer BeautifulSoup4 versions needed for web scraping

### 2. Fork textract (REJECTED)
- **Option**: Fork textract and update its dependencies
- **Reason for rejection**: Maintenance burden, textract has many dependencies

### 3. Use python-docx2txt (CONSIDERED)
- **Option**: Use docx2txt library (works for some DOC files)
- **Reason for rejection**: Limited DOC support, antiword is more reliable

### 4. Use LibreOffice subprocess (CONSIDERED)
- **Option**: Use `soffice --convert-to txt` command
- **Reason for rejection**: LibreOffice is heavy, antiword is lighter and faster

### 5. Use antiword subprocess (SELECTED ✅)
- **Option**: Direct subprocess call to antiword utility
- **Reason for selection**:
  - No Python dependency conflicts
  - Mature, reliable tool
  - Fast and lightweight
  - Clear installation path

## Future Enhancements

1. **Multiple DOC extractors**: Try antiword first, fall back to LibreOffice if available
2. **Windows support**: Provide pre-built antiword binary or use python-antiword wrapper
3. **Cloud functions**: Use cloud-based document conversion APIs
4. **Format recommendation**: Encourage users to use DOCX instead of DOC

## Conclusion

By replacing the `textract` library with a direct `antiword` subprocess call, we successfully resolved the dependency conflict while maintaining full functionality for DOC file extraction. The solution is simpler, more reliable, and avoids complex dependency management issues.

Users who need DOC support will need to install antiword (a simple one-line command on Linux/macOS), while users who only work with PDF, DOCX, TXT, or MD files have no additional requirements beyond Python packages.
