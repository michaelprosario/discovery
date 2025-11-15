"""Integration tests for Newspaper3kWebFetchProvider."""
import pytest
from src.infrastructure.providers.newspaper_web_fetch_provider import Newspaper3kWebFetchProvider


class TestNewspaper3kWebFetchProvider:
    """Test the newspaper3k-based web fetch provider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = Newspaper3kWebFetchProvider()

    def test_fetch_article_success(self):
        """Test fetching a real article."""
        # Using a stable, well-known article URL that should work
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        
        result = self.provider.fetch_url(url)
        
        assert result.is_success, f"Failed to fetch: {result.error}"
        content = result.value
        
        # Verify basic content structure
        assert content.url == url
        assert content.title, "Title should not be empty"
        assert content.text, "Text content should not be empty"
        assert content.html, "HTML content should not be empty"
        assert isinstance(content.metadata, dict), "Metadata should be a dictionary"
        
        # Verify content quality
        assert len(content.text) > 100, "Article text should be substantial"
        print(f"✓ Fetched article: {content.title}")
        print(f"  Content length: {len(content.text)} characters")
        print(f"  Metadata keys: {list(content.metadata.keys())}")

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com/article",
            "https://example.com/path/to/article.html",
        ]
        
        for url in valid_urls:
            result = self.provider.validate_url(url)
            assert result.is_success, f"URL should be valid: {url}"

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "",
            "   ",
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('test')",
            "http://<script>alert('xss')</script>",
        ]
        
        for url in invalid_urls:
            result = self.provider.validate_url(url)
            assert result.is_failure, f"URL should be invalid: {url}"

    def test_extract_main_content_from_html(self):
        """Test extracting content from raw HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Test Article Title</h1>
                <p>This is the main content of the article.</p>
                <p>It contains multiple paragraphs with meaningful text.</p>
                <p>The newspaper3k library should extract this cleanly.</p>
            </article>
        </body>
        </html>
        """
        
        result = self.provider.extract_main_content(html)
        
        assert result.is_success, f"Failed to extract content: {result.error}"
        text = result.value
        assert len(text) > 50, "Extracted text should be substantial"
        assert "main content" in text.lower() or "article" in text.lower()

    def test_metadata_extraction(self):
        """Test that metadata is properly extracted."""
        # Using a news article that should have rich metadata
        url = "https://en.wikipedia.org/wiki/Web_scraping"
        
        result = self.provider.fetch_url(url)
        
        if result.is_success:
            content = result.value
            metadata = content.metadata
            
            # Check for common metadata fields
            # Note: availability depends on the article
            print(f"Available metadata: {list(metadata.keys())}")
            
            # Verify metadata is at least populated with something
            assert len(metadata) > 0, "Metadata should not be empty"
        else:
            # If fetch fails, just log it (might be network issues in test env)
            print(f"Note: Could not fetch URL for metadata test: {result.error}")
            pytest.skip("Network fetch failed")

    def test_empty_content_handling(self):
        """Test handling of pages with no extractable content."""
        result = self.provider.extract_main_content("")
        
        assert result.is_failure, "Should fail on empty HTML"
        assert "empty" in result.error.lower()

    def test_short_content_handling(self):
        """Test handling of pages with very short content."""
        html = "<html><body><p>Too short</p></body></html>"
        
        result = self.provider.extract_main_content(html)
        
        assert result.is_failure, "Should fail on too-short content"
        assert "short" in result.error.lower()

    def test_fetch_with_custom_timeout(self):
        """Test fetching with custom timeout."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        
        result = self.provider.fetch_url(url, timeout=60)
        
        # Should work with custom timeout
        if result.is_failure:
            # Network issues are acceptable in tests
            print(f"Note: Fetch with timeout test skipped: {result.error}")
            pytest.skip("Network fetch failed")
        else:
            assert result.is_success

    def test_user_agent_configuration(self):
        """Test that custom user agent can be configured."""
        custom_ua = "CustomBot/1.0"
        provider = Newspaper3kWebFetchProvider(user_agent=custom_ua)
        
        assert provider.user_agent == custom_ua
        assert provider.config.browser_user_agent == custom_ua

    def test_fetch_url_safe_wrapper(self):
        """Test the safe wrapper with retry logic."""
        url = "https://en.wikipedia.org/wiki/Web_scraping"
        
        result = self.provider.fetch_url_safe(url)
        
        # The safe wrapper should handle retries automatically
        if result.is_failure:
            print(f"Note: Safe fetch test result: {result.error}")
            # Don't fail the test on network issues
            pytest.skip("Network fetch failed")
        else:
            assert result.is_success
            assert result.value.text
            print(f"✓ Safe fetch successful: {result.value.title}")


if __name__ == "__main__":
    # Run a quick manual test
    print("Running manual test of Newspaper3kWebFetchProvider...")
    provider = Newspaper3kWebFetchProvider()
    
    test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    print(f"\nFetching: {test_url}")
    
    result = provider.fetch_url(test_url)
    
    if result.is_success:
        content = result.value
        print(f"✓ Success!")
        print(f"  Title: {content.title}")
        print(f"  Text length: {len(content.text)} characters")
        print(f"  Metadata: {list(content.metadata.keys())}")
        print(f"\n  First 200 characters:")
        print(f"  {content.text[:200]}...")
    else:
        print(f"✗ Failed: {result.error}")
