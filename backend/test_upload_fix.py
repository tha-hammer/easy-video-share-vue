#!/usr/bin/env python3
"""
Quick test for the Sprint 2 upload initiation fix
"""
import requests
import json

def test_upload_initiation_fix():
    """Test the fixed upload initiation payload"""
    base_url = "http://localhost:8000"
    
    print("🔧 Testing Sprint 2 Upload Initiation Fix")
    print("=" * 45)
    
    # Test with correct payload including file_size
    print("Testing upload initiation with file_size...")
    
    initiate_payload = {
        "filename": "test_video.mp4",
        "content_type": "video/mp4",
        "file_size": 10485760  # 10MB
    }
    
    try:
        response = requests.post(f"{base_url}/api/upload/initiate", json=initiate_payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            upload_data = response.json()
            print("✅ Upload initiation successful!")
            print(f"   Job ID: {upload_data['job_id']}")
            print(f"   S3 Key: {upload_data['s3_key']}")
            print(f"   Presigned URL: {upload_data['presigned_url'][:80]}...")
            return True
        else:
            print(f"❌ Upload initiation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure FastAPI server is running:")
        print("   cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_upload_initiation_fix()
    if success:
        print("\n✅ Fix verified! The upload initiation now works correctly.")
        print("You can now run the full Sprint 2 test:")
        print("   cd backend && python test_sprint_2.py")
    else:
        print("\n❌ Fix verification failed.")
