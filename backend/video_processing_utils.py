"""
Video processing utilities using MoviePy for Sprint 2
Handles video splitting and text overlay operations
"""
import os
import tempfile
from typing import List
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure MoviePy to use a simpler text method
import moviepy.config as mp_config

# Try to configure ImageMagick path on Windows
import subprocess
import sys
import os

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
