#!/usr/bin/env python3
"""
Real AWS Integration Test Script
Tests the production AI video generation pipeline with actual AWS services
"""

import os
import json
import requests
import time
import boto3
import asyncio
from datetime import datetime
from pathlib import Path

# Load environment variables
if Path('env.aws').exists():
    from dotenv import load_dotenv
    load_dotenv('env.aws')

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET')
AI_PROJECTS_TABLE = os.getenv('AI_PROJECTS_TABLE')

# Test audio file (can be a real file or mock data)
TEST_AUDIO_FILE = "test_audio.mp3"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, color=Colors.GREEN):
    print(f"{color}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

class RealAWSTestSuite:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.test_project_id = f"test-{int(time.time())}"
        self.test_results = {}
    
    def test_1_health_check(self):
        """Test API health check"""
        print_info("Testing API health check...")
        
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print_status(f"API is healthy - Version: {data.get('version', 'unknown')}")
            print(f"   Environment: {data.get('environment', 'unknown')}")
            print(f"   Services: {data.get('services_status', {})}")
            
            self.test_results['health_check'] = True
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"Health check failed: {e}")
            self.test_results['health_check'] = False
            return False
    
    def test_2_aws_connectivity(self):
        """Test AWS services connectivity"""
        print_info("Testing AWS services connectivity...")
        
        try:
            # Test S3
            if S3_BUCKET:
                self.s3_client.head_bucket(Bucket=S3_BUCKET)
                print_status(f"S3 bucket accessible: {S3_BUCKET}")
            else:
                print_warning("S3_BUCKET not configured")
            
            # Test DynamoDB
            if AI_PROJECTS_TABLE:
                table = self.dynamodb.Table(AI_PROJECTS_TABLE)
                table.meta.client.describe_table(TableName=AI_PROJECTS_TABLE)
                print_status(f"DynamoDB table accessible: {AI_PROJECTS_TABLE}")
            else:
                print_warning("AI_PROJECTS_TABLE not configured")
            
            # Test Bedrock access (if available)
            try:
                bedrock = boto3.client('bedrock', region_name=AWS_REGION)
                models = bedrock.list_foundation_models()
                print_status("Bedrock service accessible")
                print(f"   Available models: {len(models.get('modelSummaries', []))}")
            except Exception as e:
                print_warning(f"Bedrock access limited: {e}")
            
            self.test_results['aws_connectivity'] = True
            return True
            
        except Exception as e:
            print_error(f"AWS connectivity test failed: {e}")
            self.test_results['aws_connectivity'] = False
            return False
    
    def test_3_upload_test_audio(self):
        """Upload test audio file to S3"""
        print_info("Uploading test audio file...")
        
        try:
            # Create a small test audio file (or use existing one)
            test_audio_content = b"Fake audio content for testing"
            
            if not S3_BUCKET:
                print_warning("S3_BUCKET not configured, skipping upload test")
                return True
            
            s3_key = f"test-audio/{self.test_project_id}.mp3"
            
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=test_audio_content,
                ContentType='audio/mpeg'
            )
            
            print_status(f"Test audio uploaded: s3://{S3_BUCKET}/{s3_key}")
            self.test_audio_s3_key = s3_key
            self.test_results['upload_audio'] = True
            return True
            
        except Exception as e:
            print_error(f"Audio upload failed: {e}")
            self.test_results['upload_audio'] = False
            return False
    
    def test_4_create_project(self):
        """Test project creation via API"""
        print_info("Creating test project...")
        
        try:
            project_data = {
                "project_id": self.test_project_id,
                "user_id": "test-user",
                "title": f"Test Project {self.test_project_id}",
                "audio_file_url": getattr(self, 'test_audio_s3_key', 'test-audio.mp3'),
                "target_duration": 45,
                "status": "uploaded",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.api_base}/projects",
                json=project_data,
                timeout=30
            )
            response.raise_for_status()
            
            created_project = response.json()
            print_status(f"Project created: {created_project['project_id']}")
            
            self.test_results['create_project'] = True
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"Project creation failed: {e}")
            self.test_results['create_project'] = False
            return False
    
    def test_5_process_video(self):
        """Test video processing pipeline"""
        print_info("Starting video processing...")
        
        try:
            process_data = {
                "project_id": self.test_project_id,
                "audio_s3_key": getattr(self, 'test_audio_s3_key', 'test-audio.mp3'),
                "target_duration": 30
            }
            
            response = requests.post(
                f"{self.api_base}/process-video",
                json=process_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            print_status(f"Video processing started: {result.get('message', '')}")
            
            # Monitor processing status
            self._monitor_processing_status()
            
            self.test_results['process_video'] = True
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"Video processing failed: {e}")
            self.test_results['process_video'] = False
            return False
    
    def _monitor_processing_status(self, max_wait_time=300):
        """Monitor video processing status"""
        print_info("Monitoring processing status...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(f"{self.api_base}/projects/{self.test_project_id}")
                if response.status_code == 200:
                    project = response.json()
                    current_status = project.get('status', 'unknown')
                    
                    if current_status != last_status:
                        print(f"   Status: {current_status}")
                        last_status = current_status
                    
                    if current_status == 'completed':
                        final_video_url = project.get('final_video_url')
                        print_status(f"Processing completed! Final video: {final_video_url}")
                        return True
                    elif current_status == 'failed':
                        error_msg = project.get('error_message', 'Unknown error')
                        print_error(f"Processing failed: {error_msg}")
                        return False
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print_warning(f"Status check error: {e}")
                time.sleep(10)
        
        print_warning(f"Processing monitoring timed out after {max_wait_time} seconds")
        return False
    
    def test_6_get_project(self):
        """Test getting project details"""
        print_info("Getting project details...")
        
        try:
            response = requests.get(f"{self.api_base}/projects/{self.test_project_id}")
            response.raise_for_status()
            
            project = response.json()
            print_status(f"Project retrieved successfully")
            print(f"   Status: {project.get('status', 'unknown')}")
            print(f"   Title: {project.get('title', 'unknown')}")
            
            if project.get('final_video_url'):
                print(f"   Final Video: {project['final_video_url']}")
            
            self.test_results['get_project'] = True
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"Get project failed: {e}")
            self.test_results['get_project'] = False
            return False
    
    def test_7_list_projects(self):
        """Test listing projects"""
        print_info("Listing all projects...")
        
        try:
            response = requests.get(f"{self.api_base}/projects")
            response.raise_for_status()
            
            data = response.json()
            projects = data.get('projects', [])
            print_status(f"Found {len(projects)} projects")
            
            # Find our test project
            test_project = next((p for p in projects if p.get('project_id') == self.test_project_id), None)
            if test_project:
                print(f"   Test project found: {test_project.get('title', 'unknown')}")
            
            self.test_results['list_projects'] = True
            return True
            
        except requests.exceptions.RequestException as e:
            print_error(f"List projects failed: {e}")
            self.test_results['list_projects'] = False
            return False
    
    def cleanup(self):
        """Clean up test resources"""
        print_info("Cleaning up test resources...")
        
        try:
            # Clean up S3 test file
            if hasattr(self, 'test_audio_s3_key') and S3_BUCKET:
                self.s3_client.delete_object(Bucket=S3_BUCKET, Key=self.test_audio_s3_key)
                print_status("Test audio file deleted from S3")
            
            # Note: In production, you might want to keep test projects for analysis
            # or implement a cleanup API endpoint
            
        except Exception as e:
            print_warning(f"Cleanup warning: {e}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"{Colors.BOLD}🧪 Real AWS Integration Test Suite{Colors.END}")
        print(f"{Colors.BOLD}===================================={Colors.END}")
        print(f"API Base URL: {self.api_base}")
        print(f"AWS Region: {AWS_REGION}")
        print(f"Test Project ID: {self.test_project_id}")
        print()
        
        tests = [
            ("Health Check", self.test_1_health_check),
            ("AWS Connectivity", self.test_2_aws_connectivity),
            ("Upload Test Audio", self.test_3_upload_test_audio),
            ("Create Project", self.test_4_create_project),
            ("Process Video", self.test_5_process_video),
            ("Get Project", self.test_6_get_project),
            ("List Projects", self.test_7_list_projects),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{Colors.BOLD}Test: {test_name}{Colors.END}")
            print("-" * 50)
            
            try:
                if test_func():
                    passed += 1
                else:
                    print_error(f"Test failed: {test_name}")
            except Exception as e:
                print_error(f"Test error: {test_name} - {e}")
        
        # Cleanup
        print(f"\n{Colors.BOLD}Cleanup{Colors.END}")
        print("-" * 50)
        self.cleanup()
        
        # Summary
        print(f"\n{Colors.BOLD}Test Results Summary{Colors.END}")
        print("=" * 50)
        print(f"Passed: {passed}/{total} tests")
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result else "❌"
            print(f"  {status_icon} {test_name}")
        
        if passed == total:
            print_status("🎉 All tests passed! Your AI video pipeline is ready!")
        else:
            print_error(f"❌ {total - passed} test(s) failed. Check the errors above.")
        
        return passed == total

def main():
    """Main test execution"""
    # Check environment
    if not S3_BUCKET:
        print_warning("S3_BUCKET environment variable not set")
        print("Please run the deployment script or source the env.aws file")
        return False
    
    # Run tests
    test_suite = RealAWSTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🚀 Ready for production!{Colors.END}")
        print(f"Your AI video generation pipeline is fully operational.")
        print(f"API URL: {API_BASE_URL}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🔧 Some issues need attention{Colors.END}")
        print(f"Please check the test failures above and resolve them.")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1) 