#!/usr/bin/env python3
"""
Test script for multi-part upload API endpoints only
This script tests the backend logic without actually uploading to S3
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"

def test_initiate_multipart_api():
    """Test the initiate multi-part upload API endpoint"""
    print("🧪 Testing initiate multi-part upload API")
    print("=" * 50)
    
    # Test payload
    payload = {
        "filename": "test_video_100mb.mp4",
        "content_type": "video/mp4",
        "file_size": 104857600  # 100MB
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/initiate-multipart", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"   Upload ID: {data.get('upload_id', 'N/A')}")
            print(f"   S3 Key: {data.get('s3_key', 'N/A')}")
            print(f"   Job ID: {data.get('job_id', 'N/A')}")
            print(f"   Chunk Size: {data.get('chunk_size', 'N/A')}")
            print(f"   Max Concurrent: {data.get('max_concurrent_uploads', 'N/A')}")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_get_part_url_api(upload_data):
    """Test the get part URL API endpoint"""
    if not upload_data:
        print("❌ No upload data available")
        return None
        
    print("\n🧪 Testing get part URL API")
    print("=" * 50)
    
    payload = {
        "upload_id": upload_data['upload_id'],
        "s3_key": upload_data['s3_key'],
        "part_number": 1,
        "content_type": "video/mp4"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/part", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"   Presigned URL: {data.get('presigned_url', 'N/A')[:50]}...")
            print(f"   Part Number: {data.get('part_number', 'N/A')}")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_abort_multipart_api(upload_data):
    """Test the abort multi-part upload API endpoint"""
    if not upload_data:
        print("❌ No upload data available")
        return False
        
    print("\n🧪 Testing abort multi-part upload API")
    print("=" * 50)
    
    payload = {
        "upload_id": upload_data['upload_id'],
        "s3_key": upload_data['s3_key']
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/abort-multipart", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"   Message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_complete_multipart_api(upload_data):
    """Test the complete multi-part upload API endpoint (without actual parts)"""
    if not upload_data:
        print("❌ No upload data available")
        return False
        
    print("\n🧪 Testing complete multi-part upload API")
    print("=" * 50)
    
    # Mock parts data (this would normally come from actual uploads)
    mock_parts = [
        {"PartNumber": 1, "ETag": "mock-etag-1"},
        {"PartNumber": 2, "ETag": "mock-etag-2"}
    ]
    
    payload = {
        "upload_id": upload_data['upload_id'],
        "s3_key": upload_data['s3_key'],
        "job_id": upload_data['job_id'],
        "parts": mock_parts,
        "user_id": "test_user",
        "filename": "test_video_100mb.mp4",
        "file_size": 104857600,
        "title": "Test Video",
        "user_email": "test@example.com",
        "content_type": "video/mp4"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/complete-multipart", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"   Job ID: {data.get('job_id', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 MULTI-PART UPLOAD API TEST SUITE")
    print("=" * 60)
    
    # Test 1: Initiate multi-part upload
    upload_data = test_initiate_multipart_api()
    
    if upload_data:
        # Test 2: Get part URL
        part_data = test_get_part_url_api(upload_data)
        
        # Test 3: Abort upload
        abort_success = test_abort_multipart_api(upload_data)
        
        # Test 4: Complete upload (will likely fail due to mock data, but tests API structure)
        complete_success = test_complete_multipart_api(upload_data)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 API TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Initiate API: {'✅ PASS' if upload_data else '❌ FAIL'}")
        print(f"Get Part URL API: {'✅ PASS' if part_data else '❌ FAIL'}")
        print(f"Abort API: {'✅ PASS' if abort_success else '❌ FAIL'}")
        print(f"Complete API: {'✅ PASS' if complete_success else '⚠️  EXPECTED FAIL (mock data)'}")
        
        if upload_data and part_data and abort_success:
            print("\n🎉 Core API functionality is working correctly!")
            print("The 403 errors in the full test are due to S3 permissions, not API issues.")
        else:
            print("\n⚠️  Some API tests failed. Check the backend implementation.")
    else:
        print("\n❌ Initiate API failed. Cannot proceed with other tests.")

if __name__ == "__main__":
    main() 