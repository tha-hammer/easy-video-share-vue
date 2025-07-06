#!/usr/bin/env python3
"""
Robust Video Processing - Alternative Implementation
Uses different approach to avoid the stdout subprocess issue
"""
import os
import tempfile
import subprocess
from typing import List
from moviepy.editor import VideoFileClip
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_video_with_ffmpeg_direct(input_path: str, output_prefix: str) -> List[str]:
    """
    Process video using direct FFmpeg calls instead of MoviePy for writing
    This avoids the subprocess stdout issue
    """
    output_paths = []
    
    try:
        # Use MoviePy only to analyze the video
        logger.info(f"Analyzing video: {input_path}")
        with VideoFileClip(input_path) as video:
            total_duration = video.duration
            fps = video.fps or 24
            width, height = video.size
        
        logger.info(f"Video info: {total_duration:.2f}s, {fps}fps, {width}x{height}")
        
        # Calculate segments
        segment_duration = 30
        num_segments = int(total_duration // segment_duration)
        if total_duration % segment_duration > 5:
            num_segments += 1
        
        logger.info(f"Will create {num_segments} segments")
        
        # Process each segment using direct FFmpeg
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            
            logger.info(f"Processing segment {i+1}/{num_segments}: {start_time:.1f}s - {end_time:.1f}s")
            
            # Use FFmpeg directly to extract and add text
            success = extract_segment_with_ffmpeg(
                input_path, output_path, start_time, end_time
            )
            
            if success:
                output_paths.append(output_path)
                logger.info(f"Segment {i+1} completed successfully")
            else:
                logger.error(f"Failed to create segment {i+1}")
                break
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Error in direct FFmpeg processing: {str(e)}")
        # Clean up any partial files
        for path in output_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        raise Exception(f"Direct FFmpeg processing failed: {str(e)}")

def extract_segment_with_ffmpeg(input_path: str, output_path: str, start_time: float, end_time: float) -> bool:
    """
    Extract video segment using direct FFmpeg command
    Includes text overlay using FFmpeg's drawtext filter with dynamic font size
    """
    try:
        duration = end_time - start_time
        
        # Get video info to calculate appropriate font size
        video_info = get_video_info_simple(input_path)
        width, height = video_info['size']
        
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
        
        logger.debug(f"Video resolution: {width}x{height} ({'vertical' if is_vertical else 'horizontal'}), calculated font size: {font_size}")
        
        # FFmpeg command with dynamic font size and top-left positioning
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files
            '-i', input_path,
            '-ss', str(start_time),  # Start time
            '-t', str(duration),     # Duration
            '-vf', f'drawtext=text=\'AI Generated Video\':fontcolor=white:fontsize={font_size}:x=30:y=30:box=1:boxcolor=black@0.6:boxborderw=5:borderw=2:bordercolor=black',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ]
        
        # Run FFmpeg with proper error handling
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 minute timeout per segment
        )
        
        if result.returncode == 0:
            # Verify output file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                logger.error(f"FFmpeg succeeded but output file is missing or empty")
                return False
        else:
            logger.error(f"FFmpeg failed with return code {result.returncode}")
            logger.error(f"FFmpeg stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout for segment {output_path}")
        return False
    except Exception as e:
        logger.error(f"FFmpeg command failed: {str(e)}")
        return False

def validate_video_file_simple(video_path: str) -> bool:
    """
    Simple video validation using FFprobe
    """
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-show_format', video_path]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception:
        return False

def get_video_info_simple(video_path: str) -> dict:
    """
    Get video info using FFprobe directly
    """
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                duration = float(data['format']['duration'])
                fps = eval(video_stream.get('r_frame_rate', '24/1'))
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                
                return {
                    'duration': duration,
                    'fps': fps,
                    'size': (width, height),
                    'format': os.path.splitext(video_path)[1].lower()
                }
        
        return {'duration': 0, 'fps': 24, 'size': (0, 0), 'format': '.mp4'}
        
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {'duration': 0, 'fps': 24, 'size': (0, 0), 'format': '.mp4'}

# Test function
def test_robust_processing(video_path: str):
    """Test the robust video processing"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    try:
        print("🎬 Robust Video Processing Test")
        print("=" * 40)
        
        # Validate video
        print("Validating video file...")
        if not validate_video_file_simple(video_path):
            print("❌ Invalid video file")
            return False
        print("✅ Video file is valid")
        
        # Get video info
        print("Getting video information...")
        video_info = get_video_info_simple(video_path)
        print(f"Duration: {video_info['duration']:.2f} seconds")
        print(f"FPS: {video_info['fps']}")
        print(f"Resolution: {video_info['size'][0]}x{video_info['size'][1]}")
        
        # Process first 3 segments only for testing
        with tempfile.TemporaryDirectory(prefix="robust_video_test_") as temp_dir:
            output_prefix = os.path.join(temp_dir, "robust_output")
            
            print("Processing first 3 segments with direct FFmpeg...")
            
            # Modify to process only first 90 seconds (3 segments) for testing
            test_input = video_path
            if video_info['duration'] > 90:
                # Create a 90-second test clip first
                test_input = os.path.join(temp_dir, "test_clip.mp4")
                cmd = [
                    'ffmpeg', '-y', '-i', video_path,
                    '-t', '90', '-c', 'copy', test_input
                ]
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    test_input = video_path  # Fall back to full video
            
            output_paths = process_video_with_ffmpeg_direct(test_input, output_prefix)
            
            print(f"✅ Robust processing completed!")
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
            print("✅ Robust video processing test successful!")
            return True
            
    except Exception as e:
        print(f"❌ Robust processing test failed: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python robust_video_processor.py <path_to_video_file>")
        print("Example: python robust_video_processor.py sample_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    success = test_robust_processing(video_path)
    
    if success:
        print("\n✅ Robust video processing works!")
        print("This approach bypasses the MoviePy subprocess issues.")
    else:
        print("\n❌ Robust processing failed.")
        sys.exit(1)
