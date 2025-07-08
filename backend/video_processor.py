"""
Unified Video Processing Module - Consolidated Implementation
Combines all video processing functionality from multiple files into a single, maintainable module.

This module consolidates:
- video_processing_utils.py (MoviePy-based)
- video_processing_utils_robust.py (FFmpeg-based)
- video_processing_utils_railway.py (Railway-optimized)
- video_processing_utils_helpers.py (enhanced features)
- robust_video_processor.py (simple version)
- simplified_video_processor.py (troubleshooting version)
"""

import os
import tempfile
import subprocess
import json
import random
import math
import shutil
from typing import List, Tuple, Optional, Dict, Any
import logging
from datetime import datetime, timezone

# Import models and dependencies
from models import (
    CuttingOptions, FixedCuttingParams, RandomCuttingParams,
    TextStrategy, TextInput, ProgressUpdate
)
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for advanced features
try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available, using FFmpeg-only mode")

try:
    from llm_service_vertexai import generate_text_variations
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM service not available, using basic text strategies")


class VideoProcessor:
    """
    Unified video processing class that handles all video operations
    with fallback mechanisms for different environments.
    """
    
    def __init__(self, use_ffmpeg_only: bool = False, environment: str = "production"):
        """
        Initialize video processor with configuration
        
        Args:
            use_ffmpeg_only: Force FFmpeg-only mode (bypasses MoviePy)
            environment: Processing environment ("production", "railway", "development")
        """
        self.use_ffmpeg_only = use_ffmpeg_only or not MOVIEPY_AVAILABLE
        self.environment = environment
        self.logger = logger
        
        # Environment-specific configurations
        self.config = self._get_environment_config()
        
        self.logger.info(f"VideoProcessor initialized: FFmpeg-only={self.use_ffmpeg_only}, Environment={environment}")
    
    def _get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        base_config = {
            "timeout_per_segment": 300,  # 5 minutes
            "default_fps": 24,
            "default_preset": "medium",
            "default_crf": 23,
            "min_font_size": 20,
            "max_font_size": 72,
            "font_size_divisor": 15,
            "text_position": (30, 30),  # x, y offset
            "text_color": "white",
            "text_background": "black@0.6",
            "text_border": "black",
            "text_border_width": 2,
            "box_border_width": 5
        }
        
        if self.environment == "railway":
            base_config.update({
                "timeout_per_segment": 180,  # 3 minutes for Railway
                "default_preset": "ultrafast",  # Faster encoding
                "default_crf": 28,  # Lower quality for speed
                "font_size_divisor": 20,  # Smaller text
            })
        elif self.environment == "development":
            base_config.update({
                "timeout_per_segment": 600,  # 10 minutes for development
                "default_preset": "fast",
                "default_crf": 25,
            })
        
        return base_config
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get comprehensive video information using FFprobe
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video information
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Extract format information
            format_info = data.get('format', {})
            duration = float(format_info.get('duration', 0))
            
            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("No video stream found")
            
            # Parse frame rate
            fps_str = video_stream.get('r_frame_rate', '24/1')
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den) if float(den) != 0 else 24
            else:
                fps = float(fps_str) if fps_str else 24
            
            return {
                'duration': duration,
                'fps': fps,
                'width': int(video_stream.get('width', 1920)),
                'height': int(video_stream.get('height', 1080)),
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'size': int(format_info.get('size', 0)),
                'format': os.path.splitext(video_path)[1].lower()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting video info for {video_path}: {str(e)}")
            # Return default values
            return {
                'duration': 0,
                'fps': self.config['default_fps'],
                'width': 1920,
                'height': 1080,
                'codec': 'unknown',
                'bitrate': 0,
                'size': 0,
                'format': '.mp4'
            }
    
    def validate_video_file(self, video_path: str) -> bool:
        """
        Validate that a file is a proper video file
        
        Args:
            video_path: Path to the video file
            
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
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and 'video' in result.stdout:
                self.logger.info(f"Video file validation successful: {video_path}")
                return True
            else:
                self.logger.error(f"Video file validation failed: {video_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating video file {video_path}: {str(e)}")
            return False
    
    def get_video_duration_from_s3(self, s3_bucket: str, s3_key: str) -> float:
        """
        Get video duration from S3 file using ffprobe with direct S3 access
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            float: Video duration in seconds
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
            
            self.logger.info(f"Getting video duration from S3: {s3_bucket}/{s3_key}")
            
            # Use ffprobe to get duration directly from S3 URL
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                s3_url
            ]
            
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
                
            self.logger.info(f"Video duration extracted: {duration} seconds")
            return duration
            
        except subprocess.TimeoutExpired:
            self.logger.error("ffprobe timed out while accessing S3 file")
            raise Exception("Timeout while analyzing video metadata")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ffprobe failed: {e.stderr}")
            if "404" in e.stderr or "No such file" in e.stderr:
                raise FileNotFoundError(f"Video file not found in S3: {s3_key}")
            raise Exception(f"Invalid video file format or corrupted: {e.stderr}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse ffprobe output: {e}")
            raise Exception("Failed to analyze video metadata")
        except Exception as e:
            self.logger.error(f"Error analyzing video duration: {e}")
            raise
    
    def calculate_segments(self, total_duration: float, cutting_options: CuttingOptions) -> Tuple[int, List[Tuple[float, float]]]:
        """
        Calculate video segments based on cutting options
        
        Args:
            total_duration: Total video duration in seconds
            cutting_options: Cutting parameters (fixed or random)
            
        Returns:
            Tuple[int, List[Tuple[float, float]]]: Number of segments and list of (start_time, end_time) pairs
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
                
            self.logger.info(f"Generated {len(segments)} fixed segments of {segment_duration}s each")
            
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
                
            self.logger.info(f"Generated {len(segments)} random segments (duration range: {min_duration}-{max_duration}s)")
        
        else:
            raise Exception(f"Unsupported cutting options type: {type(cutting_options)}")
        
        return len(segments), segments
    
    def prepare_text_overlays(
        self,
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
                    self.logger.warning("No base text provided for BASE_VARY strategy, using default")
                    return ["AI Generated Video"] * num_segments
                
                if not LLM_AVAILABLE:
                    self.logger.warning("LLM service not available, falling back to ONE_FOR_ALL")
                    base_text = text_input.base_text
                    return [base_text] * num_segments
                
                context = text_input.context if text_input else None
                self.logger.info(f"Generating {num_segments} variations for BASE_VARY strategy with context: {context}")
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
                    self.logger.warning("No unique texts provided for UNIQUE_FOR_ALL strategy, using default")
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
                self.logger.warning(f"Unknown text strategy: {text_strategy}, using default")
                return ["AI Generated Video"] * num_segments
                
        except Exception as e:
            self.logger.error(f"Error preparing text overlays: {str(e)}")
            return ["AI Generated Video"] * num_segments
    
    def escape_text_for_ffmpeg(self, text: str) -> str:
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
    
    def create_text_filter(self, text: str, video_info: Dict[str, Any], is_vertical: bool = False, position: str = "top_left", custom_xy: tuple = None) -> str:
        """
        Create FFmpeg text filter with multi-line support, safe zone, and configurable position.
        Args:
            text: Text to overlay (can contain newlines)
            video_info: Video information dictionary
            is_vertical: True if video is vertical orientation
            position: Overlay position (default: top_left)
            custom_xy: (x, y) tuple for custom position
        Returns:
            FFmpeg filter string with multi-line support
        """
        self.logger.info(f"Creating text filter for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        # Calculate font size based on video orientation and dimensions
        if is_vertical:
            font_size = width // self.config['font_size_divisor']
        else:
            font_size = height // self.config['font_size_divisor']
        font_size = max(font_size, self.config['min_font_size'])
        font_size = min(font_size, self.config['max_font_size'])
        # Use new multiline filter with safe zone and position
        try:
            result = self._create_multiline_drawtext_filter(
                text, font_size, None, is_vertical, position=position, custom_xy=custom_xy, video_info=video_info
            )
            self.logger.info(f"Multi-line filter created successfully: {result[:100]}{'...' if len(result) > 100 else ''}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to create multi-line filter: {e}")
            # Fallback to simple single-line filter
            escaped_text = self.escape_text_for_ffmpeg(text)
            fallback_filter = (
                f"drawtext=text='{escaped_text}':"
                f"fontcolor={self.config['text_color']}:"
                f"fontsize={font_size}:"
                f"x={self.config['text_position'][0]}:"
                f"y={self.config['text_position'][1]}:"
                f"box=1:"
                f"boxcolor={self.config['text_background']}"
            )
            self.logger.warning(f"Using fallback single-line filter: {fallback_filter[:100]}{'...' if len(fallback_filter) > 100 else ''}")
            return fallback_filter
    
    def _create_multiline_drawtext_filter(self, text: str, font_size: int, max_width: int, is_vertical: bool, position: str = "top_left", custom_xy: tuple = None, video_info: dict = None) -> str:
        """
        Create FFmpeg drawtext filter string for multi-line text with configurable position and safe zone logic.
        Args:
            text: Text to display (can contain newlines)
            font_size: Font size to use
            max_width: Maximum width for text wrapping (in characters)
            is_vertical: True if video is vertical, False if horizontal
            position: Overlay position ("top_left", "bottom_left", "top_right", "bottom_right", or "custom")
            custom_xy: (x, y) tuple for custom position
            video_info: Video info dict (required for dynamic scaling)
        Returns:
            FFmpeg filter string for multi-line text
        """
        import textwrap
        self.logger.info(f"Creating multi-line filter for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        self.logger.info(f"Font size: {font_size}, Max width: {max_width}, Is vertical: {is_vertical}")

        # --- Dynamic Rectangle Sizing and Padding (Safe Zone) ---
        if video_info is None:
            raise ValueError("video_info must be provided for safe zone calculation")
        video_width = video_info.get('width', 1080)
        video_height = video_info.get('height', 1920)
        # Reference: 212x420px rectangle, 8px padding, based on 1080x1920
        rect_width = int(video_width * (212 / 1080))
        rect_height = int(video_height * (420 / 1920))
        padding_x = int(video_width * (8 / 1080))
        padding_y = int(video_height * (8 / 1920))

        # --- Overlay Position Calculation ---
        if position == "top_left":
            base_x = padding_x
            base_y = padding_y
        elif position == "bottom_left":
            base_x = padding_x
            base_y = video_height - rect_height - padding_y
        elif position == "top_right":
            base_x = video_width - rect_width - padding_x
            base_y = padding_y
        elif position == "bottom_right":
            base_x = video_width - rect_width - padding_x
            base_y = video_height - rect_height - padding_y
        elif position == "custom" and custom_xy is not None:
            base_x, base_y = custom_xy
        else:
            # Default to top_left if unknown
            base_x = padding_x
            base_y = padding_y

        # --- Text Wrapping ---
        # Estimate max chars per line based on rect_width and font_size
        est_char_width = font_size * 0.6  # rough estimate
        max_chars_per_line = max(8, int(rect_width / est_char_width))
        lines = textwrap.wrap(text, width=max_chars_per_line)
        # Calculate line height
        line_height = int(font_size * 1.2)
        # Limit number of lines to fit in rect_height
        max_lines = max(1, rect_height // line_height)
        if len(lines) > max_lines:
            # Truncate and add ellipsis
            lines = lines[:max_lines]
            if len(lines) > 0:
                lines[-1] = lines[-1][:max_chars_per_line-3] + '...'
        # Remove empty lines
        original_count = len(lines)
        lines = [line.strip() for line in lines if line.strip()]
        if len(lines) != original_count:
            self.logger.info(f"Removed {original_count - len(lines)} empty lines")
        if not lines:
            self.logger.warning("No text lines after processing, returning empty filter")
            return "drawtext=text='':fontsize=1:x=0:y=0"  # Empty filter
        self.logger.info(f"Final wrapped lines: {len(lines)}")
        for i, line in enumerate(lines):
            self.logger.info(f"  Line {i+1}: '{line[:30]}{'...' if len(line) > 30 else ''}'")
        # --- Drawtext Filters ---
        filters = []
        for i, line in enumerate(lines):
            escaped_line = self.escape_text_for_ffmpeg(line)
            y_offset = base_y + (i * line_height)
            filter_str = (
                f"drawtext=text='{escaped_line}':"
                f"fontsize={font_size}:"
                f"fontcolor={self.config['text_color']}:"
                f"borderw={self.config['text_border_width']}:"
                f"bordercolor={self.config['text_border']}:"
                f"box=1:"
                f"boxcolor={self.config['text_background']}:"
                f"boxborderw=0:"
                f"x={base_x}:"
                f"y={y_offset}"
            )
            filters.append(filter_str)
            self.logger.info(f"Created filter {i+1}: {filter_str[:80]}{'...' if len(filter_str) > 80 else ''}")
        result = ','.join(filters)
        self.logger.info(f"Created {len(filters)} drawtext filters, combined length: {len(result)}")
        return result
    
    def process_segment_with_ffmpeg(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        text_overlay: str,
        position: str = "top_left",
        custom_xy: tuple = None
    ) -> bool:
        """
        Process a single video segment with precise timing and text overlay using FFmpeg
        Args:
            input_path: Path to input video
            output_path: Path for output video
            start_time: Start time in seconds
            end_time: End time in seconds
            text_overlay: Text to overlay on the video
            position: Overlay position (default: top_left)
            custom_xy: (x, y) tuple for custom position
        Returns:
            True if successful, False otherwise
        """
        try:
            video_info = self.get_video_info(input_path)
            is_vertical = video_info['height'] > video_info['width']
            text_filter = self.create_text_filter(text_overlay, video_info, is_vertical, position=position, custom_xy=custom_xy)
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(start_time),
                '-to', str(end_time),
                '-vf', text_filter,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', self.config['default_preset'],
                '-crf', str(self.config['default_crf']),
                '-y',
                output_path
            ]
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['timeout_per_segment']
            )
            if result.returncode == 0:
                self.logger.info(f"Successfully processed segment: {output_path}")
                return True
            else:
                self.logger.error(f"FFmpeg failed for segment {output_path}")
                self.logger.error(f"FFmpeg stderr: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"FFmpeg timeout for segment {output_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error processing segment {output_path}: {str(e)}")
            return False
    
    def split_video_with_precise_timing_and_dynamic_text(
        self,
        input_path: str, 
        output_prefix: str, 
        segment_times: List[Tuple[float, float]],
        text_strategy: TextStrategy,
        text_input: Optional[TextInput] = None,
        progress_callback: Optional[callable] = None,
        position: str = "top_left",
        custom_xy: tuple = None
    ) -> List[str]:
        """
        Split video with precise timing and apply dynamic text overlay based on strategy and position
        Args:
            input_path: Path to the input video file
            output_prefix: Prefix for output files
            segment_times: List of (start_time, end_time) tuples in seconds
            text_strategy: Text overlay strategy
            text_input: Text input data for the chosen strategy
            progress_callback: Optional callback for progress updates
            position: Overlay position (default: top_left)
            custom_xy: (x, y) tuple for custom position
        Returns:
            List of output file paths
        """
        output_paths = []
        try:
            self.logger.info(f"Processing video with {len(segment_times)} segments")
            self.logger.info(f"Text strategy: {text_strategy}")
            text_overlays = self.prepare_text_overlays(text_strategy, text_input, len(segment_times))
            for i, (start_time, end_time) in enumerate(segment_times):
                segment_duration = end_time - start_time
                text_overlay = text_overlays[i] if i < len(text_overlays) else "AI Generated Video"
                self.logger.info(f"Processing segment {i+1}/{len(segment_times)}: {start_time:.2f}s - {end_time:.2f}s ({segment_duration:.2f}s)")
                self.logger.info(f"Text overlay: '{text_overlay}'")
                if progress_callback:
                    progress_callback(i+1, len(segment_times), f"Processing segment {i+1}/{len(segment_times)}...")
                output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
                output_paths.append(output_path)
                success = self.process_segment_with_ffmpeg(
                    input_path=input_path,
                    output_path=output_path,
                    start_time=start_time,
                    end_time=end_time,
                    text_overlay=text_overlay,
                    position=position,
                    custom_xy=custom_xy
                )
                if not success:
                    self.logger.error(f"Failed to process segment {i+1}")
                    if output_path in output_paths:
                        output_paths.remove(output_path)
            self.logger.info(f"Successfully processed {len(output_paths)} segments")
            return output_paths
        except Exception as e:
            self.logger.error(f"Error in split_video_with_precise_timing_and_dynamic_text: {str(e)}")
            raise


# Global instance for backward compatibility
_default_processor = VideoProcessor()

# Backward compatibility functions
def get_video_info(video_path: str) -> Dict[str, Any]:
    """Backward compatibility function"""
    return _default_processor.get_video_info(video_path)

def validate_video_file(video_path: str) -> bool:
    """Backward compatibility function"""
    return _default_processor.validate_video_file(video_path)

def get_video_duration_from_s3(s3_bucket: str, s3_key: str) -> float:
    """Backward compatibility function"""
    return _default_processor.get_video_duration_from_s3(s3_bucket, s3_key)

def calculate_segments(total_duration: float, cutting_options: CuttingOptions) -> Tuple[int, List[Tuple[float, float]]]:
    """Backward compatibility function"""
    return _default_processor.calculate_segments(total_duration, cutting_options)

def split_video_with_precise_timing_and_dynamic_text(
    input_path: str, 
    output_prefix: str, 
    segment_times: List[Tuple[float, float]],
    text_strategy: TextStrategy,
    text_input: Optional[TextInput] = None,
    progress_callback: Optional[callable] = None,
    position: str = "top_left",
    custom_xy: tuple = None
) -> List[str]:
    """Backward compatibility function with position support"""
    return _default_processor.split_video_with_precise_timing_and_dynamic_text(
        input_path, output_prefix, segment_times, text_strategy, text_input, progress_callback, position, custom_xy
    )

def split_and_overlay_hardcoded(input_path: str, output_prefix: str) -> List[str]:
    """Backward compatibility function"""
    return _default_processor.split_and_overlay_hardcoded(input_path, output_prefix) 