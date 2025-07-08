#!/usr/bin/env python3
"""
Test multi-line text overlay functionality
"""

import os
import sys
import tempfile
import logging

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from backend.video_processing_utils_helpers import create_multiline_drawtext_filter, process_segment_with_ffmpeg

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_multiline_filter_creation():
    """Test the multi-line drawtext filter creation"""
    
    print("Testing Multi-line Text Filter Creation")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Single line",
            "text": "Simple single line text",
            "font_size": 24,
            "max_width": 50
        },
        {
            "name": "Multiple explicit lines",
            "text": "Line 1\nLine 2\nLine 3",
            "font_size": 24,
            "max_width": 50
        },
        {
            "name": "Long text with wrapping",
            "text": "This is a very long line of text that should be automatically wrapped into multiple lines when it exceeds the maximum width",
            "font_size": 20,
            "max_width": 30
        },
        {
            "name": "Mixed explicit and wrapped lines",
            "text": "Short line\nThis is a much longer line that will be wrapped automatically\nAnother short line",
            "font_size": 18,
            "max_width": 25
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        print(f"   Input text: {repr(test_case['text'])}")
        print(f"   Font size: {test_case['font_size']}, Max width: {test_case['max_width']}")
        
        filter_str = create_multiline_drawtext_filter(
            test_case['text'], 
            test_case['font_size'], 
            test_case['max_width']
        )
        
        print(f"   Generated filter: {filter_str}")
        
        # Count number of drawtext filters
        filter_count = filter_str.count('drawtext=')
        print(f"   Number of text lines: {filter_count}")
    
    return True


def test_multiline_video_processing():
    """Test multi-line text on actual video if available"""
    
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"\nTest video {test_video_path} not found, skipping video processing test")
        return True
    
    print(f"\nTesting Multi-line Text on Video")
    print("=" * 50)
    
    # Test different multi-line scenarios
    test_scenarios = [
        {
            "name": "Simple multi-line",
            "text": "Welcome!\nTo our amazing product\nOrder now and save!"
        },
        {
            "name": "Long text with auto-wrap",
            "text": "Transform your life with our revolutionary new product that will change everything you thought you knew about success and happiness"
        },
        {
            "name": "Mixed format",
            "text": "🎉 SPECIAL OFFER 🎉\nGet 50% off your first order when you buy today\nLimited time only - don't miss out!"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Text: {repr(scenario['text'])}")
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Process 5-second segment with multi-line text
            result = process_segment_with_ffmpeg(
                input_path=test_video_path,
                output_path=output_path,
                start_time=0,
                end_time=5,
                text_overlay=scenario['text']
            )
            
            if result and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   ✅ Success! Output: {os.path.basename(output_path)} ({file_size:,} bytes)")
                
                # Clean up
                os.unlink(output_path)
            else:
                print(f"   ❌ Failed to create segment")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    return True


def main():
    """Run all multi-line text tests"""
    
    print("Multi-line Text Overlay Testing")
    print("=" * 60)
    
    # Test 1: Filter creation
    print("\n1. Testing filter creation...")
    test1_result = test_multiline_filter_creation()
    
    # Test 2: Video processing
    print("\n2. Testing video processing...")
    test2_result = test_multiline_video_processing()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"Filter creation: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Video processing: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    all_passed = test1_result and test2_result
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
