#!/usr/bin/env python3
"""
Debug script to investigate 403 errors in multi-part upload
"""
import requests
import os

# Configuration
BASE_URL = "http://localhost:8000/api"

def create_test_video_file(size_mb: int = 5):
    """Create a test video file with random data"""
    import tempfile
    import random
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file_path = temp_file.name
    temp_file.close()
    
    # Write random data to simulate video file
    with open(temp_file_path, 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    
    return temp_file_path

def debug_403_error():
    """Debug the 403 error with detailed logging"""
    print("🔍 DEBUGGING 403 ERROR")
    print("=" * 50)
    
    # Create a small test file
    test_file_path = create_test_video_file(5)  # 5MB file
    file_size = os.path.getsize(test_file_path)
    
    try:
        # Step 1: Initiate multi-part upload
        print("1. Initiating multi-part upload...")
        initiate_payload = {
            "filename": "debug_test.mp4",
            "content_type": "video/mp4",
            "file_size": file_size
        }
        
        response = requests.post(f"{BASE_URL}/upload/initiate-multipart", json=initiate_payload)
        print(f"Initiate Response Status: {response.status_code}")
        print(f"Initiate Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ Initiate failed: {response.text}")
            return
            
        upload_data = response.json()
        upload_id = upload_data['upload_id']
        s3_key = upload_data['s3_key']
        chunk_size = upload_data['chunk_size']
        
        print(f"✅ Initiate successful")
        print(f"   Upload ID: {upload_id}")
        print(f"   S3 Key: {s3_key}")
        print(f"   Chunk Size: {chunk_size}")
        
        # Step 2: Get presigned URL for part 1
        print("\n2. Getting presigned URL for part 1...")
        part_request = {
            "upload_id": upload_id,
            "s3_key": s3_key,
            "part_number": 1,
            "content_type": "video/mp4"
        }
        
        part_response = requests.post(f"{BASE_URL}/upload/part", json=part_request)
        print(f"Part URL Response Status: {part_response.status_code}")
        print(f"Part URL Response Headers: {dict(part_response.headers)}")
        
        if part_response.status_code != 200:
            print(f"❌ Part URL failed: {part_response.text}")
            return
            
        part_data = part_response.json()
        presigned_url = part_data['presigned_url']
        
        print(f"✅ Part URL successful")
        print(f"   Presigned URL: {presigned_url[:100]}...")
        
        # Step 3: Try to upload part 1 with detailed error logging
        print("\n3. Attempting to upload part 1...")
        
        with open(test_file_path, 'rb') as f:
            chunk_data = f.read(chunk_size)
        
        print(f"   Chunk size: {len(chunk_data)} bytes")
        print(f"   Content-Type header: video/mp4")
        
        # Try the upload with detailed error handling (don't include Content-Type header for multi-part uploads)
        try:
            upload_response = requests.put(
                presigned_url,
                data=chunk_data,
                timeout=30
            )
            
            print(f"Upload Response Status: {upload_response.status_code}")
            print(f"Upload Response Headers: {dict(upload_response.headers)}")
            print(f"Upload Response Body: {upload_response.text}")
            
            if upload_response.status_code in [200, 204]:
                etag = upload_response.headers.get('ETag', '').strip('"')
                print(f"✅ Upload successful! ETag: {etag}")
            else:
                print(f"❌ Upload failed with status {upload_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request exception: {e}")
            
    except Exception as e:
        print(f"❌ General error: {e}")
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"\n🧹 Cleaned up test file")

if __name__ == "__main__":
    debug_403_error() 