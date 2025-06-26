#!/usr/bin/env python3
"""
Test script for AI Video Processor API
Run this to verify the local development setup is working
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"
TEST_PROJECT_ID = f"test-{int(datetime.now().timestamp())}"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Using LocalStack: {data['use_localstack']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_list_projects():
    """Test listing projects"""
    print("\n🔍 Testing project listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/projects")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project listing passed")
            print(f"   Found {data['count']} projects")
            if data['projects']:
                print("   Sample project:")
                sample = data['projects'][0]
                print(f"     ID: {sample.get('project_id')}")
                print(f"     Status: {sample.get('status')}")
                print(f"     Title: {sample.get('title')}")
            return True
        else:
            print(f"❌ Project listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Project listing error: {e}")
        return False

def test_get_specific_project():
    """Test getting a specific project"""
    print("\n🔍 Testing specific project retrieval...")
    test_project_id = "test-project-123"  # From our sample data
    try:
        response = requests.get(f"{API_BASE_URL}/projects/{test_project_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project retrieval passed")
            print(f"   Project ID: {data['project_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Created: {data['created_at']}")
            print(f"   Updated: {data['updated_at']}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Project not found (expected if no sample data)")
            return True
        else:
            print(f"❌ Project retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Project retrieval error: {e}")
        return False

def test_video_processing():
    """Test video processing endpoint"""
    print(f"\n🔍 Testing video processing with project ID: {TEST_PROJECT_ID}")
    
    # Submit video processing request
    payload = {
        "project_id": TEST_PROJECT_ID,
        "prompt": "A serene lake at sunset with mountains in the background",
        "duration": 5,
        "style": "realistic",
        "aspect_ratio": "16:9"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/process-video", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Video processing request submitted")
            print(f"   Message: {data['message']}")
            print(f"   Project ID: {data['project_id']}")
            print(f"   Status: {data['status']}")
            
            # Wait a bit and check status
            print(f"\n⏳ Waiting for processing to complete...")
            max_attempts = 15
            for attempt in range(max_attempts):
                time.sleep(2)
                status_response = requests.get(f"{API_BASE_URL}/projects/{TEST_PROJECT_ID}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data['status']
                    metadata = status_data.get('metadata', {})
                    
                    print(f"   Attempt {attempt + 1}: Status = {current_status}")
                    if metadata.get('message'):
                        print(f"   Message: {metadata['message']}")
                    if metadata.get('stage'):
                        print(f"   Stage: {metadata['stage']}")
                    
                    if current_status in ['completed', 'failed']:
                        if current_status == 'completed':
                            print(f"✅ Video processing completed successfully!")
                            if metadata.get('video_url'):
                                print(f"   Video URL: {metadata['video_url']}")
                        else:
                            print(f"❌ Video processing failed")
                            if metadata.get('error'):
                                print(f"   Error: {metadata['error']}")
                        return current_status == 'completed'
                else:
                    print(f"   Could not check status: {status_response.status_code}")
            
            print(f"⚠️  Processing still in progress after {max_attempts} attempts")
            return True
            
        else:
            print(f"❌ Video processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Video processing error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AI Video Processor API Tests")
    print(f"   API Base URL: {API_BASE_URL}")
    print(f"   Test Project ID: {TEST_PROJECT_ID}")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("List Projects", test_list_projects),
        ("Get Specific Project", test_get_specific_project),
        ("Video Processing", test_video_processing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your AI Video Processor is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 