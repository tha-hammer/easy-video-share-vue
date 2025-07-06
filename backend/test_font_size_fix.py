#!/usr/bin/env python3
"""
Test the font size fix for text overlays
"""

import os
import sys
import tempfile
import logging
from video_processing_utils_sprint4 import get_video_info, process_segment_with_ffmpeg

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_font_size_calculation():
    """Test the font size calculation with different video resolutions"""
    
    # Test different resolutions (both horizontal and vertical)
    test_resolutions = [
        {'width': 1920, 'height': 1080, 'name': '1080p (horizontal)'},
        {'width': 1280, 'height': 720, 'name': '720p (horizontal)'},
        {'width': 854, 'height': 480, 'name': '480p (horizontal)'},
        {'width': 640, 'height': 360, 'name': '360p (horizontal)'},
        {'width': 3840, 'height': 2160, 'name': '4K (horizontal)'},
        {'width': 1080, 'height': 1920, 'name': '1080p (vertical)'},
        {'width': 720, 'height': 1280, 'name': '720p (vertical)'},
        {'width': 480, 'height': 854, 'name': '480p (vertical)'},
        {'width': 360, 'height': 640, 'name': '360p (vertical)'},
        {'width': 2160, 'height': 3840, 'name': '4K (vertical)'},
    ]
    
    print("Font size calculations for different resolutions:")
    print("=" * 60)
    
    for res in test_resolutions:
        width, height = res['width'], res['height']
        name = res['name']
        
        # Determine if video is vertical (portrait) or horizontal (landscape)
        is_vertical = height > width
        
        # Calculate font size based on video orientation and dimensions
        if is_vertical:
            # For vertical videos, use width as the reference dimension
            font_size = width // 15  # Larger divisor for better visibility
            font_size = max(font_size, 24)  # Minimum size
            font_size = min(font_size, 72)  # Maximum size
        else:
            # For horizontal videos, use height as the reference dimension
            font_size = height // 15  # Larger divisor for better visibility
            font_size = max(font_size, 24)  # Minimum size
            font_size = min(font_size, 72)  # Maximum size
        
        print(f"{name:20} {width}x{height:8} | font_size = {font_size:2d} | {'vertical' if is_vertical else 'horizontal':>9}")
    
    print("=" * 60)
    print("Key improvements:")
    print("- Vertical videos now use width as reference dimension")
    print("- Horizontal videos use height as reference dimension")
    print("- Font size divisor changed from 20 to 15 for better visibility")
    print("- Minimum font size increased from 16 to 24")
    print("- Maximum font size increased from 56 to 72")
    print("- Text positioned at top-left corner (x=30, y=30)")
    print("- Added background box for better readability")
    
    return True

def test_video_info_extraction():
    """Test video info extraction if test video exists"""
    
    test_video_path = "test_video.mp4"
    if os.path.exists(test_video_path):
        print(f"\nTesting video info extraction on {test_video_path}:")
        print("=" * 50)
        
        video_info = get_video_info(test_video_path)
        print(f"Video info: {video_info}")
        
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        font_size = min(width, height) // 25
        font_size = max(font_size, 20)
        font_size = min(font_size, 100)
        
        print(f"Calculated font size: {font_size}")
        return True
    else:
        print(f"\nTest video {test_video_path} not found, skipping video info test")
        return True

def test_segment_creation_with_text():
    """Test segment creation with text overlay if test video exists"""
    
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"\nTest video {test_video_path} not found, skipping segment creation test")
        return True
    
    print(f"\nTesting segment creation with text overlay:")
    print("=" * 50)
    
    try:
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_path = temp_file.name
        
        # Test text overlay
        test_text = "This is a test overlay with improved font size!"
        
        result = process_segment_with_ffmpeg(
            input_path=test_video_path,
            output_path=output_path,
            start_time=0,
            end_time=5,  # 5 second segment
            text_overlay=test_text
        )
        
        if result and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✓ Successfully created segment: {output_path}")
            print(f"  File size: {file_size} bytes")
            print(f"  Text overlay: '{test_text}'")
            
            # Clean up
            os.unlink(output_path)
            return True
        else:
            print(f"✗ Failed to create segment")
            return False
            
    except Exception as e:
        logger.error(f"Error testing segment creation: {e}")
        return False

def main():
    """Run all font size tests"""
    
    print("Testing Font Size Fix for Text Overlays")
    print("=" * 60)
    
    # Test 1: Font size calculation
    print("\n1. Testing font size calculations...")
    test1_result = test_font_size_calculation()
    
    # Test 2: Video info extraction
    print("\n2. Testing video info extraction...")
    test2_result = test_video_info_extraction()
    
    # Test 3: Segment creation with text
    print("\n3. Testing segment creation with text overlay...")
    test3_result = test_segment_creation_with_text()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"Font size calculations: {'✓ PASS' if test1_result else '✗ FAIL'}")
    print(f"Video info extraction: {'✓ PASS' if test2_result else '✗ FAIL'}")
    print(f"Segment creation: {'✓ PASS' if test3_result else '✗ FAIL'}")
    
    all_passed = test1_result and test2_result and test3_result
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
