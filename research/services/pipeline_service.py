from django.conf import settings
from .search_service import SearchService
from .llm_service import LLMService
from .politician_service import PoliticianPipeline
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

        self.politician_pipeline = PoliticianPipeline(
            search_service=self.search_service,
            llm_service=self.llm_service
        )
    
    def research_politician(self, name, position, max_age = 7):
        """
        Research a politician using the pipeline.
        
        Parameters:
        - name: Politician name (will be normalized)
        - position: Required position for this research
    
        Returns:
        - ResearchResult instance with the analysis
        """
        try:
            logger.info(f"Starting research pipeline for politician: {name} ({position})")
            
            # Step 0: Normalize the politician name
            search_service = SearchService()
            normalized_name, wiki_url = search_service.normalize_politician_name(name, position)
            
            if normalized_name != name:
                logger.info(f"Using normalized name: {normalized_name} (original: {name})")
                name = normalized_name
            
            # Step 1: Get or create politician using normalized name
            politician, created = Politician.objects.get_or_create(name=name)
            if created:
                logger.info(f"Created new politician record: {name}")
            else:
                logger.info(f"Using existing politician record: {name}")

                 # Step 1.2: Check if recent research already exists
                try:
                    existing_research = ResearchResult.objects.filter(
                        politician=politician,
                        position__iexact=position
                    ).order_by('-created_at').first()
                    
                    if existing_research and existing_research.is_recent(days=max_age):
                        logger.info(f"Found recent research ({(timezone.now() - existing_research.created_at).days} days old) - returning existing result")
                        return existing_research
                    else:
                        if existing_research:
                            logger.info(f"Found existing research but it's too old ({(timezone.now() - existing_research.created_at).days} days) - will create new research")
                        else:
                            logger.info(f"No existing research found for position '{position}' - will create new research")
                except Exception as e:
                    logger.warning(f"Error checking for existing research: {str(e)}")

            # Step 1.5: Enrich politician with basic info if needed
            if created or not politician.party or not politician.image_url:
                logger.info(f"Enriching politician with basic information")
                politician = self.politician_pipeline.enrich_politician(politician, position)
            
            # Step 2: Generate search queries
            search_queries = self.search_service.generate_search_queries(name, position)
            logger.info(f"Generated {len(search_queries)} search queries")
            
            # Step 3: Search for content
            all_search_results = []
            for query in search_queries:
                results = self.search_service.search(query, num_results=2)
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
                
                if not content or len(content.strip()) < 500:
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
