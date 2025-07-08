#!/usr/bin/env python3
"""
Test script to verify multi-line text overlay functionality
"""

import os
import tempfile
from video_processor import VideoProcessor

def test_text_overlay():
    """Test the text overlay functionality with various text lengths"""
    
    # Create processor instance
    processor = VideoProcessor(environment="development")
    
    # Test with the actual long text from the log
    long_text = "Drained by the constant 3am anxiety? Frustrated zombie-women are freed daily with the protocol we practically give away at our clinic, what about you? What's holding you back from anxiety-free nights? Click to find out how."
    
    # Mock video info (1920x1080 like in the log)
    video_info = {
        'width': 1920,
        'height': 1080,
        'duration': 30.0,
        'fps': 24
    }
    
    print(f"Testing with text: '{long_text[:50]}...'")
    print(f"Text length: {len(long_text)} characters")
    
    # Test the create_text_filter method directly
    try:
        text_filter = processor.create_text_filter(long_text, video_info, is_vertical=False)
        print(f"Generated filter: {text_filter[:200]}...")
        
        # Check if it contains multiple drawtext filters
        if text_filter.count('drawtext=') > 1:
            print("✅ SUCCESS: Multiple drawtext filters detected - multi-line is working!")
        else:
            print("❌ FAILURE: Only single drawtext filter detected - multi-line is NOT working!")
            
        # Count the number of drawtext filters
        filter_count = text_filter.count('drawtext=')
        print(f"Number of drawtext filters: {filter_count}")
        
        return filter_count > 1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_text_wrapping():
    """Test the text wrapping logic specifically"""
    
    processor = VideoProcessor(environment="development")
    
    # Test the _create_multiline_drawtext_filter method directly
    long_text = "Drained by the constant 3am anxiety? Frustrated zombie-women are freed daily with the protocol we practically give away at our clinic, what about you? What's holding you back from anxiety-free nights? Click to find out how."
    
    font_size = 54  # From the log
    max_width = 40  # Reasonable max width
    is_vertical = False
    
    try:
        result = processor._create_multiline_drawtext_filter(long_text, font_size, max_width, is_vertical)
        print(f"Multi-line filter result: {result[:200]}...")
        
        # Check if it contains multiple drawtext filters
        filter_count = result.count('drawtext=')
        print(f"Number of drawtext filters: {filter_count}")
        
        if filter_count > 1:
            print("✅ SUCCESS: Text wrapping is working!")
            return True
        else:
            print("❌ FAILURE: Text wrapping is NOT working!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in text wrapping: {e}")
        return False

def test_environment_configs():
    """Test different environment configurations"""
    
    print("\n🔧 Testing Environment Configurations")
    print("=" * 50)
    
    environments = ["production", "railway", "development"]
    
    for env in environments:
        processor = VideoProcessor(environment=env)
        print(f"\n📋 {env.upper()} Environment:")
        print(f"  Timeout per segment: {processor.config['timeout_per_segment']}s")
        print(f"  Default preset: {processor.config['default_preset']}")
        print(f"  Default CRF: {processor.config['default_crf']}")
        print(f"  Font size divisor: {processor.config['font_size_divisor']}")

if __name__ == "__main__":
    print("=== Testing Multi-Line Text Overlay ===")
    
    print("\n1. Testing create_text_filter method:")
    test1_result = test_text_overlay()
    
    print("\n2. Testing _create_multiline_drawtext_filter method:")
    test2_result = test_text_wrapping()
    
    print(f"\n=== Results ===")
    print(f"Test 1 (create_text_filter): {'PASS' if test1_result else 'FAIL'}")
    print(f"Test 2 (text wrapping): {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("✅ All tests passed - multi-line text overlay should work!")
    else:
        print("❌ Some tests failed - multi-line text overlay needs fixing!")
    
    test_environment_configs() 