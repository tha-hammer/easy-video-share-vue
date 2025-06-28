#!/usr/bin/env python3
"""
Create Test Video for Sprint 2 Validation

This script creates a simple test video using FFmpeg for validating
the Sprint 2 video processing pipeline.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ FFmpeg is available")
            return True
        else:
            print("❌ FFmpeg check failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg not found in PATH")
        return False

def create_test_video(output_path: str, duration: int = 30):
    """Create a test video using FFmpeg"""
    
    print(f"Creating test video: {output_path}")
    print(f"Duration: {duration} seconds")
    
    # FFmpeg command to create a test video
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'testsrc2=duration={duration}:size=640x480:rate=30',
        '-f', 'lavfi', 
        '-i', f'sine=frequency=1000:duration={duration}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-y',  # Overwrite output file
        output_path
    ]
    
    try:
        print("Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            print(f"✓ Test video created successfully!")
            print(f"  Path: {output_path}")
            print(f"  Size: {file_size:,} bytes")
            return True
        else:
            print("❌ FFmpeg failed to create test video")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running FFmpeg: {e}")
        return False

def main():
    """Main function"""
    print("Test Video Creator for Sprint 2")
    print("=" * 40)
    
    # Check FFmpeg availability
    if not check_ffmpeg():
        print("\nPlease install FFmpeg and ensure it's in your PATH")
        print("Download from: https://ffmpeg.org/download.html")
        return False
    
    # Create test video in backend directory
    backend_dir = Path(__file__).parent
    test_video_path = backend_dir / "test_video.mp4"
    
    if test_video_path.exists():
        response = input(f"\nTest video already exists at {test_video_path}. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Using existing test video.")
            return True
    
    success = create_test_video(str(test_video_path))
    
    if success:
        print(f"\n🎉 Test video ready for Sprint 2 validation!")
        print(f"You can now run: python test_sprint2_e2e.py")
    else:
        print(f"\n❌ Failed to create test video")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
