# Web Fetch Providers

This directory contains implementations of the `IWebFetchProvider` interface for fetching and extracting content from web URLs.

## Available Providers

### 1. HttpWebFetchProvider (BeautifulSoup-based)

**File:** `http_web_fetch_provider.py`

A general-purpose web scraping provider using `httpx` for HTTP requests and `BeautifulSoup` for HTML parsing.

**Features:**
- ✅ HTTP/2 support for better performance
- ✅ Comprehensive browser-like headers to avoid bot detection
- ✅ Automatic retry with different user agents
- ✅ Heuristic-based content extraction
- ✅ JSON-LD structured data extraction as fallback
- ✅ JavaScript SPA detection
- ✅ Plain text file support

**Best for:**
- General web scraping tasks
- Sites with simple HTML structure
- When you need maximum content extraction (including navigation, etc.)
- Non-article content (documentation, wikis, general web pages)

**Usage:**
```python
from src.infrastructure.providers.http_web_fetch_provider import HttpWebFetchProvider

provider = HttpWebFetchProvider()
result = provider.fetch_url("https://example.com/article")

if result.is_success:
    content = result.value
    print(f"Title: {content.title}")
    print(f"Text: {content.text[:200]}...")
```

### 2. Newspaper3kWebFetchProvider (newspaper3k-based) ⭐ **Recommended for Articles**

**File:** `newspaper_web_fetch_provider.py`

A specialized provider using the `newspaper3k` library, optimized for extracting article content from news sites, blogs, and content-heavy pages.

**Features:**
- ✅ Superior article content extraction
- ✅ Automatic keyword extraction using NLP
- ✅ Author detection
- ✅ Publication date extraction  
- ✅ Article summary generation
- ✅ Better content vs. boilerplate separation
- ✅ Multi-language support
- ✅ Browser-like behavior to avoid detection
- ✅ Automatic retry with different user agents

**Best for:**
- News articles
- Blog posts
- Content-focused pages
- When you need clean article text without navigation/ads
- When you want automatic metadata extraction (authors, dates, keywords)

**Usage:**
```python
from src.infrastructure.providers.newspaper_web_fetch_provider import Newspaper3kWebFetchProvider

provider = Newspaper3kWebFetchProvider()
result = provider.fetch_url("https://example.com/blog/article")

if result.is_success:
    content = result.value
    print(f"Title: {content.title}")
    print(f"Text: {content.text[:200]}...")
    print(f"Keywords: {content.metadata.get('keywords', [])}")
    print(f"Authors: {content.metadata.get('authors', [])}")
    print(f"Published: {content.metadata.get('publish_date', 'Unknown')}")
```

## Comparison

| Feature | HttpWebFetchProvider | Newspaper3kWebFetchProvider |
|---------|---------------------|----------------------------|
| Article Extraction Quality | Good | ⭐ Excellent |
| Content Cleanliness | Mixed (includes nav, etc.) | ⭐ Very Clean |
| Keyword Extraction | ❌ No | ✅ Yes (NLP) |
| Author Detection | ❌ No | ✅ Yes |
| Date Detection | ❌ No | ✅ Yes |
| Summary Generation | ❌ No | ✅ Yes |
| Multi-language Support | ❌ Limited | ✅ Yes |
| Plain Text Files | ✅ Yes | ❌ No |
| General Web Pages | ✅ Yes | Mixed |
| News/Blog Articles | Good | ⭐ Excellent |
| Browser-like Headers | ✅ Yes | ✅ Yes |
| Retry Logic | ✅ Yes | ✅ Yes |

## Performance Comparison

Based on testing with Wikipedia articles:

**Web Scraping Article:**
- HttpWeb: 27,825 characters (includes navigation, footer, etc.)
- Newspaper: 19,707 characters (clean article content only)

**Python Programming Language Article:**
- HttpWeb: 92,800 characters (includes all page elements)
- Newspaper: 33,814 characters (main article content only)

**Key Insight:** Newspaper3k extracts cleaner, more focused content specifically for article-style pages, while HttpWebFetchProvider extracts more total content including boilerplate.

## Choosing the Right Provider

### Use Newspaper3kWebFetchProvider when:
- ✅ Scraping news articles
- ✅ Scraping blog posts  
- ✅ You need clean article text
- ✅ You want automatic metadata (authors, dates, keywords)
- ✅ You want NLP features (summary, keywords)
- ✅ Quality over quantity of extracted text

### Use HttpWebFetchProvider when:
- ✅ Scraping general web pages
- ✅ Scraping documentation sites
- ✅ You need ALL page content
- ✅ Working with plain text files
- ✅ Page structure is non-standard
- ✅ Quantity over quality of extracted text

## Configuration Options

Both providers support:

**Custom User Agent:**
```python
provider = Newspaper3kWebFetchProvider(
    user_agent="MyBot/1.0"
)
```

**Custom Timeout:**
```python
result = provider.fetch_url(url, timeout=60)
```

**Safe Fetch with Retries:**
```python
# Automatically retries up to 3 times with different strategies
result = provider.fetch_url_safe(url)
```

## Anti-Bot Detection Features

Both providers include comprehensive anti-bot detection measures:

1. **Realistic Browser Headers**: Mimic Chrome, Firefox, Safari
2. **User Agent Rotation**: Try multiple user agents on failure
3. **Random Delays**: Avoid pattern detection
4. **HTTP/2 Support**: Modern browser behavior
5. **Referer Headers**: Natural browsing simulation
6. **Cookie Support**: Session management

## Testing

Run the comparison script to see both providers in action:

```bash
uv run python scripts/compare_providers.py
```

Run integration tests:

```bash
uv run pytest tests/integration/test_newspaper_provider.py -v
```

## Dependencies

**HttpWebFetchProvider:**
- `httpx[http2]` - HTTP client with HTTP/2 support
- `beautifulsoup4` - HTML parsing

**Newspaper3kWebFetchProvider:**
- `newspaper3k` - Article extraction library
- `lxml_html_clean` - HTML cleaning (required dependency)
- Includes: NLP features (NLTK), CSS selector support, etc.

## Future Improvements

Potential enhancements:

1. **Selenium/Playwright Integration**: For JavaScript-heavy sites
2. **Caching Layer**: Avoid re-fetching same URLs
3. **Rate Limiting**: Built-in rate limit compliance
4. **Proxy Support**: Rotate through proxy servers
5. **Custom Extraction Rules**: Site-specific extraction patterns

## License

Part of the Discovery project.
