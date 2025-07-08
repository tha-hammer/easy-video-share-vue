#!/usr/bin/env python3
"""
Test script for multi-part upload functionality
This script tests the new multi-part upload endpoints for large video files
"""
import requests
import os
import tempfile
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api"

def create_test_video_file(size_mb: int = 50):
    """Create a test video file of specified size for upload testing"""
    # Create a test file with random data (not a real video, just for testing upload)
    test_content = b"0" * (size_mb * 1024 * 1024)  # Create file of specified size
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_file.write(test_content)
    temp_file.close()
    
    return temp_file.name

def test_multipart_upload_flow(file_size_mb: int = 50):
    """Test complete multi-part upload flow"""
    print(f"🚀 Testing multi-part upload flow with {file_size_mb}MB file")
    print("=" * 60)
    
    # Step 1: Create test file
    test_file_path = create_test_video_file(file_size_mb)
    file_size = os.path.getsize(test_file_path)
    
    print(f"📁 Created test file: {test_file_path}")
    print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    try:
        # Step 2: Initiate multi-part upload
        print("\n1. Initiating multi-part upload...")
        initiate_payload = {
            "filename": f"test_video_{file_size_mb}mb.mp4",
            "content_type": "video/mp4",
            "file_size": file_size
        }
        
        response = requests.post(f"{BASE_URL}/upload/initiate-multipart", json=initiate_payload)
        if response.status_code != 200:
            print(f"❌ Failed to initiate multi-part upload: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        upload_data = response.json()
        upload_id = upload_data['upload_id']
        s3_key = upload_data['s3_key']
        job_id = upload_data['job_id']
        chunk_size = upload_data['chunk_size']
        max_concurrent = upload_data['max_concurrent_uploads']
        
        print(f"✅ Multi-part upload initiated successfully")
        print(f"   Upload ID: {upload_id}")
        print(f"   S3 Key: {s3_key}")
        print(f"   Job ID: {job_id}")
        print(f"   Chunk Size: {chunk_size:,} bytes ({chunk_size/1024/1024:.1f} MB)")
        print(f"   Max Concurrent: {max_concurrent}")
        
        # Step 3: Calculate chunks and upload parts
        total_chunks = (file_size + chunk_size - 1) // chunk_size  # Ceiling division
        print(f"\n2. Uploading {total_chunks} chunks...")
        
        uploaded_parts = []
        
        with open(test_file_path, 'rb') as f:
            for part_number in range(1, total_chunks + 1):
                # Get presigned URL for this part
                part_request = {
                    "upload_id": upload_id,
                    "s3_key": s3_key,
                    "part_number": part_number,
                    "content_type": "video/mp4"
                }
                
                part_response = requests.post(f"{BASE_URL}/upload/part", json=part_request)
                if part_response.status_code != 200:
                    print(f"❌ Failed to get presigned URL for part {part_number}: {part_response.status_code}")
                    return False
                
                part_data = part_response.json()
                presigned_url = part_data['presigned_url']
                
                # Calculate chunk boundaries
                start = (part_number - 1) * chunk_size
                end = min(start + chunk_size, file_size)
                chunk_data = f.read(end - start)
                
                # Upload the chunk (don't include Content-Type header for multi-part uploads)
                upload_response = requests.put(
                    presigned_url,
                    data=chunk_data
                )
                
                if upload_response.status_code in [200, 204]:
                    etag = upload_response.headers.get('ETag', '').strip('"')
                    uploaded_parts.append({
                        "PartNumber": part_number,
                        "ETag": etag
                    })
                    print(f"   ✅ Part {part_number}/{total_chunks} uploaded (ETag: {etag[:20]}...)")
                else:
                    print(f"❌ Failed to upload part {part_number}: {upload_response.status_code}")
                    return False
        
        # Step 4: Complete multi-part upload
        print(f"\n3. Completing multi-part upload...")
        complete_payload = {
            "upload_id": upload_id,
            "s3_key": s3_key,
            "job_id": job_id,
            "parts": uploaded_parts,
            "user_id": "test_user",
            "filename": f"test_video_{file_size_mb}mb.mp4",
            "file_size": file_size,
            "title": f"Test Video {file_size_mb}MB",
            "user_email": "test@example.com",
            "content_type": "video/mp4"
        }
        
        complete_response = requests.post(f"{BASE_URL}/upload/complete-multipart", json=complete_payload)
        if complete_response.status_code == 200:
            result = complete_response.json()
            print("✅ Multi-part upload completed successfully!")
            print(f"   Job ID: {result['job_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to complete multi-part upload: {complete_response.status_code}")
            print(f"Response: {complete_response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error during multi-part upload test: {e}")
        return False
    finally:
        # Cleanup test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"🧹 Cleaned up test file: {test_file_path}")

def test_abort_multipart_upload():
    """Test aborting a multi-part upload"""
    print(f"\n🧪 Testing abort multi-part upload functionality")
    print("=" * 60)
    
    # Create a small test file
    test_file_path = create_test_video_file(5)  # 5MB file
    file_size = os.path.getsize(test_file_path)
    
    try:
        # Initiate upload
        initiate_payload = {
            "filename": "test_abort.mp4",
            "content_type": "video/mp4",
            "file_size": file_size
        }
        
        response = requests.post(f"{BASE_URL}/upload/initiate-multipart", json=initiate_payload)
        if response.status_code != 200:
            print(f"❌ Failed to initiate upload for abort test: {response.status_code}")
            return False
            
        upload_data = response.json()
        upload_id = upload_data['upload_id']
        s3_key = upload_data['s3_key']
        
        # Abort the upload
        abort_payload = {
            "upload_id": upload_id,
            "s3_key": s3_key
        }
        
        abort_response = requests.post(f"{BASE_URL}/upload/abort-multipart", json=abort_payload)
        if abort_response.status_code == 200:
            print("✅ Multi-part upload aborted successfully!")
            return True
        else:
            print(f"❌ Failed to abort multi-part upload: {abort_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during abort test: {e}")
        return False
    finally:
        # Cleanup test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def main():
    """Run all multi-part upload tests"""
    print("🧪 MULTI-PART UPLOAD TEST SUITE")
    print("=" * 60)
    
    # Test 1: Small file (should use multi-part)
    print("\n📦 Test 1: Small file (50MB)")
    success1 = test_multipart_upload_flow(50)
    
    # Test 2: Large file (should use multi-part)
    print("\n📦 Test 2: Large file (100MB)")
    success2 = test_multipart_upload_flow(100)
    
    # Test 3: Abort functionality
    success3 = test_abort_multipart_upload()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Small file upload: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Large file upload: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Abort functionality: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 All tests passed! Multi-part upload is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main() 