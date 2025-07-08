"""
Manual test script for BASE_VARY strategy
Dispatch a video processing task with LLM-generated text variations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

# Example usage:
# 1. Upload a video to S3 and get the S3 key
# 2. Replace 'your-s3-key-here' with the actual S3 key
# 3. Run this script to test BASE_VARY strategy

def test_base_vary_processing():
    s3_key = "uploads/test_video.mp4"  # Replace with actual S3 key
    job_id = "test-base-vary-job"
    
    cutting_options = {
        "type": "fixed",
        "duration_seconds": 20
    }
    
    text_input = {
        "strategy": "base_vary",
        "base_text": "Unlock your potential today",
        "context": "motivational, self-improvement, action-oriented",
        "unique_texts": None
    }
    
    print("Dispatching BASE_VARY video processing task...")
    print(f"S3 Key: {s3_key}")
    print(f"Job ID: {job_id}")
    print(f"Text Input: {text_input}")
    
    # Dispatch the task
    task = process_video_task.delay(
        s3_input_key=s3_key,
        job_id=job_id,
        cutting_options=cutting_options,
        text_strategy="base_vary",
        text_input=text_input
    )
    
    print(f"Task dispatched with ID: {task.id}")
    print("Monitor worker logs for LLM generation and video processing")
    print("Check S3 for processed video segments with text variations")

if __name__ == "__main__":
    test_base_vary_processing()
