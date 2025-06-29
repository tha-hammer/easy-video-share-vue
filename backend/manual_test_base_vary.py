#!/usr/bin/env python3
"""
Manual Test Script - BASE_VARY Strategy
Tests LLM-powered text variations applied to video segments
"""

import sys
import os
import json
from celery.result import AsyncResult

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import process_video_task
from models import TextStrategy, TextInput, FixedCuttingParams

def test_base_vary_strategy():
    """Test BASE_VARY strategy with real Celery task dispatch"""
    
    # Replace with your actual S3 video key
    s3_video_key = "uploads/334ffc54-cb76-4f38-8c27-194911324caf/20250628_215659_test_video.mp4"
    job_id = "test-base-vary-001"
    
    # Configure text input for BASE_VARY
    text_input = TextInput(
        strategy=TextStrategy.BASE_VARY,
        base_text="Check out our new product launch!",
        context="sales pitch, excitement, call to action",
        unique_texts=None
    )
    
    # Configure cutting options
    cutting_options = FixedCuttingParams(
        type="fixed",
        duration_seconds=30
    )
    
    print(f"🚀 Dispatching BASE_VARY test task...")
    print(f"S3 Key: {s3_video_key}")
    print(f"Job ID: {job_id}")
    print(f"Base Text: {text_input.base_text}")
    print(f"Context: {text_input.context}")
    
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
    print("1. Watch Celery worker logs for LLM API calls")
    print("2. Check generated text variations in worker output")
    print("3. Inspect S3 output videos for correct text overlays")
    print("4. Verify each segment has different but related text")
    
    return result

if __name__ == "__main__":
    test_base_vary_strategy()
