#!/usr/bin/env python3
"""
Quick ImageMagick Test and Fix
Tests text rendering capabilities and provides solutions
"""
import sys
import subprocess

def test_imagemagick():
    """Test if ImageMagick is available"""
    print("🔍 Testing ImageMagick availability...")
    
    try:
        # Test ImageMagick command
        result = subprocess.run(['magick', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ImageMagick is installed and accessible")
            version_line = result.stdout.split('\n')[0]
            print(f"   Version: {version_line}")
            return True
        else:
            print("❌ ImageMagick command failed")
            return False
    except FileNotFoundError:
        print("❌ ImageMagick not found in PATH")
        return False
    except Exception as e:
        print(f"❌ ImageMagick test error: {e}")
        return False

def test_moviepy_text():
    """Test MoviePy text rendering"""
    print("\n🎬 Testing MoviePy text rendering...")
    
    try:
        from moviepy.editor import TextClip
        import tempfile
        import os
        
        # Test basic text clip creation
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_text.mp4")
            
            # Try the fallback method
            try:
                text_clip = TextClip(
                    "TEST TEXT",
                    fontsize=40,
                    color='white'
                ).set_duration(1)
                
                print("✅ Basic text rendering works")
                text_clip.close()
                return True
                
            except Exception as e:
                print(f"❌ Basic text rendering failed: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ MoviePy import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ MoviePy text test failed: {e}")
        return False

def install_pillow():
    """Install Pillow if missing"""
    print("\n📦 Installing Pillow for text rendering...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow==10.1.0'], 
                      check=True)
        print("✅ Pillow installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Pillow: {e}")
        return False

def provide_imagemagick_instructions():
    """Provide ImageMagick installation instructions"""
    print("\n🛠️  ImageMagick Installation Instructions:")
    print("=" * 50)
    print("1. Download ImageMagick for Windows:")
    print("   https://imagemagick.org/script/download.php#windows")
    print("   → Download: ImageMagick-7.x.x-Q16-HDRI-x64-dll.exe")
    print("")
    print("2. Install with these settings:")
    print("   ✅ Check 'Install development headers and libraries for C and C++'")
    print("   ✅ Check 'Add application directory to your system path'")
    print("")
    print("3. Restart your terminal/IDE after installation")
    print("")
    print("4. Test installation:")
    print("   magick -version")
    print("")
    print("Alternative: Use the updated video processing (with Pillow fallback)")

def main():
    """Main test function"""
    print("🎨 ImageMagick and Text Rendering Test")
    print("=" * 45)
    
    # Test ImageMagick
    imagemagick_ok = test_imagemagick()
    
    # Install Pillow if needed
    try:
        import PIL
        print("✅ Pillow is already installed")
    except ImportError:
        install_pillow()
    
    # Test MoviePy text
    moviepy_ok = test_moviepy_text()
    
    print("\n📋 Results Summary:")
    print(f"   ImageMagick: {'✅' if imagemagick_ok else '❌'}")
    print(f"   MoviePy Text: {'✅' if moviepy_ok else '❌'}")
    
    if not imagemagick_ok:
        provide_imagemagick_instructions()
    
    if moviepy_ok:
        print("\n✅ Video processing should work now!")
        print("   Try running the video test again:")
        print("   python test_video_processing.py \"your_video.mp4\"")
    else:
        print("\n❌ Text rendering still has issues")
        print("   Install ImageMagick for best results")

if __name__ == "__main__":
    main()
