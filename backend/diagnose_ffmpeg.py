#!/usr/bin/env python3
"""
FFmpeg Configuration and Test Tool
Diagnoses and fixes FFmpeg issues with MoviePy
"""
import subprocess
import os
import sys
import tempfile

def test_ffmpeg_availability():
    """Test if FFmpeg is available and working"""
    print("🔍 Testing FFmpeg availability...")
    
    try:
        # Test ffmpeg command
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is installed and accessible")
            version_line = result.stdout.split('\n')[0]
            print(f"   Version: {version_line}")
            return True
        else:
            print("❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def test_ffprobe_availability():
    """Test if FFprobe is available"""
    print("\n🔍 Testing FFprobe availability...")
    
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFprobe is available")
            return True
        else:
            print("❌ FFprobe command failed")
            return False
    except FileNotFoundError:
        print("❌ FFprobe not found in PATH")
        return False
    except Exception as e:
        print(f"❌ FFprobe test error: {e}")
        return False

def configure_moviepy_ffmpeg():
    """Configure MoviePy to find FFmpeg"""
    print("\n🔧 Configuring MoviePy FFmpeg settings...")
    
    try:
        import moviepy.config as mp_config
        
        # Try to find FFmpeg executable
        try:
            result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                ffmpeg_path = result.stdout.strip().split('\n')[0]
                print(f"Found FFmpeg at: {ffmpeg_path}")
                
                # Set FFmpeg binary path
                mp_config.FFMPEG_BINARY = ffmpeg_path
                
                # Also set FFprobe if available
                ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
                if os.path.exists(ffprobe_path):
                    mp_config.FFPROBE_BINARY = ffprobe_path
                    print(f"Set FFprobe path: {ffprobe_path}")
                
                print("✅ MoviePy FFmpeg configuration complete")
                return True
        except Exception as e:
            print(f"Could not configure FFmpeg path: {e}")
            
    except ImportError:
        print("❌ Could not import MoviePy config")
        return False
    
    return False

def test_moviepy_video_export():
    """Test MoviePy video export functionality"""
    print("\n🎬 Testing MoviePy video export...")
    
    try:
        from moviepy.editor import ColorClip
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_export.mp4")
            
            # Create a simple test clip
            clip = ColorClip(size=(320, 240), color=(255, 0, 0), duration=1)
            
            # Try to export with different codec settings
            try:
                clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print("✅ MoviePy video export successful")
                    clip.close()
                    return True
                else:
                    print("❌ Video file was not created or is empty")
                    
            except Exception as e:
                print(f"❌ Video export failed: {e}")
                
                # Try with simpler settings
                try:
                    simple_output = os.path.join(temp_dir, "test_simple.mp4")
                    clip.write_videofile(
                        simple_output,
                        verbose=False,
                        logger=None
                    )
                    
                    if os.path.exists(simple_output):
                        print("✅ Simple video export successful")
                        clip.close()
                        return True
                        
                except Exception as e2:
                    print(f"❌ Simple export also failed: {e2}")
            
            clip.close()
            return False
            
    except Exception as e:
        print(f"❌ MoviePy test setup failed: {e}")
        return False

def provide_ffmpeg_installation_guide():
    """Provide FFmpeg installation instructions"""
    print("\n🛠️  FFmpeg Installation Guide for Windows:")
    print("=" * 50)
    
    print("\n📋 Option 1: Chocolatey (Recommended)")
    print("   choco install ffmpeg")
    
    print("\n📋 Option 2: Winget")
    print("   winget install Gyan.FFmpeg")
    
    print("\n📋 Option 3: Manual Installation")
    print("   1. Download from: https://www.gyan.dev/ffmpeg/builds/")
    print("   2. Download: ffmpeg-release-essentials.zip")
    print("   3. Extract to C:\\ffmpeg")
    print("   4. Add C:\\ffmpeg\\bin to your PATH environment variable")
    print("   5. Restart your terminal/IDE")
    
    print("\n📋 Option 4: Through conda (if using conda)")
    print("   conda install ffmpeg")

def create_simple_video_processor():
    """Create a simplified video processor that avoids the stdout issue"""
    print("\n🔧 Creating simplified video processor...")
    
    simplified_code = '''
def split_and_overlay_simple(input_path: str, output_prefix: str, max_segments: int = 5) -> List[str]:
    """
    Simplified video processing with better error handling
    Limits to first few segments to avoid long processing times
    """
    output_paths = []
    
    try:
        # Load the input video
        video = VideoFileClip(input_path)
        total_duration = video.duration
        
        # Limit segments for testing
        segment_duration = 30
        num_segments = min(int(total_duration // segment_duration), max_segments)
        
        print(f"Processing {num_segments} segments (limited for testing)")
        
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            # Extract segment
            segment = video.subclip(start_time, end_time)
            
            # Skip text overlay for now - just process the video
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            
            # Use simpler export settings
            segment.write_videofile(
                output_path,
                codec='libx264',
                preset='ultrafast',  # Faster encoding
                verbose=False,
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            output_paths.append(output_path)
            segment.close()
            
            print(f"Completed segment {i+1}/{num_segments}")
        
        video.close()
        return output_paths
        
    except Exception as e:
        # Clean up on error
        for path in output_paths:
            if os.path.exists(path):
                os.remove(path)
        raise Exception(f"Simplified video processing failed: {str(e)}")
'''
    
    # Write to a file
    with open('simplified_video_processor.py', 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Simplified Video Processor - Troubleshooting Version
Processes only a few segments with simpler settings
"""
import os
from typing import List
from moviepy.editor import VideoFileClip

''' + simplified_code)
    
    print("✅ Created simplified_video_processor.py")
    print("   This version processes fewer segments with simpler settings")

def main():
    """Main diagnostic function"""
    print("🔧 FFmpeg and MoviePy Diagnostic Tool")
    print("=" * 45)
    
    # Test FFmpeg
    ffmpeg_ok = test_ffmpeg_availability()
    ffprobe_ok = test_ffprobe_availability()
    
    if not ffmpeg_ok:
        provide_ffmpeg_installation_guide()
        return 1
    
    # Configure MoviePy
    config_ok = configure_moviepy_ffmpeg()
    
    # Test MoviePy export
    export_ok = test_moviepy_video_export()
    
    print(f"\n📋 Diagnostic Results:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   FFprobe: {'✅' if ffprobe_ok else '❌'}")
    print(f"   MoviePy Config: {'✅' if config_ok else '❌'}")
    print(f"   Video Export: {'✅' if export_ok else '❌'}")
    
    if export_ok:
        print("\n✅ FFmpeg and MoviePy are working correctly!")
        print("The 'stdout' error should be resolved.")
        print("\nTry running your video test again:")
        print('python test_video_processing.py "your_video.mp4"')
    else:
        print("\n⚠️  Video export issues detected")
        create_simple_video_processor()
        print("\nTry the simplified processor:")
        print("python simplified_video_processor.py")
    
    return 0 if export_ok else 1

if __name__ == "__main__":
    exit(main())
