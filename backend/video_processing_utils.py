"""
Video processing utilities using MoviePy for Sprint 2
Handles video splitting and text overlay operations
"""
import os
import tempfile
import random
import math
import subprocess
import json
from typing import List, Tuple
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import logging
from models import CuttingOptions, FixedCuttingParams, RandomCuttingParams
from s3_utils import download_file_from_s3
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure MoviePy to use a simpler text method
import moviepy.config as mp_config

# Try to configure ImageMagick path on Windows
def configure_imagemagick():
    """Configure ImageMagick for MoviePy on Windows"""
    try:
        # Try to find ImageMagick
        result = subprocess.run(['where', 'magick'], capture_output=True, text=True)
        if result.returncode == 0:
            magick_path = result.stdout.strip().split('\n')[0]
            imagemagick_dir = os.path.dirname(magick_path)
            magick_exe = os.path.join(imagemagick_dir, "magick.exe")
            
            if os.path.exists(magick_exe):
                mp_config.IMAGEMAGICK_BINARY = magick_exe
                logger.info(f"Configured ImageMagick binary: {magick_exe}")
                return True
    except Exception as e:
        logger.warning(f"Could not configure ImageMagick: {e}")
    
    return False

# Configure ImageMagick on import
IMAGEMAGICK_CONFIGURED = configure_imagemagick()

# Test if ImageMagick is working
try:
    from moviepy.video.tools.drawing import color_gradient
    IMAGEMAGICK_AVAILABLE = True
    logger.info("ImageMagick is available for advanced text features")
except Exception as e:
    IMAGEMAGICK_AVAILABLE = False
    logger.warning(f"ImageMagick not available, using basic text rendering: {e}")


def split_and_overlay_hardcoded(input_path: str, output_prefix: str) -> List[str]:
    """
    Split video into hardcoded 30-second segments and add hardcoded text overlay
    
    Args:
        input_path: Local path to the input video file
        output_prefix: Prefix for output filenames (without extension)
    
    Returns:
        List of paths to the generated video segments
    """
    output_paths = []
    
    try:
        # Load the input video
        logger.info(f"Loading video from: {input_path}")
        video = VideoFileClip(input_path)
        
        # Get video duration
        total_duration = video.duration
        logger.info(f"Video duration: {total_duration:.2f} seconds")
        
        # Hardcoded parameters for Sprint 2
        segment_duration = 30  # 30 seconds per segment
        overlay_text = "AI Generated Video"  # Hardcoded text
        
        # Calculate number of segments
        num_segments = int(total_duration // segment_duration)
        if total_duration % segment_duration > 5:  # Include remainder if > 5 seconds
            num_segments += 1
            
        logger.info(f"Creating {num_segments} segments of {segment_duration} seconds each")
        
        # Process each segment
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            logger.info(f"Processing segment {i+1}/{num_segments}: {start_time:.1f}s - {end_time:.1f}s")
            
            # Extract segment
            segment = video.subclip(start_time, end_time)
            
            # Create text overlay with fallback for missing ImageMagick
            try:
                if IMAGEMAGICK_AVAILABLE:
                    # Use full-featured text with stroke
                    text_clip = TextClip(
                        overlay_text,
                        fontsize=50,
                        color='white',
                        stroke_color='black',
                        stroke_width=2,
                        font='Arial-Bold'
                    ).set_position(('center', 'bottom')).set_duration(segment.duration)
                else:
                    # Use basic text without stroke (ImageMagick not available)
                    text_clip = TextClip(
                        overlay_text,
                        fontsize=50,
                        color='white',
                        method='caption',
                        size=(segment.w, None)
                    ).set_position(('center', 'bottom')).set_duration(segment.duration)
                
                # Ensure text clip has the same FPS as the video
                if segment.fps:
                    text_clip.fps = segment.fps
                else:
                    text_clip.fps = video.fps if video.fps else 24
                    
            except Exception as text_error:
                logger.warning(f"Text overlay failed, using simple method: {text_error}")
                # Fallback: very basic text
                text_clip = TextClip(
                    overlay_text,
                    fontsize=40,
                    color='white'
                ).set_position(('center', 'bottom')).set_duration(segment.duration)
                
                # Set FPS for fallback text too
                text_clip.fps = video.fps if video.fps else 24
            
            # Composite video with text overlay
            final_clip = CompositeVideoClip([segment, text_clip])
            
            # Generate output path
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            output_paths.append(output_path)
            
            # Write the segment to file with robust error handling and FPS fix
            logger.info(f"Writing segment to: {output_path}")
            try:
                # Ensure the clip has FPS set
                if final_clip.fps is None:
                    final_clip.fps = video.fps if video.fps else 24  # Default to 24 fps
                
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    fps=final_clip.fps,  # Explicitly set FPS
                    preset='medium',  # Balanced speed/quality
                    verbose=False,
                    logger=None,  # Suppress MoviePy logging
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    ffmpeg_params=['-hide_banner', '-loglevel', 'error']  # Reduce FFmpeg output
                )
            except Exception as write_error:
                logger.error(f"Failed to write segment {i+1}: {write_error}")
                # Try with simpler settings
                try:
                    logger.info(f"Retrying segment {i+1} with simpler settings...")
                    final_clip.write_videofile(
                        output_path,
                        fps=24,  # Force 24 fps
                        verbose=False,
                        logger=None,
                        preset='ultrafast'
                    )
                except Exception as retry_error:
                    logger.error(f"Retry also failed for segment {i+1}: {retry_error}")
                    raise Exception(f"Could not write video segment: {retry_error}")
            
            # Clean up clips to free memory
            segment.close()
            text_clip.close()
            final_clip.close()
            
            logger.info(f"Segment {i+1} completed successfully")
        
        # Close the original video
        video.close()
        
        logger.info(f"Video processing completed. Generated {len(output_paths)} segments")
        return output_paths
        
    except Exception as e:
        logger.error(f"Error in video processing: {str(e)}")
        # Clean up any partial files
        for path in output_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Cleaned up partial file: {path}")
                except:
                    pass
        raise Exception(f"Video processing failed: {str(e)}")


def get_video_info(video_path: str) -> dict:
    """
    Get basic information about a video file
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with video information (duration, fps, resolution, etc.)
    """
    try:
        with VideoFileClip(video_path) as video:
            return {
                'duration': video.duration,
                'fps': video.fps,
                'size': video.size,  # (width, height)
                'format': os.path.splitext(video_path)[1].lower()
            }
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")


def validate_video_file(video_path: str) -> bool:
    """
    Validate that a file is a readable video
    
    Args:
        video_path: Path to the video file
        
    Returns:
        True if valid video file, False otherwise
    """
    try:
        with VideoFileClip(video_path) as video:
            # Try to read first frame
            _ = video.get_frame(0)
            return video.duration > 0
    except Exception as e:
        logger.warning(f"Video validation failed: {str(e)}")
        return False


def get_video_duration_from_s3(s3_bucket: str, s3_key: str) -> float:
    """
    Get video duration from S3 file using ffprobe with direct S3 access
    
    Args:
        s3_bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        float: Video duration in seconds
        
    Raises:
        Exception: If file cannot be accessed or is not a valid video
    """
    try:
        # Generate presigned URL for S3 access
        from s3_utils import generate_presigned_url
        s3_url = generate_presigned_url(
            bucket_name=s3_bucket,
            object_key=s3_key,
            client_method='get_object',
            content_type=None,
            expiration=300  # 5 minutes
        )
        
        logger.info(f"Getting video duration from S3: {s3_bucket}/{s3_key}")
        
        # Use ffprobe to get duration directly from S3 URL
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            s3_url
        ]
        
        logger.info(f"Running ffprobe command: {' '.join(cmd[:3])}... [URL hidden]")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        probe_data = json.loads(result.stdout)
        
        # Extract duration from format or video stream
        duration = None
        
        # Try to get duration from format first
        if 'format' in probe_data and 'duration' in probe_data['format']:
            duration = float(probe_data['format']['duration'])
        
        # Fallback to video stream duration
        if duration is None:
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and 'duration' in stream:
                    duration = float(stream['duration'])
                    break
        
        if duration is None:
            raise Exception("Could not extract video duration from file")
            
        logger.info(f"Video duration extracted: {duration} seconds")
        return duration
        
    except subprocess.TimeoutExpired:
        logger.error("ffprobe timed out while accessing S3 file")
        raise Exception("Timeout while analyzing video metadata")
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed: {e.stderr}")
        if "404" in e.stderr or "No such file" in e.stderr:
            raise FileNotFoundError(f"Video file not found in S3: {s3_key}")
        raise Exception(f"Invalid video file format or corrupted: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe output: {e}")
        raise Exception("Failed to analyze video metadata")
    except Exception as e:
        logger.error(f"Error analyzing video duration: {e}")
        raise



def calculate_segments(total_duration: float, cutting_options: CuttingOptions) -> Tuple[int, List[Tuple[float, float]]]:
    """
    Calculate video segments based on cutting options
    
    Args:
        total_duration: Total video duration in seconds
        cutting_options: Cutting parameters (fixed or random)
        
    Returns:
        Tuple[int, List[Tuple[float, float]]]: Number of segments and list of (start_time, end_time) pairs
        
    Raises:
        Exception: If video is too short for the specified cutting parameters
    """
    segments = []
    
    if isinstance(cutting_options, FixedCuttingParams):
        # Fixed duration segments
        segment_duration = cutting_options.duration_seconds
        
        if segment_duration > total_duration:
            raise Exception(f"Video is too short ({total_duration:.1f}s) to generate segments with duration {segment_duration}s")
            
        current_time = 0.0
        while current_time < total_duration:
            end_time = min(current_time + segment_duration, total_duration)
            segments.append((current_time, end_time))
            current_time = end_time
            
        logger.info(f"Generated {len(segments)} fixed segments of {segment_duration}s each")
        
    elif isinstance(cutting_options, RandomCuttingParams):
        # Random duration segments
        min_duration = cutting_options.min_duration
        max_duration = cutting_options.max_duration
        
        if min_duration > total_duration:
            raise Exception(f"Video is too short ({total_duration:.1f}s) for minimum segment duration {min_duration}s")
            
        current_time = 0.0
        while current_time < total_duration:
            # Generate random duration for this segment
            remaining_time = total_duration - current_time
            
            # Ensure we don't exceed remaining time
            max_possible = min(max_duration, remaining_time)
            min_possible = min(min_duration, remaining_time)
            
            if min_possible > max_possible:
                # Last segment is shorter than min_duration, include it anyway
                segment_duration = remaining_time
            else:
                segment_duration = random.uniform(min_possible, max_possible)
                
            end_time = current_time + segment_duration
            segments.append((current_time, end_time))
            current_time = end_time
            
        logger.info(f"Generated {len(segments)} random segments (duration range: {min_duration}-{max_duration}s)")
    
    else:
        raise Exception(f"Unsupported cutting options type: {type(cutting_options)}")
    
    return len(segments), segments
