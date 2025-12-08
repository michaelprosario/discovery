"""Dependency helpers for article search services."""
from functools import lru_cache
import os

from fastapi import Depends, HTTPException

from ...core.interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ...core.services.article_search_service import ArticleSearchService
from ...infrastructure.providers.gemini_article_search_provider import GeminiArticleSearchProvider
from ...infrastructure.providers.duckduckgo_article_search_provider import DuckDuckGoArticleSearchProvider


@lru_cache()
def _get_gemini_article_search_provider() -> IArticleSearchProvider:
    """Return a cached GeminiArticleSearchProvider instance."""
    return GeminiArticleSearchProvider()


@lru_cache()
def _get_duckduckgo_article_search_provider() -> IArticleSearchProvider:
    """Return a cached DuckDuckGoArticleSearchProvider instance."""
    return DuckDuckGoArticleSearchProvider()


def get_article_search_provider() -> IArticleSearchProvider:
    """
    Expose the configured article search provider for FastAPI dependencies.
    
    Provider selection is controlled by the ARTICLE_SEARCH_PROVIDER environment variable:
    - 'duckduckgo' or 'ddg': Use DuckDuckGo search (default, no API key needed)
    - 'gemini': Use Gemini AI with Google search grounding (requires API key)
    """
    provider_type = os.getenv("ARTICLE_SEARCH_PROVIDER", "duckduckgo").lower()
    
    try:
        if provider_type in ("gemini",):
            return _get_gemini_article_search_provider()
        else:  # Default to DuckDuckGo
            return _get_duckduckgo_article_search_provider()
    except Exception as exc:  # pragma: no cover - configuration errors surface as HTTP errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize article search provider ({provider_type}): {exc}",
        ) from exc


def get_article_search_service(
    provider: IArticleSearchProvider = Depends(get_article_search_provider),
) -> ArticleSearchService:
    """Wire ArticleSearchService with the configured provider."""
    return ArticleSearchService(provider)
