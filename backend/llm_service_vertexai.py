"""
LLM Service - Sprint 4 Implementation (Vertex AI)
Vertex AI Gemini integration for dynamic text generation
"""

import os
import logging
from typing import List, Optional
from google import genai
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered text generation using Vertex AI Gemini"""
    
    def __init__(self):
        """Initialize the LLM service with Vertex AI"""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_LOCATION
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        
        # Configure Vertex AI client
        try:
            self.client = genai.Client(
                project=self.project_id,
                location=self.location,
                vertexai=True
            )
            logger.info(f"LLM Service initialized with Vertex AI - Project: {self.project_id}, Location: {self.location}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
            raise
    
    def generate_text_variations(self, base_text: str, num_variations: int, context: Optional[str] = None) -> List[str]:
        """
        Generate text variations from base text for BASE_VARY strategy
        
        Args:
            base_text: The original text provided by the user
            num_variations: Number of variations to generate
            context: Optional context for LLM prompt (e.g., 'sales', 'engagement', 'educational')
            
        Returns:
            List of text variations including the original base text
        """
        try:
            logger.info(f"Generating {num_variations} variations for base text: '{base_text}'")
            if context:
                logger.info(f"Using context: '{context}'")
            
            # Create a comprehensive prompt for social media content variations with context
            prompt = f"""You are an expert social media content creator specializing in short-form video content. Given the base text below, generate {num_variations - 1} creative and distinct variations that maintain the same core message but use different phrasings, calls-to-action, or emotional tones.

Base text: "{base_text}"
"""
            
            # Add context-specific instructions if context is provided
            if context:
                context_lower = context.lower()
                if "sales" in context_lower or "sell" in context_lower:
                    prompt += f"""
Context: {context}
Focus on sales-oriented variations with strong calls-to-action, urgency, value propositions, and conversion-focused language. Include phrases that encourage immediate action.
"""
                elif "engagement" in context_lower or "social" in context_lower:
                    prompt += f"""
Context: {context}
Focus on engagement-oriented variations that encourage interaction, questions, comments, sharing, and community building. Use conversational and interactive language.
"""
                elif "education" in context_lower or "learn" in context_lower:
                    prompt += f"""
Context: {context}
Focus on educational variations that highlight learning opportunities, knowledge sharing, tips, insights, and informative content. Use authoritative yet accessible language.
"""
                else:
                    prompt += f"""
Context: {context}
Tailor the variations to match this specific context while maintaining the core message. Adjust tone, vocabulary, and calls-to-action accordingly.
"""
            
            prompt += f"""
Requirements:
- Keep variations concise (suitable for video overlays, max 10-15 words)
- Maintain the original intent and context
- Vary the phrasing and calls-to-action significantly
- Consider different emotional tones (excited, urgent, friendly, professional)
- Make them suitable for social media engagement
- Focus on compelling, action-oriented language
- Each variation should feel distinct and purposeful

Generate exactly {num_variations - 1} variations, one per line, without numbering or bullet points:
"""

            # Generate variations using Vertex AI
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if not response.text:
                raise Exception("No response generated from Vertex AI")
            
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
        Test the Vertex AI connection
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            logger.info("Testing Vertex AI connection...")
            
            # Simple test prompt
            test_prompt = "Say exactly: 'API connection successful' in exactly those words."
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=test_prompt
            )
            
            if response.text and "API connection successful" in response.text:
                logger.info("Vertex AI connection test successful")
                return True
            else:
                logger.warning(f"Unexpected API response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Vertex AI connection test failed: {str(e)}")
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


def generate_text_variations(base_text: str, num_variations: int, context: Optional[str] = None) -> List[str]:
    """
    Convenience function to generate text variations
    
    Args:
        base_text: The original text provided by the user
        num_variations: Number of variations to generate
        context: Optional context for LLM prompt
        
    Returns:
        List of text variations including the original base text
    """
    service = get_llm_service()
    return service.generate_text_variations(base_text, num_variations, context)


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
