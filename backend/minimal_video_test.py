#!/usr/bin/env python3
"""
Minimal Video Processing Test
Tests basic MoviePy functionality without complex features
"""
import sys
import os
import tempfile
from moviepy.editor import VideoFileClip

def minimal_video_test(video_path: str):
    """Test basic video processing without text overlays"""
    print("🎬 Minimal Video Processing Test")
    print("=" * 40)
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    try:
        print(f"Loading video: {os.path.basename(video_path)}")
        video = VideoFileClip(video_path)
        
        print(f"Duration: {video.duration:.2f} seconds")
        print(f"Size: {video.size}")
        
        # Test creating a simple 10-second clip
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_clip.mp4")
            
            # Extract just first 10 seconds
            test_clip = video.subclip(0, min(10, video.duration))
            
            print("Writing 10-second test clip...")
            test_clip.write_videofile(
                output_path,
                fps=video.fps if video.fps else 24,  # Explicitly set FPS
                verbose=False,
                logger=None
            )
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ Success! Created {os.path.getsize(output_path):,} byte file")
                test_clip.close()
                video.close()
                return True
            else:
                print("❌ Output file was not created or is empty")
                
        test_clip.close()
        video.close()
        return False
        
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python minimal_video_test.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    success = minimal_video_test(video_path)
    
    if success:
        print("\n✅ Basic video processing works!")
        print("The issue might be with text overlays or complex processing.")
    else:
        print("\n❌ Basic video processing failed.")
        print("This indicates a fundamental FFmpeg/MoviePy issue.")

if __name__ == "__main__":
    main()
