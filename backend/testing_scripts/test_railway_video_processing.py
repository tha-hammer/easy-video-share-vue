#!/usr/bin/env python3
"""
Test Railway Video Processing
Tests the simplified video processing for Railway deployment
"""
import os
import tempfile
import subprocess
from video_processor import (
    split_video_with_precise_timing_and_dynamic_text,
    get_video_info_railway,
    validate_video_file_railway
)
from models import TextStrategy, TextInput

def test_ffmpeg_installation():
    """Test if FFmpeg is properly installed"""
    print("🔍 Testing FFmpeg installation...")
    
    try:
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

def test_ffprobe_installation():
    """Test if FFprobe is properly installed"""
    print("\n🔍 Testing FFprobe installation...")
    
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

def create_test_video():
    """Create a simple test video using FFmpeg"""
    print("\n🎬 Creating test video...")
    
    test_video_path = "test_video.mp4"
    
    try:
        # Create a simple 60-second test video
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-f', 'lavfi',
            '-i', 'testsrc=duration=60:size=1280x720:rate=30',
            '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=60',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',
            '-crf', '30',
            test_video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(test_video_path):
            print("✅ Test video created successfully")
            return test_video_path
        else:
            print("❌ Failed to create test video")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return None

def test_video_info():
    """Test video info extraction"""
    print("\n📊 Testing video info extraction...")
    
    test_video = create_test_video()
    if not test_video:
        print("❌ Cannot test video info without test video")
        return False
    
    try:
        info = get_video_info_railway(test_video)
        print(f"✅ Video info extracted:")
        print(f"   Duration: {info['duration']:.2f} seconds")
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   Codec: {info['codec']}")
        return True
    except Exception as e:
        print(f"❌ Error extracting video info: {e}")
        return False
    finally:
        # Clean up test video
        if os.path.exists(test_video):
            os.remove(test_video)

def test_video_validation():
    """Test video file validation"""
    print("\n✅ Testing video file validation...")
    
    test_video = create_test_video()
    if not test_video:
        print("❌ Cannot test validation without test video")
        return False
    
    try:
        is_valid = validate_video_file_railway(test_video)
        if is_valid:
            print("✅ Video validation successful")
            return True
        else:
            print("❌ Video validation failed")
            return False
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False
    finally:
        # Clean up test video
        if os.path.exists(test_video):
            os.remove(test_video)

def test_video_processing():
    """Test the main video processing function"""
    print("\n🎬 Testing video processing...")
    
    test_video = create_test_video()
    if not test_video:
        print("❌ Cannot test processing without test video")
        return False
    
    try:
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_prefix = os.path.join(temp_dir, "processed_test")
            
            # Define segment times (3 segments of 20 seconds each)
            segment_times = [(0, 20), (20, 40), (40, 60)]
            
            # Test with different text strategies
            text_strategies = [
                TextStrategy.ONE_FOR_ALL,
                TextStrategy.BASE_VARY,
                TextStrategy.UNIQUE_FOR_ALL
            ]
            
            for strategy in text_strategies:
                print(f"\n   Testing strategy: {strategy}")
                
                # Prepare text input
                text_input = None
                if strategy == TextStrategy.BASE_VARY:
                    text_input = TextInput(base_text="Test Video")
                elif strategy == TextStrategy.UNIQUE_FOR_ALL:
                    text_input = TextInput(segment_texts=[
                        "Test Video - Part 1",
                        "Test Video - Part 2", 
                        "Test Video - Part 3"
                    ])
                
                # Process video
                output_paths = split_video_with_precise_timing_and_dynamic_text(
                    input_path=test_video,
                    output_prefix=output_prefix,
                    segment_times=segment_times,
                    text_strategy=strategy,
                    text_input=text_input
                )
                
                if output_paths and len(output_paths) == 3:
                    print(f"   ✅ Strategy {strategy} successful: {len(output_paths)} segments created")
                    
                    # Verify output files exist and have content
                    for i, path in enumerate(output_paths):
                        if os.path.exists(path) and os.path.getsize(path) > 1000:
                            print(f"      ✅ Segment {i+1}: {os.path.basename(path)} ({os.path.getsize(path)} bytes)")
                        else:
                            print(f"      ❌ Segment {i+1}: File missing or too small")
                            return False
                else:
                    print(f"   ❌ Strategy {strategy} failed: {len(output_paths) if output_paths else 0} segments")
                    return False
        
        print("✅ All video processing tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error during video processing test: {e}")
        return False
    finally:
        # Clean up test video
        if os.path.exists(test_video):
            os.remove(test_video)

def main():
    """Run all tests"""
    print("🚀 Railway Video Processing Test Suite")
    print("=" * 50)
    
    tests = [
        ("FFmpeg Installation", test_ffmpeg_installation),
        ("FFprobe Installation", test_ffprobe_installation),
        ("Video Info Extraction", test_video_info),
        ("Video Validation", test_video_validation),
        ("Video Processing", test_video_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Railway video processing is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 