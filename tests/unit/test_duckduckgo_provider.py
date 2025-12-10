"""Unit tests for DuckDuckGo article search provider."""
import pytest
from unittest.mock import Mock, patch
from src.core.queries.article_search_queries import ArticleSearchQuery, ArticleResult
from src.infrastructure.providers.duckduckgo_article_search_provider import DuckDuckGoArticleSearchProvider


class TestDuckDuckGoProvider:
    """Test suite for DuckDuckGo article search provider."""

    def test_provider_initialization(self):
        """Test that provider initializes correctly."""
        provider = DuckDuckGoArticleSearchProvider()
        assert provider is not None
        assert provider.region == "wt-wt"
        assert provider.safesearch == "moderate"

    def test_provider_with_custom_settings(self):
        """Test provider with custom region and safesearch."""
        provider = DuckDuckGoArticleSearchProvider(region="us-en", safesearch="on")
        assert provider.region == "us-en"
        assert provider.safesearch == "on"

    def test_build_search_query(self):
        """Test search query building."""
        provider = DuckDuckGoArticleSearchProvider()
        question = "What is Python clean architecture?"
        query = provider._build_search_query(question)
        
        assert "Python clean architecture" in query
        assert "blog OR article OR guide" in query

    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        provider = DuckDuckGoArticleSearchProvider()
        
        assert "github.com" in provider._extract_domain("https://github.com/user/repo")
        assert "medium.com" in provider._extract_domain("https://www.medium.com/article")
        assert "example.com" in provider._extract_domain("http://example.com/path")

    def test_is_valid_article_url(self):
        """Test URL validation logic."""
        provider = DuckDuckGoArticleSearchProvider()
        
        # Valid article URLs
        assert provider._is_valid_article_url("https://blog.example.com/article/title")
        assert provider._is_valid_article_url("https://medium.com/@user/story")
        
        # Invalid URLs
        assert not provider._is_valid_article_url("https://example.com")  # Homepage
        assert not provider._is_valid_article_url("https://example.com/")  # Homepage
        assert not provider._is_valid_article_url("https://example.com/video.mp4")  # Video
        assert not provider._is_valid_article_url("https://example.com/doc.pdf")  # PDF

    @patch('src.infrastructure.providers.duckduckgo_article_search_provider.DDGS')
    def test_search_articles_success(self, mock_ddgs):
        """Test successful article search."""
        # Mock the DDGS search results
        mock_results = [
            {
                "title": "Clean Architecture in Python",
                "href": "https://blog.example.com/clean-architecture",
                "body": "Guide to clean architecture..."
            },
            {
                "title": "Python Best Practices",
                "href": "https://medium.com/python-practices",
                "body": "Learn Python best practices..."
            }
        ]
        
        # Setup mock
        mock_instance = Mock()
        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)
        mock_instance.text = Mock(return_value=iter(mock_results))
        mock_ddgs.return_value = mock_instance
        
        # Execute test
        provider = DuckDuckGoArticleSearchProvider()
        query = ArticleSearchQuery(question="Python clean architecture", max_results=2)
        result = provider.search_articles(query)
        
        # Verify
        assert result.is_success
        assert len(result.value.articles) <= 2
        assert all(isinstance(a, ArticleResult) for a in result.value.articles)

    @patch('src.infrastructure.providers.duckduckgo_article_search_provider.DDGS')
    def test_search_filters_excluded_domains(self, mock_ddgs):
        """Test that excluded domains are filtered out."""
        # Mock results including excluded domains
        mock_results = [
            {"title": "Reddit Discussion", "href": "https://reddit.com/r/python", "body": "..."},
            {"title": "Good Article", "href": "https://blog.example.com/article", "body": "..."},
            {"title": "YouTube Video", "href": "https://youtube.com/watch?v=123", "body": "..."},
            {"title": "Another Article", "href": "https://dev.to/article", "body": "..."},
        ]
        
        mock_instance = Mock()
        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)
        mock_instance.text = Mock(return_value=iter(mock_results))
        mock_ddgs.return_value = mock_instance
        
        provider = DuckDuckGoArticleSearchProvider()
        query = ArticleSearchQuery(question="Test", max_results=10)
        result = provider.search_articles(query)
        
        assert result.is_success
        # Should only get the blog articles, not reddit or youtube
        for article in result.value.articles:
            assert "reddit.com" not in article.link.lower()
            assert "youtube.com" not in article.link.lower()

    @patch('src.infrastructure.providers.duckduckgo_article_search_provider.DDGS')
    def test_search_handles_errors(self, mock_ddgs):
        """Test error handling in search."""
        # Make the search raise an exception
        mock_ddgs.side_effect = Exception("Network error")
        
        provider = DuckDuckGoArticleSearchProvider()
        query = ArticleSearchQuery(question="Test", max_results=5)
        result = provider.search_articles(query)
        
        assert result.is_failure
        assert "error" in result.error.lower()
