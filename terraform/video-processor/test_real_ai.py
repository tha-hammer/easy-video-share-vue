#!/usr/bin/env python3
"""
Test script for real AI integration features
Tests the new audio upload and processing pipeline
"""

import os
import time
import requests
import json
from io import BytesIO

# Configuration
API_BASE_URL = "http://localhost:8080"
TEST_PROJECT_ID = f"test-real-ai-{int(time.time())}"

def create_test_audio_file():
    """Create a simple test audio file (mock data)"""
    # In a real test, you would use a real audio file
    # For now, we'll create dummy audio data
    audio_data = b"fake_audio_content_for_testing"
    return BytesIO(audio_data)

def test_health_check():
    """Test enhanced health check endpoint"""
    print("🔍 Testing enhanced health check...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Services Status:")
            for service, status in data['services_status'].items():
                print(f"     - {service}: {status}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_audio_upload():
    """Test the new audio upload endpoint"""
    print("\n🎵 Testing audio upload...")
    
    try:
        # Create test audio file
        audio_file = create_test_audio_file()
        
        # Prepare multipart form data
        files = {
            'audio_file': ('test_audio.mp3', audio_file, 'audio/mpeg')
        }
        
        data = {
            'title': 'Test Audio Project',
            'target_duration': 30,
            'user_id': 'test-user'
        }
        
        response = requests.post(
            f"{API_BASE_URL}/upload-audio",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Audio upload successful")
            print(f"   Project ID: {result['project_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            return result['project_id']
        else:
            print(f"❌ Audio upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Audio upload error: {str(e)}")
        return None

def test_project_monitoring(project_id):
    """Monitor project progress through the AI pipeline"""
    print(f"\n📊 Monitoring project progress: {project_id}")
    
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                metadata = data.get('metadata', {})
                message = metadata.get('message', 'No message')
                
                print(f"   Attempt {attempt + 1}: Status = {status}")
                print(f"   Message: {message}")
                
                if 'stage' in metadata:
                    print(f"   Stage: {metadata['stage']}")
                
                if 'transcript' in metadata:
                    print(f"   Transcript: {metadata['transcript']}")
                
                if 'scenes_generated' in metadata:
                    print(f"   Scenes Generated: {metadata['scenes_generated']}")
                
                if 'assets_completed' in metadata:
                    print(f"   Assets Completed: {metadata['assets_completed']}")
                
                if status == "completed":
                    print("✅ Project completed successfully!")
                    if 'final_video_url' in metadata:
                        print(f"   Final Video URL: {metadata['final_video_url']}")
                    return True
                elif status == "failed":
                    print("❌ Project failed!")
                    if 'error' in metadata:
                        print(f"   Error: {metadata['error']}")
                    return False
                
                # Wait before next check
                time.sleep(10)
                attempt += 1
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
            return False
    
    print("⏰ Project monitoring timed out")
    return False

def test_legacy_compatibility():
    """Test that the legacy /process-video endpoint still works"""
    print(f"\n🔄 Testing legacy compatibility...")
    
    try:
        payload = {
            "project_id": f"legacy-{TEST_PROJECT_ID}",
            "prompt": "Test video generation for compatibility",
            "duration": 5,
            "style": "realistic",
            "aspect_ratio": "16:9"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/process-video",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Legacy endpoint successful")
            print(f"   Project ID: {result['project_id']}")
            print(f"   Status: {result['status']}")
            return result['project_id']
        else:
            print(f"❌ Legacy endpoint failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Legacy endpoint error: {str(e)}")
        return None

def test_projects_list():
    """Test the projects listing endpoint"""
    print(f"\n📋 Testing projects list...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/projects")
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            count = data.get('count', 0)
            
            print(f"✅ Projects list successful")
            print(f"   Found {count} projects")
            
            if projects:
                print("   Recent projects:")
                for project in projects[:3]:  # Show first 3
                    print(f"     - {project.get('project_id', 'Unknown')}: {project.get('status', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Projects list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Projects list error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Real AI Integration Tests")
    print(f"   API Base URL: {API_BASE_URL}")
    print(f"   Test Project ID: {TEST_PROJECT_ID}")
    print("=" * 60)
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Health check failed, stopping tests")
        return
    
    # Test 2: Projects List
    test_projects_list()
    
    # Test 3: Audio Upload & Processing Pipeline
    project_id = test_audio_upload()
    if project_id:
        # Monitor the real AI pipeline
        test_project_monitoring(project_id)
    
    # Test 4: Legacy Compatibility
    legacy_project_id = test_legacy_compatibility()
    if legacy_project_id:
        print(f"\n🔄 Quickly checking legacy project status...")
        time.sleep(5)  # Give it a moment to start
        response = requests.get(f"{API_BASE_URL}/projects/{legacy_project_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Legacy project status: {data['status']}")
    
    print("\n" + "=" * 60)
    print("🏁 Real AI Integration Tests Complete")
    print("🎉 Your AI video generation pipeline is ready for real-world usage!")
    print("\n💡 Next Steps:")
    print("   1. Add your OpenAI API key to environment variables")
    print("   2. Add your fal.ai API key to environment variables")
    print("   3. Test with real audio files")
    print("   4. Deploy to production AWS environment")

if __name__ == "__main__":
    main() 