"""DuckDuckGo search provider for article search - direct web search without AI."""
from typing import List
import re

from ...core.interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ...core.queries.article_search_queries import (
    ArticleSearchQuery,
    ArticleSearchResult,
    ArticleResult,
)
from ...core.results.result import Result

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    DDGS = None


class DuckDuckGoArticleSearchProvider(IArticleSearchProvider):
    """
    Implementation of article search using DuckDuckGo web search.

    This provider uses the duckduckgo-search library to perform direct web searches
    for articles. It's free, doesn't require API keys, and provides direct search results
    without AI intermediation.

    Advantages:
    - No API key required
    - Free to use
    - Fast and reliable
    - Direct search results from the web
    - Better control over search filtering
    """

    def __init__(self, region: str = "wt-wt", safesearch: str = "moderate"):
        """
        Initialize the DuckDuckGo provider.

        Args:
            region: Region code for search (default: wt-wt for worldwide)
            safesearch: Safe search setting ('on', 'moderate', 'off')
        """
        if DDGS is None:
            raise ImportError(
                "ddgs package is required. "
                "Install it with: pip install ddgs"
            )

        self.region = region
        self.safesearch = safesearch

    def search_articles(self, query: ArticleSearchQuery) -> Result[ArticleSearchResult]:
        """
        Search for articles using DuckDuckGo web search.

        This method performs a web search and filters results to find high-quality
        articles, blog posts, and guides.

        Args:
            query: ArticleSearchQuery containing the search question

        Returns:
            Result[ArticleSearchResult]: Success with found articles or failure
        """
        try:
            # Create search query
            search_query = self._build_search_query(query.question)

            # Perform the search - request more results to filter from
            max_to_fetch = min(query.max_results * 3, 30)

            # Execute search with proper error handling
            try:
                with DDGS() as ddgs:
                    results = list(
                        ddgs.text(
                            query=search_query,
                            region=self.region,
                            safesearch=self.safesearch,
                            max_results=max_to_fetch,
                        )
                    )
            except Exception as search_error:
                # Provide more specific error message for search failures
                return Result.failure(
                    f"DuckDuckGo search request failed: {str(search_error)}"
                )

            if not results:
                return Result.failure("No articles found for the search query")

            # Filter and convert results to ArticleResult objects
            articles = self._filter_and_convert_results(results, query.max_results)

            if not articles:
                return Result.failure(
                    "No suitable articles found after filtering low-quality sources"
                )

            article_result = ArticleSearchResult(articles=articles)
            return Result.success(article_result)

        except Exception as e:
            return Result.failure(f"DuckDuckGo search error: {str(e)}")

    def _build_search_query(self, question: str) -> str:
        """
        Build an optimized search query from the user's question.

        Enhances the search with keywords to find high-quality articles and guides.

        Args:
            question: The user's question

        Returns:
            Optimized search query string
        """
        # Add search operators to find articles, guides, and tutorials
        # This helps filter out forums, product pages, etc.
        enhanced_query = f'{question} (blog OR article OR guide OR tutorial OR "how to")'
        return enhanced_query

    def _filter_and_convert_results(
        self, results: List[dict], max_results: int
    ) -> List[ArticleResult]:
        """
        Filter search results to find high-quality articles and convert to ArticleResult.

        Filters out:
        - Social media posts
        - Forums (Reddit, StackOverflow, etc.)
        - Video sites
        - Shopping/product pages
        - News aggregators without original content

        Prioritizes:
        - Blog posts
        - Educational content
        - In-depth guides
        - Technical documentation

        Args:
            results: Raw search results from DuckDuckGo
            max_results: Maximum number of articles to return

        Returns:
            List of filtered ArticleResult objects
        """
        articles = []

        # Domains to exclude (low-quality or non-article sources)
        excluded_domains = {
            "reddit.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "instagram.com",
            "tiktok.com",
            "youtube.com",
            "vimeo.com",
            "pinterest.com",
            "stackoverflow.com",
            "stackexchange.com",
            "amazon.com",
            "ebay.com",
            "walmart.com",
            "news.google.com",
            "news.yahoo.com",
        }

        # Keywords that suggest low-quality content
        excluded_title_keywords = [
            "buy now",
            "shop",
            "price",
            "discount",
            "sale",
            "forum",
            "watch video",
        ]

        for result in results:
            # Extract URL and title
            url = result.get("href") or result.get("link", "")
            title = result.get("title", "")

            if not url or not title:
                continue

            # Check if domain is excluded
            domain = self._extract_domain(url)
            if any(excluded in domain.lower() for excluded in excluded_domains):
                continue

            # Check if title contains excluded keywords
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in excluded_title_keywords):
                continue

            # Check if URL looks like a valid article
            if not self._is_valid_article_url(url):
                continue

            # Add the article
            articles.append(ArticleResult(title=title, link=url))

            # Stop when we have enough results
            if len(articles) >= max_results:
                break

        return articles

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain name
        """
        # Simple regex to extract domain
        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if match:
            return match.group(1)
        return ""

    def _is_valid_article_url(self, url: str) -> bool:
        """
        Check if URL looks like a valid article page.

        Excludes:
        - Homepage URLs (too short)
        - URLs with video/image file extensions
        - URLs with query parameters suggesting pagination or comments

        Args:
            url: URL to check

        Returns:
            True if URL appears to be an article
        """
        url_lower = url.lower()

        # Exclude file extensions that are not articles
        excluded_extensions = [".pdf", ".mp4", ".mp3", ".jpg", ".png", ".gif", ".zip"]
        if any(url_lower.endswith(ext) for ext in excluded_extensions):
            return False

        # Exclude URLs that are likely comment pages or pagination
        excluded_patterns = ["?page=", "&page=", "/comments/", "#comment"]
        if any(pattern in url_lower for pattern in excluded_patterns):
            return False

        # URL should have some path (not just domain)
        # This filters out homepages
        path = url.split("://")[-1].split("/")[1:]  # Get path parts after domain
        if len(path) < 1 or (len(path) == 1 and not path[0]):
            return False

        return True
