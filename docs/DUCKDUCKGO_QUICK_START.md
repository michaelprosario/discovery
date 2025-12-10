# Quick Start: Using DuckDuckGo Search Provider

This guide shows you how to start using the new DuckDuckGo search provider for the "Add Sources by Search" feature.

## Step 1: Install Dependencies

```bash
cd /workspaces/discovery
pip install ddgs
```

## Step 2: Configure the Provider

Edit your `.env` file and add:

```bash
# Use DuckDuckGo for article search (default, free, no API key needed)
ARTICLE_SEARCH_PROVIDER=duckduckgo
```

Or to use Gemini (requires API key):

```bash
# Use Gemini AI for article search
ARTICLE_SEARCH_PROVIDER=gemini
```

## Step 3: Restart the Server

```bash
# Stop any running server
pkill -f "python -m src.api.main"

# Start with new configuration
python -m src.api.main
```

## Step 4: Test the Feature

### Option A: Use the UI

1. Open the Discovery Portal at `http://localhost:4200`
2. Navigate to a notebook
3. Click "Add Sources by Search"
4. Enter a search query like "Python clean architecture best practices"
5. Click "Search and Add"
6. See high-quality articles added to your notebook!

### Option B: Use the API Directly

```bash
curl -X POST http://localhost:8000/api/sources/search-and-add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "notebook_id": "your-notebook-id",
    "search_phrase": "Python testing best practices",
    "max_results": 5
  }'
```

## What to Expect

The DuckDuckGo provider will:

✅ **Find high-quality articles** from blogs, educational sites, and technical resources
✅ **Filter out low-quality sources** like Reddit threads, YouTube videos, shopping sites
✅ **Return direct links** to the original articles
✅ **Work instantly** without any API setup or costs

### Example Search Results

For "Python clean architecture best practices", you might see:

1. **Clean Architecture in Python** - blog.example.com
2. **Python Best Practices Guide** - realpython.com
3. **Structuring Your Python Project** - docs.python-guide.org
4. **Clean Code in Python** - testdriven.io
5. **Python Architecture Patterns** - medium.com

## Switching Between Providers

You can switch between DuckDuckGo and Gemini anytime:

```bash
# Switch to DuckDuckGo (free, fast, direct results)
export ARTICLE_SEARCH_PROVIDER=duckduckgo

# Switch to Gemini (AI-powered, requires API key)
export ARTICLE_SEARCH_PROVIDER=gemini
```

Restart the server after changing the provider.

## Troubleshooting

### Package Not Found

```bash
pip install ddgs
```

### No Results Found

- Try a different search query
- Make your query more specific
- Check your internet connection

### Import Errors

Ensure you're running the server correctly:

```bash
# Use module syntax
python -m src.api.main

# Not: python src/api/main.py
```

## Next Steps

- Read the full documentation: `docs/DUCKDUCKGO_SEARCH_IMPLEMENTATION.md`
- Review the implementation: `src/infrastructure/providers/duckduckgo_article_search_provider.py`
- Check the tests: `tests/unit/test_duckduckgo_provider.py`

## Feedback

If you encounter any issues or have suggestions for improvement:

1. Check the documentation in `docs/DUCKDUCKGO_SEARCH_IMPLEMENTATION.md`
2. Review the summary in `docs/DUCKDUCKGO_IMPLEMENTATION_SUMMARY.md`
3. Run the tests: `python -m pytest tests/unit/test_duckduckgo_provider.py -v`

That's it! Enjoy better search results with the DuckDuckGo provider! 🎉
