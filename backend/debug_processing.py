#!/usr/bin/env python3
"""
Debug Sprint 2 Processing Pipeline
Diagnose why no 'processed' folder is being created in S3
"""
import requests
import time
import os

def debug_processing_pipeline():
    """Debug the complete processing pipeline to identify issues"""
    
    print("🔍 Sprint 2 Processing Pipeline Debug")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Check API health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI is running and healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server")
        print("   → Start with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ API health check error: {e}")
        return False
    
    # Step 2: Check Redis connectivity from API
    print("\n2. Testing Redis connection from API...")
    try:
        # Test if we can initiate upload (this tests Redis indirectly)
        test_payload = {
            "filename": "debug_test.mp4",
            "content_type": "video/mp4",
            "file_size": 1000000
        }
        response = requests.post(f"{base_url}/api/upload/initiate", json=test_payload)
        if response.status_code == 200:
            upload_data = response.json()
            job_id = upload_data['job_id']
            s3_key = upload_data['s3_key']
            print("✅ Upload initiation works (Redis accessible)")
            print(f"   Test Job ID: {job_id}")
        else:
            print(f"❌ Upload initiation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload initiation error: {e}")
        return False
    
    # Step 3: Test job dispatch
    print("\n3. Testing job dispatch to Celery...")
    try:
        complete_payload = {
            "s3_key": s3_key,
            "job_id": job_id
        }
        response = requests.post(f"{base_url}/api/upload/complete", json=complete_payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Job dispatch successful")
            print(f"   Job Status: {result['status']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Job dispatch failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Job dispatch error: {e}")
        return False
    
    # Step 4: Check if worker is processing
    print(f"\n4. Monitoring job processing...")
    print("   ⚠️  Note: This job will fail because no actual file was uploaded to S3")
    print("   ⚠️  But we can see if the worker picks it up and tries to process it")
    print("   ⚠️  Check your Celery worker logs for activity...")
    
    print(f"\n📋 Debug Summary:")
    print(f"   Test Job ID: {job_id}")
    print(f"   Test S3 Key: {s3_key}")
    print(f"   Expected behavior: Worker should try to download from S3 and fail")
    print(f"   (This confirms the worker is running and picking up jobs)")
    
    return True

def check_worker_status():
    """Check if Celery worker is running"""
    print("\n🔧 Worker Status Check")
    print("=" * 30)
    
    # Check Redis container
    print("Checking Redis container...")
    redis_check = os.system('docker ps | findstr easy-video-share-redis > nul 2>&1')
    if redis_check == 0:
        print("✅ Redis container is running")
    else:
        print("❌ Redis container is not running")
        print("   → Start with: .\\scripts\\start-redis.ps1")
        return False
    
    # Check if worker process might be running
    print("\nChecking for Celery worker process...")
    print("   → Look for a terminal/console running: celery -A tasks worker")
    print("   → If not running, start with: .\\scripts\\start-worker.ps1")
    
    return True

def provide_troubleshooting_steps():
    """Provide step-by-step troubleshooting"""
    print("\n🛠️  TROUBLESHOOTING: No 'processed' folder in S3")
    print("=" * 55)
    
    print("\n📋 Root Cause Analysis:")
    print("   The 'processed' folder only gets created when:")
    print("   1. ✅ A real video file is uploaded to S3")
    print("   2. ✅ The Celery worker is running") 
    print("   3. ✅ The worker successfully processes the video")
    print("   4. ✅ Processed segments are uploaded back to S3")
    
    print("\n📋 Step-by-Step Fix:")
    print("   1. Ensure Redis is running:")
    print("      .\\scripts\\start-redis.ps1")
    print("   ")
    print("   2. Start the FastAPI server:")
    print("      cd backend")
    print("      python main.py")
    print("   ")
    print("   3. Start the Celery worker (NEW TERMINAL):")
    print("      .\\scripts\\start-worker.ps1")
    print("   ")
    print("   4. Upload a REAL video file:")
    print("      cd backend")
    print("      python real_upload_test.py \"path\\to\\your\\video.mp4\"")
    print("   ")
    print("   5. Monitor worker logs for processing activity")
    print("   ")
    print("   6. Check S3 for 'processed' folder after processing completes")
    
    print("\n⚠️  Common Issues:")
    print("   • Worker not started → No processing happens")
    print("   • No real video uploaded → Nothing to process")  
    print("   • FFmpeg not installed → Processing fails")
    print("   • AWS credentials expired → S3 upload fails")
    
    print("\n🔍 Next Steps:")
    print("   1. Run this debug again after starting worker")
    print("   2. Upload a real video file")
    print("   3. Watch worker logs for processing activity")
    print("   4. Check S3 for results")

def main():
    """Main debug function"""
    success = debug_processing_pipeline()
    
    if success:
        check_worker_status()
    
    provide_troubleshooting_steps()
    
    print(f"\n💡 Key Point: 'processed' folder is created ONLY after successful video processing!")
    print(f"   The basic API tests (test_sprint_2.py) don't upload real files.")
    print(f"   Use real_upload_test.py with an actual video file to see processed results.")

if __name__ == "__main__":
    main()
