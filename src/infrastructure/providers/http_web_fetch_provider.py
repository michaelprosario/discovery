"""HTTP implementation of IWebFetchProvider using httpx."""
from typing import Dict, Any
import re
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from ...core.interfaces.providers.i_web_fetch_provider import IWebFetchProvider, WebContent
from ...core.results.result import Result


class HttpWebFetchProvider(IWebFetchProvider):
    """
    HTTP-based implementation of IWebFetchProvider.

    Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
    Follows the Dependency Inversion Principle by implementing the Core interface.
    """

    def __init__(self, user_agent: str = None):
        """
        Initialize the web fetch provider.

        Args:
            user_agent: Custom user agent string (optional)
        """
        self.user_agent = user_agent or "Discovery/0.1.0 (Research Application)"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_url(self, url: str, timeout: int = 30) -> Result[WebContent]:
        """
        Fetch content from a URL and extract main content.

        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Result[WebContent]: Success with web content or failure
        """
        try:
            # Validate URL first
            validation_result = self.validate_url(url)
            if validation_result.is_failure:
                return Result.failure(validation_result.error)

            # Fetch the URL
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = self._extract_title(soup, url)

            # Extract main content
            text_result = self.extract_main_content(response.text)
            if text_result.is_failure:
                return Result.failure(f"Failed to extract content: {text_result.error}")

            text = text_result.value

            # Extract metadata
            metadata = self._extract_metadata(soup, response)

            web_content = WebContent(
                url=url,
                title=title,
                html=response.text,
                text=text,
                metadata=metadata
            )

            return Result.success(web_content)

        except httpx.TimeoutException:
            return Result.failure(f"Request timeout after {timeout} seconds")
        except httpx.HTTPStatusError as e:
            return Result.failure(f"HTTP error {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            return Result.failure(f"Request error: {str(e)}")
        except Exception as e:
            return Result.failure(f"Unexpected error fetching URL: {str(e)}")

    def validate_url(self, url: str) -> Result[bool]:
        """
        Validate that a URL is properly formatted and accessible.

        Args:
            url: The URL to validate

        Returns:
            Result[bool]: Success with True if valid, False otherwise, or failure
        """
        try:
            # Check basic format
            if not url or not url.strip():
                return Result.failure("URL cannot be empty")

            url = url.strip()

            # Check protocol
            if not (url.startswith('http://') or url.startswith('https://')):
                return Result.failure("URL must start with http:// or https://")

            # Parse URL
            parsed = urlparse(url)

            # Validate components
            if not parsed.netloc:
                return Result.failure("Invalid URL: missing domain")

            # Check for suspicious patterns
            if any(char in url for char in ['<', '>', '"', "'"]):
                return Result.failure("Invalid URL: contains suspicious characters")

            return Result.success(True)

        except Exception as e:
            return Result.failure(f"URL validation error: {str(e)}")

    def extract_main_content(self, html: str) -> Result[str]:
        """
        Extract the main content from HTML, removing ads, navigation, etc.

        Uses a simple heuristic-based approach to identify main content.
        Can be enhanced with libraries like readability-lxml for better results.

        Args:
            html: Raw HTML content

        Returns:
            Result[str]: Success with extracted text or failure
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                tag.decompose()

            # Try to find main content area
            main_content = None

            # Try common main content selectors
            for selector in ['main', 'article', '[role="main"]', '.main-content', '#main-content', '.content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.body

            if not main_content:
                return Result.failure("Could not extract main content from HTML")

            # Extract text
            text = main_content.get_text(separator='\n', strip=True)

            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
            text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
            text = text.strip()

            if not text:
                return Result.failure("No text content found")

            return Result.success(text)

        except Exception as e:
            return Result.failure(f"Content extraction error: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract page title from HTML.

        Args:
            soup: BeautifulSoup parsed HTML
            url: Original URL (fallback)

        Returns:
            str: Extracted title or URL as fallback
        """
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # Try h1 tag
        h1 = soup.find('h1')
        if h1 and h1.get_text():
            return h1.get_text().strip()

        # Fallback to URL
        return url

    def _extract_metadata(self, soup: BeautifulSoup, response: httpx.Response) -> Dict[str, Any]:
        """
        Extract metadata from HTML and HTTP response.

        Args:
            soup: BeautifulSoup parsed HTML
            response: HTTP response object

        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {}

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc['content'].strip()

        # Extract Open Graph metadata
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        for tag in og_tags:
            if tag.get('property') and tag.get('content'):
                key = tag['property'].replace('og:', '')
                metadata[f'og_{key}'] = tag['content'].strip()

        # Extract author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag and author_tag.get('content'):
            metadata['author'] = author_tag['content'].strip()

        # Extract published date
        date_tag = soup.find('meta', attrs={'name': 'publish-date'}) or \
                   soup.find('meta', property='article:published_time')
        if date_tag and date_tag.get('content'):
            metadata['published_date'] = date_tag['content'].strip()

        # HTTP headers
        metadata['content_type'] = response.headers.get('content-type', 'unknown')
        metadata['charset'] = response.encoding or 'utf-8'

        # Final URL (after redirects)
        metadata['final_url'] = str(response.url)

        return metadata
