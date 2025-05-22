import os
import logging
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from django.conf import settings
from .prompt_service import PromptService

# Set up logger for this module
logger = logging.getLogger("LLM Service")

class LLMService:
    """
    Service for interacting with Gemini Language Model to analyze
    various content based on queries.
    """
    
    def __init__(self, api_key = None, model: str = "gemini-1.5-pro"):
        """
        Initialize the LLM service using Gemini API.
        
        Parameters:
        - model: Gemini model name/version to use
        """
        logger.info(f"Initializing LLM Service with model: {model}")
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY")

        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.model = model
        self.generation_config = GenerationConfig(
            temperature=0,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1000000,
        )
        
        # Initialize the prompt service
        self.prompt_service = PromptService()
        
        logger.info("LLM Service initialized successfully")
        
    def query(self, prompt: str) -> Dict[str, Any]:
        """
        Send a query to the Gemini LLM.
        
        Parameters:
        - prompt: The formatted query string for the LLM
        
        Returns:
        - Dictionary containing the LLM response
        """
        logger.info(f"Sending query to LLM model: {self.model}")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        try:
            # Initialize the model
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self.generation_config
            )
            
            # Generate content
            logger.info("Generating content from Gemini...")
            response = model.generate_content(prompt)
            
            # Process and return the response
            if response.candidates and response.candidates[0].content:
                content = response.candidates[0].content
                text_parts = []
                
                # Extract text from parts
                for part in content.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                
                response_text = "\n".join(text_parts)
                logger.info(f"Content generated successfully: {len(response_text)} characters")
                logger.debug(f"First 100 chars of response: {response_text[:100]}...")
                
                return {
                    "response": response_text,
                    "raw_response": response
                }
            else:
                logger.warning("LLM returned empty response")
                return {
                    "response": "No response was generated",
                    "error": "Empty response from model"
                }
                
        except Exception as e:
            logger.error(f"Error during LLM query: {str(e)}")
            return {
                "response": "Error occurred during LLM query",
                "error": str(e)
            }
    
    def analyze_politician_background(self, name: str, position: str, content_list: List[str]) -> str:
        """
        Analyze the background of a politician using Gemini.
        
        Parameters:
        - name: Politician name
        - position: Politician position
        - content_list: List of text content to analyze
        
        Returns:
        - String containing background information
        """
        logger.info(f"Analyzing background for politician: {name} ({position})")
        
        # Check if we have enough content to analyze
        if not content_list:
            logger.warning("No content provided for background analysis")
            return f"No background information available for {name}."
        
        # Format the content for analysis
        content_text = self._prepare_content_for_analysis(content_list)
        
        # Get the prompt
        prompt = self.prompt_service.get_prompt(
            'politician_background',
            name=name,
            position=position,
            content_text=content_text
        )
        
        # Query the LLM
        result = self.query(prompt)
        if "error" in result:
            logger.error(f"Error in background analysis: {result['error']}")
            return f"Background analysis for {name} could not be completed due to an error: {result['error']}"
        
        return result.get("response", f"No background information available for {name}.")
    
    def analyze_politician_accomplishments(self, name: str, position: str, content_list: List[str]) -> str:
        """
        Analyze the accomplishments of a politician using Gemini.
        
        Parameters:
        - name: Politician name
        - position: Politician position
        - content_list: List of text content to analyze
        
        Returns:
        - String containing accomplishments in markdown bullet format
        """
        logger.info(f"Analyzing accomplishments for politician: {name} ({position})")
        
        if not content_list:
            logger.warning("No content provided for accomplishments analysis")
            return "No accomplishments information available."
        
        content_text = self._prepare_content_for_analysis(content_list)
        
        prompt = self.prompt_service.get_prompt(
            'politician_accomplishments',
            name=name,
            position=position,
            content_text=content_text
        )
        
        result = self.query(prompt)
        if "error" in result:
            logger.error(f"Error in accomplishments analysis: {result['error']}")
            return f"Accomplishments analysis for {name} could not be completed due to an error: {result['error']}"
        
        return result.get("response", "No accomplishments information available.")
    
    def analyze_politician_criticisms(self, name: str, position: str, content_list: List[str]) -> str:
        """
        Analyze the criticisms of a politician using Gemini.
        
        Parameters:
        - name: Politician name
        - position: Politician position
        - content_list: List of text content to analyze
        
        Returns:
        - String containing criticisms in markdown bullet format
        """
        logger.info(f"Analyzing criticisms for politician: {name} ({position})")
        
        if not content_list:
            logger.warning("No content provided for criticisms analysis")
            return "No criticisms information available."
        
        content_text = self._prepare_content_for_analysis(content_list)
        
        prompt = self.prompt_service.get_prompt(
            'politician_criticisms',
            name=name,
            position=position,
            content_text=content_text
        )
        
        result = self.query(prompt)
        if "error" in result:
            logger.error(f"Error in criticisms analysis: {result['error']}")
            return f"Criticisms analysis for {name} could not be completed due to an error: {result['error']}"
        
        return result.get("response", "No criticisms information available.")
    
    def analyze_politician_summary(self, name: str, position: str, background: str, accomplishments: str, criticisms: str, content_list: List[str]) -> str:
        """
        Create a summary judgment for a politician using all prior analyses.
        
        Parameters:
        - name: Politician name
        - position: Politician position
        - background: Background analysis text
        - accomplishments: Accomplishments analysis text
        - criticisms: Criticisms analysis text
        - content_list: List of text content for additional context
        
        Returns:
        - String containing the summary judgment
        """
        logger.info(f"Creating summary judgment for politician: {name} ({position})")
        
        # Use a smaller subset of content for additional context if provided
        content_text = ""
        if content_list:
            # Use just a small sample for additional context since we already have the analyses
            sample_content = content_list[:min(3, len(content_list))]
            content_text = self._prepare_content_for_analysis(sample_content, max_chars=20000)
        
        prompt = self.prompt_service.get_prompt(
            'politician_summary',
            name=name,
            position=position,
            background=background,
            accomplishments=accomplishments,
            criticisms=criticisms,
            content_text=content_text
        )
        
        result = self.query(prompt)
        if "error" in result:
            logger.error(f"Error in summary judgment: {result['error']}")
            return f"Summary judgment for {name} could not be completed due to an error: {result['error']}"
        
        return result.get("response", "No summary judgment available.")
    
    def _prepare_content_for_analysis(self, content_list: List[str], max_chars: int = 1000000) -> str:
        """Helper method to prepare content for analysis with consistent formatting"""
        content_text = "\n\n".join([f"Document {i+1}: {content[:5000]}" for i, content in enumerate(content_list)])
        logger.info(f"Total content length for analysis: {len(content_text)} characters")
        
        # Trim if too long
        if len(content_text) > max_chars:
            logger.warning(f"Content too long ({len(content_text)} chars), trimming to {max_chars} chars")
            content_text = content_text[:max_chars] + "... [content truncated due to length]"
        
        return content_text