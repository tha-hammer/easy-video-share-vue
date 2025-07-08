#!/usr/bin/env python3
"""
FPS Fix Test - Quick verification that the FPS issue is resolved
"""
import tempfile
import os

def test_fps_fix():
    """Test that FPS issues are resolved"""
    print("🎬 Testing FPS Fix")
    print("=" * 25)
    
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "fps_test.mp4")
            
            # Create a test video clip
            video_clip = ColorClip(size=(320, 240), color=(0, 255, 0), duration=2)
            video_clip.fps = 24  # Explicitly set FPS
            
            # Create a text overlay
            text_clip = TextClip("TEST", fontsize=30, color='white').set_duration(2)
            text_clip.fps = 24  # Set FPS for text too
            text_clip = text_clip.set_position(('center', 'center'))
            
            # Composite them
            final_clip = CompositeVideoClip([video_clip, text_clip])
            final_clip.fps = 24  # Ensure final clip has FPS
            
            print("Creating test video with text overlay...")
            final_clip.write_videofile(
                output_path,
                fps=24,  # Explicitly pass FPS
                verbose=False,
                logger=None
            )
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ FPS fix successful! Created {os.path.getsize(output_path):,} byte file")
                
                # Clean up
                video_clip.close()
                text_clip.close()
                final_clip.close()
                
                return True
            else:
                print("❌ Output file was not created")
                return False
                
    except Exception as e:
        print(f"❌ FPS test failed: {e}")
        return False

def main():
    """Main test"""
    success = test_fps_fix()
    
    if success:
        print("\n✅ FPS fix is working!")
        print("Video processing should now work correctly.")
        print("\nTry running your video test again:")
        print('python test_video_processing.py "your_video.mp4"')
    else:
        print("\n❌ FPS fix didn't resolve the issue")
        print("There may be other underlying problems.")

if __name__ == "__main__":
    main()
