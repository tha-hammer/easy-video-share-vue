"""
Test script for Sprint 4 LLM integration
Tests Gemini API connection and text generation functionality
"""

import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from llm_service import test_llm_connection, generate_text_variations
from models import TextStrategy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_gemini_api_connection():
    """Test basic Gemini API connectivity"""
    print("=" * 50)
    print("Testing Gemini API Connection")
    print("=" * 50)
    
    try:
        success = test_llm_connection()
        if success:
            print("✅ Gemini API connection successful!")
            return True
        else:
            print("❌ Gemini API connection failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing Gemini API: {str(e)}")
        return False


def test_text_variations():
    """Test text variation generation"""
    print("\n" + "=" * 50)
    print("Testing Text Variation Generation")
    print("=" * 50)
    
    test_cases = [
        {
            "base_text": "Transform your business with AI",
            "num_variations": 4
        },
        {
            "base_text": "Start your fitness journey today",
            "num_variations": 3
        },
        {
            "base_text": "Learn coding in 30 days",
            "num_variations": 5
        }
    ]
    
    all_success = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Base Text: '{test_case['base_text']}'")
        print(f"Requested Variations: {test_case['num_variations']}")
        
        try:
            variations = generate_text_variations(
                test_case['base_text'], 
                test_case['num_variations']
            )
            
            print(f"Generated {len(variations)} variations:")
            for j, variation in enumerate(variations, 1):
                print(f"  {j}. '{variation}'")
            
            if len(variations) == test_case['num_variations']:
                print("✅ Correct number of variations generated")
            else:
                print(f"⚠️  Expected {test_case['num_variations']}, got {len(variations)}")
                
        except Exception as e:
            print(f"❌ Error generating variations: {str(e)}")
            all_success = False
    
    return all_success


def test_sprint4_integration():
    """Test complete Sprint 4 integration"""
    print("\n" + "=" * 60)
    print("Sprint 4 LLM Integration Test")
    print("=" * 60)
    
    # Test API connection
    api_success = test_gemini_api_connection()
    
    # Test text generation
    text_success = test_text_variations()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    if api_success and text_success:
        print("✅ All Sprint 4 LLM tests passed!")
        print("🚀 Ready for Sprint 4 video processing!")
        return True
    else:
        print("❌ Some tests failed:")
        if not api_success:
            print("  - API connection failed")
        if not text_success:
            print("  - Text generation failed")
        return False


if __name__ == "__main__":
    print("Sprint 4 LLM Service Test")
    print("=" * 60)
    
    # Check environment
    from config import settings
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("Please set GEMINI_API_KEY in your .env file")
        sys.exit(1)
    
    print(f"✅ GEMINI_API_KEY found: {settings.GEMINI_API_KEY[:10]}...")
    
    # Run tests
    success = test_sprint4_integration()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
