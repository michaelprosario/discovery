"""Article search router for the Discovery API."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List

from ..core.services.article_search_service import ArticleSearchService
from ..core.queries.article_search_queries import ArticleSearchQuery
from .dependencies.article_search import get_article_search_service

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
    responses={404: {"description": "Not found"}},
)


class ArticleSearchRequest(BaseModel):
    """Request model for article search."""
    question: str = Field(..., description="The question to search for articles about", min_length=1)
    max_results: int = Field(10, description="Maximum number of articles to return", ge=1, le=20)


class ArticleResponse(BaseModel):
    """Response model for individual articles."""
    title: str = Field(..., description="The title of the article")
    link: str = Field(..., description="The URL link to the article")


class ArticleSearchResponse(BaseModel):
    """Response model for article search results."""
    robust_articles: List[ArticleResponse] = Field(..., description="List of found articles")


@router.post("/search", response_model=ArticleSearchResponse)
async def search_articles(
    request: ArticleSearchRequest,
    service: ArticleSearchService = Depends(get_article_search_service)
) -> ArticleSearchResponse:
    """
    Search for high-quality blog articles that answer a specific question.

    This endpoint uses AI-powered search to find authoritative, in-depth articles
    that provide comprehensive answers to the given question.

    Args:
        request: ArticleSearchRequest containing the question and search parameters
        service: Injected ArticleSearchService

    Returns:
        ArticleSearchResponse: List of found articles with titles and links

    Raises:
        HTTPException: If the search fails or validation errors occur
    """
    query = ArticleSearchQuery(
        question=request.question,
        max_results=request.max_results
    )

    result = service.search_articles(query)

    if result.is_failure:
        raise HTTPException(
            status_code=400,
            detail=result.error
        )

    articles_data = result.value.to_dict()

    return ArticleSearchResponse(**articles_data)