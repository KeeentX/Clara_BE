from googlesearch import search
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse, quote
import logging
import sys

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SearchService")

class SearchService:
    """
    Service for searching information about politicians
    from web sources.
    """
    
    def __init__(self, api_key=None, search_engine="google", debug=True):
        """
        Initialize the search service.
        
        Parameters:
        - api_key: Optional API key for search service
        - search_engine: Search engine to use (google, bing, etc.)
        - debug: Enable debug mode
        """
        self.api_key = api_key
        self.search_engine = search_engine
        self.debug = debug
        logger.info(f"SearchService initialized with search_engine={search_engine}")

    def generate_search_queries(self, name, position):
        """
        Generate a list of search queries for researching a politician.
        
        Parameters:
        - name: Politician name
        - position: Current or most recent position
        
        Returns:
        - List of search query strings
        """
        logger.info(f"Generating search queries for: {name} ({position})")
        
        # Base queries about the politician
        base_queries = [
            f"{name} {position}",
            f"{name} politician background",
            f"{name} biography",
            f"{name} political career",
        ]
        
        # Accomplishments queries
        accomplishment_queries = [
            f"{name} accomplishments",
            f"{name} legislation authored",
            f"{name} policy success",
        ]
        
        # Criticism and controversy queries
        criticism_queries = [
            f"{name} controversy and scandal",
            f"{name} corruption allegations",
            f"{name} ethics investigation",
        ]
        
        # Background and history queries
        background_queries = [
            f"{name} education background",
            f"{name} political history",
            f"{name} family background",
            f"{name} business interests",
            f"{name} financial disclosure",
        ]
        
        # Combine all queries
        all_queries = base_queries + accomplishment_queries + criticism_queries + background_queries
        
        # Add position-specific queries if position is provided
        if position and len(position.strip()) > 0:
            position_queries = [
                f"{name} {position} record",
                f"{name} {position} performance",
                f"{name} {position} tenure",
                f"{name} before {position}",
            ]
            all_queries.extend(position_queries)
        
        # Remove duplicates while preserving order
        unique_queries = []
        for query in all_queries:
            if query not in unique_queries:
                unique_queries.append(query)
        
        logger.info(f"Generated {len(unique_queries)} search queries")
        return unique_queries
    
    def is_website_url(self, url):
        """
        Check if URL is a website (not a PDF, image, or other file type)
        Returns True for website URLs, False for file downloads
        """
        # File extensions to exclude
        excluded_extensions = [
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.zip',
            '.rar', '.tar', '.gz', '.7z'
        ]
        
        try:
            # Skip relative URLs
            if url.startswith('/'):
                return False
                
            # Check parsed URL
            parsed_url = urlparse(url)
            
            # Make sure it's a full URL with scheme and domain
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
                
            path = parsed_url.path.lower()
            
            # Check for file extensions in the path
            for ext in excluded_extensions:
                if path.endswith(ext):
                    return False
            
            # Check for file extension in query parameters
            if re.search(r'file(name|type)=.*\.(pdf|doc|jpg|png)', url.lower()):
                return False
                
            return True
        except Exception:
            return False
        
    def search(self, query, num_results=10):
        """
        Search for information using the specified query.
        
        Parameters:
        - query: Search query string
        - num_results: Number of results to return
        
        Returns:
        - List of search results, each containing url, title, and snippet
        """
        logger.info(f"Searching for: '{query}', num_results={num_results}")
        
        if self.search_engine.lower() == "google":
            results = self._google_search(query, num_results)
            if results is None:
                results = []
            # Add the query to the results for reference
            for result in results:
                result['query'] = query
            logger.info(f"Search returned {len(results)} results for query: '{query}'")
            return results
        else:
            logger.error(f"Search engine '{self.search_engine}' not supported")
            raise ValueError(f"Search engine '{self.search_engine}' not supported")
    
    def _google_search(self, query, num_results=10):
        """Use the googlesearch library to perform a Google search."""
        search_results = []
        skipped_count = 0
        error_count = 0
        
        try:
            search_urls = []
            # Get more URLs than needed to account for filtered ones
            for url in search(query, num_results=num_results*3, lang='en'):
                if self.is_website_url(url):
                    search_urls.append(url)
                    if len(search_urls) >= num_results*2:  # Get twice as many as needed to account for errors
                        break
                else:
                    skipped_count += 1
            
            logger.info(f"Found {len(search_urls)} valid URLs (skipped {skipped_count})")
            
            # Process each URL to get content
            for url in search_urls:
                if len(search_results) >= num_results:
                    break
                    
                try:
                    title, snippet = self._get_title_and_snippet(url)
                    
                    # Skip results with empty content
                    if snippet and snippet.strip() != "No snippet available":
                        search_results.append({
                            "url": url,
                            "title": title,
                            "snippet": snippet
                        })
                        logger.info(f"Added result with URL: {url}")
                    else:
                        logger.info(f"Skipped URL with empty content: {url}")
                except Exception as e:
                    error_count += 1
                    logger.info(f"Failed to get content from {url}: {str(e)[:50]}...")
                
                time.sleep(1)  # Be respectful with rate limiting
            
            logger.info(f"Search complete: {len(search_results)} results, {error_count} errors")
            return search_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)[:100]}")
            return []
    
    def _get_title_and_snippet(self, url):
        """Get the title and a snippet of text from a URL."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Ensure we're working with UTF-8 text
        if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string.strip() if soup.title else "No title found"
        
        # Get snippet (first few paragraphs or relevant text)
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') 
                     if len(p.get_text(strip=True)) > 50]
        
        if paragraphs:
            # Join the first few paragraphs up to ~200 chars
            snippet_text = ""
            for p in paragraphs:
                if len(snippet_text) < 200:
                    snippet_text += p + " "
                else:
                    break
            snippet = snippet_text[:250] + "..." if len(snippet_text) > 250 else snippet_text
        else:
            # Fallback to any text content
            all_text = soup.get_text(separator=' ', strip=True)
            snippet = all_text[:250] + "..." if len(all_text) > 250 else all_text
        
        if not snippet or snippet.strip() == "":
            snippet = "No snippet available"
            
        return title, snippet
    
    def fetch_content(self, url):
        """
        Fetch and extract content from a URL.
        
        Parameters:
        - url: The URL to fetch content from
        
        Returns:
        - Extracted content as text
        """
        logger.info(f"Fetching content from: {url}")
        
        try:
            # Try with requests first
            content = self._scrape_with_requests(url)
            
            # If we got empty content or mostly ads, try with Selenium
            if not content or len(content.split()) < 100:
                if self.debug:
                    logger.info(f"Limited content with requests, trying Selenium for {url}")
                content = self._scrape_with_selenium(url)
            
            if content:
                content_length = len(content)
                logger.info(f"Extracted {content_length} characters from {url}")
            else:
                logger.info(f"No content extracted from {url}")
                
            return content
            
        except Exception as e:
            logger.error(f"Error fetching content: {str(e)[:100]}")
            return ""
    
    def _scrape_with_requests(self, url):
        """Scrape content using requests and BeautifulSoup (for simple pages)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Ensure we're working with UTF-8 text
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different content extraction strategies
            # 1. Look for article or main content containers
            content_containers = soup.select('article, .article, .content, .post, main, #main, #content')
            if content_containers:
                return ' '.join([container.get_text(separator=' ', strip=True) for container in content_containers])
            
            # 2. Get all paragraphs, excluding ones that might be ads or navigation
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') 
                         if len(p.get_text(strip=True)) > 100]  # Filter out short paragraphs likely to be ads
            if paragraphs:
                return ' '.join(paragraphs)
                
            # 3. Fallback: get general text content
            return soup.get_text(separator=' ', strip=True)
        
        except Exception as e:
            if self.debug:
                logger.info(f"Error with requests: {str(e)[:100]}")
            return ""
    
    def _scrape_with_selenium(self, url):
        """Scrape content using Selenium (for JavaScript-heavy pages)"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        driver = None
        try:
            # Set up headless Chrome browser
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Initialize the Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            # Wait for JavaScript to load content
            time.sleep(2)
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Try different content extraction strategies
            content_containers = soup.select('article, .article, .content, .post, main, #main, #content')
            if content_containers:
                return ' '.join([container.get_text(separator=' ', strip=True) for container in content_containers])
            
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') 
                         if len(p.get_text(strip=True)) > 100]
            if paragraphs:
                return ' '.join(paragraphs)
                
            return soup.get_text(separator=' ', strip=True)
        
        except Exception as e:
            if self.debug:
                logger.info(f"Error with Selenium: {str(e)[:100]}")
            return ""
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def close(self):
        """Clean up any resources."""
        pass

    def search_politician_image(self, name, position=None):
        """
        Search for a single image of the politician using free methods.
        
        Parameters:
        - name: Politician name
        - position: Current or most recent position (optional)
        
        Returns:
        - Dictionary with image URL and metadata, or None if no image found
        """
        logger.info(f"Searching for image of politician: {name}")
        
        # Method 1: Try Wikipedia first (most reliable for politicians)
        result = self._search_wikipedia_image(name)
        if result:
            logger.info(f"Found image via Wikipedia: {result['url']}")
            return result
        
        # Method 2: Try DuckDuckGo (no API key required)
        result = self._search_duckduckgo_image(name, position)
        if result:
            logger.info(f"Found image via DuckDuckGo: {result['url']}")
            return result
        
        # Method 3: Fall back to Google Images scraping
        result = self._scrape_google_images(name, position)
        if result:
            logger.info(f"Found image via Google scraping: {result['url']}")
            return result
        
        logger.warning(f"No image found for {name}")
        return None
    
    def _search_wikipedia_image(self, name):
        """
        Search for politician image on Wikipedia using the free Wikipedia API.
        
        Parameters:
        - name: Politician name
        
        Returns:
        - Dictionary with image data or None
        """
        try:
            logger.info(f"Searching Wikipedia for {name}")
            
            # Step 1: Search for the Wikipedia page
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(name)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; PoliticianResearchBot/1.0)'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have a thumbnail image
                if 'thumbnail' in data and 'source' in data['thumbnail']:
                    image_url = data['thumbnail']['source']
                    
                    # Get higher resolution version if available
                    if 'originalimage' in data and 'source' in data['originalimage']:
                        image_url = data['originalimage']['source']
                    
                    # Validate the image URL
                    if self._is_valid_image_url(image_url):
                        return {
                            'url': image_url,
                            'title': data.get('title', name),
                            'source': 'wikipedia',
                            'page_url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            'description': data.get('description', ''),
                            'search_method': 'wikipedia_api'
                        }
            
            # If direct search fails, try searching Wikipedia's search API
            search_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(f"{name} politician")
            response = requests.get(search_api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'thumbnail' in data and 'source' in data['thumbnail']:
                    image_url = data['thumbnail']['source']
                    if 'originalimage' in data and 'source' in data['originalimage']:
                        image_url = data['originalimage']['source']
                    
                    if self._is_valid_image_url(image_url):
                        return {
                            'url': image_url,
                            'title': data.get('title', name),
                            'source': 'wikipedia',
                            'page_url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            'description': data.get('description', ''),
                            'search_method': 'wikipedia_api_search'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {str(e)}")
            return None
    
    def _search_duckduckgo_image(self, name, position=None):
        """
        Search for images using DuckDuckGo (no API key required).
        
        Parameters:
        - name: Politician name
        - position: Current or most recent position (optional)
        
        Returns:
        - Dictionary with image data or None
        """
        try:
            logger.info(f"Searching DuckDuckGo for {name}")
            
            # Construct search query
            if position:
                query = f"{name} {position} politician"
            else:
                query = f"{name} politician"
            
            # DuckDuckGo image search endpoint
            search_url = "https://duckduckgo.com/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Get initial page to get tokens
            session = requests.Session()
            response = session.get(search_url, headers=headers)
            
            # Extract vqd token from the page
            vqd_match = re.search(r'vqd=([\d-]+)', response.text)
            if not vqd_match:
                return None
            
            vqd = vqd_match.group(1)
            
            # Now search for images
            image_search_url = "https://duckduckgo.com/i.js"
            params = {
                'l': 'us-en',
                'o': 'json',
                'q': query,
                'vqd': vqd,
                'f': ',,,',
                'p': '1'
            }
            
            response = session.get(image_search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data and len(data['results']) > 0:
                    # Get the first result
                    result = data['results'][0]
                    image_url = result.get('image')
                    
                    if self._is_valid_image_url(image_url):
                        return {
                            'url': image_url,
                            'title': result.get('title', name),
                            'source': result.get('source', 'duckduckgo'),
                            'width': result.get('width'),
                            'height': result.get('height'),
                            'search_method': 'duckduckgo'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")
            return None
    
    def _scrape_google_images(self, name, position=None):
        """
        Scrape Google Images for a single image result (improved version).
        
        Parameters:
        - name: Politician name
        - position: Current or most recent position (optional)
        
        Returns:
        - Dictionary with image data or None
        """
        try:
            logger.info(f"Scraping Google Images for {name}")
            
            # Construct search query
            if position:
                query = f"{name} {position} politician"
            else:
                query = f"{name} politician"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Google Images search URL
            search_url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&safe=active&tbs=itp:face"  # Filter for faces
            
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Look for images in script tags (primary method)
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'AF_initDataChunkQueue' in script.string:
                    script_content = script.string
                    
                    # More refined regex to find image URLs
                    image_patterns = [
                        r'"(https://[^"]*\.(?:jpg|jpeg|png|gif|webp)(?:\?[^"]*)?)"',
                        r'"(https://encrypted-tbn\d\.gstatic\.com/images\?[^"]*)"',
                        r'"(https://[^"]*googleapis\.com/[^"]*\.(?:jpg|jpeg|png))"'
                    ]
                    
                    for pattern in image_patterns:
                        image_urls = re.findall(pattern, script_content, re.IGNORECASE)
                        
                        for image_url in image_urls:
                            # Clean up the URL
                            image_url = image_url.replace('\\u003d', '=').replace('\\u0026', '&')
                            
                            if self._is_valid_image_url(image_url) and self._is_likely_person_image(image_url):
                                return {
                                    'url': image_url,
                                    'title': f"Image of {name}",
                                    'source': 'google_images',
                                    'thumbnail': image_url,
                                    'search_method': 'google_scraping_script'
                                }
            
            # Method 2: Look for img tags with specific attributes
            img_tags = soup.find_all('img')
            for img in img_tags:
                # Check various image attributes
                image_url = None
                for attr in ['data-src', 'src', 'data-iurl']:
                    if img.get(attr):
                        image_url = img.get(attr)
                        break
                
                if image_url and self._is_valid_image_url(image_url) and self._is_likely_person_image(image_url):
                    return {
                        'url': image_url,
                        'title': img.get('alt', f"Image of {name}"),
                        'source': 'google_images',
                        'thumbnail': image_url,
                        'search_method': 'google_scraping_img_tags'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Google Images: {str(e)}")
            return None
    
    def _is_valid_image_url(self, url):
        """
        Check if URL points to a valid image.
        
        Parameters:
        - url: Image URL to validate
        
        Returns:
        - Boolean indicating if URL is valid
        """
        if not url:
            return False
        
        try:
            # Check if URL has image extension or is from known image services
            url_lower = url.lower()
            
            # Valid image extensions
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            has_image_extension = any(ext in url_lower for ext in image_extensions)
            
            # Known image hosting services
            image_services = [
                'upload.wikimedia.org',
                'commons.wikimedia.org', 
                'encrypted-tbn',
                'gstatic.com',
                'googleapis.com',
                'imgur.com',
                'flickr.com'
            ]
            is_image_service = any(service in url_lower for service in image_services)
            
            # Parse URL to check if it's well-formed
            parsed = urlparse(url)
            has_valid_scheme = parsed.scheme in ['http', 'https']
            has_valid_domain = parsed.netloc != ''
            
            # Exclude certain domains that typically don't host politician images
            excluded_domains = [
                'ads.', 'doubleclick.', 'googleadservices.', 'googlesyndication.',
                'facebook.com/tr', 'analytics.', 'google-analytics.'
            ]
            is_not_ad_domain = not any(domain in url_lower for domain in excluded_domains)
            
            return (has_image_extension or is_image_service) and has_valid_scheme and has_valid_domain and is_not_ad_domain
            
        except Exception:
            return False
    
    def _is_likely_person_image(self, url):
        """
        Check if the image URL is likely to be a person/politician image.
        
        Parameters:
        - url: Image URL to check
        
        Returns:
        - Boolean indicating if it's likely a person image
        """
        url_lower = url.lower()
        
        # Exclude obvious non-person images
        exclude_keywords = [
            'logo', 'icon', 'banner', 'flag', 'seal', 'chart', 'graph',
            'map', 'building', 'background', 'texture', 'pattern'
        ]
        
        for keyword in exclude_keywords:
            if keyword in url_lower:
                return False
        
        # Prefer URLs that suggest person/portrait images
        prefer_keywords = [
            'portrait', 'headshot', 'photo', 'person', 'face', 'profile'
        ]
        
        # If it has person-related keywords, prefer it
        for keyword in prefer_keywords:
            if keyword in url_lower:
                return True
        
        # Default to True if no negative indicators
        return True
    
    def verify_image_accessibility(self, image_url):
        """
        Verify that an image URL is accessible and returns an image.
        
        Parameters:
        - image_url: URL to verify
        
        Returns:
        - Boolean indicating if image is accessible
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Make a HEAD request to check if image exists
            response = requests.head(image_url, headers=headers, timeout=5, allow_redirects=True)
            
            # Check if response is successful and content type is image
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                return content_type.startswith('image/')
            
            return False
            
        except Exception:
            return False