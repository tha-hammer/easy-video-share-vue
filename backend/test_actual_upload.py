#!/usr/bin/env python3
"""
Test script that actually uploads a file to S3 using the presigned URL
"""

import requests
import json
import os
import tempfile
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api"

def create_test_video_file():
    """Create a small test video file for upload"""
    # Create a small test file (not a real video, just for testing upload)
    test_content = b"This is a test video file content for upload testing"
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_file.write(test_content)
    temp_file.close()
    
    return temp_file.name

def test_actual_upload():
    """Test complete upload flow with actual file upload to S3"""
    print("🚀 Testing complete upload flow with actual file...")
    print("=" * 60)
    
    # Step 1: Create test file
    test_file_path = create_test_video_file()
    file_size = os.path.getsize(test_file_path)
    
    print(f"📁 Created test file: {test_file_path}")
    print(f"📏 File size: {file_size} bytes")
    
    try:
        # Step 2: Initiate upload
        print("\n🔍 Step 1: Initiating upload...")
        initiate_payload = {
            "filename": "test_video_actual.mp4",
            "content_type": "video/mp4",
            "file_size": file_size
        }
        
        response = requests.post(f"{BASE_URL}/upload/initiate", json=initiate_payload)
        if response.status_code != 200:
            print(f"❌ Initiate upload failed: {response.text}")
            return False
            
        upload_data = response.json()
        presigned_url = upload_data["presigned_url"]
        s3_key = upload_data["s3_key"]
        job_id = upload_data["job_id"]
        
        print(f"✅ Upload initiated successfully")
        print(f"📋 Job ID: {job_id}")
        print(f"📋 S3 Key: {s3_key}")
        
        # Step 3: Upload file to S3 using presigned URL
        print("\n🔍 Step 2: Uploading file to S3...")
        
        with open(test_file_path, 'rb') as file:
            upload_response = requests.put(
                presigned_url,
                data=file,
                headers={'Content-Type': 'video/mp4'}
            )
        
        if upload_response.status_code == 200:
            print("✅ File uploaded to S3 successfully!")
        else:
            print(f"❌ S3 upload failed: {upload_response.status_code} - {upload_response.text}")
            return False
        
        # Step 4: Complete upload (notify backend)
        print("\n🔍 Step 3: Notifying backend of completed upload...")
        
        complete_payload = {
            "s3_key": s3_key,
            "job_id": job_id
        }
        
        complete_response = requests.post(f"{BASE_URL}/upload/complete", json=complete_payload)
        
        if complete_response.status_code == 200:
            result = complete_response.json()
            print("✅ Backend notified successfully!")
            print(f"📋 Job Status: {result['status']}")
            print(f"📋 Message: {result['message']}")
        else:
            print(f"❌ Backend notification failed: {complete_response.text}")
            return False
        
        # Step 5: Verification instructions
        print("\n🔍 Verification Steps:")
        print("1. Check AWS S3 Console:")
        print(f"   - Bucket: easy-video-share-silmari-dev")
        print(f"   - Path: {s3_key}")
        print("2. AWS CLI verification:")
        print(f"   aws s3 ls s3://easy-video-share-silmari-dev/{s3_key}")
        print("3. Check if Celery task is processing:")
        print("   - Look at Celery worker logs if running")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up test file
        try:
            os.unlink(test_file_path)
            print(f"\n🧹 Cleaned up test file: {test_file_path}")
        except:
            pass

def main():
    """Run the actual upload test"""
    if test_actual_upload():
        print("\n🎉 Complete upload flow test PASSED!")
        print("\nNext: Start Celery worker to process the job:")
        print("celery -A tasks worker --loglevel=info --pool=solo")
    else:
        print("\n❌ Upload flow test FAILED!")

if __name__ == "__main__":
    main()
