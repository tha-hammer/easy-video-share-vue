"""
Enhanced Video Processing Utils - Sprint 4 Implementation
Precise segment timing and dynamic text overlay with LLM integration
"""

import os
import tempfile
import subprocess
import shutil
import json
from typing import List, Tuple, Optional
import logging
from models import TextStrategy, TextInput, CuttingOptions
from llm_service_vertexai import generate_text_variations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_video_info(video_path: str) -> dict:
    """
    Get video information including dimensions using FFprobe
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary containing video information (width, height, duration, etc.)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'v:0',  # First video stream
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                return {
                    'width': int(stream.get('width', 1920)),
                    'height': int(stream.get('height', 1080)),
                    'duration': float(stream.get('duration', 0)),
                    'fps': eval(stream.get('r_frame_rate', '30/1'))
                }
        
        logger.warning(f"Could not get video info for {video_path}, using defaults")
        return {'width': 1920, 'height': 1080, 'duration': 0, 'fps': 30}
        
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {'width': 1920, 'height': 1080, 'duration': 0, 'fps': 30}


def split_video_with_precise_timing_and_dynamic_text(
    input_path: str, 
    output_prefix: str, 
    segment_times: List[Tuple[float, float]],
    text_strategy: TextStrategy,
    text_input: Optional[TextInput] = None,
    progress_callback: Optional[callable] = None
) -> List[str]:
    """
    Split video with precise timing and apply dynamic text overlay based on strategy
    
    Args:
        input_path: Path to the input video file
        output_prefix: Prefix for output files
        segment_times: List of (start_time, end_time) tuples in seconds
        text_strategy: Text overlay strategy
        text_input: Text input data for the chosen strategy
        
    Returns:
        List of output file paths
    """
    output_paths = []
    
    try:
        logger.info(f"Processing video with {len(segment_times)} segments")
        logger.info(f"Text strategy: {text_strategy}")
        
        # Prepare text overlays based on strategy
        text_overlays = prepare_text_overlays(text_strategy, text_input, len(segment_times))
        
        # Process each segment with precise timing
        for i, (start_time, end_time) in enumerate(segment_times):
            segment_duration = end_time - start_time
            text_overlay = text_overlays[i] if i < len(text_overlays) else "AI Generated Video"
            
            logger.info(f"Processing segment {i+1}/{len(segment_times)}: {start_time:.2f}s - {end_time:.2f}s ({segment_duration:.2f}s)")
            logger.info(f"Text overlay: '{text_overlay}'")
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i+1, len(segment_times), f"Processing segment {i+1}/{len(segment_times)}...")
            
            # Generate output path
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            output_paths.append(output_path)
            
            # Use FFmpeg for precise cutting and text overlay
            success = process_segment_with_ffmpeg(
                input_path=input_path,
                output_path=output_path,
                start_time=start_time,
                end_time=end_time,
                text_overlay=text_overlay
            )
            
            if not success:
                logger.error(f"Failed to process segment {i+1}")
                # Remove from output paths if processing failed
                if output_path in output_paths:
                    output_paths.remove(output_path)
        
        logger.info(f"Successfully processed {len(output_paths)} segments")
        return output_paths
        
    except Exception as e:
        logger.error(f"Error in split_video_with_precise_timing_and_dynamic_text: {str(e)}")
        raise


def prepare_text_overlays(
    text_strategy: TextStrategy, 
    text_input: Optional[TextInput], 
    num_segments: int
) -> List[str]:
    """
    Prepare text overlays based on the selected strategy
    
    Args:
        text_strategy: Text overlay strategy
        text_input: Text input data
        num_segments: Number of segments to generate text for
        
    Returns:
        List of text overlays for each segment
    """
    try:
        if text_strategy == TextStrategy.ONE_FOR_ALL:
            # Single text for all segments
            base_text = text_input.base_text if text_input and text_input.base_text else "AI Generated Video"
            return [base_text] * num_segments
            
        elif text_strategy == TextStrategy.BASE_VARY:
            # Generate variations using LLM with context
            if not text_input or not text_input.base_text:
                logger.warning("No base text provided for BASE_VARY strategy, using default")
                return ["AI Generated Video"] * num_segments
            
            context = text_input.context if text_input else None
            logger.info(f"Generating {num_segments} variations for BASE_VARY strategy with context: {context}")
            variations = generate_text_variations(text_input.base_text, num_segments, context)
            
            # Ensure we have exactly the right number of variations
            if len(variations) < num_segments:
                # Pad with the base text if we don't have enough
                while len(variations) < num_segments:
                    variations.append(text_input.base_text)
            elif len(variations) > num_segments:
                # Trim if we have too many
                variations = variations[:num_segments]
            
            return variations
            
        elif text_strategy == TextStrategy.UNIQUE_FOR_ALL:
            # Use user-provided unique text for each segment
            if not text_input or not text_input.unique_texts:
                logger.warning("No unique texts provided for UNIQUE_FOR_ALL strategy, using default")
                return ["AI Generated Video"] * num_segments
            
            unique_texts = text_input.unique_texts
            
            # Ensure we have text for each segment
            if len(unique_texts) < num_segments:
                # Pad with the last provided text or default
                last_text = unique_texts[-1] if unique_texts else "AI Generated Video"
                while len(unique_texts) < num_segments:
                    unique_texts.append(last_text)
            elif len(unique_texts) > num_segments:
                # Trim if we have too many
                unique_texts = unique_texts[:num_segments]
            
            return unique_texts
            
        else:
            logger.warning(f"Unknown text strategy: {text_strategy}, using default")
            return ["AI Generated Video"] * num_segments
            
    except Exception as e:
        logger.error(f"Error preparing text overlays: {str(e)}")
        return ["AI Generated Video"] * num_segments


def process_segment_with_ffmpeg(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    text_overlay: str
) -> bool:
    """
    Process a single video segment with precise timing and text overlay using FFmpeg
    
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
        # Escape special characters in text for FFmpeg
        escaped_text = escape_text_for_ffmpeg(text_overlay)
        
        # Get video dimensions to calculate appropriate font size
        video_info = get_video_info(input_path)
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        
        # Calculate font size as a percentage of the smaller dimension
        # This ensures text is readable but not overwhelming
        font_size = min(width, height) // 20  # Much smaller divisor for very small text
        font_size = max(font_size, 16)  # Minimum font size for readability
        font_size = min(font_size, 18)  # Maximum font size to prevent huge text
        
        logger.info(f"Video dimensions: {width}x{height}, calculated font size: {font_size}")
        print(f"DEBUG: Video dimensions: {width}x{height}, calculated font size: {font_size}")
        
        # Create multi-line text filter
        max_chars_per_line = width // (font_size // 2)  # Estimate characters per line based on font size
        max_chars_per_line = max(max_chars_per_line, 9)  # Minimum characters per line
        max_chars_per_line = min(max_chars_per_line, 30)  # Maximum characters per line
        
        drawtext_filter = create_multiline_drawtext_filter(text_overlay, font_size, max_chars_per_line)
        
        # Build FFmpeg command for precise cutting with multi-line text overlay
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_time),  # Start time
            '-to', str(end_time),    # End time
            '-vf', drawtext_filter,
            '-c:v', 'libx264',       # Video codec
            '-c:a', 'aac',           # Audio codec
            '-preset', 'medium',      # Encoding preset for balance of speed and quality
            '-crf', '23',            # Constant Rate Factor for quality
            '-y',                    # Overwrite output file
            output_path
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Execute FFmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5-minute timeout per segment
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully processed segment: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg failed for segment {output_path}")
            logger.error(f"FFmpeg stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout for segment {output_path}")
        return False
    except Exception as e:
        logger.error(f"Error processing segment {output_path}: {str(e)}")
        return False


def escape_text_for_ffmpeg(text: str) -> str:
    """
    Escape special characters in text for FFmpeg drawtext filter
    
    Args:
        text: Original text
        
    Returns:
        Escaped text safe for FFmpeg
    """
    # Escape characters that have special meaning in FFmpeg drawtext
    escaped = text.replace("'", "\\'")  # Escape single quotes
    escaped = escaped.replace(":", "\\:")  # Escape colons
    escaped = escaped.replace("\\", "\\\\")  # Escape backslashes
    escaped = escaped.replace("%", "\\%")  # Escape percent signs
    
    return escaped


def validate_video_file(file_path: str) -> bool:
    """
    Validate that a file is a proper video file using FFprobe
    
    Args:
        file_path: Path to the video file
        
    Returns:
        True if valid video, False otherwise
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'csv=p=0',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and 'video' in result.stdout:
            logger.info(f"Video file validation successful: {file_path}")
            return True
        else:
            logger.error(f"Video file validation failed: {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating video file {file_path}: {str(e)}")
        return False


def get_video_info_ffprobe(file_path: str) -> dict:
    """
    Get video information using FFprobe
    
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
            raise Exception(f"FFprobe failed: {result.stderr}")
        
        import json
        data = json.loads(result.stdout)
        
        # Extract video duration
        duration = float(data['format']['duration'])
        
        # Find video stream
        video_stream = None
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise Exception("No video stream found")
        
        return {
            'duration': duration,
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {str(e)}")
        raise


def create_multiline_drawtext_filter(text: str, font_size: int, max_width: int) -> str:
    """
    Create FFmpeg drawtext filter string for multi-line text
    
    Args:
        text: Text to display (can contain newlines)
        font_size: Font size to use
        max_width: Maximum width for text wrapping (in characters)
        
    Returns:
        FFmpeg filter string for multi-line text
    """
    import textwrap
    
    # Split text by explicit newlines first
    lines = text.split('\n')
    
    # Then wrap long lines
    wrapped_lines = []
    for line in lines:
        if len(line) > max_width:
            # Wrap long lines
            wrapped = textwrap.fill(line, width=max_width).split('\n')
            wrapped_lines.extend(wrapped)
        else:
            wrapped_lines.append(line)
    
    # Remove empty lines
    wrapped_lines = [line.strip() for line in wrapped_lines if line.strip()]
    
    if not wrapped_lines:
        return "drawtext=text='':fontsize=1:x=0:y=0"  # Empty filter
    
    # Create multiple drawtext filters
    filters = []
    line_height = font_size + 4  # Add some padding between lines
    
    total_lines = len(wrapped_lines)
    for i, line in enumerate(wrapped_lines):
        escaped_line = escape_text_for_ffmpeg(line)
        y_offset = 30 + ((total_lines - i - 1) * line_height)  # First line at top, stack downward
        filter_str = f"drawtext=text='{escaped_line}':fontsize={font_size}:fontcolor=white:borderw=1:bordercolor=black:x=20:y=h-th-{y_offset}"
        filters.append(filter_str)
    
    # Combine filters with comma separation
    return ','.join(filters)
