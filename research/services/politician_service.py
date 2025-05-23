import logging
from typing import Dict, Any, Optional, List
from ..models import Politician
from .search_service import SearchService
from .llm_service import LLMService

logger = logging.getLogger("PoliticianPipeline")

class PoliticianPipeline:
    """
    Pipeline for extracting and managing basic politician information:
    - party affiliation
    - short biography
    - image URL
    - policy positions/stances
    """
    
    def __init__(self, search_service=None, llm_service=None):
        """
        Initialize the politician pipeline service.
        
        Parameters:
        - search_service: Optional SearchService instance
        - llm_service: Optional LLMService instance
        """
        self.search_service = search_service or SearchService()
        self.llm_service = llm_service or LLMService()
        logger.info("PoliticianPipeline initialized")
    
    def enrich_politician(self, politician: Politician, position: str) -> Politician:
        """
        Enrich a politician model with additional information.
        
        Parameters:
        - politician: Politician model instance to enrich
        - position: The politician's position for context
        
        Returns:
        - Updated Politician instance
        """
        logger.info(f"Enriching politician data for: {politician.name} ({position})")
        
        # Get party affiliation if not already set
        if not politician.party:
            politician.party = self.get_party_affiliation(politician.name, position)
            
        # Get image URL if not already set
        if not politician.image_url:
            politician.image_url = self.get_image_url(politician.name, position)
            
        # Get short bio if not already set
        if not politician.bio:
            politician.bio = self.get_short_bio(politician.name, position)
            
        # Get policy stances if not already set
        if not politician.issues:
            politician.issues = self.get_policy_stances(politician.name, position)
            
        # Save the updated politician
        politician.save()
        logger.info(f"Politician {politician.name} enriched with additional data")
        
        return politician
        
    def get_party_affiliation(self, name: str, position: str) -> str:
        """Get the party affiliation of a politician"""
        logger.info(f"Getting party affiliation for {name}")
        
        # Generate search queries for party information
        party_queries = [
            f"{name} political party affliation",
        ]
        
        # Search for party information
        party_content = self._search_and_extract_content(party_queries, 3)
        
        if party_content:
            # Extract party from content using LLM
            party = self.llm_service.extract_party_affiliation(name, position, party_content)
            logger.info(f"Extracted party for {name}: {party}")
            return party
        
        logger.warning(f"Could not determine party for {name}")
        return ""
    
    def get_image_url(self, name: str, position: str) -> str:
        """Get an image URL for the politician"""
        logger.info(f"Getting image URL for {name}")
        
        # Search for images
        image_url = self.search_service.search_politician_image(name, position)
        
        if image_url:
            logger.info(f"Found image for {name}: {image_url}")
            return image_url
        
        logger.warning(f"Could not find image for {name}")
        return ""
    
    def get_short_bio(self, name: str, position: str) -> str:
        """Get a short biography for the politician"""
        logger.info(f"Getting short bio for {name}")
        
        # Generate search queries for biographical information
        bio_queries = [
            f"{name} biography",
            f"{name} {position} profile",
            f"{name} career summary"
        ]
        
        # Search for biographical information
        bio_content = self._search_and_extract_content(bio_queries, 1)
        
        if bio_content:
            # Extract short bio from content using LLM
            bio = self.llm_service.extract_short_bio(name, position, bio_content)
            logger.info(f"Extracted short bio for {name} ({len(bio)} chars)")
            return bio
        
        logger.warning(f"Could not generate bio for {name}")
        return ""
    
    def get_policy_stances(self, name: str, position: str) -> Dict[str, Dict[str, str]]:
        """Get key policy positions for the politician"""
        logger.info(f"Getting policy stances for {name}")
        
        # Generate search queries for policy positions
        policy_queries = [
            f"{name} policy positions",
            f"{name} stance on issues",
            f"{name} {position} policies"
        ]
        
        # Search for policy information
        policy_content = self._search_and_extract_content(policy_queries, 5)
        
        if policy_content:
            # Extract policy stances from content using LLM
            stances = self.llm_service.extract_policy_stances(name, position, policy_content)
            logger.info(f"Extracted {len(stances)} policy stances for {name}")
            return stances
        
        logger.warning(f"Could not determine policy stances for {name}")
        return {}
    
    def _search_and_extract_content(self, queries: List[str], results_per_query: int = 3) -> List[str]:
        """Helper method to search and extract content for multiple queries"""
        all_content = []
        
        for query in queries:
            search_results = self.search_service.search(query, num_results=results_per_query)
            
            if search_results:
                for result in search_results:
                    content = self.search_service.fetch_content(result['url'])
                    if content and len(content.strip()) > 100:
                        all_content.append(content)
        
        return all_content