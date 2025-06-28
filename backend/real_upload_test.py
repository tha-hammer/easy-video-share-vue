#!/usr/bin/env python3
"""
Real Video Upload Test for AWS Console Validation
This script performs an actual video upload and processing to generate real S3 results
"""
import requests
import os
import sys
from pathlib import Path

def upload_real_video_for_validation(video_path: str):
    """Upload a real video file for processing and AWS Console validation"""
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(video_path)
    filename = os.path.basename(video_path)
    
    print("🎬 Real Video Upload Test for AWS Console Validation")
    print("=" * 60)
    print(f"Video file: {filename}")
    print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Initiate upload
    print("\n1. Requesting presigned URL...")
    initiate_payload = {
        "filename": filename,
        "content_type": "video/mp4",
        "file_size": file_size
    }
    
    try:
        response = requests.post(f"{base_url}/api/upload/initiate", json=initiate_payload)
        if response.status_code != 200:
            print(f"❌ Failed to get presigned URL: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        upload_data = response.json()
        job_id = upload_data['job_id']
        s3_key = upload_data['s3_key']
        presigned_url = upload_data['presigned_url']
        
        print(f"✅ Presigned URL obtained")
        print(f"   Job ID: {job_id}")
        print(f"   S3 Key: {s3_key}")
        
    except Exception as e:
        print(f"❌ Error requesting presigned URL: {e}")
        return False
    
    # Step 2: Upload to S3
    print(f"\n2. Uploading {filename} to S3...")
    try:
        with open(video_path, 'rb') as f:
            files = {'file': f}
            response = requests.put(
                presigned_url,
                data=f.read(),
                headers={'Content-Type': 'video/mp4'}
            )
        
        if response.status_code in [200, 204]:
            print("✅ Video uploaded to S3 successfully!")
        else:
            print(f"❌ S3 upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        return False
    
    # Step 3: Notify backend
    print("\n3. Notifying backend to start processing...")
    complete_payload = {
        "s3_key": s3_key,
        "job_id": job_id
    }
    
    try:
        response = requests.post(f"{base_url}/api/upload/complete", json=complete_payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Processing job queued successfully!")
            print(f"   Job ID: {result['job_id']}")
            print(f"   Status: {result['status']}")
        else:
            print(f"❌ Failed to queue processing: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error notifying backend: {e}")
        return False
    
    # Step 4: Provide AWS Console validation instructions
    print("\n" + "="*60)
    print("🔍 AWS CONSOLE VALIDATION INSTRUCTIONS")
    print("="*60)
    print("1. Go to AWS S3 Console: https://console.aws.amazon.com/s3/")
    print("2. Open bucket: easy-video-share-silmari-dev")
    print("3. Check the following locations:")
    print(f"   📁 uploads/{job_id}/")
    print(f"      └── {os.path.basename(s3_key)} (original upload)")
    print(f"   📁 processed/{job_id}/ (after worker processes)")
    print(f"      ├── processed_{job_id}_segment_001.mp4")
    print(f"      ├── processed_{job_id}_segment_002.mp4")
    print(f"      └── processed_{job_id}_segment_XXX.mp4")
    print("\n4. Download and verify processed videos contain:")
    print("   - 30-second segments (or shorter for last segment)")
    print("   - 'AI Generated Video' text overlay at bottom center")
    print("   - White text with black outline")
    
    print(f"\n📋 Job Details for Tracking:")
    print(f"   Job ID: {job_id}")
    print(f"   Original S3 Key: {s3_key}")
    print(f"   Processed Location: processed/{job_id}/")
    
    print("\n⚠️  Make sure the Celery worker is running to see processed results!")
    print("   Run: .\\scripts\\start-worker.ps1")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python real_upload_test.py <path_to_video_file>")
        print("Example: python real_upload_test.py sample_video.mp4")
        print("\nThis will upload a real video file and provide AWS Console validation steps.")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code != 200:
            print("❌ FastAPI server is not running")
            print("Start it with: cd backend && python main.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server")
        print("Start it with: cd backend && python main.py")
        sys.exit(1)
    
    success = upload_real_video_for_validation(video_path)
    
    if success:
        print("\n✅ Real video upload test completed!")
        print("Check the AWS Console as instructed above to validate results.")
    else:
        print("\n❌ Real video upload test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
