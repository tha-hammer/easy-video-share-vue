#!/usr/bin/env python3
"""
MoviePy ImageMagick Configuration Fix
Helps configure MoviePy to properly find ImageMagick on Windows
"""
import os
import subprocess
import sys

def find_imagemagick_path():
    """Find the ImageMagick installation path"""
    print("🔍 Searching for ImageMagick installation...")
    
    # Common installation paths
    common_paths = [
        r"C:\Program Files\ImageMagick-7.*",
        r"C:\Program Files (x86)\ImageMagick-7.*",
        r"C:\ImageMagick",
        r"C:\tools\ImageMagick"
    ]
    
    # Try to find via command
    try:
        result = subprocess.run(['where', 'magick'], capture_output=True, text=True)
        if result.returncode == 0:
            magick_path = result.stdout.strip().split('\n')[0]
            imagemagick_dir = os.path.dirname(magick_path)
            print(f"✅ Found ImageMagick via PATH: {imagemagick_dir}")
            return imagemagick_dir
    except Exception as e:
        print(f"Could not find via PATH: {e}")
    
    # Try common paths
    import glob
    for pattern in common_paths:
        matches = glob.glob(pattern)
        if matches:
            path = matches[0]
            print(f"✅ Found ImageMagick at: {path}")
            return path
    
    print("❌ Could not automatically find ImageMagick")
    return None

def configure_moviepy_imagemagick(imagemagick_path):
    """Configure MoviePy to use ImageMagick"""
    print(f"🔧 Configuring MoviePy to use ImageMagick at: {imagemagick_path}")
    
    try:
        # Import moviepy and configure
        import moviepy.config as mp_config
        
        # Set the ImageMagick binary path
        magick_exe = os.path.join(imagemagick_path, "magick.exe")
        if os.path.exists(magick_exe):
            mp_config.IMAGEMAGICK_BINARY = magick_exe
            print(f"✅ Set IMAGEMAGICK_BINARY to: {magick_exe}")
        else:
            print(f"❌ magick.exe not found at: {magick_exe}")
            return False
        
        # Test the configuration
        from moviepy.editor import TextClip
        test_clip = TextClip("TEST", fontsize=20, color='white').set_duration(1)
        test_clip.close()
        print("✅ MoviePy ImageMagick configuration successful!")
        return True
        
    except Exception as e:
        print(f"❌ MoviePy configuration failed: {e}")
        return False

def create_moviepy_config_file(imagemagick_path):
    """Create a moviepy config file"""
    print("📝 Creating MoviePy configuration file...")
    
    try:
        import moviepy
        moviepy_dir = os.path.dirname(moviepy.__file__)
        config_file = os.path.join(moviepy_dir, "config_defaults.py")
        
        magick_exe = os.path.join(imagemagick_path, "magick.exe")
        
        # Read existing config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Update or add ImageMagick path
        if 'IMAGEMAGICK_BINARY' in content:
            # Replace existing
            import re
            content = re.sub(
                r'IMAGEMAGICK_BINARY\s*=.*',
                f'IMAGEMAGICK_BINARY = r"{magick_exe}"',
                content
            )
        else:
            # Add new
            content += f'\nIMAGEMAGICK_BINARY = r"{magick_exe}"\n'
        
        # Write config
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created config file: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")
        return False

def test_text_rendering():
    """Test text rendering after configuration"""
    print("\n🎬 Testing text rendering after configuration...")
    
    try:
        from moviepy.editor import TextClip
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with stroke (ImageMagick feature)
            try:
                text_clip = TextClip(
                    "AI Generated Video",
                    fontsize=50,
                    color='white',
                    stroke_color='black',
                    stroke_width=2
                ).set_duration(1)
                
                print("✅ Advanced text rendering (with stroke) works!")
                text_clip.close()
                return True
                
            except Exception as e:
                print(f"❌ Advanced text rendering failed: {e}")
                
                # Try basic text
                try:
                    text_clip = TextClip(
                        "AI Generated Video",
                        fontsize=50,
                        color='white'
                    ).set_duration(1)
                    
                    print("✅ Basic text rendering works!")
                    text_clip.close()
                    return True
                    
                except Exception as e2:
                    print(f"❌ Basic text rendering also failed: {e2}")
                    return False
                
    except Exception as e:
        print(f"❌ Text rendering test failed: {e}")
        return False

def main():
    """Main configuration function"""
    print("🎨 MoviePy ImageMagick Configuration Tool")
    print("=" * 45)
    
    # Find ImageMagick
    imagemagick_path = find_imagemagick_path()
    if not imagemagick_path:
        print("\n❌ Cannot configure MoviePy without finding ImageMagick")
        print("Please ensure ImageMagick is properly installed")
        return 1
    
    # Configure MoviePy
    config_success = configure_moviepy_imagemagick(imagemagick_path)
    
    if not config_success:
        # Try creating config file
        config_success = create_moviepy_config_file(imagemagick_path)
    
    # Test the configuration
    if config_success:
        test_success = test_text_rendering()
        
        if test_success:
            print("\n✅ MoviePy ImageMagick configuration complete!")
            print("Video processing with text overlays should now work.")
            print("\nTry running your video test again:")
            print('python test_video_processing.py "your_video.mp4"')
            return 0
        else:
            print("\n⚠️  Configuration may be incomplete")
    
    print("\n❌ MoviePy ImageMagick configuration failed")
    print("\nAlternative: Use the updated video processing with Pillow fallback")
    return 1

if __name__ == "__main__":
    exit(main())
