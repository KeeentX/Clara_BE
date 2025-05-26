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
            f"{name} criticism",
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

    def search_politician_image(self, name, position=""):
        """
        Search for an image of a politician - using normalized name and Wikipedia.
        
        Parameters:
        - name: Politician name (will be normalized first)
        - position: Politician position (optional)
        
        Returns:
        - URL of an image if found, empty string otherwise
        """
        logger.info(f"Searching for image of {name}")
        
        try:
            # First normalize the name to get the standard version
            normalized_name, wiki_url = self.normalize_politician_name(name, position)
            
            # If we found a normalized name, use that for the image search
            if normalized_name != name:
                logger.info(f"Using normalized name for image search: {normalized_name}")
                name = normalized_name
            
            # Try Wikipedia image lookup with the normalized name
            wiki_image = self._get_wikipedia_image(name)
            if wiki_image:
                logger.info(f"Found Wikipedia image for {name}")
                return wiki_image
                
            # If we have a Wikipedia URL but no image was found through the API,
            # we could try to extract the image from the page itself
            if wiki_url:
                logger.info(f"Trying to extract image from Wikipedia page")
                image_url = self._extract_image_from_page(wiki_url, name)
                if image_url:
                    return image_url
            
            # No image found from Wikipedia sources
            logger.warning(f"No Wikipedia image found for {name}")
            return ""
            
        except Exception as e:
            logger.error(f"Error in image search: {str(e)}")
            return ""

    def _get_wikipedia_image(self, name):
        """Get an image from Wikipedia using their API"""
        try:
            # Format the name for Wikipedia
            wiki_name = name.replace(' ', '_')
            
            # Try to get Wikipedia summary which often includes an image
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; PoliticianResearchBot/1.0)'
            }
            
            response = requests.get(wiki_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if there's an image in the response
                if 'thumbnail' in data and 'source' in data['thumbnail']:
                    # Try to get the higher resolution original image
                    if 'originalimage' in data and 'source' in data['originalimage']:
                        return data['originalimage']['source']
                    return data['thumbnail']['source']
                    
            return ""
            
        except Exception as e:
            logger.info(f"Wikipedia image error: {str(e)[:50]}...")
            return ""

    def _is_valid_image_url(self, url):
        """Simple check if a URL appears to be an image"""
        if not url:
            return False
            
        # Check if URL has an image file extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)

    def _extract_image_from_page(self, url, name):
        """Extract a likely politician image from a webpage"""
        try:
            content = self._scrape_with_requests(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for images that might be the politician
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src:
                    continue
                    
                # Convert relative URL to absolute if needed
                if src.startswith('/'):
                    parsed_url = urlparse(url)
                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                    
                # Skip tiny images (likely icons)
                width = img.get('width')
                height = img.get('height')
                if width and height and (int(width) < 100 or int(height) < 100):
                    continue
                    
                # Look for images that might contain the politician's name or relevant terms
                alt_text = img.get('alt', '').lower()
                name_parts = name.lower().split()
                
                # Check if all parts of the name appear in the alt text or src
                if all(part in alt_text or part in src.lower() for part in name_parts):
                    return src
                    
                # Check for common politician image indicators
                relevant_terms = ['portrait', 'headshot', 'photo', 'profile', 'politician']
                if any(term in alt_text or term in src.lower() for term in relevant_terms):
                    return src
                    
            return ""
            
        except Exception as e:
            logger.info(f"Error extracting image: {str(e)[:50]}...")
            return ""
    
    def normalize_politician_name(self, name, position=""):
        """
        Attempts to find the standardized/official name of a politician using Wikipedia and LLM.
        Gathers context about the politician first to improve accuracy.
        
        Parameters:
        - name: The input name (could be nickname, misspelling, etc.)
        - position: Position to help narrow down the search
        
        Returns:
        - Tuple of (normalized_name, wikipedia_url) or (original_name, None) if not found
        """
        logger.info(f"Normalizing politician name: {name}")
        
        try:
            # Step 1: Gather context about the politician
            context = self._gather_politician_context(name, position)
            
            # Step 2: Try LLM-based normalization with context
            if context:
                normalized_name = self._normalize_name_with_llm(name, position, context)
                if normalized_name and normalized_name != name:
                    logger.info(f"LLM normalized '{name}' to '{normalized_name}' with context")
                    
                    # Try to find Wikipedia page for the normalized name
                    wiki_name = normalized_name.replace(' ', '_')
                    wiki_url = f"https://en.wikipedia.org/wiki/{wiki_name}"
                    
                    # Verify this page exists
                    verify_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
                    headers = {'User-Agent': 'Mozilla/5.0 (compatible; PoliticianResearchBot/1.0)'}
                    
                    try:
                        response = requests.get(verify_url, headers=headers, timeout=5)
                        if response.status_code == 200:
                            # We found a Wikipedia page for the LLM-normalized name
                            return normalized_name, wiki_url
                    except Exception:
                        pass  # Continue with other approaches
        
            # Step 3: Try direct Wikipedia lookup with original name
            wiki_name = name.replace(' ', '_')
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; PoliticianResearchBot/1.0)'}
            
            response = requests.get(wiki_url, headers=headers, timeout=5)
            
            # If direct lookup works, verify it's the right person
            if response.status_code == 200:
                data = response.json()
                if 'title' in data and 'extract' in data:
                    wiki_title = data['title']
                    wiki_extract = data['extract']
                    page_url = f"https://en.wikipedia.org/wiki/{wiki_name}"
                    
                    # Verify this is the right person by checking the content
                    if self._verify_politician_match(wiki_extract, name, position):
                        logger.info(f"Found Wikipedia page: normalized '{name}' to '{wiki_title}'")
                        return wiki_title, page_url
                    else:
                        logger.info(f"Found Wikipedia page for '{wiki_title}' but doesn't match our politician")
        
            # Step 4: Try search with position
            search_query = f"{name} {position} politician wikipedia"
            search_results = self.search(search_query, num_results=5)
            
            for result in search_results:
                url = result.get('url', '')
                if 'wikipedia.org/wiki/' in url:
                    # Extract the title from the Wikipedia URL
                    path_parts = urlparse(url).path.split('/')
                    if len(path_parts) > 2:
                        wiki_name = path_parts[-1]
                        wiki_title = wiki_name.replace('_', ' ')
                        
                        # Get content to verify
                        verify_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
                        try:
                            verify_response = requests.get(verify_url, headers=headers, timeout=5)
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json()
                                if 'title' in verify_data and 'extract' in verify_data:
                                    wiki_title = verify_data['title']
                                    
                                    # Verify this is the right person
                                    if self._verify_politician_match(verify_data.get('extract', ''), name, position):
                                        logger.info(f"Found Wikipedia page via search: normalized '{name}' to '{wiki_title}'")
                                        return wiki_title, url
                        except Exception as e:
                            logger.info(f"Error verifying Wikipedia page: {str(e)[:50]}...")
                            continue
            
            # Step 5: If we have an LLM-normalized name but no Wikipedia page, return just the name
            if 'normalized_name' in locals() and normalized_name and normalized_name != name:
                return normalized_name, None
                
            # No normalization found
            logger.info(f"No normalization found for '{name}'")
            return name, None
        
        except Exception as e:
            logger.error(f"Error while normalizing politician name: {str(e)}")
            return name, None

    def _gather_politician_context(self, name, position=""):
        """
        Gather context information about a politician to help with name normalization.
        Prioritizes Wikipedia and reliable sources.
        
        Parameters:
        - name: Original politician name
        - position: Position if known
        
        Returns:
        - String with context information
        """
        try:
            context_pieces = []
            
            # Try Wikipedia first (direct search)
            wiki_name = name.replace(' ', '_')
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; PoliticianResearchBot/1.0)'}
            
            try:
                response = requests.get(wiki_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'extract' in data:
                        # We found Wikipedia context directly
                        context_pieces.append(f"Wikipedia information: {data['extract']}")
            except Exception:
                pass
                
            # If no Wikipedia context, try general search
            if not context_pieces:
                # Create search queries focused on biographical information
                search_queries = [
                    f"{name} {position} politician wikipedia",
                    f"{name} {position} biography",
                    f"{name} politician profile"
                ]
                
                for query in search_queries[:2]:  # Limit to first 2 queries for efficiency
                    results = self.search(query, num_results=3)
                    
                    for result in results:
                        # Prioritize Wikipedia and official sources
                        url = result.get('url', '')
                        if 'wikipedia.org' in url or '.gov.' in url or 'official' in url.lower():
                            try:
                                # Get a small snippet of content
                                content = self._scrape_with_requests(url)
                                if content:
                                    # Limit content length for LLM processing
                                    snippet = content[:1000] if len(content) > 1000 else content
                                    source_name = "Wikipedia" if "wikipedia.org" in url else "Official source" if ".gov" in url else "Source"
                                    context_pieces.append(f"{source_name}: {snippet}")
                                    break  # Just get one good source per query
                            except Exception:
                                continue
                    
                    if len(context_pieces) >= 2:  # If we have enough context, stop searching
                        break
            
            # Return the combined context
            return "\n\n".join(context_pieces)
                
        except Exception as e:
            logger.error(f"Error gathering context: {str(e)}")
            return ""

    def _normalize_name_with_llm(self, name, position="", context=""):
        """
        Use the LLM service to normalize a politician name with context.
        This is especially useful for nicknames and alternative names.
        
        Parameters:
        - name: Original name
        - position: Position if known
        - context: Biographical context about the politician
        
        Returns:
        - Normalized name or original if normalization fails
        """
        try:
            from research.services.llm_service import LLMService
            
            llm_service = LLMService()
            
            # Create a prompt for the LLM to normalize the name
            position_context = f" who serves/served as {position}" if position else ""
            
            prompt = f"""
            Task: Identify the standard/official name of the Filipino politician.
            
            Input: "{name}"{position_context}
            
            Context about the politician:
            {context}
            
            Output requirements:
            - Return ONLY the full standard name with no explanations or additional text
            - If this is a nickname, find the real name
            - If this is a common name of a political family, identify the specific politician based on the position provided
            - If uncertain, return the original name unchanged
            - Do not include titles like "Senator", "Governor", etc. in the name unless they are part of the proper name
            - Filipino politicians often have nicknames that are completely different from their legal names
            
            Output:
            """
            
            result = llm_service.query(prompt)
            
            if "error" not in result and "response" in result:
                normalized_name = result["response"].strip()
                # Check if the LLM actually changed the name
                if normalized_name.lower() != name.lower():
                    return normalized_name
                    
            return name
            
        except Exception as e:
            logger.error(f"LLM normalization error: {str(e)}")
            return name
            
    def _verify_politician_match(self, text, name, position):
        """
        Verify if a Wikipedia article is about the politician we're looking for.
        
        Parameters:
        - text: Article extract/content
        - name: Original politician name
        - position: Politician position
        
        Returns:
        - Boolean indicating if it's likely the same person
        """
        text_lower = text.lower()
        name_lower = name.lower()
        
        # If position is mentioned and specific enough, it's a strong indicator
        if position and len(position) > 3 and position.lower() in text_lower:
            # Split the name and check if at least the last name is present
            name_parts = name_lower.split()
            if len(name_parts) > 0 and name_parts[-1] in text_lower:
                return True
                
        # Check for exact name matches
        if name_lower in text_lower:
            return True
            
        # Check for variations of the name
        name_parts = name_lower.split()
        
        # For Filipino politicians with nicknames, the last name is usually reliable
        surname = name_parts[-1] if len(name_parts) > 0 else ""
        
        # If the surname appears and it's not extremely common
        if surname and surname in text_lower:
            common_surnames = ['garcia', 'santos', 'reyes', 'cruz', 'dela cruz', 'gonzales', 'bautista', 'lopez']
            if surname not in common_surnames:
                return True
            elif len(text_lower.split()) > 100:  # If article is substantial with common surname
                # Check if first name initial + last name appears
                if len(name_parts) > 1 and f"{name_parts[0][0]}. {surname}" in text_lower:
                    return True
                # Check if text mentions politician role
                political_terms = ['politician', 'mayor', 'governor', 'senator', 'congressman', 
                                'representative', 'official', 'elected', 'public servant']
                if any(term in text_lower for term in political_terms):
                    return True
                return False  # Common surname without additional evidence
            return False
                    
        # Not enough evidence
        return False