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
            
            # Create text overlay
            text_clip = TextClip(
                overlay_text,
                fontsize=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold'
            ).set_position(('center', 'bottom')).set_duration(segment.duration)
            
            # Composite video with text overlay
            final_clip = CompositeVideoClip([segment, text_clip])
            
            # Generate output path
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            output_paths.append(output_path)
            
            # Write the segment to file
            logger.info(f"Writing segment to: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None  # Suppress MoviePy logging
            )
            
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
