"""
LLM Service - Sprint 4 Implementation
Gemini API integration for dynamic text generation
"""

import os
import logging
from typing import List, Optional
import google.generativeai as genai
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered text generation using Gemini API"""
    
    def __init__(self):
        """Initialize the LLM service with Gemini API"""
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("LLM Service initialized with Gemini API")
    
    def generate_text_variations(self, base_text: str, num_variations: int) -> List[str]:
        """
        Generate text variations from base text for BASE_VARY strategy
        
        Args:
            base_text: The original text provided by the user
            num_variations: Number of variations to generate
            
        Returns:
            List of text variations including the original base text
        """
        try:
            logger.info(f"Generating {num_variations} variations for base text: '{base_text}'")
            
            # Create a comprehensive prompt for social media content variations
            prompt = f"""
You are a social media content expert. Given the base text below, generate {num_variations - 1} creative variations that maintain the same core message but use different phrasings, calls-to-action, or emotional tones.

Base text: "{base_text}"

Requirements:
- Keep variations concise (suitable for video overlays)
- Maintain the original intent and context
- Vary the phrasing and calls-to-action
- Consider different emotional tones (excited, urgent, friendly, professional)
- Make them suitable for social media engagement
- Focus on sales, engagement, or encouraging user interaction (comments, DMs, etc.)

Generate exactly {num_variations - 1} variations, one per line, without numbering or bullet points:
"""

            # Generate variations using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("No response generated from Gemini API")
            
            # Parse the response into individual variations
            variations = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            
            # Ensure we have the right number of variations
            if len(variations) > num_variations - 1:
                variations = variations[:num_variations - 1]
            elif len(variations) < num_variations - 1:
                # If we didn't get enough variations, pad with the original text
                while len(variations) < num_variations - 1:
                    variations.append(base_text)
            
            # Include the original base text as the first variation
            result = [base_text] + variations
            
            logger.info(f"Successfully generated {len(result)} text variations")
            for i, variation in enumerate(result):
                logger.info(f"Variation {i+1}: '{variation}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate text variations: {str(e)}")
            # Fallback: return the base text repeated for the number of variations
            fallback_variations = [base_text] * num_variations
            logger.warning(f"Using fallback: returning base text {num_variations} times")
            return fallback_variations
    
    def validate_api_connection(self) -> bool:
        """
        Test the Gemini API connection
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            logger.info("Testing Gemini API connection...")
            
            # Simple test prompt
            test_prompt = "Say 'API connection successful' in exactly those words."
            response = self.model.generate_content(test_prompt)
            
            if response.text and "API connection successful" in response.text:
                logger.info("Gemini API connection test successful")
                return True
            else:
                logger.warning(f"Unexpected API response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {str(e)}")
            return False


# Global LLM service instance
llm_service = None


def get_llm_service() -> LLMService:
    """
    Get or create the global LLM service instance
    
    Returns:
        LLMService instance
    """
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service


def generate_text_variations(base_text: str, num_variations: int) -> List[str]:
    """
    Convenience function to generate text variations
    
    Args:
        base_text: The original text provided by the user
        num_variations: Number of variations to generate
        
    Returns:
        List of text variations including the original base text
    """
    service = get_llm_service()
    return service.generate_text_variations(base_text, num_variations)


def test_llm_connection() -> bool:
    """
    Convenience function to test LLM API connection
    
    Returns:
        True if API is accessible, False otherwise
    """
    try:
        service = get_llm_service()
        return service.validate_api_connection()
    except Exception as e:
        logger.error(f"Failed to test LLM connection: {str(e)}")
        return False
