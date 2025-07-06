"""
Railway-Optimized Video Processing Utils
Simplified FFmpeg commands with robust error handling for Railway deployment
"""
import os
import tempfile
import subprocess
import json
from typing import List, Tuple, Optional
import logging
from models import TextStrategy, TextInput, CuttingOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def split_video_with_precise_timing_and_dynamic_text(
    input_path: str, 
    output_prefix: str, 
    segment_times: List[Tuple[float, float]],
    text_strategy: TextStrategy,
    text_input: Optional[TextInput] = None,
    progress_callback: Optional[callable] = None
) -> List[str]:
    """
    Railway-optimized video splitting with simplified text overlay
    
    Args:
        input_path: Path to the input video file
        output_prefix: Prefix for output files
        segment_times: List of (start_time, end_time) tuples in seconds
        text_strategy: Text overlay strategy
        text_input: Text input data for the chosen strategy
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of output file paths
    """
    output_paths = []
    
    try:
        logger.info(f"Railway: Processing video with {len(segment_times)} segments")
        logger.info(f"Railway: Text strategy: {text_strategy}")
        
        # Prepare text overlays based on strategy
        text_overlays = prepare_text_overlays_simple(text_strategy, text_input, len(segment_times))
        
        # Process each segment with simplified FFmpeg
        for i, (start_time, end_time) in enumerate(segment_times):
            segment_duration = end_time - start_time
            text_overlay = text_overlays[i] if i < len(text_overlays) else "AI Generated Video"
            
            logger.info(f"Railway: Processing segment {i+1}/{len(segment_times)}: {start_time:.2f}s - {end_time:.2f}s ({segment_duration:.2f}s)")
            logger.info(f"Railway: Text overlay: '{text_overlay}'")
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i+1, len(segment_times), f"Processing segment {i+1}/{len(segment_times)}...")
            
            # Generate output path
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            output_paths.append(output_path)
            
            # Use simplified FFmpeg for Railway
            success = process_segment_railway_simple(
                input_path=input_path,
                output_path=output_path,
                start_time=start_time,
                end_time=end_time,
                text_overlay=text_overlay
            )
            
            if not success:
                logger.error(f"Railway: Failed to process segment {i+1}")
                # Remove from output paths if processing failed
                if output_path in output_paths:
                    output_paths.remove(output_path)
        
        logger.info(f"Railway: Successfully processed {len(output_paths)} segments")
        return output_paths
        
    except Exception as e:
        logger.error(f"Railway: Error in split_video_with_precise_timing_and_dynamic_text: {str(e)}")
        raise


def prepare_text_overlays_simple(
    text_strategy: TextStrategy, 
    text_input: Optional[TextInput], 
    num_segments: int
) -> List[str]:
    """
    Prepare text overlays using simplified approach for Railway
    """
    try:
        if text_strategy == TextStrategy.ONE_FOR_ALL:
            # Use same text for all segments
            base_text = "AI Generated Video"
            if text_input and text_input.base_text:
                base_text = text_input.base_text
            return [base_text] * num_segments
            
        elif text_strategy == TextStrategy.BASE_VARY:
            # Use base text with simple variations
            base_text = "AI Generated Video"
            if text_input and text_input.base_text:
                base_text = text_input.base_text
            
            variations = [
                f"{base_text}",
                f"{base_text} - Part 1",
                f"{base_text} - Part 2", 
                f"{base_text} - Part 3",
                f"{base_text} - Part 4",
                f"{base_text} - Part 5"
            ]
            
            # Cycle through variations
            result = []
            for i in range(num_segments):
                result.append(variations[i % len(variations)])
            return result
            
        elif text_strategy == TextStrategy.UNIQUE_FOR_ALL:
            # Use provided unique texts or fallback
            if text_input and text_input.segment_texts:
                texts = text_input.segment_texts
                # Ensure we have enough texts
                while len(texts) < num_segments:
                    texts.append(f"AI Generated Video - Part {len(texts) + 1}")
                return texts[:num_segments]
            else:
                # Fallback to numbered segments
                return [f"AI Generated Video - Part {i+1}" for i in range(num_segments)]
        
        else:
            # Default fallback
            return ["AI Generated Video"] * num_segments
            
    except Exception as e:
        logger.error(f"Railway: Error preparing text overlays: {str(e)}")
        return ["AI Generated Video"] * num_segments


def process_segment_railway_simple(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    text_overlay: str
) -> bool:
    """
    Process a single video segment with simplified FFmpeg for Railway
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        start_time: Start time in seconds
        end_time: End time in seconds
        text_overlay: Text to overlay on the video
        
    Returns:
        True if successful, False otherwise
    """
    try:
        duration = end_time - start_time
        
        # Get video info to calculate appropriate font size
        video_info = get_video_info_railway(input_path)
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        
        # Calculate simple font size
        font_size = min(width, height) // 20  # Simple calculation
        font_size = max(font_size, 20)  # Minimum size
        font_size = min(font_size, 60)  # Maximum size
        
        logger.info(f"Railway: Video dimensions: {width}x{height}, font size: {font_size}")
        
        # Escape text for FFmpeg (simplified)
        escaped_text = text_overlay.replace("'", "\\'").replace(":", "\\:")
        
        # Simplified FFmpeg command for Railway
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files
            '-loglevel', 'error',  # Reduce verbosity
            '-i', input_path,
            '-ss', str(start_time),  # Start time
            '-t', str(duration),     # Duration
            '-vf', f'drawtext=text=\'{escaped_text}\':fontcolor=white:fontsize={font_size}:x=30:y=30:box=1:boxcolor=black@0.5',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',  # Faster encoding for Railway
            '-crf', '28',            # Lower quality for faster processing
            output_path
        ]
        
        logger.info(f"Railway: Running FFmpeg for segment: {os.path.basename(output_path)}")
        logger.debug(f"Railway: FFmpeg command: {' '.join(cmd[:5])}... [rest hidden]")
        
        # Execute FFmpeg command with detailed error handling
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10-minute timeout per segment
        )
        
        if result.returncode == 0:
            # Verify output file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # At least 1KB
                logger.info(f"Railway: Successfully processed segment: {output_path}")
                return True
            else:
                logger.error(f"Railway: FFmpeg succeeded but output file is missing or too small")
                if result.stderr:
                    logger.error(f"Railway: FFmpeg stderr: {result.stderr}")
                return False
        else:
            logger.error(f"Railway: FFmpeg failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Railway: FFmpeg stderr: {result.stderr}")
            if result.stdout:
                logger.error(f"Railway: FFmpeg stdout: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Railway: FFmpeg timeout for segment {output_path}")
        return False
    except Exception as e:
        logger.error(f"Railway: Error processing segment {output_path}: {str(e)}")
        return False


def get_video_info_railway(file_path: str) -> dict:
    """
    Get video information using FFprobe with Railway-optimized error handling
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Dictionary with video information
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"Railway: FFprobe failed, using defaults: {result.stderr}")
            return {'duration': 0, 'width': 1920, 'height': 1080, 'codec': 'unknown'}
        
        data = json.loads(result.stdout)
        
        # Extract video duration
        duration = float(data.get('format', {}).get('duration', 0))
        
        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            logger.warning("Railway: No video stream found, using defaults")
            return {'duration': duration, 'width': 1920, 'height': 1080, 'codec': 'unknown'}
        
        return {
            'duration': duration,
            'width': int(video_stream.get('width', 1920)),
            'height': int(video_stream.get('height', 1080)),
            'codec': video_stream.get('codec_name', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Railway: Error getting video info: {str(e)}")
        return {'duration': 0, 'width': 1920, 'height': 1080, 'codec': 'unknown'}


def validate_video_file_railway(file_path: str) -> bool:
    """
    Validate video file using simplified approach for Railway
    
    Args:
        file_path: Path to the video file
        
    Returns:
        True if valid video, False otherwise
    """
    try:
        # Simple file existence check
        if not os.path.exists(file_path):
            logger.error(f"Railway: Video file does not exist: {file_path}")
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size < 1000:  # Less than 1KB
            logger.error(f"Railway: Video file too small: {file_size} bytes")
            return False
        
        # Try to get basic info
        video_info = get_video_info_railway(file_path)
        if video_info['duration'] <= 0:
            logger.error(f"Railway: Invalid video duration: {video_info['duration']}")
            return False
        
        logger.info(f"Railway: Video file validation successful: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Railway: Error validating video file {file_path}: {str(e)}")
        return False


# Backward compatibility functions
def get_video_info(video_path: str) -> dict:
    """Alias for Railway version"""
    return get_video_info_railway(video_path)


def validate_video_file(file_path: str) -> bool:
    """Alias for Railway version"""
    return validate_video_file_railway(file_path) 