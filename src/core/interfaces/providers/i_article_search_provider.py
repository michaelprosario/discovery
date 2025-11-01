"""Interface for AI-powered article search provider."""
from abc import ABC, abstractmethod
from ...queries.article_search_queries import ArticleSearchQuery, ArticleSearchResult
from ...results.result import Result


class IArticleSearchProvider(ABC):
    """
    Abstract interface for AI-powered article search providers.

    This interface defines the contract for searching blog articles
    using AI models with web search capabilities.
    """

    @abstractmethod
    def search_articles(self, query: ArticleSearchQuery) -> Result[ArticleSearchResult]:
        """
        Search for high-quality blog articles that answer a specific question.

        Args:
            query: ArticleSearchQuery containing the search question and parameters

        Returns:
            Result[ArticleSearchResult]: Success with found articles or failure message
        """
        pass