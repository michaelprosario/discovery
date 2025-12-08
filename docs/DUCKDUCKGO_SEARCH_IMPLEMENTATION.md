# DuckDuckGo Article Search Implementation

## Overview

This document describes the new DuckDuckGo-based article search infrastructure implementation as an alternative to the Gemini AI search provider.

## Why DuckDuckGo?

The original implementation used Gemini AI with Google Search grounding, which had several limitations:

- **Quality Issues**: Search results from Gemini's grounding feature were sometimes inconsistent or not relevant
- **API Dependency**: Required a Gemini API key and incurred costs per search
- **Indirect Results**: AI intermediation could sometimes filter out good results

The new DuckDuckGo implementation offers:

- ✅ **No API Key Required**: Free to use without authentication
- ✅ **Direct Web Search**: Direct search results from DuckDuckGo
- ✅ **Better Control**: Fine-grained filtering of low-quality sources
- ✅ **Fast & Reliable**: Quick responses without AI processing overhead
- ✅ **Cost-Free**: No per-request charges

## Architecture

The implementation follows Clean Architecture principles:

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (sources_router.py)                          │
│  - POST /api/sources/search-and-add                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Service Layer (article_search_service.py)              │
│  - Business logic and validation                        │
│  - Orchestrates provider operations                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Provider Interface (i_article_search_provider.py)      │
│  - Abstract contract for search providers               │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴──────────────┐
        ▼                          ▼
┌──────────────────┐   ┌──────────────────────────┐
│ Gemini Provider  │   │ DuckDuckGo Provider      │
│ (AI-based)       │   │ (Direct web search)      │
└──────────────────┘   └──────────────────────────┘
```

## Implementation Details

### DuckDuckGoArticleSearchProvider

**Location**: `src/infrastructure/providers/duckduckgo_article_search_provider.py`

**Key Features**:

1. **Enhanced Search Query Building**
   - Adds search operators to find high-quality content
   - Query example: `"Python architecture (blog OR article OR guide OR tutorial)"`

2. **Domain Filtering**
   - Excludes low-quality sources: Reddit, Twitter, YouTube, StackOverflow, shopping sites
   - Prioritizes: blogs, educational content, in-depth guides, technical documentation

3. **URL Validation**
   - Filters out homepage URLs (too generic)
   - Excludes file downloads (PDFs, videos, images)
   - Removes pagination and comment pages

4. **Smart Result Limiting**
   - Fetches 3x requested results to allow filtering
   - Returns only high-quality results after filtering

### Configuration

The provider is configured via environment variable:

```bash
# Use DuckDuckGo (default)
export ARTICLE_SEARCH_PROVIDER=duckduckgo

# Use Gemini AI
export ARTICLE_SEARCH_PROVIDER=gemini
```

**Dependency Injection**: `src/api/dependencies/article_search.py`

The system automatically selects the appropriate provider based on the environment variable.

## Installation

Add the required dependency:

```bash
pip install ddgs
```

Or update `pyproject.toml`:

```toml
dependencies = [
    ...
    "ddgs>=9.0.0",
]
```

## Usage

### Via API

```bash
curl -X POST http://localhost:8000/api/sources/search-and-add \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "abc123",
    "search_phrase": "Python clean architecture best practices",
    "max_results": 5
  }'
```

### Via Angular Frontend

The existing `AddSourceBySearch` component works seamlessly with the new provider:

```typescript
// discoveryPortal/src/app/add-source-by-search/add-source-by-search.ts
const request: AddSourcesBySearchRequest = {
  notebook_id: this.notebookId,
  search_phrase: this.searchPhrase.trim(),
  max_results: this.maxResults
};

this.sourceService.addSourcesBySearch(request).subscribe({
  next: (response) => {
    // Handle results - same as before
  }
});
```

### Programmatically

```python
from src.core.queries.article_search_queries import ArticleSearchQuery
from src.infrastructure.providers.duckduckgo_article_search_provider import DuckDuckGoArticleSearchProvider

# Create provider
provider = DuckDuckGoArticleSearchProvider()

# Search
query = ArticleSearchQuery(
    question="What are the best practices for Python testing?",
    max_results=5
)

result = provider.search_articles(query)

if result.is_success:
    for article in result.value.articles:
        print(f"{article.title}")
        print(f"{article.link}\n")
```

## Testing

### Unit Tests

```bash
python -m pytest tests/unit/test_duckduckgo_provider.py -v
```

**Test Coverage**:
- Provider initialization
- Custom configuration
- Search query building
- Domain extraction
- URL validation
- Search execution (mocked)
- Domain filtering
- Error handling

### Manual Testing

```python
# Quick test
from ddgs import DDGS

with DDGS() as ddgs:
    results = ddgs.text("Python clean architecture", max_results=5)
    for r in results:
        print(f"{r['title']}\n{r['href']}\n")
```

## Comparison: Gemini vs DuckDuckGo

| Feature | Gemini Provider | DuckDuckGo Provider |
|---------|----------------|---------------------|
| API Key Required | ✅ Yes | ❌ No |
| Cost | Per-request charges | Free |
| Search Quality | AI-curated | Direct web results |
| Speed | Moderate (AI processing) | Fast (direct search) |
| Customization | Limited | High (manual filtering) |
| Reliability | API-dependent | Very reliable |
| Domain Filtering | AI-based | Rule-based |

## Configuration Options

### DuckDuckGo Provider Options

```python
provider = DuckDuckGoArticleSearchProvider(
    region="wt-wt",      # Worldwide (default)
    safesearch="moderate" # 'on', 'moderate', 'off'
)
```

### Environment Variables

```bash
# Provider selection
ARTICLE_SEARCH_PROVIDER=duckduckgo  # or 'gemini'

# For Gemini (if using)
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
```

## Future Enhancements

Potential improvements for the DuckDuckGo provider:

1. **Configurable Filters**: Allow custom excluded domains via config
2. **Result Ranking**: Implement relevance scoring algorithm
3. **Cache Integration**: Cache search results to reduce API calls
4. **Multi-Provider**: Combine results from multiple search engines
5. **Content Preview**: Fetch and display article snippets
6. **Language Detection**: Filter by article language

## Troubleshooting

### Import Errors

If you see `ImportError: attempted relative import beyond top-level package`:
- This is normal when running scripts directly
- Use `python -m` to run modules: `python -m src.api.main`
- Or ensure proper PYTHONPATH setup

### No Results Found

If searches return no results:
- Check your internet connection
- Verify the search query is not too specific
- Try reducing filters (modify excluded domains)

### Package Not Found

```bash
# Install the ddgs package
pip install ddgs

# Update from old package name
pip uninstall duckduckgo-search
pip install ddgs
```

## Files Modified/Created

### New Files
- `src/infrastructure/providers/duckduckgo_article_search_provider.py` - Main implementation
- `tests/unit/test_duckduckgo_provider.py` - Unit tests
- `docs/DUCKDUCKGO_SEARCH_IMPLEMENTATION.md` - This documentation

### Modified Files
- `src/api/dependencies/article_search.py` - Added provider selection logic
- `pyproject.toml` - Added `ddgs` dependency
- `src/infrastructure/providers/__init__.py` - Updated to avoid import issues

## Conclusion

The DuckDuckGo implementation provides a robust, free, and reliable alternative to the Gemini AI search provider. It offers better control over search quality through explicit filtering rules and eliminates the need for API keys and associated costs.

The implementation maintains compatibility with existing code through the provider interface pattern, making it easy to switch between providers or add new ones in the future.
