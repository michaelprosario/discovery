"""Gemini AI provider for article search with Google search integration."""
import json
import os
from typing import Any, List, Optional

from ...core.interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ...core.queries.article_search_queries import ArticleSearchQuery, ArticleSearchResult
from ...core.results.result import Result

# import environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - surfaced through explicit error handling
    genai = None
    types = None


class GeminiArticleSearchProvider(IArticleSearchProvider):
    """
    Implementation of article search using Google's Gemini AI with search grounding.

    This provider uses Gemini Flash 2.5 with Google search enabled to find
    high-quality blog articles that answer specific questions.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Gemini API key. Falls back to GEMINI_API_KEY or GOOGLE_AI_API_KEY env vars
        """
        if genai is None or types is None:
            raise ImportError("google-genai package is required. Install it with: pip install google-genai")

        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY (or legacy GOOGLE_AI_API_KEY) environment variable."
            )

        # Initialize the client using the new API
        self._client = genai.Client(api_key=self._api_key)
        self._model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def search_articles(self, query: ArticleSearchQuery) -> Result[ArticleSearchResult]:
        """
        Search for articles using Gemini with Google search grounding.

        Args:
            query: ArticleSearchQuery containing the search question

        Returns:
            Result[ArticleSearchResult]: Success with found articles or failure
        """
        try:
            prompt = self._build_search_prompt(query.question, query.max_results)
            
            # Configure Google search tool using the new API
            # Note: response_mime_type cannot be used with tools
            config = types.GenerateContentConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=4096,
                tools=[{"google_search": {}}]
            )

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config
            )

            response_text = self._extract_response_text(response)
            if not response_text:
                return Result.failure("No response received from Gemini")

            response_json = self._load_json_payload(response_text)
            if response_json is None:
                return Result.failure("Failed to parse response as JSON")

            # The Gemini response with grounding may have a different structure
            if 'robust_articles' not in response_json and 'articles' in response_json:
                response_json['robust_articles'] = response_json.pop('articles')

            article_result = ArticleSearchResult.from_dict(response_json)
            if len(article_result.articles) > query.max_results:
                article_result = ArticleSearchResult(
                    articles=article_result.articles[: query.max_results]
                )

            return Result.success(article_result)

        except Exception as e:
            return Result.failure(f"Gemini API error: {str(e)}")

    def _build_search_prompt(self, question: str, max_results: int) -> str:
        """
        Build the search prompt for Gemini.

        Args:
            question: The user's question
            max_results: Maximum number of results to return

        Returns:
            Formatted prompt string
        """
        return f"""**Key Question to Answer:** {question}

**Goal:** Find {min(max_results, 10)} high-quality, in-depth blog posts, articles, or guides that provide a comprehensive, robust, and well-cited answer to the Key Question. Prioritize articles that go beyond a surface-level list.

**Quality Filters (Implicit Search Intent):**
1. **Depth:** Must provide detailed explanations, 'how-to' steps, or scientific rationale.
2. **Robustness:** Should appear authoritative (e.g., from reputable blogs, journals, or experts).
3. **Format:** Must be a blog post, article, or online guide (exclude forums, simple news snippets, videos, or bare product pages).

**Output Requirement:** Return ONLY a single JSON object with the key `robust_articles`. Each object in the array must contain only two keys: `title` (the article's title) and `link` (the full URL). Do not include any other text, explanations, or formatting outside the JSON.

**Example of Desired Output Format:**
```json
{{
  "robust_articles": [
    {{
      "title": "A Comprehensive Guide to Optimizing Sleep Hygiene for Deep Rest",
      "link": "https://example.com/sleep-guide-1"
    }},
    {{
      "title": "Beyond Melatonin: 7 Non-Pharmacological Interventions for Insomnia",
      "link": "https://anothersite.org/deep-sleep-interventions"
    }}
  ]
}}
```

Important: Return ONLY the JSON object, no additional text or formatting."""

    def _extract_response_text(self, response: Any) -> Optional[str]:
        """Extract plain text from a Gemini response object."""
        try:
            # Try to get text directly
            if hasattr(response, 'text'):
                return response.text
        except (ValueError, AttributeError):
            pass
        
        # Fallback to extracting from candidates structure
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
        except (AttributeError, IndexError):
            pass
            
        return None

    def _clean_json_response(self, response_text: str) -> str:
        """Strip Markdown code fences that occasionally wrap model output."""
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
            
        return text.strip()

    def _load_json_payload(self, response_text: str) -> Optional[dict]:
        """Attempt to load JSON payload from Gemini output with light cleanup."""
        cleaned = self._clean_json_response(response_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    return None
        return None