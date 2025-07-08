#!/usr/bin/env python3
"""
Standalone LLM Testing Script - Sprint 4.1

This script allows for rapid, interactive LLM prompt iteration and edge case testing
without running a full video processing pipeline.

Use this for:
1. Testing different base_text and context combinations
2. Iterating on prompt engineering
3. Verifying LLM output quality and variety
4. Edge case testing (empty context, special characters, etc.)
"""

import sys
import os
import json
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, environment variables may not be loaded")

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from llm_service_vertexai import generate_text_variations, test_llm_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """Test LLM API connection"""
    print("🔗 Testing LLM API Connection...")
    
    try:
        connected = test_llm_connection()
        if connected:
            print("✅ LLM API connection successful!")
            return True
        else:
            print("❌ LLM API connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False


def run_text_generation_test(base_text: str, num_variations: int, context: Optional[str] = None):
    """Run a single text generation test with the given parameters"""
    print(f"\n📝 Generating {num_variations} variations")
    print(f"Base text: '{base_text}'")
    print(f"Context: {context if context else 'None'}")
    print("-" * 50)
    
    try:
        variations = generate_text_variations(
            base_text=base_text,
            num_variations=num_variations,
            context=context
        )
        
        print(f"✅ Generated {len(variations)} variations:")
        for i, variation in enumerate(variations, 1):
            print(f"  {i:2d}. {variation}")
        
        print(f"\n📊 Quality metrics:")
        print(f"   - Total variations: {len(variations)}")
        print(f"   - Average length: {sum(len(v) for v in variations) / len(variations):.1f} chars")
        print(f"   - Unique variations: {len(set(variations))}")
        
        return variations
        
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        return None


def predefined_test_cases():
    """Run predefined test cases covering various scenarios"""
    print("\n🧪 Running Predefined Test Cases")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Sales - Product Launch",
            "base_text": "Transform your business with our new AI platform",
            "context": "sales pitch, urgent call to action, limited time offer",
            "num_variations": 4
        },
        {
            "name": "Educational - Learning Content",
            "base_text": "Master Python programming in 30 days",
            "context": "educational content, beginner-friendly, step-by-step learning",
            "num_variations": 3
        },
        {
            "name": "Engagement - Community Building",
            "base_text": "Join our growing community of creators",
            "context": "engagement, social interaction, community building",
            "num_variations": 5
        },
        {
            "name": "No Context - Generic Test",
            "base_text": "Discover something amazing today",
            "context": None,
            "num_variations": 3
        },
        {
            "name": "Short Text - Minimal Input",
            "base_text": "New update!",
            "context": "excitement, announcement",
            "num_variations": 4
        },
        {
            "name": "Long Text - Complex Message",
            "base_text": "Experience the future of video creation with our revolutionary AI-powered platform that transforms your content",
            "context": "technology showcase, innovation, professional",
            "num_variations": 3
        }
    ]
    
    all_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test Case {i}: {test_case['name']}")
        result = run_text_generation_test(
            base_text=test_case['base_text'],
            num_variations=test_case['num_variations'],
            context=test_case['context']
        )
        all_results.append({
            "test_case": test_case,
            "result": result,
            "success": result is not None
        })
    
    # Summary
    successful_tests = sum(1 for r in all_results if r['success'])
    print(f"\n📊 Test Summary:")
    print(f"   - Total tests: {len(test_cases)}")
    print(f"   - Successful: {successful_tests}")
    print(f"   - Failed: {len(test_cases) - successful_tests}")
    
    return all_results


def interactive_testing():
    """Interactive mode for custom testing"""
    print("\n🎮 Interactive LLM Testing Mode")
    print("=" * 40)
    print("Enter your own base text and context to test the LLM!")
    print("Type 'quit' to exit.")
    
    while True:
        print("\n" + "-" * 40)
        
        # Get base text
        base_text = input("📝 Enter base text: ").strip()
        if base_text.lower() == 'quit':
            break
        
        if not base_text:
            print("❌ Base text cannot be empty!")
            continue
        
        # Get context (optional)
        context = input("🎯 Enter context (optional): ").strip()
        if not context:
            context = None
        
        # Get number of variations
        try:
            num_variations = int(input("🔢 Number of variations (default 3): ").strip() or "3")
            if num_variations < 1 or num_variations > 10:
                print("❌ Number of variations must be between 1 and 10!")
                continue
        except ValueError:
            print("❌ Invalid number! Using default (3)")
            num_variations = 3
        
        # Run the test
        run_text_generation_test(base_text, num_variations, context)


def edge_case_testing():
    """Test edge cases and error handling"""
    print("\n🧪 Edge Case Testing")
    print("=" * 30)
    
    edge_cases = [
        {
            "name": "Empty Context",
            "base_text": "Test with empty context",
            "context": "",
            "num_variations": 2
        },
        {
            "name": "Special Characters",
            "base_text": "Testing with émojis 🚀 & spécial chars!",
            "context": "special characters, unicode",
            "num_variations": 2
        },
        {
            "name": "Very Long Context",
            "base_text": "Long context test",
            "context": "This is a very long context string with many words and descriptors to test how the LLM handles extensive context information and whether it can still generate good variations with lots of guidance",
            "num_variations": 2
        },
        {
            "name": "Single Variation",
            "base_text": "Testing single variation",
            "context": "minimal output",
            "num_variations": 1
        }
    ]
    
    for test_case in edge_cases:
        print(f"\n🔍 Edge case: {test_case['name']}")
        run_text_generation_test(
            base_text=test_case['base_text'],
            num_variations=test_case['num_variations'],
            context=test_case['context'] if test_case['context'] else None
        )


def main():
    """Main function with menu system"""
    print("🤖 LLM Standalone Testing Tool - Sprint 4.1")
    print("=" * 50)
    
    # Test connection first
    if not test_connection():
        print("\n❌ Cannot proceed without LLM API connection!")
        print("Check your Google Cloud credentials and project configuration.")
        return False
    
    while True:
        print("\n📋 Testing Options:")
        print("1. Run predefined test cases")
        print("2. Interactive testing")
        print("3. Edge case testing")
        print("4. Test API connection")
        print("5. Quit")
        
        choice = input("\n🎯 Select option (1-5): ").strip()
        
        if choice == "1":
            predefined_test_cases()
        elif choice == "2":
            interactive_testing()
        elif choice == "3":
            edge_case_testing()
        elif choice == "4":
            test_connection()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice! Please select 1-5.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
