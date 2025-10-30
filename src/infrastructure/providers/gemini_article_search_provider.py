"""Gemini AI provider for article search with Google search integration."""
import json
import os
from typing import Dict, Any

from ...core.interfaces.providers.i_article_search_provider import IArticleSearchProvider
from ...core.queries.article_search_queries import ArticleSearchQuery, ArticleSearchResult
from ...core.results.result import Result

try:
    import google.generativeai as genai
    from google.generativeai import types as genai_types
except ImportError:
    genai = None
    genai_types = None


class GeminiArticleSearchProvider(IArticleSearchProvider):
    """
    Implementation of article search using Google's Gemini AI with search grounding.

    This provider uses Gemini Flash 2.5 with Google search enabled to find
    high-quality blog articles that answer specific questions.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Google AI API key. If None, will use GOOGLE_AI_API_KEY env var
        """
        if genai is None or genai_types is None:
            raise ImportError("google-generativeai package is required. Install it with: pip install google-generativeai")
            
        self._api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self._api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_AI_API_KEY environment variable.")

        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash-exp")

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

            # Configure the model to use Google search
            generation_config = genai.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent results
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
            )

            # Generate response with search grounding
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config,
                tools=[
                    genai_types.Tool(
                        google_search_retrieval=genai_types.protos.GoogleSearchRetrieval()
                    )
                ],
            )

            if not response.text:
                return Result.failure("No response received from Gemini")

            # Parse the JSON response
            try:
                response_data = json.loads(response.text)
                article_result = ArticleSearchResult.from_dict(response_data)
                return Result.success(article_result)
            except json.JSONDecodeError as e:
                return Result.failure(f"Failed to parse response as JSON: {str(e)}")

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