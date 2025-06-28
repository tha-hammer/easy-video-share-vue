#!/usr/bin/env python3
"""
Simplified Video Processor - Troubleshooting Version
Processes only a few segments with simpler settings
"""
import os
from typing import List
from moviepy.editor import VideoFileClip


def split_and_overlay_simple(input_path: str, output_prefix: str, max_segments: int = 5) -> List[str]:
    """
    Simplified video processing with better error handling
    Limits to first few segments to avoid long processing times
    """
    output_paths = []
    
    try:
        # Load the input video
        video = VideoFileClip(input_path)
        total_duration = video.duration
        
        # Limit segments for testing
        segment_duration = 30
        num_segments = min(int(total_duration // segment_duration), max_segments)
        
        print(f"Processing {num_segments} segments (limited for testing)")
        
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            # Extract segment
            segment = video.subclip(start_time, end_time)
            
            # Skip text overlay for now - just process the video
            output_path = f"{output_prefix}_segment_{i+1:03d}.mp4"
            
            # Use simpler export settings
            segment.write_videofile(
                output_path,
                codec='libx264',
                preset='ultrafast',  # Faster encoding
                verbose=False,
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            output_paths.append(output_path)
            segment.close()
            
            print(f"Completed segment {i+1}/{num_segments}")
        
        video.close()
        return output_paths
        
    except Exception as e:
        # Clean up on error
        for path in output_paths:
            if os.path.exists(path):
                os.remove(path)
        raise Exception(f"Simplified video processing failed: {str(e)}")
