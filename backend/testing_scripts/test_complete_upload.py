#!/usr/bin/env python3
"""
Complete end-to-end test with actual file upload to S3
"""

import requests
import json
import tempfile
import os

# Configuration
BASE_URL = "http://localhost:8000/api"

def create_test_video_file():
    """Create a small test video file"""
    # Create a simple text file as a mock video for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', mode='w') as f:
        f.write("Mock video content for testing S3 upload functionality")
        return f.name

def test_complete_upload_flow():
    """Test the complete upload flow with actual file upload"""
    print("🚀 Testing Complete Upload Flow with Real File")
    print("=" * 50)
    
    # Step 1: Create test file
    test_file_path = create_test_video_file()
    file_size = os.path.getsize(test_file_path)
    print(f"📁 Created test file: {test_file_path} ({file_size} bytes)")
    
    try:
        # Step 2: Initiate upload
        print("\n🔍 Step 1: Initiating upload...")
        initiate_payload = {
            "filename": "test_upload.mp4",
            "content_type": "video/mp4",
            "file_size": file_size
        }
        
        response = requests.post(f"{BASE_URL}/upload/initiate", json=initiate_payload)
        if response.status_code != 200:
            print(f"❌ Initiate upload failed: {response.text}")
            return False
            
        upload_data = response.json()
        print(f"✅ Upload initiated. Job ID: {upload_data['job_id']}")
        print(f"📍 S3 Key: {upload_data['s3_key']}")
        
        # Step 3: Upload file to S3 using presigned URL
        print("\n🔍 Step 2: Uploading file to S3...")
        with open(test_file_path, 'rb') as file_data:
            s3_response = requests.put(
                upload_data['presigned_url'],
                data=file_data,
                headers={'Content-Type': 'video/mp4'}
            )
        
        if s3_response.status_code == 200:
            print("✅ File uploaded to S3 successfully!")
        else:
            print(f"❌ S3 upload failed: {s3_response.status_code} - {s3_response.text}")
            return False
        
        # Step 4: Complete upload and start processing
        print("\n🔍 Step 3: Completing upload and starting processing...")
        complete_payload = {
            "s3_key": upload_data['s3_key'],
            "job_id": upload_data['job_id']
        }
        
        response = requests.post(f"{BASE_URL}/upload/complete", json=complete_payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload completed! Status: {result['status']}")
            print(f"📋 Message: {result['message']}")
        else:
            print(f"❌ Complete upload failed: {response.text}")
            return False
        
        print(f"\n🎉 Complete upload flow successful!")
        print(f"📍 Check AWS S3 Console for file at: {upload_data['s3_key']}")
        print(f"🔗 S3 URL: https://easy-video-share-silmari-dev.s3.amazonaws.com/{upload_data['s3_key']}")
        
        return True
        
    finally:
        # Cleanup test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"🗑️ Cleaned up test file: {test_file_path}")

if __name__ == "__main__":
    test_complete_upload_flow()
