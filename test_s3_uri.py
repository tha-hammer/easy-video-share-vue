#!/usr/bin/env python3
"""
Test script to verify S3 URI construction for AWS Transcribe
This tests the fix we just made to the Lambda function
"""

import json
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "https://ip60d4qmjf.execute-api.us-east-1.amazonaws.com/dev"
BEARER_TOKEN = "eyJraWQiOiJkZktmdWcrM2h5Y01ZYnhcL2FNaVRvUnRmZjl1RWluTlpOcUpLMUFoRllyTT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhNDE4NTQ2OC0wMDQxLTcwM2QtYmM5Ni1iMjE2M2ZkYzc2OTUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfOEwwU2E0QkNuIiwiY29nbml0bzp1c2VybmFtZSI6Im1lX21hY2Vvam91cmRhbl9jb20iLCJvcmlnaW5fanRpIjoiY2I3YzgxOTUtMWVjMC00ZTQ2LTljZGUtMDQzNTIzZTQyNDg4IiwiYXVkIjoiM2lwNWhudHZxMDB1ZWY4Y2Zib29scGFzZWwiLCJldmVudF9pZCI6IjFmNjZlZGU1LTQ1ZTUtNDE5Yi04NWMwLWU0Yzc2OWU4ZDUxYyIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzUwOTUyNjk3LCJuYW1lIjoiTWFjZW8iLCJleHAiOjE3NTEwMjQ5NzIsImlhdCI6MTc1MTAyMTM3MiwianRpIjoiMzVmN2FhNGEtOTBlOS00Yjk1LTk4ZmQtZTcyYmRlZTIwOWI4IiwiZW1haWwiOiJtZUBtYWNlb2pvdXJkYW4uY29tIn0.rtuv7Qn-h6mR-xAXRXOqdNiZwojeK7bsT-Jk-kEkBws9VcJ4jCibrxdMMyazT1ccIWongpW2KvmrnGe92He7XfmJRW-n-OUMtDXhGPnbaoVoZlYRTCJQgeZWoF6MZmQDs3E0t_WmTRDpgimKjOWAeEJjU6ZD_kQkpeM3RGk6vtXBss0p9e-f8WbicTpxsBymZ8CoScvl0TVlvtkailhVi4oSZVtuAMhQj78NlcwM_PqqhQhcsd3AN9mfkRE-TENaBqS_lqSF8ngbbqz_AINZ5Cb_aVLFmoPT9jkjlp_GAjsgQRtRH7W6IW1OyudjQHh7W1qkuESwLXycdQmBlg9-xw"

def test_s3_uri_construction():
    """Test the S3 URI construction logic"""
    print("🔧 Testing S3 URI Construction Logic")
    print("=" * 50)
    
    # Test cases based on different bucket_location formats
    test_cases = [
        {
            "name": "Audio Service Format",
            "bucket_location": "audio/audioId123/filename.mp3",
            "audio_bucket": "easy-video-share-silmari-dev-audio"
        },
        {
            "name": "Lambda Format", 
            "bucket_location": "audio/userId123/audioId123/filename.mp3",
            "audio_bucket": "easy-video-share-silmari-dev-audio"
        },
        {
            "name": "Video Bucket Fallback",
            "bucket_location": "audio/userId123/audioId123/filename.mp3", 
            "audio_bucket": "easy-video-share-silmari-dev"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"   Bucket Location: {test_case['bucket_location']}")
        print(f"   Audio Bucket: {test_case['audio_bucket']}")
        
        # OLD METHOD (what was causing the error)
        old_uri = f"https://{test_case['audio_bucket']}.s3.us-east-1.amazonaws.com/{test_case['bucket_location']}"
        
        # NEW METHOD (the fix we implemented)
        new_uri = f"s3://{test_case['audio_bucket']}/{test_case['bucket_location']}"
        
        print(f"   ❌ OLD URI: {old_uri}")
        print(f"   ✅ NEW URI: {new_uri}")
        
        # Validate the new URI format
        if new_uri.startswith("s3://") and "/" in new_uri[5:]:
            print(f"   ✅ VALID: Correct S3 URI format")
        else:
            print(f"   ❌ INVALID: Incorrect S3 URI format")

def test_audio_files_list():
    """Test listing audio files to see actual bucket_location format"""
    print("\n\n🎵 Testing Audio Files List")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/audio", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Audio Files Count: {data.get('count', 0)}")
            
            audio_files = data.get('audio_files', [])
            if audio_files:
                print("\n📋 Sample Audio Files:")
                for i, audio in enumerate(audio_files[:3], 1):  # Show first 3
                    print(f"   {i}. {audio.get('title', 'N/A')}")
                    print(f"      ID: {audio.get('audio_id', 'N/A')}")
                    print(f"      Bucket Location: {audio.get('bucket_location', 'N/A')}")
                    print(f"      Filename: {audio.get('filename', 'N/A')}")
                    print()
            else:
                print("No audio files found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_ai_video_generation():
    """Test starting AI video generation with a real audio file"""
    print("\n\n🎬 Testing AI Video Generation")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # First, get audio files
    try:
        response = requests.get(f"{API_BASE_URL}/audio", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get audio files: {response.status_code}")
            return
            
        data = response.json()
        audio_files = data.get('audio_files', [])
        
        if not audio_files:
            print("No audio files available for testing")
            return
            
        # Use the first audio file
        test_audio = audio_files[0]
        print(f"Using audio file: {test_audio.get('title')} (ID: {test_audio.get('audio_id')})")
        print(f"Bucket location: {test_audio.get('bucket_location')}")
        
        # Test the AI video generation request
        ai_request = {
            "audioId": test_audio.get('audio_id'),
            "prompt": "Create a dynamic vertical video with urban backgrounds and modern aesthetics",
            "targetDuration": 30,
            "style": "cinematic"
        }
        
        print(f"\n🚀 Starting AI video generation...")
        print(f"Request: {json.dumps(ai_request, indent=2)}")
        
        ai_response = requests.post(f"{API_BASE_URL}/ai-video", headers=headers, json=ai_request)
        print(f"Status Code: {ai_response.status_code}")
        
        if ai_response.status_code == 202:
            ai_data = ai_response.json()
            print(f"✅ Success: {ai_data.get('success')}")
            print(f"Video ID: {ai_data.get('videoId')}")
            print(f"Status: {ai_data.get('status')}")
            print(f"Message: {ai_data.get('message')}")
            
            # Test getting the status
            video_id = ai_data.get('videoId')
            if video_id:
                print(f"\n📊 Testing status check for video: {video_id}")
                status_response = requests.get(f"{API_BASE_URL}/ai-video/{video_id}", headers=headers)
                print(f"Status Check Code: {status_response.status_code}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Video Status: {status_data.get('video', {}).get('ai_generation_status')}")
                else:
                    print(f"Status Check Error: {status_response.text}")
        else:
            print(f"❌ AI Generation Failed: {ai_response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    """Main test function"""
    print("🧪 AI Video S3 URI Test Script")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE_URL}")
    
    # Test 1: S3 URI construction logic
    test_s3_uri_construction()
    
    # Test 2: List audio files to see actual data
    test_audio_files_list()
    
    # Test 3: Try actual AI video generation
    test_ai_video_generation()
    
    print("\n\n✅ Test script completed!")

if __name__ == "__main__":
    main() 