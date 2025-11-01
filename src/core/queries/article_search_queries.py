"""Query objects for Article Search operations following CQRS pattern."""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ArticleSearchQuery:
    """Query to search for blog articles that answer a specific question."""

    question: str
    max_results: int = 10


@dataclass
class ArticleResult:
    """Result representing a single article from search."""

    title: str
    link: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "link": self.link
        }


@dataclass
class ArticleSearchResult:
    """Result from an article search containing multiple articles."""

    articles: List[ArticleResult]

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "robust_articles": [article.to_dict() for article in self.articles]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ArticleSearchResult':
        """Create ArticleSearchResult from dictionary data."""
        articles_data = data.get("robust_articles", [])
        articles = [
            ArticleResult(title=item["title"], link=item["link"])
            for item in articles_data
        ]
        return ArticleSearchResult(articles=articles)