#!/usr/bin/env python3
"""
Test script for Easy Video Share Backend API
Tests all Sprint 1 endpoints locally
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_VIDEO_PATH = None  # We'll create a dummy file for testing

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_initiate_upload():
    """Test initiate upload endpoint"""
    print("\n🔍 Testing initiate upload endpoint...")
    try:
        payload = {
            "filename": "test_video.mp4",
            "content_type": "video/mp4",
            "file_size": 1024000  # 1MB
        }

        response = requests.post(f"{BASE_URL}/upload/initiate", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Initiate upload failed: {e}")
        return None

def test_complete_upload(s3_key, job_id):
    """Test complete upload endpoint"""
    print("\n🔍 Testing complete upload endpoint...")
    try:
        payload = {
            "s3_key": s3_key,
            "job_id": job_id
        }

        response = requests.post(f"{BASE_URL}/upload/complete", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Complete upload failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Easy Video Share Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)

    # Test health endpoint
    if not test_health_endpoint():
        print("❌ Health check failed. Make sure the backend is running on localhost:8000")
        return

    print("✅ Health check passed!")

    # Test initiate upload
    upload_data = test_initiate_upload()
    if not upload_data:
        print("❌ Initiate upload test failed")
        return

    print("✅ Initiate upload test passed!")

    # Test complete upload
    if test_complete_upload(upload_data["s3_key"], upload_data["job_id"]):
        print("✅ Complete upload test passed!")
    else:
        print("❌ Complete upload test failed")
        return

    print("\n🎉 All tests passed! Backend is working correctly.")
    print("\nNext steps:")
    print("1. Configure your AWS credentials in backend/.env")
    print("2. Start Redis server: redis-server")
    print("3. Start Celery worker: celery -A backend.tasks worker --loglevel=info")

if __name__ == "__main__":
    main()
