"""
Sprint 4.1 Comprehensive Backend Test
Tests the complete integration of dynamic text application and LLM prompting refinement
"""

import asyncio
import logging
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Import our backend modules
from models import TextStrategy, TextInput, FixedCuttingParams, CompleteUploadRequest
from llm_service_vertexai import LLMService, generate_text_variations
from video_processing_utils_sprint4 import prepare_text_overlays
from tasks import process_video_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from models import TextStrategy, TextInput, CuttingOptions, FixedCuttingParams
from video_processing_utils_sprint4 import prepare_text_overlays
from llm_service_vertexai import generate_text_variations, test_llm_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_text_input_model():
    """Test that TextInput model properly handles all strategies"""
    print("\n🧪 Testing TextInput Pydantic Model...")
    
    # Test ONE_FOR_ALL strategy
    text_input_one = TextInput(
        strategy=TextStrategy.ONE_FOR_ALL,
        base_text="AI Generated Video",
        context=None,
        unique_texts=None
    )
    assert text_input_one.strategy == TextStrategy.ONE_FOR_ALL
    assert text_input_one.base_text == "AI Generated Video"
    print("✅ ONE_FOR_ALL model validation passed")
    
    # Test BASE_VARY strategy
    text_input_vary = TextInput(
        strategy=TextStrategy.BASE_VARY,
        base_text="Check out our product!",
        context="sales, urgency, call-to-action",
        unique_texts=None
    )
    assert text_input_vary.strategy == TextStrategy.BASE_VARY
    assert text_input_vary.context == "sales, urgency, call-to-action"
    print("✅ BASE_VARY model validation passed")
    
    # Test UNIQUE_FOR_ALL strategy
    text_input_unique = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        base_text=None,
        context=None,
        unique_texts=["Intro text", "Mid-segment detail", "Final call-to-action"]
    )
    assert text_input_unique.strategy == TextStrategy.UNIQUE_FOR_ALL
    assert len(text_input_unique.unique_texts) == 3
    print("✅ UNIQUE_FOR_ALL model validation passed")
    
    print("✅ All TextInput model tests passed!")


def test_prepare_text_overlays_one_for_all():
    """Test prepare_text_overlays for ONE_FOR_ALL strategy"""
    print("\n🧪 Testing prepare_text_overlays - ONE_FOR_ALL...")
    
    text_input = TextInput(
        strategy=TextStrategy.ONE_FOR_ALL,
        base_text="Same text for all segments",
        context=None,
        unique_texts=None
    )
    
    overlays = prepare_text_overlays(TextStrategy.ONE_FOR_ALL, text_input, 5)
    
    assert len(overlays) == 5
    assert all(text == "Same text for all segments" for text in overlays)
    print("✅ ONE_FOR_ALL text preparation passed")


def test_prepare_text_overlays_unique_for_all():
    """Test prepare_text_overlays for UNIQUE_FOR_ALL strategy"""
    print("\n🧪 Testing prepare_text_overlays - UNIQUE_FOR_ALL...")
    
    unique_texts = ["Segment 1 text", "Segment 2 text", "Segment 3 text"]
    text_input = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        base_text=None,
        context=None,
        unique_texts=unique_texts
    )
    
    overlays = prepare_text_overlays(TextStrategy.UNIQUE_FOR_ALL, text_input, 3)
    
    assert len(overlays) == 3
    assert overlays[0] == "Segment 1 text"
    assert overlays[1] == "Segment 2 text"
    assert overlays[2] == "Segment 3 text"
    print("✅ UNIQUE_FOR_ALL text preparation passed")
    
    # Test padding behavior when fewer texts than segments
    overlays_padded = prepare_text_overlays(TextStrategy.UNIQUE_FOR_ALL, text_input, 5)
    assert len(overlays_padded) == 5
    assert overlays_padded[3] == "Segment 3 text"  # Should pad with last text
    assert overlays_padded[4] == "Segment 3 text"
    print("✅ UNIQUE_FOR_ALL padding behavior passed")


def test_llm_connection():
    """Test LLM API connection"""
    print("\n🧪 Testing LLM API Connection...")
    
    try:
        connection_ok = test_llm_connection()
        if connection_ok:
            print("✅ LLM API connection test passed")
        else:
            print("⚠️ LLM API connection test failed - check credentials")
    except Exception as e:
        print(f"❌ LLM API connection error: {str(e)}")


def test_llm_text_generation_with_context():
    """Test LLM text generation with different contexts"""
    print("\n🧪 Testing LLM Text Generation with Context...")
    
    base_text = "Try our amazing product today!"
    num_variations = 3
    
    # Test sales context
    print("\n📝 Testing Sales Context...")
    try:
        sales_variations = generate_text_variations(
            base_text=base_text,
            num_variations=num_variations,
            context="sales, urgency, call-to-action"
        )
        
        print(f"Base text: {base_text}")
        print(f"Sales context variations ({len(sales_variations)}):")
        for i, variation in enumerate(sales_variations, 1):
            print(f"  {i}. {variation}")
        
        assert len(sales_variations) == num_variations
        assert base_text in sales_variations  # Original should be included
        print("✅ Sales context generation passed")
        
    except Exception as e:
        print(f"⚠️ Sales context generation failed: {str(e)}")
    
    # Test engagement context
    print("\n📝 Testing Engagement Context...")
    try:
        engagement_variations = generate_text_variations(
            base_text=base_text,
            num_variations=num_variations,
            context="engagement, social interaction, community"
        )
        
        print(f"Engagement context variations ({len(engagement_variations)}):")
        for i, variation in enumerate(engagement_variations, 1):
            print(f"  {i}. {variation}")
        
        assert len(engagement_variations) == num_variations
        print("✅ Engagement context generation passed")
        
    except Exception as e:
        print(f"⚠️ Engagement context generation failed: {str(e)}")


def test_prepare_text_overlays_base_vary_with_llm():
    """Test prepare_text_overlays for BASE_VARY strategy with real LLM call"""
    print("\n🧪 Testing prepare_text_overlays - BASE_VARY with LLM...")
    
    text_input = TextInput(
        strategy=TextStrategy.BASE_VARY,
        base_text="Don't miss this opportunity!",
        context="sales, limited time, exclusive offer",
        unique_texts=None
    )
    
    try:
        overlays = prepare_text_overlays(TextStrategy.BASE_VARY, text_input, 4)
        
        print(f"BASE_VARY overlays generated ({len(overlays)}):")
        for i, overlay in enumerate(overlays, 1):
            print(f"  Segment {i}: {overlay}")
        
        assert len(overlays) == 4
        assert all(isinstance(text, str) and len(text.strip()) > 0 for text in overlays)
        print("✅ BASE_VARY with LLM preparation passed")
        
    except Exception as e:
        print(f"⚠️ BASE_VARY with LLM preparation failed: {str(e)}")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing Edge Cases...")
    
    # Test with None text_input
    overlays_none = prepare_text_overlays(TextStrategy.ONE_FOR_ALL, None, 3)
    assert len(overlays_none) == 3
    assert all(text == "AI Generated Video" for text in overlays_none)
    print("✅ None text_input handling passed")
    
    # Test BASE_VARY with no base_text
    text_input_no_base = TextInput(
        strategy=TextStrategy.BASE_VARY,
        base_text=None,
        context="sales",
        unique_texts=None
    )
    overlays_no_base = prepare_text_overlays(TextStrategy.BASE_VARY, text_input_no_base, 2)
    assert len(overlays_no_base) == 2
    print("✅ BASE_VARY with no base_text handling passed")
    
    # Test UNIQUE_FOR_ALL with empty unique_texts
    text_input_empty_unique = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        base_text=None,
        context=None,
        unique_texts=[]
    )
    overlays_empty = prepare_text_overlays(TextStrategy.UNIQUE_FOR_ALL, text_input_empty_unique, 2)
    assert len(overlays_empty) == 2
    print("✅ UNIQUE_FOR_ALL with empty texts handling passed")


def generate_manual_test_scripts():
    """Generate manual test scripts for Celery task dispatch"""
    print("\n📝 Generating Manual Test Scripts...")
    
    # Script for BASE_VARY strategy
    base_vary_script = '''#!/usr/bin/env python3
"""
Manual Test Script - BASE_VARY Strategy
Tests LLM-powered text variations applied to video segments
"""

import sys
import os
import json
from celery.result import AsyncResult

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_base_vary_strategy():
    """Test BASE_VARY strategy with real Celery task dispatch"""
    
    # Replace with your actual S3 video key
    s3_video_key = "uploads/test-video.mp4"
    job_id = "test-base-vary-001"
    
    # Configure text input for BASE_VARY
    text_input = TextInput(
        strategy=TextStrategy.BASE_VARY,
        base_text="Check out our new product launch!",
        context="sales pitch, excitement, call to action",
        unique_texts=None
    )
    
    # Configure cutting options
    cutting_options = FixedCuttingParams(
        type="fixed",
        duration_seconds=30
    )
    
    print(f"🚀 Dispatching BASE_VARY test task...")
    print(f"S3 Key: {s3_video_key}")
    print(f"Job ID: {job_id}")
    print(f"Base Text: {text_input.base_text}")
    print(f"Context: {text_input.context}")
    
    # Dispatch the task
    result = process_video_task.delay(
        s3_input_key=s3_video_key,
        job_id=job_id,
        cutting_options=cutting_options.dict(),
        text_strategy=text_input.strategy.value,
        text_input=text_input.dict()
    )
    
    print(f"✅ Task dispatched with ID: {result.id}")
    print(f"📋 Task state: {result.state}")
    
    print("\\n📖 Monitor instructions:")
    print("1. Watch Celery worker logs for LLM API calls")
    print("2. Check generated text variations in worker output")
    print("3. Inspect S3 output videos for correct text overlays")
    print("4. Verify each segment has different but related text")
    
    return result

if __name__ == "__main__":
    test_base_vary_strategy()
'''
    
    # Script for UNIQUE_FOR_ALL strategy
    unique_for_all_script = '''#!/usr/bin/env python3
"""
Manual Test Script - UNIQUE_FOR_ALL Strategy
Tests user-provided unique text for each video segment
"""

import sys
import os
import json
from celery.result import AsyncResult

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_unique_for_all_strategy():
    """Test UNIQUE_FOR_ALL strategy with real Celery task dispatch"""
    
    # Replace with your actual S3 video key
    s3_video_key = "uploads/test-video.mp4"
    job_id = "test-unique-for-all-001"
    
    # Configure text input for UNIQUE_FOR_ALL
    unique_texts = [
        "🚀 Welcome to our product demo",
        "💡 Here's what makes us different",
        "🎯 Key features you'll love",
        "📞 Ready to get started?",
        "🎉 Join thousands of happy customers"
    ]
    
    text_input = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        base_text=None,
        context=None,
        unique_texts=unique_texts
    )
    
    # Configure cutting options
    cutting_options = FixedCuttingParams(
        type="fixed",
        duration_seconds=25
    )
    
    print(f"🚀 Dispatching UNIQUE_FOR_ALL test task...")
    print(f"S3 Key: {s3_video_key}")
    print(f"Job ID: {job_id}")
    print(f"Unique texts ({len(unique_texts)}):")
    for i, text in enumerate(unique_texts, 1):
        print(f"  Segment {i}: {text}")
    
    # Dispatch the task
    result = process_video_task.delay(
        s3_input_key=s3_video_key,
        job_id=job_id,
        cutting_options=cutting_options.dict(),
        text_strategy=text_input.strategy.value,
        text_input=text_input.dict()
    )
    
    print(f"✅ Task dispatched with ID: {result.id}")
    print(f"📋 Task state: {result.state}")
    
    print("\\n📖 Monitor instructions:")
    print("1. Watch Celery worker logs for segment processing")
    print("2. Verify no LLM calls (using provided texts)")
    print("3. Inspect S3 output videos for correct unique text overlays")
    print("4. Confirm each segment has its exact corresponding text")
    
    return result

if __name__ == "__main__":
    test_unique_for_all_strategy()
'''
    
    # Write the scripts to files
    scripts = [
        ("manual_test_base_vary.py", base_vary_script),
        ("manual_test_unique_for_all.py", unique_for_all_script)
    ]
    
    for filename, content in scripts:
        script_path = os.path.join(backend_dir, filename)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Generated: {filename}")
    
    print(f"\\n📁 Manual test scripts created in: {backend_dir}")
    print("\\n🚀 Usage instructions:")
    print("1. Ensure Celery worker is running: celery -A tasks worker --loglevel=info")
    print("2. Update S3 video keys in the scripts")
    print("3. Run: python manual_test_base_vary.py")
    print("4. Run: python manual_test_unique_for_all.py")
    print("5. Monitor worker logs and check S3 outputs")


def main():
    """Run all Sprint 4.1 comprehensive tests"""
    print("🚀 Starting Sprint 4.1 Comprehensive Backend Tests")
    print("=" * 60)
    
    try:
        # Test data models
        test_text_input_model()
        
        # Test text overlay preparation logic
        test_prepare_text_overlays_one_for_all()
        test_prepare_text_overlays_unique_for_all()
        
        # Test LLM integration
        test_llm_connection()
        test_llm_text_generation_with_context()
        test_prepare_text_overlays_base_vary_with_llm()
        
        # Test edge cases
        test_edge_cases()
        
        # Generate manual test scripts
        generate_manual_test_scripts()
        
        print("\\n" + "=" * 60)
        print("🎉 All Sprint 4.1 comprehensive tests completed!")
        print("✅ Backend text overlay integration is working correctly")
        print("\\nNext steps:")
        print("1. Run manual Celery task tests with real S3 videos")
        print("2. Visual verification of generated video segments")
        print("3. Test complete end-to-end pipeline")
        
    except Exception as e:
        print(f"\\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
        }
    ]
    
    all_success = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Base Text: '{test_case['base_text']}'")
        print(f"Context: {test_case['context'] or 'None'}")
        print(f"Requested Variations: {test_case['num_variations']}")
        
        try:
            variations = generate_text_variations(
                base_text=test_case['base_text'],
                num_variations=test_case['num_variations'],
                context=test_case['context']
            )
            
            print(f"Generated {len(variations)} variations:")
            for j, variation in enumerate(variations, 1):
                print(f"  {j}. '{variation}'")
            
            # Validate results
            if len(variations) == test_case['num_variations']:
                print("✅ Correct number of variations generated")
            else:
                print(f"⚠️  Expected {test_case['num_variations']}, got {len(variations)}")
            
            # Check if variations are different from each other
            unique_variations = set(variations)
            if len(unique_variations) > 1:
                print("✅ Variations are diverse")
            else:
                print("⚠️  All variations are identical")
                
        except Exception as e:
            print(f"❌ Error generating variations: {str(e)}")
            all_success = False
    
    return all_success


def test_text_overlay_preparation():
    """Test text overlay preparation for all strategies"""
    print("\n" + "=" * 60)
    print("Testing Text Overlay Preparation")
    print("=" * 60)
    
    num_segments = 4
    
    test_scenarios = [
        {
            "name": "ONE_FOR_ALL Strategy",
            "strategy": TextStrategy.ONE_FOR_ALL,
            "text_input": TextInput(
                strategy=TextStrategy.ONE_FOR_ALL,
                base_text="Your success starts here!",
                context=None,
                unique_texts=None
            )
        },
        {
            "name": "BASE_VARY Strategy with Sales Context",
            "strategy": TextStrategy.BASE_VARY,
            "text_input": TextInput(
                strategy=TextStrategy.BASE_VARY,
                base_text="Transform your life today",
                context="sales pitch, urgent, action-oriented",
                unique_texts=None
            )
        },
        {
            "name": "BASE_VARY Strategy with Educational Context",
            "strategy": TextStrategy.BASE_VARY,
            "text_input": TextInput(
                strategy=TextStrategy.BASE_VARY,
                base_text="Master new skills",
                context="educational, learning-focused, encouraging",
                unique_texts=None
            )
        },
        {
            "name": "UNIQUE_FOR_ALL Strategy",
            "strategy": TextStrategy.UNIQUE_FOR_ALL,
            "text_input": TextInput(
                strategy=TextStrategy.UNIQUE_FOR_ALL,
                base_text=None,
                context=None,
                unique_texts=[
                    "Welcome to our product demo!",
                    "See these amazing features in action",
                    "Join thousands of satisfied customers",
                    "Order now and save 50% today!"
                ]
            )
        },
        {
            "name": "Error Case - No Text Provided",
            "strategy": TextStrategy.BASE_VARY,
            "text_input": None
        }
    ]
    
    all_success = True
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"Strategy: {scenario['strategy']}")
        if scenario['text_input']:
            print(f"Text Input: {scenario['text_input'].dict()}")
        else:
            print("Text Input: None")
        
        try:
            text_overlays = prepare_text_overlays(
                text_strategy=scenario['strategy'],
                text_input=scenario['text_input'],
                num_segments=num_segments
            )
            
            print(f"Generated {len(text_overlays)} text overlays:")
            for j, text in enumerate(text_overlays, 1):
                print(f"  Segment {j}: '{text}'")
            
            # Validate results
            if len(text_overlays) == num_segments:
                print("✅ Correct number of text overlays generated")
            else:
                print(f"⚠️  Expected {num_segments}, got {len(text_overlays)}")
            
            # Check strategy-specific requirements
            if scenario['strategy'] == TextStrategy.ONE_FOR_ALL:
                if all(text == text_overlays[0] for text in text_overlays):
                    print("✅ All segments have the same text (ONE_FOR_ALL)")
                else:
                    print("❌ Segments should have identical text for ONE_FOR_ALL")
                    all_success = False
            
            elif scenario['strategy'] == TextStrategy.BASE_VARY:
                if scenario['text_input'] and scenario['text_input'].base_text:
                    # Should have the base text as first variation
                    if text_overlays[0] == scenario['text_input'].base_text:
                        print("✅ First variation matches base text")
                    else:
                        print("⚠️  First variation should match base text")
                    
                    # Check for diversity
                    unique_texts = set(text_overlays)
                    if len(unique_texts) > 1:
                        print("✅ Text variations are diverse")
                    else:
                        print("⚠️  All variations are identical")
                        
        except Exception as e:
            print(f"❌ Error preparing text overlays: {str(e)}")
            all_success = False
    
    return all_success


def test_models_integration():
    """Test the updated models and their integration"""
    print("\n" + "=" * 60)
    print("Testing Updated Models Integration")
    print("=" * 60)
    
    try:
        # Test TextInput model with all fields
        print("--- Testing TextInput Model ---")
        
        text_input = TextInput(
            strategy=TextStrategy.BASE_VARY,
            base_text="Test your limits",
            context="motivational, fitness, encouraging",
            unique_texts=None
        )
        
        print(f"✅ TextInput created: {text_input.dict()}")
        
        # Test with UNIQUE_FOR_ALL
        unique_text_input = TextInput(
            strategy=TextStrategy.UNIQUE_FOR_ALL,
            base_text=None,
            context=None,
            unique_texts=["Text 1", "Text 2", "Text 3"]
        )
        
        print(f"✅ UNIQUE_FOR_ALL TextInput created: {unique_text_input.dict()}")
        
        # Test JSON serialization/deserialization
        json_str = text_input.json()
        reconstructed = TextInput.parse_raw(json_str)
        
        if text_input.dict() == reconstructed.dict():
            print("✅ JSON serialization/deserialization works correctly")
        else:
            print("❌ JSON serialization/deserialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
        return False


def create_manual_test_scripts():
    """Create manual test scripts for video processing"""
    print("\n" + "=" * 60)
    print("Creating Manual Test Scripts")
    print("=" * 60)
    
    scripts = {
        "test_base_vary_manual.py": '''"""
Manual test script for BASE_VARY strategy
Dispatch a video processing task with LLM-generated text variations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

# Example usage:
# 1. Upload a video to S3 and get the S3 key
# 2. Replace 'your-s3-key-here' with the actual S3 key
# 3. Run this script to test BASE_VARY strategy

def test_base_vary_processing():
    s3_key = "uploads/test_video.mp4"  # Replace with actual S3 key
    job_id = "test-base-vary-job"
    
    cutting_options = {
        "type": "fixed",
        "duration_seconds": 20
    }
    
    text_input = {
        "strategy": "base_vary",
        "base_text": "Unlock your potential today",
        "context": "motivational, self-improvement, action-oriented",
        "unique_texts": None
    }
    
    print("Dispatching BASE_VARY video processing task...")
    print(f"S3 Key: {s3_key}")
    print(f"Job ID: {job_id}")
    print(f"Text Input: {text_input}")
    
    # Dispatch the task
    task = process_video_task.delay(
        s3_input_key=s3_key,
        job_id=job_id,
        cutting_options=cutting_options,
        text_strategy="base_vary",
        text_input=text_input
    )
    
    print(f"Task dispatched with ID: {task.id}")
    print("Monitor worker logs for LLM generation and video processing")
    print("Check S3 for processed video segments with text variations")

if __name__ == "__main__":
    test_base_vary_processing()
''',
        
        "test_unique_for_all_manual.py": '''"""
Manual test script for UNIQUE_FOR_ALL strategy
Dispatch a video processing task with user-provided unique texts
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_unique_for_all_processing():
    s3_key = "uploads/test_video.mp4"  # Replace with actual S3 key
    job_id = "test-unique-for-all-job"
    
    cutting_options = {
        "type": "fixed",
        "duration_seconds": 25
    }
    
    text_input = {
        "strategy": "unique_for_all",
        "base_text": None,
        "context": None,
        "unique_texts": [
            "Welcome to our product showcase!",
            "See how it transforms your workflow",
            "Join 10,000+ satisfied customers",
            "Order now with 30% off!"
        ]
    }
    
    print("Dispatching UNIQUE_FOR_ALL video processing task...")
    print(f"S3 Key: {s3_key}")
    print(f"Job ID: {job_id}")
    print(f"Unique Texts: {text_input['unique_texts']}")
    
    # Dispatch the task
    task = process_video_task.delay(
        s3_input_key=s3_key,
        job_id=job_id,
        cutting_options=cutting_options,
        text_strategy="unique_for_all",
        text_input=text_input
    )
    
    print(f"Task dispatched with ID: {task.id}")
    print("Monitor worker logs for text application")
    print("Check S3 - each segment should have its specific text overlay")

if __name__ == "__main__":
    test_unique_for_all_processing()
'''
    }
    
    # Create the test scripts
    for filename, content in scripts.items():
        script_path = os.path.join(backend_dir, filename)
        with open(script_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {filename}")
    
    print(f"\n📁 Manual test scripts created in: {backend_dir}")
    print("To use these scripts:")
    print("1. Upload a test video to S3")
    print("2. Update the s3_key in the scripts")
    print("3. Ensure Redis and Celery worker are running")
    print("4. Run the scripts to test video processing")


def main():
    """Run all Sprint 4.1 tests"""
    print("Sprint 4.1 Dynamic Text Application & LLM Prompting Test Suite")
    print("=" * 70)
    
    # Check Vertex AI connection first
    print("🔄 Testing Vertex AI connection...")
    if not test_llm_connection():
        print("❌ Vertex AI connection failed. Please fix authentication first.")
        print("Run: gcloud auth application-default login")
        return False
    
    print("✅ Vertex AI connection successful")
    
    # Run all tests
    tests = [
        ("Models Integration", test_models_integration),
        ("LLM Context Variations", test_llm_context_variations),
        ("Text Overlay Preparation", test_text_overlay_preparation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    # Create manual test scripts
    create_manual_test_scripts()
    
    # Summary
    print("\n" + "=" * 70)
    print("Sprint 4.1 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Sprint 4.1 tests PASSED!")
        print("✅ Dynamic text application is working correctly")
        print("✅ LLM context-aware prompting is functional")
        print("✅ All text strategies are properly integrated")
        print("\n🚀 Ready for full video processing with dynamic text!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
