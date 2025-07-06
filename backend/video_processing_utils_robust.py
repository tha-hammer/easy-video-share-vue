"""
Updated Video Processing Utils - Sprint 2 Robust Version
Uses direct FFmpeg calls to avoid subprocess stdout issues
"""
import os
import tempfile
import subprocess
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def split_and_overlay_hardcoded_robust(input_path: str, output_prefix: str) -> List[str]:
    """
    Robust video splitting with hardcoded text overlay using direct FFmpeg
    Avoids MoviePy subprocess issues
    """
    output_paths = []
    
    try:
        # Get video info using FFprobe
        logger.info(f"Analyzing video: {input_path}")
        video_info = get_video_info_ffprobe(input_path)
        
        total_duration = video_info['duration']
        logger.info(f"Video duration: {total_duration:.2f} seconds")
        
        # Hardcoded parameters for Sprint 2
        segment_duration = 30  # 30 seconds per segment
        overlay_text = "AI Generated Video"  # Hardcoded text
        
        # Calculate number of segments
        num_segments = int(total_duration // segment_duration)
        if total_duration % segment_duration > 5:  # Include remainder if > 5 seconds
            num_segments += 1
            
        logger.info(f"Creating {num_segments} segments of {segment_duration} seconds each")
        
        # Process each segment using direct FFmpeg
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            logger.info(f"Processing segment {i+1}/{num_segments}: {start_time:.1f}s - {end_time:.1f}s")
            
            # Generate output path
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            output_paths.append(output_path)
            
            # Extract segment with text overlay using FFmpeg
            success = extract_segment_with_text_ffmpeg(
                input_path, output_path, start_time, end_time, overlay_text
            )
            
            if not success:
                logger.error(f"Failed to create segment {i+1}")
                raise Exception(f"Failed to create segment {i+1}")
            
            logger.info(f"Segment {i+1} completed successfully")
        
        logger.info(f"Video processing completed. Generated {len(output_paths)} segments")
        return output_paths
        
    except Exception as e:
        logger.error(f"Error in robust video processing: {str(e)}")
        # Clean up any partial files
        for path in output_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Cleaned up partial file: {path}")
                except:
                    pass
        raise Exception(f"Robust video processing failed: {str(e)}")

def extract_segment_with_text_ffmpeg(input_path: str, output_path: str, start_time: float, end_time: float, text: str) -> bool:
    """
    Extract video segment with text overlay using direct FFmpeg
    """
    try:
        duration = end_time - start_time
        
        # Get video info to calculate appropriate font size
        video_info = get_video_info_ffprobe(input_path)
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        
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
        
        logger.info(f"Video dimensions: {width}x{height} ({'vertical' if is_vertical else 'horizontal'}), calculated font size: {font_size}")
        
        # Escape text for FFmpeg
        escaped_text = text.replace("'", "\\'").replace(":", "\\:")
        
        # FFmpeg command with text overlay positioned at top-left
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files
            '-loglevel', 'error',  # Reduce verbosity
            '-i', input_path,
            '-ss', str(start_time),  # Start time
            '-t', str(duration),     # Duration
            '-vf', f'drawtext=text=\'{escaped_text}\':fontcolor=white:fontsize={font_size}:x=30:y=30:box=1:boxcolor=black@0.6:boxborderw=5:borderw=2:bordercolor=black',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ]
        
        logger.info(f"Running FFmpeg for segment: {os.path.basename(output_path)}")
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 minute timeout per segment
        )
        
        if result.returncode == 0:
            # Verify output file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # At least 1KB
                return True
            else:
                logger.error(f"FFmpeg succeeded but output file is missing or too small")
                if result.stderr:
                    logger.error(f"FFmpeg stderr: {result.stderr}")
                return False
        else:
            logger.error(f"FFmpeg failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"FFmpeg stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout for segment {output_path}")
        return False
    except Exception as e:
        logger.error(f"FFmpeg command failed: {str(e)}")
        return False

def get_video_info_ffprobe(video_path: str) -> dict:
    """
    Get video information using FFprobe
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
            
            if video_stream and 'format' in data:
                duration = float(data['format']['duration'])
                
                # Parse frame rate
                fps_str = video_stream.get('r_frame_rate', '24/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 24
                else:
                    fps = float(fps_str) if fps_str else 24
                
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                
                return {
                    'duration': duration,
                    'fps': fps,
                    'size': (width, height),
                    'format': os.path.splitext(video_path)[1].lower()
                }
        
        # Fallback values
        return {'duration': 0, 'fps': 24, 'size': (0, 0), 'format': '.mp4'}
        
    except Exception as e:
        logger.error(f"Error getting video info with FFprobe: {str(e)}")
        return {'duration': 0, 'fps': 24, 'size': (0, 0), 'format': '.mp4'}

def validate_video_file_robust(video_path: str) -> bool:
    """
    Validate video file using FFprobe
    """
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-show_format', video_path]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"Video validation failed: {str(e)}")
        return False

def get_video_info(video_path: str) -> dict:
    """
    Get video info - alias for FFprobe version
    """
    return get_video_info_ffprobe(video_path)

def validate_video_file(video_path: str) -> bool:
    """
    Validate video file - alias for robust version
    """
    return validate_video_file_robust(video_path)

# Keep the original function name for backwards compatibility
def split_and_overlay_hardcoded(input_path: str, output_prefix: str) -> List[str]:
    """
    Original function name - now uses robust implementation
    """
    return split_and_overlay_hardcoded_robust(input_path, output_prefix)
