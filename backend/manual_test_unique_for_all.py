#!/usr/bin/env python3
"""
Manual Test Script - UNIQUE_FOR_ALL Strategy
Tests user-provided unique text for each video segment
"""

import sys
import os
import json
from celery.result import AsyncResult

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_unique_for_all_strategy():
    """Test UNIQUE_FOR_ALL strategy with real Celery task dispatch"""
    
    # Replace with your actual S3 video key
    s3_video_key = "uploads/test-video.mp4"
    job_id = "test-unique-for-all-001"
    
    # Configure text input for UNIQUE_FOR_ALL
    unique_texts = [
        "🚀 Welcome to our product demo",
        "💡 Here's what makes us different",
        "🎯 Key features you'll love",
        "📞 Ready to get started?",
        "🎉 Join thousands of happy customers"
    ]
    
    text_input = TextInput(
        strategy=TextStrategy.UNIQUE_FOR_ALL,
        base_text=None,
        context=None,
        unique_texts=unique_texts
    )
    
    # Configure cutting options
    cutting_options = FixedCuttingParams(
        type="fixed",
        duration_seconds=25
    )
    
    print(f"🚀 Dispatching UNIQUE_FOR_ALL test task...")
    print(f"S3 Key: {s3_video_key}")
    print(f"Job ID: {job_id}")
    print(f"Unique texts ({len(unique_texts)}):")
    for i, text in enumerate(unique_texts, 1):
        print(f"  Segment {i}: {text}")
    
    # Dispatch the task
    result = process_video_task.delay(
        s3_input_key=s3_video_key,
        job_id=job_id,
        cutting_options=cutting_options.dict(),
        text_strategy=text_input.strategy.value,
        text_input=text_input.dict()
    )
    
    print(f"✅ Task dispatched with ID: {result.id}")
    print(f"📋 Task state: {result.state}")
    
    print("\n📖 Monitor instructions:")
    print("1. Watch Celery worker logs for segment processing")
    print("2. Verify no LLM calls (using provided texts)")
    print("3. Inspect S3 output videos for correct unique text overlays")
    print("4. Confirm each segment has its exact corresponding text")
    
    return result

if __name__ == "__main__":
    test_unique_for_all_strategy()
