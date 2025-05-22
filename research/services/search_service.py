from googlesearch import search
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse
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