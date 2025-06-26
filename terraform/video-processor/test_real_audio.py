#!/usr/bin/env python3
"""
Real Audio File Testing Script
Test the AI video generation pipeline with actual audio files
"""

import sys
import os
import time
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8080"

def test_health_check():
    """Test that the API is running and healthy"""
    print("🔍 Checking API health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Version: {data['version']}")
            print(f"   Environment: {data['environment']}")
            
            services = data.get('services_status', {})
            print("   Services:")
            for service, status in services.items():
                status_icon = "✅" if status in ["initialized", "available"] else "⚠️"
                print(f"     {status_icon} {service}: {status}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def upload_audio_file(audio_file_path, title=None, target_duration=45):
    """Upload a real audio file to the AI video generation pipeline"""
    
    # Validate file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return None
    
    # Get file info
    file_path = Path(audio_file_path)
    file_size = file_path.stat().st_size
    file_name = file_path.name
    
    # Auto-generate title if not provided
    if not title:
        title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    print(f"\n🎵 Uploading audio file...")
    print(f"   File: {file_name}")
    print(f"   Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"   Title: {title}")
    print(f"   Target Duration: {target_duration} seconds")
    
    try:
        # Prepare the file upload
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'audio_file': (file_name, audio_file, 'audio/mpeg')
            }
            
            data = {
                'title': title,
                'target_duration': target_duration,
                'user_id': 'real-test-user'
            }
            
            print(f"   📤 Uploading... (this may take a moment for large files)")
            
            response = requests.post(
                f"{API_BASE_URL}/upload-audio",
                files=files,
                data=data,
                timeout=120  # 2 minute timeout for large files
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   Project ID: {result['project_id']}")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result.get('message', 'Processing started')}")
                return result['project_id']
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None

def monitor_project(project_id, max_wait_minutes=10):
    """Monitor project progress with real-time updates"""
    print(f"\n📊 Monitoring project: {project_id}")
    print(f"   Max wait time: {max_wait_minutes} minutes")
    print("   " + "=" * 50)
    
    max_attempts = max_wait_minutes * 6  # Check every 10 seconds
    attempt = 0
    last_status = ""
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                metadata = data.get('metadata', {})
                
                # Only print if status changed
                if status != last_status:
                    print(f"\n   🔄 Status: {status}")
                    if 'message' in metadata:
                        print(f"   💬 {metadata['message']}")
                    
                    if 'stage' in metadata:
                        print(f"   📍 Stage: {metadata['stage']}")
                    
                    last_status = status
                
                # Show additional details for certain stages
                if 'transcript' in metadata and len(metadata['transcript']) > 0:
                    transcript = metadata['transcript']
                    if len(transcript) > 100:
                        transcript = transcript[:100] + "..."
                    print(f"   📝 Transcript: {transcript}")
                
                if 'scenes_generated' in metadata:
                    print(f"   🎬 Scenes Generated: {metadata['scenes_generated']}")
                
                if 'assets_completed' in metadata:
                    print(f"   🎨 Assets Completed: {metadata['assets_completed']}")
                
                # Check for completion
                if status == "completed":
                    print(f"\n✅ SUCCESS! Video generation completed!")
                    if 'final_video_url' in metadata:
                        print(f"   🎥 Final Video: {metadata['final_video_url']}")
                    if 'processing_time' in metadata:
                        print(f"   ⏱️  Processing Time: {metadata['processing_time']}")
                    return True
                    
                elif status == "failed":
                    print(f"\n❌ FAILED! Video generation failed!")
                    if 'error' in metadata:
                        print(f"   ❗ Error: {metadata['error']}")
                    return False
                
                # Progress indicator
                if attempt > 0 and attempt % 6 == 0:  # Every minute
                    elapsed_minutes = attempt // 6
                    print(f"   ⏳ {elapsed_minutes} minute(s) elapsed...")
                
                time.sleep(10)
                attempt += 1
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Monitoring error: {str(e)}")
            return False
    
    print(f"\n⏰ Timeout reached ({max_wait_minutes} minutes)")
    print("   The project may still be processing. Check status manually.")
    return False

def main():
    """Main test function"""
    print("🎬 Real Audio File Testing")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\n❌ Please provide an audio file path")
        print("\nUsage:")
        print(f"   python {sys.argv[0]} <audio_file_path> [title] [target_duration]")
        print("\nExample:")
        print(f"   python {sys.argv[0]} my_audio.mp3")
        print(f"   python {sys.argv[0]} my_audio.mp3 \"My Video Title\" 60")
        print("\nSupported formats: MP3, WAV, M4A, AAC, OGG")
        return
    
    audio_file_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    target_duration = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    
    # Test 1: Health Check
    print("\n1️⃣ API Health Check")
    if not test_health_check():
        print("\n❌ API is not healthy. Make sure the service is running:")
        print("   cd terraform/video-processor && docker-compose up -d")
        return
    
    # Test 2: Upload Audio File
    print("\n2️⃣ Audio File Upload")
    project_id = upload_audio_file(audio_file_path, title, target_duration)
    
    if not project_id:
        print("\n❌ Upload failed. Check the error messages above.")
        return
    
    # Test 3: Monitor Progress
    print("\n3️⃣ AI Processing Pipeline")
    success = monitor_project(project_id, max_wait_minutes=15)  # 15 minute timeout
    
    # Final Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS! Your audio file has been transformed into a video!")
        print(f"\n📋 Summary:")
        print(f"   📁 Original File: {audio_file_path}")
        print(f"   🆔 Project ID: {project_id}")
        print(f"   ✅ Status: Completed")
        print(f"\n💡 Next Steps:")
        print(f"   • Add real API keys (OpenAI, fal.ai) to test with actual AI")
        print(f"   • Try different audio files and durations")
        print(f"   • Deploy to production AWS environment")
    else:
        print("❌ The video generation did not complete successfully.")
        print(f"\n🔍 Troubleshooting:")
        print(f"   • Check project status: curl {API_BASE_URL}/projects/{project_id}")
        print(f"   • Check API logs: docker-compose logs video-processor")
        print(f"   • Verify audio file format and quality")

if __name__ == "__main__":
    main() 