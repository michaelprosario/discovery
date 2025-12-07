"""HTTP implementation of IWebFetchProvider using httpx."""
import json
from typing import Dict, Any
import re
import random
import time
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
    Enhanced with anti-bot detection evasion techniques.
    """

    def __init__(self, user_agent: str = None):
        """
        Initialize the web fetch provider.

        Args:
            user_agent: Custom user agent string (optional)
        """
        # Use a realistic Chrome browser user agent to avoid bot detection
        default_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
        self.user_agent = user_agent or default_user_agent
        
        # Enhanced headers to mimic a real browser request
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
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

            # Enhanced headers for this specific request
            request_headers = self.headers.copy()
            
            # Add a realistic referrer if it's not the first request
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                request_headers["Referer"] = f"https://{parsed_url.netloc}/"
            
            # Add random delay to avoid pattern detection
            time.sleep(random.uniform(0.5, 2.0))
            
            # Fetch the URL with enhanced browser-like configuration
            client_config = {
                "follow_redirects": True,
                "timeout": timeout,
                # Additional browser-like settings
                "http2": True,  # Enable HTTP/2 support like modern browsers
                "verify": True,  # Verify SSL certificates
                "cookies": {},  # Enable cookie jar
                "limits": httpx.Limits(max_keepalive_connections=10, max_connections=20),
            }
            
            with httpx.Client(**client_config) as client:
                # Sometimes websites block direct access, try accessing homepage first
                try:
                    # Quick request to homepage to establish session
                    homepage_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                    if url != homepage_url:
                        client.get(homepage_url, headers=request_headers, timeout=10)
                        time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass  # Continue even if homepage request fails
                
                response = client.get(url, headers=request_headers)
                response.raise_for_status()

            # Determine if content is plain text or HTML
            content_type = response.headers.get('content-type', '').lower()
            is_plain_text = (
                'text/plain' in content_type or
                url.endswith('.txt') or
                url.endswith('.md')
            )

            if is_plain_text:
                # Handle plain text files
                text = response.text.strip()

                # Extract a simple title from URL
                title = url.split('/')[-1] if '/' in url else url

                # Basic metadata
                metadata = {
                    'content_type': content_type,
                    'charset': response.encoding or 'utf-8',
                    'final_url': str(response.url)
                }

                web_content = WebContent(
                    url=url,
                    title=title,
                    html=response.text,  # Store raw text in html field too
                    text=text,
                    metadata=metadata
                )

                return Result.success(web_content)
            else:
                # Handle HTML content (existing logic)
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
            error_msg = f"HTTP error {e.response.status_code}"
            if e.response.status_code == 403:
                error_msg += " (Forbidden - website may be blocking automated requests)"
            elif e.response.status_code == 429:
                error_msg += " (Rate limited - too many requests)"
            elif e.response.status_code == 503:
                error_msg += " (Service unavailable - website may have anti-bot protection)"
            return Result.failure(f"{error_msg}: {e}")
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
            
            # Normalize URL protocol to lowercase (e.g., Https:// -> https://)
            if url.startswith('Https://'):
                url = 'https://' + url[8:]
            elif url.startswith('Http://'):
                url = 'http://' + url[7:]

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

        Uses a comprehensive heuristic-based approach to identify main content.
        Can be enhanced with libraries like readability-lxml for better results.

        Args:
            html: Raw HTML content

        Returns:
            Result[str]: Success with extracted text or failure
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript', 'form']):
                tag.decompose()

            # Try to find main content area with comprehensive selectors
            main_content = None

            # Try common main content selectors (expanded list)
            selectors = [
                'main',
                'article', 
                '[role="main"]',
                '.main-content',
                '#main-content',
                '.content',
                '.post-content',
                '.entry-content', 
                '.article-content',
                '.blog-content',
                '.page-content',
                '.single-content',
                '.post-body',
                '.article-body',
                '.story-body',
                '.content-area',
                '.primary-content',
                '#content',
                '.wp-content',  # WordPress sites
                '.post',
                '.entry',
                '.article',
                'div[class*="content"]',
                'div[class*="post"]',
                'div[class*="article"]'
            ]
            
            for selector in selectors:
                try:
                    main_content = soup.select_one(selector)
                    if main_content and main_content.get_text(strip=True):
                        # Check if this content looks substantial
                        text_length = len(main_content.get_text(strip=True))
                        if text_length > 100:  # At least 100 characters
                            break
                except Exception:
                    continue
                main_content = None

            # If no main content found, try finding the largest text block
            if not main_content:
                # Find all div elements and pick the one with most text
                divs = soup.find_all('div')
                best_div = None
                max_text_length = 0
                
                for div in divs:
                    # Skip divs with certain classes that are likely not main content
                    div_class = ' '.join(div.get('class', []))
                    if any(skip in div_class.lower() for skip in ['nav', 'menu', 'sidebar', 'footer', 'header', 'comment', 'social', 'share', 'ad']):
                        continue
                        
                    text = div.get_text(strip=True)
                    if len(text) > max_text_length and len(text) > 200:
                        max_text_length = len(text)
                        best_div = div
                        
                if best_div:
                    main_content = best_div

            # If still no main content found, use body but try to filter out navigation
            if not main_content:
                main_content = soup.body
                if main_content:
                    # Remove likely navigation and sidebar elements
                    for unwanted in main_content.find_all(attrs={'class': lambda x: x and any(term in ' '.join(x).lower() for term in ['nav', 'menu', 'sidebar', 'social', 'share', 'comment', 'related', 'suggested'])}):
                        unwanted.decompose()

            if not main_content:
                # Check if this is a JavaScript-heavy SPA with no server-side rendering
                if self._is_javascript_spa(soup):
                    return Result.failure(
                        "This appears to be a JavaScript Single Page Application (SPA) that loads content dynamically. "
                        "The HTML received contains no meaningful content - it's just a skeleton that gets populated by JavaScript. "
                        "To scrape such sites, you would need a headless browser like Selenium or Playwright that can execute JavaScript."
                    )
                return Result.failure("Could not extract main content from HTML")

            # Extract text
            text = main_content.get_text(separator='\\n', strip=True)

            # Clean up whitespace
            text = re.sub(r'\\n\\s*\\n', '\\n\\n', text)  # Multiple newlines to double newline
            text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
            text = text.strip()

            if not text:
                # Try to extract from JSON-LD structured data as fallback
                json_ld_text = self._extract_from_json_ld(soup)
                if json_ld_text:
                    return Result.success(json_ld_text)
                return Result.failure("No text content found after extraction")
                
            if len(text) < 50:
                # This might be a JavaScript-heavy site - try to detect and provide helpful error
                script_tags = soup.find_all('script')
                if len(script_tags) > 10:  # Lots of scripts suggest SPA
                    return Result.failure(
                        f"Extracted content too short ({len(text)} characters). "
                        "This appears to be a JavaScript-heavy site that loads content dynamically. "
                        "Consider using a browser-based scraping tool or checking if the site has an API."
                    )
                return Result.failure(f"Extracted content too short ({len(text)} characters), likely not main content")

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

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> str | None:
        """
        Try to extract content from JSON-LD structured data.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            str | None: Extracted text content or None if not found
        """
        try:
            # Look for JSON-LD script tags
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        # Look for article content
                        if item.get('@type') in ['Article', 'BlogPosting', 'NewsArticle', 'TechArticle']:
                            # Try different content fields
                            content_fields = ['articleBody', 'text', 'description', 'abstract']
                            for field in content_fields:
                                content = item.get(field)
                                if content and isinstance(content, str) and len(content) > 100:
                                    return content
                                    
                        # Look for WebPage content
                        elif item.get('@type') == 'WebPage':
                            description = item.get('description')
                            if description and len(description) > 100:
                                return description
                                
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
                    
            return None
            
        except Exception:
            return None

    def _is_javascript_spa(self, soup: BeautifulSoup) -> bool:
        """
        Detect if a site is a JavaScript Single Page Application with no server-side rendering.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            bool: True if this appears to be a JavaScript SPA with no meaningful content
        """
        # Check for indicators of SPA
        indicators = 0
        
        # No title tag or empty title
        if not soup.title or not soup.title.string or len(soup.title.string.strip()) == 0:
            indicators += 1
            
        # Very little text content in body
        if soup.body:
            body_text = soup.body.get_text(strip=True)
            if len(body_text) < 200:  # Very little actual text content
                indicators += 1
        
        # No substantial paragraphs
        paragraphs = soup.find_all('p')
        substantial_paragraphs = sum(1 for p in paragraphs if len(p.get_text(strip=True)) > 50)
        if substantial_paragraphs == 0:
            indicators += 1
            
        # Many script tags (common in SPAs)
        script_tags = soup.find_all('script')
        if len(script_tags) > 5:  # Lots of scripts
            indicators += 1
            
        # Look for common SPA framework indicators
        spa_indicators = ['react', 'vue', 'angular', 'ember', 'svelte', 'app.js', 'main.js', 'bundle.js']
        for script in script_tags:
            src = script.get('src', '')
            if any(indicator in src.lower() for indicator in spa_indicators):
                indicators += 1
                break
                
        # Check for div with id like "root", "app", "main-app" that's common in SPAs
        spa_root_selectors = ['#root', '#app', '#main-app', '#application', '#react-root']
        for selector in spa_root_selectors:
            if soup.select_one(selector):
                indicators += 1
                break
        
        # If we have 3 or more indicators, it's likely a SPA
        return indicators >= 3

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
            # Safari on macOS (newer version)
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            # Chrome Mobile Android
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # iPhone Safari
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]

    def fetch_with_retry(self, url: str, timeout: int = 30, max_retries: int = 3) -> Result[WebContent]:
        """
        Fetch URL with retry logic using different user agents and strategies if initial attempt fails.
        
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
                
                # Try with a different user agent and modified headers
                original_user_agent = self.user_agent
                original_headers = self.headers.copy()
                
                self.user_agent = alternative_agents[i]
                
                # Modify headers for each retry attempt with more sophistication
                base_headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "cross-site" if i > 0 else "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
                
                # Add DNT header conditionally
                if i % 2 == 0:
                    base_headers["DNT"] = "1"
                    
                # For mobile user agents, adjust headers and add mobile-specific ones
                if "Mobile" in self.user_agent or "iPhone" in self.user_agent:
                    base_headers["Viewport-Width"] = "375"
                    base_headers["Device-Memory"] = "2"
                    base_headers["Sec-CH-UA-Mobile"] = "?1"
                    
                # Add some randomization to headers
                if i == 1:
                    # Try with CloudFlare bypass headers
                    base_headers["CF-RAY"] = f"{random.randint(10000000, 99999999)}-LAX"
                    base_headers["CF-Connecting-IP"] = "127.0.0.1"
                elif i == 2:
                    # Try without certain headers that might trigger detection
                    base_headers.pop("Sec-Fetch-Site", None)
                    base_headers.pop("Sec-Fetch-Dest", None)
                    base_headers.pop("Sec-Fetch-Mode", None)
                    base_headers.pop("Sec-Fetch-User", None)
                
                self.headers = base_headers
                
                try:
                    retry_result = self.fetch_url(url, timeout)
                    
                    # Restore original settings
                    self.user_agent = original_user_agent
                    self.headers = original_headers
                    
                    if retry_result.is_success:
                        return retry_result
                except Exception:
                    # Restore original settings even on exception
                    self.user_agent = original_user_agent
                    self.headers = original_headers
                    continue
                
                # Restore original settings for next iteration
                self.user_agent = original_user_agent
                self.headers = original_headers
                    
        return result
    
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
