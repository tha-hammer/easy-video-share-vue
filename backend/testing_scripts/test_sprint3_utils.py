#!/usr/bin/env python3
"""
Sprint 3 Video Processing Utils Test

This script tests the new video processing utility functions independently:
1. get_video_duration_from_s3
2. calculate_segments

Requirements:
- AWS credentials configured
- Test video file in S3
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import FixedCuttingParams, RandomCuttingParams
from video_processor import get_video_duration_from_s3, calculate_segments
from config import settings
import boto3
from botocore.exceptions import ClientError

def list_s3_videos():
    """List video files in the S3 bucket to help user choose"""
    print(f"Listing video files in bucket: {settings.AWS_BUCKET_NAME}")
    print("-" * 50)
    
    try:
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        response = s3_client.list_objects_v2(Bucket=settings.AWS_BUCKET_NAME)
        
        if 'Contents' not in response:
            print("No files found in bucket")
            return []
            
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        video_files = []
        
        for obj in response['Contents']:
            key = obj['Key']
            if any(key.lower().endswith(ext) for ext in video_extensions):
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"  {key} ({size_mb:.1f} MB)")
                video_files.append(key)
        
        if not video_files:
            print("No video files found")
            
        return video_files
        
    except Exception as e:
        print(f"Error listing S3 contents: {e}")
        return []


def parse_s3_input(user_input: str) -> str:
    """Parse user input and extract S3 key from URI or return as-is"""
    user_input = user_input.strip()
    
    # If user provided full S3 URI, extract the key part
    if user_input.startswith('s3://'):
        parts = user_input.replace('s3://', '').split('/', 1)
        if len(parts) == 2:
            bucket, key = parts
            print(f"Detected S3 URI. Using bucket: {bucket}, key: {key}")
            return key
        else:
            print("Invalid S3 URI format")
            return None
    
    # Otherwise assume it's already just the key
    return user_input


def test_video_duration_analysis(s3_key: str):
    """Test video duration analysis"""
    print(f"Testing video duration analysis for: {s3_key}")
    
    try:
        duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, s3_key)
        print(f"✓ Video duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"✗ Failed to get video duration: {e}")
        return None

def test_calculate_segments_fixed(duration: float):
    """Test fixed segment calculation"""
    print(f"\nTesting fixed segment calculation (30s segments)...")
    
    cutting_params = FixedCuttingParams(duration_seconds=30)
    
    try:
        num_segments, segment_times = calculate_segments(duration, cutting_params)
        print(f"✓ Fixed segments calculated:")
        print(f"  Number of segments: {num_segments}")
        print(f"  Segment times:")
        for i, (start, end) in enumerate(segment_times):
            print(f"    Segment {i+1}: {start:.2f}s - {end:.2f}s (duration: {end-start:.2f}s)")
        return True
    except Exception as e:
        print(f"✗ Failed to calculate fixed segments: {e}")
        return False

def test_calculate_segments_random(duration: float):
    """Test random segment calculation"""
    print(f"\nTesting random segment calculation (15-45s range)...")
    
    cutting_params = RandomCuttingParams(min_duration=15, max_duration=45)
    
    try:
        num_segments, segment_times = calculate_segments(duration, cutting_params)
        print(f"✓ Random segments calculated:")
        print(f"  Number of segments: {num_segments}")
        print(f"  Segment times:")
        for i, (start, end) in enumerate(segment_times):
            print(f"    Segment {i+1}: {start:.2f}s - {end:.2f}s (duration: {end-start:.2f}s)")
        return True
    except Exception as e:
        print(f"✗ Failed to calculate random segments: {e}")
        return False

def test_error_cases(duration: float):
    """Test error handling"""
    print(f"\nTesting error cases...")
    
    # Test with segment duration longer than video
    print("Testing segment duration longer than video...")
    long_cutting_params = FixedCuttingParams(duration_seconds=int(duration + 100))
    
    try:
        calculate_segments(duration, long_cutting_params)
        print("✗ Expected error for too long segment duration")
        return False
    except Exception as e:
        print(f"✓ Correctly caught error: {e}")
    
    # Test with minimum duration longer than video
    print("Testing minimum duration longer than video...")
    long_random_params = RandomCuttingParams(min_duration=int(duration + 50), max_duration=int(duration + 100))
    
    try:
        calculate_segments(duration, long_random_params)
        print("✗ Expected error for too long minimum duration")
        return False
    except Exception as e:
        print(f"✓ Correctly caught error: {e}")
    
    return True

def main():
    """Main function"""
    print("Sprint 3 Video Processing Utils Test")
    print("=" * 50)
    
    print(f"Using S3 bucket: {settings.AWS_BUCKET_NAME}")
    print()
    print("Would you like to see available video files? (y/n)")
    if input().lower().startswith('y'):
        video_files = list_s3_videos()
        print()
    
    print("Enter S3 key of test video:")
    print("Examples:")
    print("  - uploads/my-video.mp4")
    print("  - test_video.mp4")
    print("  - s3://bucket-name/path/video.mp4 (will auto-extract key)")
    print()
    s3_input = input("S3 key/URI: ").strip()
    
    if not s3_input:
        print("No S3 key provided. Exiting.")
        return
    
    # Parse the input to extract just the key
    s3_key = parse_s3_input(s3_input)
    if not s3_key:
        print("Invalid input format. Exiting.")
        return
    
    print(f"Using S3 key: {s3_key}")
    print()
    
    # Test 1: Get video duration
    duration = test_video_duration_analysis(s3_key)
    if duration is None:
        print("Cannot proceed without video duration")
        return
    
    # Test 2: Calculate fixed segments
    test_calculate_segments_fixed(duration)
    
    # Test 3: Calculate random segments
    test_calculate_segments_random(duration)
    
    # Test 4: Error cases
    test_error_cases(duration)
    
    print("\n" + "=" * 50)
    print("Sprint 3 video processing utils tests completed!")

if __name__ == "__main__":
    main()
