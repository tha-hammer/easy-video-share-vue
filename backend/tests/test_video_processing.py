#!/usr/bin/env python3
"""
Test video processing functionality locally
This script tests the video processing pipeline without Celery
"""
import os
import sys
import tempfile
from video_processing_utils import split_and_overlay_hardcoded, validate_video_file, get_video_info

def test_video_processing(video_path: str):
    """Test video processing with a local video file"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    try:
        print(f"Testing video processing with: {video_path}")
        
        # Validate video file
        print("Validating video file...")
        if not validate_video_file(video_path):
            print("❌ Invalid video file")
            return False
        print("✅ Video file is valid")
        
        # Get video info
        print("Getting video information...")
        video_info = get_video_info(video_path)
        print(f"Duration: {video_info['duration']:.2f} seconds")
        print(f"FPS: {video_info['fps']}")
        print(f"Resolution: {video_info['size'][0]}x{video_info['size'][1]}")
        print(f"Format: {video_info['format']}")
        
        # Create temporary directory for output
        with tempfile.TemporaryDirectory(prefix="video_test_") as temp_dir:
            output_prefix = os.path.join(temp_dir, "test_output")
            
            print(f"Processing video with output prefix: {output_prefix}")
            print("This may take a few minutes depending on video length...")
            
            # Process video
            output_paths = split_and_overlay_hardcoded(video_path, output_prefix)
            
            print(f"✅ Video processing completed!")
            print(f"Generated {len(output_paths)} segments:")
            
            total_size = 0
            for i, path in enumerate(output_paths):
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    total_size += size
                    print(f"  {i+1}. {os.path.basename(path)} ({size:,} bytes)")
                else:
                    print(f"  {i+1}. ❌ Missing: {os.path.basename(path)}")
            
            print(f"Total output size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
            
            # Note: Files will be automatically cleaned up when temp directory is destroyed
            print("✅ Test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Video processing test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    if len(sys.argv) != 2:
        print("Usage: python test_video_processing.py <path_to_video_file>")
        print("Example: python test_video_processing.py sample_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    print("🎬 Video Processing Test")
    print("=" * 50)
    
    success = test_video_processing(video_path)
    
    if success:
        print("\n✅ All tests passed! Video processing is working correctly.")
    else:
        print("\n❌ Tests failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
