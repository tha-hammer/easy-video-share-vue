"""
Manual test script for UNIQUE_FOR_ALL strategy
Dispatch a video processing task with user-provided unique texts
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_unique_for_all_processing():
    s3_key = "uploads/test_video.mp4"  # Replace with actual S3 key
    job_id = "test-unique-for-all-job"
    
    cutting_options = {
        "type": "fixed",
        "duration_seconds": 25
    }
    
    text_input = {
        "strategy": "unique_for_all",
        "base_text": None,
        "context": None,
        "unique_texts": [
            "Welcome to our product showcase!",
            "See how it transforms your workflow",
            "Join 10,000+ satisfied customers",
            "Order now with 30% off!"
        ]
    }
    
    print("Dispatching UNIQUE_FOR_ALL video processing task...")
    print(f"S3 Key: {s3_key}")
    print(f"Job ID: {job_id}")
    print(f"Unique Texts: {text_input['unique_texts']}")
    
    # Dispatch the task
    task = process_video_task.delay(
        s3_input_key=s3_key,
        job_id=job_id,
        cutting_options=cutting_options,
        text_strategy="unique_for_all",
        text_input=text_input
    )
    
    print(f"Task dispatched with ID: {task.id}")
    print("Monitor worker logs for text application")
    print("Check S3 - each segment should have its specific text overlay")

if __name__ == "__main__":
    test_unique_for_all_processing()
