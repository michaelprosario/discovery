"""Dependency helpers for article search services."""
from functools import lru_cache

from fastapi import Depends, HTTPException

from ...core.interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ...core.services.article_search_service import ArticleSearchService
from ...infrastructure.providers.gemini_article_search_provider import GeminiArticleSearchProvider


@lru_cache()
def _get_gemini_article_search_provider() -> IArticleSearchProvider:
    """Return a cached GeminiArticleSearchProvider instance."""
    return GeminiArticleSearchProvider()


def get_article_search_provider() -> IArticleSearchProvider:
    """Expose the configured article search provider for FastAPI dependencies."""
    try:
        return _get_gemini_article_search_provider()
    except Exception as exc:  # pragma: no cover - configuration errors surface as HTTP errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Gemini article search provider: {exc}",
        ) from exc


def get_article_search_service(
    provider: IArticleSearchProvider = Depends(get_article_search_provider),
) -> ArticleSearchService:
    """Wire ArticleSearchService with the configured provider."""
    return ArticleSearchService(provider)
