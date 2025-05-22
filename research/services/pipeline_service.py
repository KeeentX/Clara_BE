from django.conf import settings
from .search_service import SearchService
from .llm_service import LLMService  # This now uses our updated Gemini implementation
from ..models import Politician, ResearchResult
import logging
import sys
import os

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Pipeline Service")

class ResearchPipeline:
    """
    Pipeline for researching politicians by orchestrating
    search and LLM analysis.
    """
    
    def __init__(self, search_api_key=None):
        """
        Initialize the research pipeline.
        
        Parameters:
        - search_api_key: Optional API key for search service
        """
        # Use provided key or fall back to settings for search
        self.search_api_key = search_api_key or getattr(settings, 'SEARCH_API_KEY', None)
        
        # Initialize services
        self.search_service = SearchService(api_key=self.search_api_key)
        
        # Initialize the LLM service - now uses environment variable
        try:
            self.llm_service = LLMService()  # No API key needed as parameter anymore
            logger.info("LLM Service initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize LLM Service: {str(e)}")
            # Consider whether to raise the exception or continue with limited functionality
            self.llm_service = None
    
    def research_politician(self, name, position=None):
        """
        Research a politician using the pipeline.
        
        Parameters:
        - name: Politician name
        - position: Optional politician position
        
        Returns:
        - ResearchResult instance with the analysis
        """
        # Step 1: Find or create the politician
        politician, created = Politician.objects.get_or_create(
            name=name,
            defaults={'position': position or ''}
        )
        
        # Step 2: Generate search queries
        queries = self._generate_search_queries(name, position)
        
        # Step 3: Perform searches
        all_search_results = []
        seen_urls = set()

        for query in queries:
            results = self.search_service.search(query, num_results=10)
            for result in results:
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    all_search_results.append(result)
                else:
                    logger.info(f"Duplicate URL found: {result['url']}, skipping.")
        
        # Step 4: Fetch content from top results
        content_list = []
        extracted_content_texts = []  # Store just the text content for LLM analysis
        
        for result in all_search_results: 
            content = self.search_service.fetch_content(result['url'])

            if not content or len(content.strip()) < 100:
                logger.info(f"Skipping URL with insufficient content: {result['url']}")
                continue

            content_dict = {
                'url': result['url'],
                'title': result['title'],
                'content': content,
                'query' : result['query'], 
            }
            content_list.append(content_dict)
            extracted_content_texts.append(content)
        
        # Step 5: Analyze with LLM
        if self.llm_service and extracted_content_texts:
            try:
                logger.info(f"Analyzing {name} with LLM using {len(extracted_content_texts)} content sources")
                analysis = self.llm_service.analyze_politician(
                    name=name, 
                    position=position or "politician", 
                    content_list=extracted_content_texts
                )
                
                # Step 6: Create and save research result
                research_result = ResearchResult.objects.create(
                    politician=politician,
                    background=analysis.get('background', ''),
                    accomplishments=analysis.get('accomplishments', ''),
                    criticisms=analysis.get('criticisms', ''),
                    summary=analysis.get('summary', ''),
                    sources=[
                        {
                            'url': content['url'],
                            'title': content['title'],
                            'query': content['query'],
                        } 
                        for content in content_list 
                    ]
                )
                
                logger.info(f"Completed research for {name}")
                return research_result
            except Exception as e:
                logger.error(f"Error during LLM analysis: {str(e)}")
                # Return partial results if LLM analysis fails
                return {
                    "politician": politician,
                    "error": str(e),
                    "content_list": content_list
                }
        else:
            logger.warning(f"Skipping LLM analysis: LLM service not available or no content extracted")
            # Return just the content list if LLM analysis is skipped
            return content_list
    
    def _generate_search_queries(self, name, position=None):
        """
        Generate search queries for a politician.
        
        Parameters:
        - name: Politician name
        - position: Optional politician position
        
        Returns:
        - List of search query strings
        """
        queries = [
            f"{name} personal biography and early life",
            f"{name} political background",
            f"{name} career and credentials",
            f"{name} accomplishments and achievements",
            f"{name} policy positions on key issues",
            f"{name} issues and corruption",
            f"{name} criticism and controversy",
            f"{name} ethics investigations and watchdog reports",
            f"{name} endorsements and affiliations", 
        ]
        
        if position:
            queries.append(f"{name} {position}")
            queries.append(f"{name} {position} background")
            queries.append(f"{name} {position} achievements")
            queries.append(f"{name} {position} criticism")
        
        return queries