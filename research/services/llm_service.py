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
        
    # The query method remains unchanged
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
        
    # Modified to use the PromptService
    def analyze_politician(self, name: str, position: str, content_list: List[str]) -> Dict[str, Any]:
        """
        Analyze information about a politician using Gemini.
        
        Parameters:
        - name: Politician name
        - position: Politician position
        - content_list: List of text content to analyze
        
        Returns:
        - Dictionary containing background, accomplishments, criticisms, and summary judgment
        """
        logger.info(f"Analyzing politician: {name} ({position})")
        logger.info(f"Number of content sources: {len(content_list)}")
        
        # Check if we have enough content to analyze
        if not content_list:
            logger.warning("No content provided for analysis")
            return {
                "background": f"No information available for {name}.",
                "accomplishments": "No information available.",
                "criticisms": "No information available.",
                "summary": "Insufficient information to form a judgment.",
                "error": "No content provided for analysis",
                "sources": []
            }
        
        # Format the content for analysis
        content_text = "\n\n".join([f"Document {i+1}: {content[:5000]}" for i, content in enumerate(content_list)])
        logger.info(f"Total content length for analysis: {len(content_text)} characters")
        
        # Trim if too long
        if len(content_text) > 100000:
            logger.warning(f"Content too long ({len(content_text)} chars), trimming to 100,000 chars")
            content_text = content_text[:100000] + "... [content truncated due to length]"
        
        # Get the prompt from the PromptService
        prompt = self.prompt_service.get_prompt(
            'politician_analysis',
            name=name,
            position=position,
            content_text=content_text
        )
        
        # Use the query method to perform the analysis
        logger.info("Sending politician analysis query to LLM")
        result = self.query(prompt)
        
        try:
            # Parse the JSON from the response
            import json
            response_text = result.get("response", "{}")
            logger.info("Parsing JSON response from LLM")
            
            # Extract JSON if it's embedded in markdown or other text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
                logger.debug("Extracted JSON from markdown code block with json syntax")
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
                logger.debug("Extracted JSON from markdown code block")
            else:
                json_text = response_text
                logger.debug("Using raw response as JSON")
                
            parsed_response = json.loads(json_text)
            logger.info("Successfully parsed JSON response")
            
            analysis_result = {
                "background": parsed_response.get("background", "No background information available."),
                "accomplishments": parsed_response.get("accomplishments", "No accomplishments listed."),
                "criticisms": parsed_response.get("criticisms", "No criticisms found."),
                "summary": parsed_response.get("summary", "No summary judgment available."),
                "sources": [{"title": f"Document {i+1}", "content": content[:100] + "..."} 
                           for i, content in enumerate(content_list)]
            }
            
            logger.info(f"Analysis complete for {name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            logger.debug(f"Failed response text: {result.get('response')[:500]}...")
            
            # Fallback in case of parsing errors
            return {
                "background": f"Background for {name}, who serves as {position}.",
                "accomplishments": "Information could not be parsed correctly.",
                "criticisms": "Information could not be parsed correctly.",
                "summary": "Could not generate a summary judgment due to parsing errors.",
                "error": str(e),
                "raw_response": result.get("response")
            }