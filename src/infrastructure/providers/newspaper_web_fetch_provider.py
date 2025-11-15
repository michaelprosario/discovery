"""Newspaper3k implementation of IWebFetchProvider for improved article extraction."""
import random
import re
import time
from typing import Dict, Any
from urllib.parse import urlparse
from newspaper import Article, Config

from ...core.interfaces.providers.i_web_fetch_provider import IWebFetchProvider, WebContent
from ...core.results.result import Result


class Newspaper3kWebFetchProvider(IWebFetchProvider):
    """
    Newspaper3k-based implementation of IWebFetchProvider.

    Uses the newspaper3k library for enhanced article extraction with better
    content quality, automatic image detection, and metadata extraction.
    Configured to mimic a real browser to avoid bot detection.
    """

    def __init__(self, user_agent: str = None, language: str = 'en'):
        """
        Initialize the web fetch provider.

        Args:
            user_agent: Custom user agent string (optional)
            language: Language for article parsing (default: 'en')
        """
        # Use a realistic Chrome browser user agent to avoid bot detection
        default_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
        self.user_agent = user_agent or default_user_agent
        self.language = language
        
        # Configure newspaper3k to behave like a browser
        self.config = Config()
        self.config.browser_user_agent = self.user_agent
        self.config.request_timeout = 30
        self.config.fetch_images = False  # Disable image fetching for faster performance
        self.config.memoize_articles = False  # Don't cache articles
        self.config.language = language
        
        # Enhanced headers to mimic a real browser request
        self.config.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",  # Removed 'br' - brotli not supported without extra dependency
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def _sanitize_html(self, html: str) -> str:
        """
        Remove XML-incompatible characters from HTML content.
        
        XML 1.0 only allows specific character ranges:
        - #x9 (tab)
        - #xA (line feed)
        - #xD (carriage return)  
        - [#x20-#xD7FF] (printable characters and most Unicode)
        - [#xE000-#xFFFD] (private use and other valid Unicode)
        
        This removes NULL bytes and control characters that cause
        "All strings must be XML compatible" errors in newspaper3k.
        
        Args:
            html: Raw HTML content that may contain invalid characters
            
        Returns:
            str: Sanitized HTML content safe for XML parsing
        """
        if not html:
            return html
        
        # Remove NULL bytes and control characters (except tab, LF, CR)
        # Pattern matches: \x00-\x08, \x0B, \x0C, \x0E-\x1F, \x7F-\x9F
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', html)
        
        return sanitized

    def fetch_url(self, url: str, timeout: int = 30) -> Result[WebContent]:
        """
        Fetch content from a URL and extract main content using newspaper3k.

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

            # Add random delay to avoid pattern detection
            time.sleep(random.uniform(0.5, 2.0))
            
            # Create article object with our configuration
            article = Article(url, config=self.config)
            
            # Update timeout if provided
            if timeout != 30:
                article.config.request_timeout = timeout
            
            # Download and parse the article
            article.download()
            
            # Sanitize HTML content before parsing to remove XML-incompatible characters
            if article.html:
                article.html = self._sanitize_html(article.html)
            
            article.parse()
            
            # Extract NLP features (keywords, summary) if available
            try:
                article.nlp()
            except Exception:
                # NLP features are optional, continue without them
                pass

            # Extract title
            title = article.title or self._extract_title_from_url(url)
            
            # Extract main text content and sanitize it
            text = article.text.strip()
            if text:
                text = self._sanitize_html(text)  # Also sanitize extracted text
            
            if not text:
                return Result.failure("No text content extracted from article")
            
            # Check for minimum content length
            if len(text) < 50:
                return Result.failure(f"Extracted content too short ({len(text)} characters), likely not main content")

            # Build metadata
            metadata = self._build_metadata(article)

            web_content = WebContent(
                url=url,
                title=title,
                html=article.html,
                text=text,
                metadata=metadata
            )

            return Result.success(web_content)

        except Exception as e:
            error_msg = str(e)
            
            # Provide more helpful error messages
            if "404" in error_msg:
                return Result.failure(f"Page not found (404): {url}")
            elif "403" in error_msg:
                return Result.failure("HTTP error 403 (Forbidden - website may be blocking automated requests)")
            elif "429" in error_msg:
                return Result.failure("HTTP error 429 (Rate limited - too many requests)")
            elif "503" in error_msg:
                return Result.failure("HTTP error 503 (Service unavailable - website may have anti-bot protection)")
            elif "timeout" in error_msg.lower():
                return Result.failure(f"Request timeout after {timeout} seconds")
            elif "connection" in error_msg.lower():
                return Result.failure(f"Connection error: {error_msg}")
            else:
                return Result.failure(f"Failed to fetch article: {error_msg}")

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
        Extract the main content from HTML using newspaper3k.

        Note: This method creates a temporary article object from HTML.
        For best results, use fetch_url() instead which handles the full workflow.

        Args:
            html: Raw HTML content

        Returns:
            Result[str]: Success with extracted text or failure
        """
        try:
            if not html or not html.strip():
                return Result.failure("HTML content cannot be empty")

            # Sanitize HTML before parsing to remove XML-incompatible characters
            html = self._sanitize_html(html)

            # Create a temporary article for parsing
            # Note: newspaper3k works best with URLs, this is a fallback
            article = Article('', config=self.config)
            article.set_html(html)
            article.parse()
            
            # Extract NLP features if possible
            try:
                article.nlp()
            except Exception:
                pass

            text = article.text.strip()
            # Also sanitize the extracted text
            if text:
                text = self._sanitize_html(text)

            if not text:
                return Result.failure("Could not extract text content from HTML")
                
            if len(text) < 50:
                return Result.failure(f"Extracted content too short ({len(text)} characters), likely not main content")

            return Result.success(text)

        except Exception as e:
            return Result.failure(f"Content extraction error: {str(e)}")

    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a simple title from URL as fallback.

        Args:
            url: The URL

        Returns:
            str: Extracted title from URL
        """
        return url.split('/')[-1] if '/' in url else url

    def _build_metadata(self, article: Article) -> Dict[str, Any]:
        """
        Build metadata dictionary from newspaper3k Article object.

        Args:
            article: Parsed Article object

        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = {}

        # Basic article metadata
        if article.authors:
            # Ensure authors is a list (could be a set)
            metadata['authors'] = list(article.authors) if not isinstance(article.authors, list) else article.authors
            metadata['author'] = ', '.join(metadata['authors'])

        if article.publish_date:
            metadata['publish_date'] = article.publish_date.isoformat()

        # Top image
        if article.top_image:
            metadata['top_image'] = article.top_image

        # Meta description
        if article.meta_description:
            metadata['description'] = article.meta_description

        # Keywords extracted via NLP - convert set to list for JSON serialization
        if article.keywords:
            metadata['keywords'] = list(article.keywords) if not isinstance(article.keywords, list) else article.keywords

        # Summary generated via NLP
        if article.summary:
            metadata['summary'] = article.summary

        # Videos - convert set to list for JSON serialization
        if article.movies:
            metadata['videos'] = list(article.movies) if not isinstance(article.movies, list) else article.movies

        # Source URL metadata
        if article.source_url:
            metadata['source_url'] = article.source_url

        # Canonical link
        if article.canonical_link:
            metadata['canonical_link'] = article.canonical_link

        # Language detected
        if hasattr(article, 'meta_lang') and article.meta_lang:
            metadata['language'] = article.meta_lang

        # Article tags/categories - convert set to list for JSON serialization
        if article.tags:
            metadata['tags'] = list(article.tags) if not isinstance(article.tags, list) else article.tags

        return metadata

    def fetch_with_retry(self, url: str, timeout: int = 30, max_retries: int = 3) -> Result[WebContent]:
        """
        Fetch URL with retry logic using different user agents if initial attempt fails.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts with different strategies
            
        Returns:
            Result[WebContent]: Success with web content or failure
        """
        # First attempt with default user agent
        result = self.fetch_url(url, timeout)
        if result.is_success:
            return result
            
        # If first attempt failed, try alternative strategies
        if max_retries > 0 and any(code in str(result.error) for code in ["403", "429", "503", "Forbidden", "blocked", "Rate limited"]):
            alternative_agents = self._get_alternative_user_agents()
            
            for i in range(min(max_retries, len(alternative_agents))):
                # Progressive delay - longer waits for later retries
                wait_time = random.uniform(2, 6) * (i + 1)
                time.sleep(wait_time)
                
                # Save original configuration
                original_user_agent = self.user_agent
                original_headers = self.config.headers.copy()
                
                # Update user agent
                self.user_agent = alternative_agents[i]
                self.config.browser_user_agent = self.user_agent
                
                # Update headers
                self.config.headers["User-Agent"] = self.user_agent
                
                # Add some variation to headers for each retry
                if "Mobile" in self.user_agent or "iPhone" in self.user_agent:
                    self.config.headers["Viewport-Width"] = "375"
                    self.config.headers["Device-Memory"] = "2"
                    self.config.headers["Sec-CH-UA-Mobile"] = "?1"
                
                try:
                    retry_result = self.fetch_url(url, timeout)
                    
                    # Restore original configuration
                    self.user_agent = original_user_agent
                    self.config.browser_user_agent = original_user_agent
                    self.config.headers = original_headers
                    
                    if retry_result.is_success:
                        return retry_result
                except Exception:
                    # Restore original configuration even on exception
                    self.user_agent = original_user_agent
                    self.config.browser_user_agent = original_user_agent
                    self.config.headers = original_headers
                    continue
                
                # Restore for next iteration
                self.user_agent = original_user_agent
                self.config.browser_user_agent = original_user_agent
                self.config.headers = original_headers
                    
        return result

    def _get_alternative_user_agents(self) -> list[str]:
        """
        Get a list of alternative browser user agents for retry attempts.
        
        Returns:
            list[str]: List of realistic user agent strings
        """
        return [
            # Latest Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            # Chrome Mobile Android
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # iPhone Safari
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]

    def fetch_url_safe(self, url: str, timeout: int = 30) -> Result[WebContent]:
        """
        Safe wrapper that automatically uses retry logic for better success rates.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Result[WebContent]: Success with web content or failure
        """
        return self.fetch_with_retry(url, timeout, max_retries=3)
