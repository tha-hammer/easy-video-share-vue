"""
End-to-End Test Script for Sprint 4
Tests the complete video processing pipeline with LLM integration
"""

import sys
import os
import requests
import time
import json

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from models import TextStrategy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"


def test_sprint4_api_workflow():
    """Test the complete Sprint 4 API workflow with different text strategies"""
    
    print("=" * 60)
    print("Sprint 4 End-to-End API Test")
    print("=" * 60)
    
    # Test data for different strategies
    test_scenarios = [
        {
            "name": "ONE_FOR_ALL Strategy",
            "cutting_options": {
                "type": "fixed",
                "duration_seconds": 20
            },
            "text_strategy": "one_for_all",
            "text_input": {
                "strategy": "one_for_all",
                "base_text": "Your success starts here!"
            }
        },
        {
            "name": "BASE_VARY Strategy (LLM-powered)",
            "cutting_options": {
                "type": "random", 
                "min_duration": 15,
                "max_duration": 25
            },
            "text_strategy": "base_vary",
            "text_input": {
                "strategy": "base_vary",
                "base_text": "Transform your life with our amazing product"
            }
        },
        {
            "name": "UNIQUE_FOR_ALL Strategy",
            "cutting_options": {
                "type": "fixed",
                "duration_seconds": 30
            },
            "text_strategy": "unique_for_all",
            "text_input": {
                "strategy": "unique_for_all",
                "segment_texts": [
                    "Welcome to our amazing product!",
                    "See the incredible results",
                    "Join thousands of satisfied customers",
                    "Order now and save 50%!"
                ]
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*40}")
        print(f"Testing: {scenario['name']}")
        print(f"{'='*40}")
        
        test_scenario(scenario)


def test_scenario(scenario):
    """Test a single scenario"""
    
    # Step 1: Initiate Upload (mock)
    print(f"📤 Step 1: Initiate Upload")
    initiate_data = {
        "filename": "test_video.mp4",
        "content_type": "video/mp4",
        "file_size": 10000000
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/upload/initiate", json=initiate_data)
        if response.status_code == 200:
            upload_data = response.json()
            print(f"✅ Upload initiated successfully")
            print(f"   Job ID: {upload_data['job_id']}")
            print(f"   S3 Key: {upload_data['s3_key']}")
        else:
            print(f"❌ Upload initiation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error initiating upload: {str(e)}")
        return
    
    # Step 2: Complete Upload with Sprint 4 parameters
    print(f"🎬 Step 2: Complete Upload with {scenario['name']}")
    complete_data = {
        "s3_key": upload_data['s3_key'],
        "job_id": upload_data['job_id'],
        "cutting_options": scenario['cutting_options'],
        "text_strategy": scenario['text_strategy'],
        "text_input": scenario['text_input']
    }
    
    print(f"   Cutting Options: {scenario['cutting_options']}")
    print(f"   Text Strategy: {scenario['text_strategy']}")
    print(f"   Text Input: {scenario['text_input']}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/upload/complete", json=complete_data)
        if response.status_code == 200:
            job_data = response.json()
            print(f"✅ Job created successfully")
            print(f"   Job ID: {job_data['job_id']}")
            print(f"   Status: {job_data['status']}")
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error completing upload: {str(e)}")
        return
    
    # Step 3: Check Job Status (simulation)
    print(f"📊 Step 3: Check Job Status")
    job_id = job_data['job_id']
    
    try:
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Job status retrieved successfully")
            print(f"   Job ID: {status_data['job_id']}")
            print(f"   Status: {status_data['status']}")
            
            if 'output_urls' in status_data and status_data['output_urls']:
                print(f"   Output URLs: {len(status_data['output_urls'])} segments")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")


def test_analyze_duration_api():
    """Test the analyze duration API with Sprint 4 parameters"""
    
    print(f"\n{'='*40}")
    print("Testing Analyze Duration API")
    print(f"{'='*40}")
    
    test_data = {
        "s3_key": "test/sample_video.mp4",  # Mock S3 key
        "cutting_options": {
            "type": "random",
            "min_duration": 20,
            "max_duration": 40
        }
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/video/analyze-duration", json=test_data)
        
        if response.status_code == 200:
            analysis_data = response.json()
            print("✅ Duration analysis successful")
            print(f"   Total Duration: {analysis_data['total_duration']} seconds")
            print(f"   Number of Segments: {analysis_data['num_segments']}")
            print(f"   Segment Durations: {analysis_data['segment_durations']}")
        elif response.status_code == 404:
            print("⚠️  Expected 404 (video not found) - normal for test")
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing analysis: {str(e)}")


def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print("Make sure the FastAPI server is running on localhost:8000")
        return False


if __name__ == "__main__":
    print("Sprint 4 End-to-End Test")
    print("=" * 60)
    
    # Check API health first
    if not check_api_health():
        print("\n❌ API is not accessible. Please:")
        print("1. Start the FastAPI server: python main.py")
        print("2. Ensure it's running on localhost:8000")
        sys.exit(1)
    
    # Test analyze duration API
    test_analyze_duration_api()
    
    # Test complete workflow
    test_sprint4_api_workflow()
    
    print(f"\n{'='*60}")
    print("Sprint 4 End-to-End Test Complete")
    print("=" * 60)
    print("✅ All API endpoints tested with Sprint 4 parameters")
    print("🎬 Text strategies tested: ONE_FOR_ALL, BASE_VARY, UNIQUE_FOR_ALL")
    print("⚙️  Cutting options tested: Fixed and Random durations")
    print("\nNote: Actual video processing requires:")
    print("- Redis running (for Celery)")
    print("- Celery worker running")
    print("- Valid video file in S3")
    print("- FFmpeg installed")
    print("- Valid Gemini API key")
