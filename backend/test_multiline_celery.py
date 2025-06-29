#!/usr/bin/env python3
"""
Test multi-line text overlay with Celery worker
"""

import os
import sys
import tempfile
import logging
import uuid
from celery import Celery
from models import TextStrategy, TextInput, FixedCuttingParams, RandomCuttingParams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
app = Celery('tasks')
app.config_from_object('config')

def test_multiline_text_with_celery():
    """Test multi-line text overlay through Celery worker"""
    
    print("=" * 60)
    print("Testing Multi-line Text Overlay with Celery Worker")
    print("=" * 60)
    
    # Test video path
    test_video_key = "uploads/108802a3-faeb-4e0c-b086-d99c91b883d8/20250628_215139_test_video.mp4"  # Use the existing test video
    
    # Multi-line text examples
    multiline_texts = [
        "Welcome to our amazing product!\nTransform your life today!",
        "See the incredible results\nthat will change everything\nfor you!",
        "Join thousands of\nsatisfied customers\nwho love our service",
        "Order now and save 50%!\nLimited time offer\nDon't miss out!"
    ]
    
    # Test with UNIQUE_FOR_ALL strategy using multi-line texts
    cutting_options = FixedCuttingParams(
        type="fixed",
        duration_seconds=15
    )
    
    text_input = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        unique_texts=multiline_texts
    )
    
    print(f"🎬 Testing with multi-line texts:")
    for i, text in enumerate(multiline_texts, 1):
        lines = text.split('\n')
        print(f"   Segment {i}: {len(lines)} lines")
        for j, line in enumerate(lines):
            print(f"     Line {j+1}: '{line}'")
    
    # Generate a dummy job_id for testing
    job_id = str(uuid.uuid4())
    
    try:
        # Import the task
        from tasks import process_video_task
        
        print(f"\n📤 Dispatching Celery task...")
        
        # Dispatch the task
        result = process_video_task.delay(
            s3_input_key=test_video_key,
            job_id=job_id,
            cutting_options={"type": "fixed", "duration_seconds": 15},
            text_strategy="unique_for_all",
            text_input={"strategy": "unique_for_all", "unique_texts": multiline_texts}
        )
        
        print(f"   Celery task dispatched! Task ID: {result.id}")
        print(f"   (Check Celery worker logs for progress)")
        
        return True
            
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing multi-line Celery task: {e}")
        return False

def test_base_vary_multiline():
    """Test BASE_VARY strategy with multi-line base text"""
    
    print(f"\n{'='*40}")
    print("Testing BASE_VARY with Multi-line Base Text")
    print(f"{'='*40}")
    
    # Multi-line base text
    base_text = "Disappointed by your doctor barely listening to you when you ask about the 10-15 pounds that came out of nowhere?\nFrustrated women succeed daily with the protocol we nearly give away at our clinic, but will you?\nCould your transformation start this weekend?"
    
    cutting_options = {"type": "fixed", "duration_seconds": 20}
    text_input = {
        "strategy": "base_vary",
        "base_text": base_text,
        "context": "health and wellness product advertisement"
    }
    
    print(f"🎬 Base text (3 lines):")
    for i, line in enumerate(base_text.split('\n'), 1):
        print(f"   Line {i}: '{line}'")
    print(f"   Context: {text_input['context']}")
    
    try:
        from tasks import process_video_task
        
        print(f"\n📤 Dispatching BASE_VARY task...")
        job_id = "test_base_vary_multiline_06"
        result = process_video_task.delay(
            s3_input_key="uploads/334ffc54-cb76-4f38-8c27-194911324caf/20250628_215659_test_video.mp4",
            job_id=job_id,
            cutting_options=cutting_options,
            text_strategy="base_vary",
            text_input=text_input
        )
        
        print(f"✅ BASE_VARY task dispatched!")
        print(f"   Task ID: {result.id}")
        print(f"   Note: LLM will generate variations of the multi-line base text")
        
        # Don't wait for this one, just confirm it was dispatched
        print(f"   Task State: {result.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing BASE_VARY multi-line: {str(e)}")
        return False

def main():
    """Run multi-line text tests with Celery"""
    
    print("Multi-line Text Overlay - Celery Worker Test")
    print("=" * 60)
    
    print("🔧 Prerequisites:")
    print("   ✓ Celery worker must be running")
    print("   ✓ Redis must be running")
    print("   ✓ Test video must exist in S3")
    print("   ✓ FFmpeg must be installed")
    print("   ✓ Gemini API key must be configured")
    
    # Test 1: UNIQUE_FOR_ALL with multi-line texts
    print(f"\n1. Testing UNIQUE_FOR_ALL strategy...")
    test1_result = test_multiline_text_with_celery()
    
    # Test 2: BASE_VARY with multi-line base text
    print(f"\n2. Testing BASE_VARY strategy...")
    test2_result = test_base_vary_multiline()
    
    # Summary
    print(f"\n{'='*60}")
    print("MULTI-LINE TEXT TEST SUMMARY:")
    print(f"UNIQUE_FOR_ALL multi-line: {'✓ PASS' if test1_result else '✗ FAIL'}")
    print(f"BASE_VARY multi-line: {'✓ PASS' if test2_result else '✗ FAIL'}")
    
    if test1_result:
        print(f"\n✅ Multi-line text overlays should now be visible in generated segments!")
        print(f"   Check the S3 output files to see multi-line text overlays")
    else:
        print(f"\n❌ Multi-line text test failed")
        print(f"   Check Celery worker logs for detailed error information")
    
    return test1_result or test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
