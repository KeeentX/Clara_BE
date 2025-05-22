import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger("Prompt Service")

class PromptService:
    """
    Service for managing and rendering prompts for LLM interactions.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the Prompt Service.
        
        Parameters:
        - prompts_dir: Directory containing prompt templates
        """
        self.prompts_dir = prompts_dir or getattr(settings, 'PROMPTS_DIR', None) or os.path.join('services', 'prompts')
        logger.info(f"Initializing Prompt Service with directory: {self.prompts_dir}")
        
        # Define prompt mappings
        self.prompt_map = {
            'politician_analysis': 'politician_analysis.txt',
            'politician_summary': 'politician_summary.txt',
            'politician_criticisms': 'politician_criticisms.txt',
            'politician_accomplishments': 'politician_accomplishments.txt',
            'politician_background': 'politician_background.txt',
        }
        
        logger.info("Prompt Service initialized successfully")
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from a file.
        
        Parameters:
        - prompt_name: Name of the prompt file
        
        Returns:
        - The prompt template string
        """
        try:
            full_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'prompts', 
                prompt_name
            )
            logger.info(f"Loading prompt from: {full_path}")
            
            with open(full_path, 'r') as f:
                prompt_template = f.read()
            
            return prompt_template
            
        except Exception as e:
            logger.error(f"Error loading prompt from {prompt_name}: {str(e)}")
            raise ValueError(f"Failed to load prompt: {str(e)}")
    
    def render_prompt(self, prompt_template: str, **kwargs) -> str:
        """
        Render a prompt template with the provided variables using standard Python formatting.
        
        Parameters:
        - prompt_template: The prompt template string
        - **kwargs: Variables to use in the template
        
        Returns:
        - The rendered prompt string
        """
        try:
            rendered_prompt = prompt_template.format(**kwargs)
            logger.debug(f"Rendered prompt length: {len(rendered_prompt)} characters")
            return rendered_prompt
            
        except Exception as e:
            logger.error(f"Error rendering prompt: {str(e)}")
            raise ValueError(f"Failed to render prompt: {str(e)}")
    
    def get_prompt(self, key: str, **kwargs) -> str:
        """
        Get a prompt by its key and render it with the provided variables.
        
        Parameters:
        - key: The key identifying the prompt (e.g., 'politician_analysis')
        - **kwargs: Variables to use in the template
        
        Returns:
        - The rendered prompt string
        """
        if key not in self.prompt_map:
            logger.error(f"Unknown prompt key: {key}")
            raise ValueError(f"Unknown prompt key: {key}")
        
        prompt_file = self.prompt_map[key]
        prompt_template = self.load_prompt(prompt_file)
        return self.render_prompt(prompt_template, **kwargs)
    
    def register_prompt(self, key: str, file_name: str):
        """
        Register a new prompt mapping.
        
        Parameters:
        - key: The prompt key to register
        - file_name: The file name in the prompts directory
        """
        self.prompt_map[key] = file_name
        logger.info(f"Registered prompt {key} -> {file_name}")