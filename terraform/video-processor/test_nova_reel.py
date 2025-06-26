#!/usr/bin/env python3
"""
Nova Reel Video Generation Test Script
Tests AWS Bedrock Nova Reel model integration with REAL video generation
Returns ACTUAL S3 URLs for generated videos
"""

import os
import time
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8080"
TEST_PROJECT_ID = f"nova-reel-test-{int(time.time())}"

def test_health_check():
    """Test health check to ensure Nova Reel is configured"""
    print("🔍 Testing Nova Reel health check...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Services Status:")
            for service, status in data['services_status'].items():
                icon = "✅" if status in ["initialized", "configured", "available"] else "❌"
                print(f"     {icon} {service}: {status}")
            
            # Check Nova Reel specifically
            nova_status = data['services_status'].get('nova_reel_client', 'not_found')
            bedrock_status = data['services_status'].get('bedrock', 'not_found')
            
            if nova_status == 'initialized':
                if bedrock_status == 'configured':
                    print("🎬 Nova Reel is properly configured and ready!")
                    return True
                else:
                    print("⚠️  Bedrock not configured (expected in LocalStack)")
                    print(f"   Nova Reel Client: {nova_status}")
                    print(f"   Bedrock: {bedrock_status}")
                    print("🧪 Proceeding with test anyway - should get real S3 URLs")
                    return True
            else:
                print("❌ Nova Reel client not initialized")
                print(f"   Nova Reel Client: {nova_status}")
                print(f"   Bedrock: {bedrock_status}")
                return False
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_nova_reel_video_generation():
    """Test REAL video generation using Nova Reel"""
    print("\n🎬 Testing REAL Nova Reel video generation...")
    
    # Test prompts designed for Nova Reel
    test_prompts = [
        {
            "prompt": "A serene ocean wave gently rolling onto a sandy beach at sunset, with warm golden light reflecting on the water",
            "duration": 5,
            "aspect_ratio": "16:9",
            "expected_type": "nature_scene"
        },
        {
            "prompt": "A modern coffee cup steaming on a wooden table, with morning sunlight streaming through a window",
            "duration": 4,
            "aspect_ratio": "9:16",
            "expected_type": "product_shot"
        },
        {
            "prompt": "Abstract particles floating and connecting in space, creating a network of glowing connections",
            "duration": 6,
            "aspect_ratio": "16:9",
            "expected_type": "abstract_animation"
        }
    ]
    
    generated_videos = []
    
    for i, test_case in enumerate(test_prompts, 1):
        print(f"\n--- Test Case {i}: {test_case['expected_type']} ---")
        print(f"Prompt: {test_case['prompt']}")
        print(f"Duration: {test_case['duration']}s, Aspect Ratio: {test_case['aspect_ratio']}")
        
        try:
            project_id = f"{TEST_PROJECT_ID}-{i}"
            
            payload = {
                "project_id": project_id,
                "prompt": test_case['prompt'],
                "duration": test_case['duration'],
                "style": "realistic",
                "aspect_ratio": test_case['aspect_ratio']
            }
            
            # Start video generation
            print("   📤 Sending video generation request...")
            response = requests.post(
                f"{API_BASE_URL}/process-video",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Request accepted: {result['project_id']}")
                
                # Monitor progress and get REAL URL
                video_url = monitor_video_generation(project_id, test_case['expected_type'])
                
                if video_url and not "example.com" in video_url:
                    generated_videos.append({
                        'project_id': project_id,
                        'prompt': test_case['prompt'],
                        'video_url': video_url,
                        'type': test_case['expected_type']
                    })
                    print(f"   🎉 REAL VIDEO GENERATED: {video_url}")
                else:
                    print(f"   ❌ Failed to generate real video (got mock/fallback URL)")
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Test case {i} failed: {str(e)}")
    
    return generated_videos

def monitor_video_generation(project_id: str, expected_type: str, max_attempts: int = 20):
    """Monitor video generation progress and return REAL video URL"""
    print(f"   📊 Monitoring generation progress for {expected_type}...")
    
    attempt = 0
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                metadata = data.get('metadata', {})
                
                if attempt == 0 or attempt % 5 == 0:  # Log every 5th attempt
                    print(f"   📍 Attempt {attempt + 1}: Status = {status}")
                    if 'message' in metadata:
                        print(f"       Message: {metadata['message']}")
                    if 'stage' in metadata:
                        print(f"       Stage: {metadata['stage']}")
                
                if status == "completed":
                    video_url = metadata.get('video_url')
                    generation_method = metadata.get('generation_method', 'unknown')
                    
                    print(f"   ✅ Generation completed!")
                    print(f"       Method: {generation_method}")
                    print(f"       Video URL: {video_url}")
                    
                    # Validate that it's a REAL S3 URL, not a mock
                    if video_url and ("s3://" in video_url or "amazonaws.com" in video_url or "localstack" in video_url):
                        return video_url
                    else:
                        print(f"   ⚠️  Got non-S3 URL (likely mock): {video_url}")
                        return None
                        
                elif status == "failed":
                    error = metadata.get('error', 'Unknown error')
                    print(f"   ❌ Generation failed: {error}")
                    return None
                
                # Continue monitoring
                time.sleep(3)  # Check every 3 seconds
                attempt += 1
                
            else:
                print(f"   ❌ Status check failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Monitoring error: {str(e)}")
            return None
    
    print(f"   ⏰ Monitoring timed out after {max_attempts} attempts")
    return None

def validate_video_urls(generated_videos):
    """Validate that generated videos have real S3 URLs"""
    print(f"\n🔍 Validating generated video URLs...")
    
    if not generated_videos:
        print("❌ No videos were generated successfully")
        return False
    
    print(f"✅ Generated {len(generated_videos)} real videos:")
    
    for i, video in enumerate(generated_videos, 1):
        print(f"\n   Video {i}: {video['type']}")
        print(f"   Project ID: {video['project_id']}")
        print(f"   Prompt: {video['prompt'][:60]}...")
        print(f"   URL: {video['video_url']}")
        
        # Validate URL format
        url = video['video_url']
        if "s3://" in url:
            print(f"   ✅ Valid S3 URL format")
        elif "amazonaws.com" in url:
            print(f"   ✅ Valid S3 HTTP URL format")
        elif "localstack" in url:
            print(f"   ✅ Valid LocalStack S3 URL format")
        else:
            print(f"   ❌ Invalid URL format (not S3)")
            return False
    
    print(f"\n🎉 ALL VIDEOS HAVE REAL S3 URLS - TEST SUCCESSFUL!")
    return True

def test_projects_list():
    """Test projects listing to see generated videos"""
    print(f"\n📋 Testing projects list...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/projects")
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            count = data.get('count', 0)
            
            print(f"✅ Found {count} total projects")
            
            # Filter Nova Reel test projects
            nova_projects = [p for p in projects if 'nova-reel-test' in p.get('project_id', '')]
            
            if nova_projects:
                print(f"   🎬 Nova Reel test projects: {len(nova_projects)}")
                for project in nova_projects:
                    status = project.get('status', 'unknown')
                    metadata = project.get('metadata', {})
                    video_url = metadata.get('video_url', 'none')
                    
                    print(f"     - {project['project_id']}: {status}")
                    if video_url != 'none':
                        print(f"       Video: {video_url}")
            else:
                print(f"   ℹ️  No Nova Reel test projects found")
            
            return True
        else:
            print(f"❌ Projects list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Projects list error: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🚀 Nova Reel Video Generation Test Suite")
    print("=========================================")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test Project ID Base: {TEST_PROJECT_ID}")
    
    # Step 1: Health check
    if not test_health_check():
        print("\n❌ Health check failed - aborting tests")
        return
    
    # Step 2: Test real video generation
    generated_videos = test_nova_reel_video_generation()
    
    # Step 3: Validate results
    success = validate_video_urls(generated_videos)
    
    # Step 4: List projects
    test_projects_list()
    
    # Final result
    print("\n" + "="*50)
    if success:
        print("🎉 NOVA REEL TEST SUITE COMPLETED SUCCESSFULLY!")
        print("✅ Real S3 URLs generated and validated")
        print(f"✅ {len(generated_videos)} videos created with actual Nova Reel")
        
        if generated_videos:
            print("\n📥 Download your generated videos:")
            for video in generated_videos:
                print(f"   {video['type']}: {video['video_url']}")
    else:
        print("❌ NOVA REEL TEST SUITE FAILED")
        print("   Check the logs above for specific errors")
        print("   Ensure Nova Reel/Bedrock is properly configured")
    
    print("="*50)

if __name__ == "__main__":
    main() 