"""Article search service - orchestrates AI-powered article search operations."""
from ..interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ..queries.article_search_queries import ArticleSearchQuery, ArticleSearchResult
from ..results.result import Result


class ArticleSearchService:
    """
    Domain service for managing AI-powered article search operations.

    This service orchestrates searches for high-quality blog articles
    using AI models with web search capabilities.
    It depends on provider abstractions (DIP).
    """

    def __init__(self, article_search_provider: IArticleSearchProvider):
        """
        Initialize the service with its dependencies.

        Args:
            article_search_provider: Provider abstraction for AI article search
        """
        self._article_search_provider = article_search_provider

    def search_articles(self, query: ArticleSearchQuery) -> Result[ArticleSearchResult]:
        """
        Search for high-quality blog articles that answer a specific question.

        Business Logic:
        - Validates the search query
        - Delegates to AI provider for web search and content analysis
        - Returns formatted article results

        Args:
            query: ArticleSearchQuery with search question and parameters

        Returns:
            Result[ArticleSearchResult]: Success with article results or failure
        """
        # Validate query
        if not query.question or not query.question.strip():
            return Result.failure("Search question cannot be empty")

        if query.max_results <= 0:
            return Result.failure("Max results must be greater than 0")

        if query.max_results > 20:
            return Result.failure("Max results cannot exceed 20")

        # Delegate to AI provider
        search_result = self._article_search_provider.search_articles(query)

        if search_result.is_failure:
            return Result.failure(f"Failed to search articles: {search_result.error}")

        return Result.success(search_result.value)