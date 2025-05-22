from django.conf import settings
from .search_service import SearchService
from .llm_service import LLMService  # This now uses our updated Gemini implementation
from ..models import Politician, ResearchResult
import logging
import sys
import os
from typing import Dict, Any, List, Union
from django.utils import timezone
from .prompt_service import PromptService

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Research Pipeline")

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
    
    def research_politician(self, name, position):
        """
        Research a politician using the pipeline.
        
        Parameters:
        - name: Politician name
        - position: Required position for this research
        
        Returns:
        - ResearchResult instance with the analysis
        """
        try:
            logger.info(f"Starting research pipeline for politician: {name} ({position})")
            
            # Step 1: Get or create politician
            politician, created = Politician.objects.get_or_create(name=name)
            if created:
                logger.info(f"Created new politician record: {name}")
            else:
                logger.info(f"Using existing politician record: {name}")
            
            # Step 2: Generate search queries
            search_queries = self.search_service.generate_search_queries(name, position)
            logger.info(f"Generated {len(search_queries)} search queries")
            
            # Step 3: Search for content
            all_search_results = []
            for query in search_queries:
                results = self.search_service.search(query, num_results=3)
                if results:
                    for result in results:
                        result['query'] = query  # Track which query led to this result
                    all_search_results.extend(results)
            
            logger.info(f"Found {len(all_search_results)} search results")
            
            # Step 4: Extract content from search results
            content_list = []
            extracted_content_texts = []
            
            for result in all_search_results: 
                content = self.search_service.fetch_content(result['url'])
                
                if not content or len(content.strip()) < 100:
                    logger.info(f"Skipping URL with insufficient content: {result['url']}")
                    continue
                
                content_dict = {
                    'url': result['url'],
                    'title': result['title'],
                    'content': content,
                    'query': result['query'], 
                }
                content_list.append(content_dict)
                extracted_content_texts.append(content)
            
            # Step 5: Analyze with LLM (now broken into separate calls)
            if self.llm_service and extracted_content_texts:
                try:
                    logger.info(f"Starting multi-part analysis for {name} with LLM using {len(extracted_content_texts)} content sources")
                    
                    # Background analysis
                    logger.info("Step 5.1: Analyzing background")
                    background = self.llm_service.analyze_politician_background(
                        name=name, 
                        position=position, 
                        content_list=extracted_content_texts
                    )
                    
                    # Accomplishments analysis
                    logger.info("Step 5.2: Analyzing accomplishments")
                    accomplishments = self.llm_service.analyze_politician_accomplishments(
                        name=name, 
                        position=position, 
                        content_list=extracted_content_texts
                    )
                    
                    # Criticisms analysis
                    logger.info("Step 5.3: Analyzing criticisms")
                    criticisms = self.llm_service.analyze_politician_criticisms(
                        name=name, 
                        position=position, 
                        content_list=extracted_content_texts
                    )
                    
                    # Summary judgment (using all previous analyses)
                    logger.info("Step 5.4: Creating summary judgment")
                    summary = self.llm_service.analyze_politician_summary(
                        name=name, 
                        position=position,
                        background=background,
                        accomplishments=accomplishments,
                        criticisms=criticisms,
                        content_list=extracted_content_texts
                    )
                    
                    # Step 6: Create and save research result
                    research_result = ResearchResult.objects.create(
                        politician=politician,
                        position=position,
                        background=background,
                        accomplishments=accomplishments,
                        criticisms=criticisms,
                        summary=summary,
                        sources=[
                            {
                                'url': content['url'],
                                'title': content['title'],
                                'query': content['query'],
                                'content': content['content'],
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
                logger.warning("No LLM service available or no content found")
                return {
                    "politician": politician,
                    "error": "No content found or LLM service unavailable",
                    "content_list": content_list
                }
                
        except Exception as e:
            logger.error(f"Error in research pipeline: {str(e)}")
            return {
                "name": name,
                "position": position,
                "error": str(e)
            }
    