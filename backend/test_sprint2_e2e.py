#!/usr/bin/env python3
"""
End-to-End Sprint 2 Validation Test

This script validates the complete Sprint 2 workflow:
1. Initiates upload and gets presigned URL
2. Uploads a real video file to S3
3. Completes upload to trigger processing
4. Polls job status until completion
5. Validates processed outputs in S3

Requirements:
- Backend API running (python main.py)
- Celery worker running (python run_worker.py) 
- Redis running (scripts/start-redis.ps1)
- AWS credentials configured
- Test video file available
"""

import asyncio
import requests
import time
import os
import sys
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
# TEST_VIDEO_PATH = r"C:\Users\Maceo\Downloads\celebrating_the_promise_-_the_birth_of_jesus.mp4"  # You can change this to any video file
TEST_VIDEO_PATH = "test_video.mp4"  # You can change this to any video file

class Sprint2E2EValidator:
    def __init__(self, api_base_url: str, test_video_path: str):
        self.api_base_url = api_base_url
        self.test_video_path = test_video_path
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.log("Checking prerequisites...")
        
        # Check if test video exists
        if not os.path.exists(self.test_video_path):
            self.log(f"Test video not found: {self.test_video_path}", "ERROR")
            self.log("Please provide a test video file or update TEST_VIDEO_PATH", "ERROR")
            return False
            
        # Check API health
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("✓ API is running and healthy")
            else:
                self.log(f"API health check failed: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"Cannot connect to API: {e}", "ERROR")
            self.log("Please ensure the backend API is running (python main.py)", "ERROR")
            return False
            
        self.log("All prerequisites met!")
        return True
        
    def get_file_info(self, file_path: str) -> dict:
        """Get file information for upload"""
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Simple content type detection
        ext = os.path.splitext(filename)[1].lower()
        content_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm'
        }
        content_type = content_type_map.get(ext, 'video/mp4')
        
        return {
            'filename': filename,
            'content_type': content_type,
            'file_size': file_size
        }
        
    def initiate_upload(self, file_info: dict) -> dict:
        """Step 1: Initiate upload and get presigned URL"""
        self.log("Step 1: Initiating upload...")
        
        payload = {
            'filename': file_info['filename'],
            'content_type': file_info['content_type'],
            'file_size': file_info['file_size']
        }
        
        response = self.session.post(f"{self.api_base_url}/upload/initiate", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to initiate upload: {response.status_code} - {response.text}")
            
        result = response.json()
        self.log(f"✓ Upload initiated. Job ID: {result['job_id']}")
        return result
        
    def upload_to_s3(self, presigned_url: str, file_path: str, content_type: str) -> bool:
        """Step 2: Upload file to S3 using presigned URL"""
        self.log("Step 2: Uploading file to S3...")
        
        with open(file_path, 'rb') as file:
            headers = {'Content-Type': content_type}
            response = requests.put(presigned_url, data=file, headers=headers)
            
        if response.status_code in [200, 204]:
            self.log("✓ File uploaded successfully to S3")
            return True
        else:
            raise Exception(f"S3 upload failed: {response.status_code} - {response.text}")
            
    def complete_upload(self, s3_key: str, job_id: str) -> dict:
        """Step 3: Complete upload to trigger processing"""
        self.log("Step 3: Completing upload and starting processing...")
        
        payload = {
            's3_key': s3_key,
            'job_id': job_id
        }
        
        response = self.session.post(f"{self.api_base_url}/upload/complete", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to complete upload: {response.status_code} - {response.text}")
            
        result = response.json()
        self.log(f"✓ Processing started. Status: {result['status']}")
        return result
        
    def poll_job_status(self, job_id: str, max_wait_time: int = 600) -> dict:
        """Step 4: Poll job status until completion"""
        self.log("Step 4: Polling job status...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait_time:
            response = self.session.get(f"{self.api_base_url}/jobs/{job_id}/status")
            
            if response.status_code != 200:
                self.log(f"Failed to get job status: {response.status_code}", "ERROR")
                time.sleep(5)
                continue
                
            status_data = response.json()
            current_status = status_data['status']
            
            if current_status != last_status:
                self.log(f"Job status: {current_status}")
                last_status = current_status
                
            if current_status == "COMPLETED":
                self.log("✓ Job completed successfully!")
                return status_data
            elif current_status == "FAILED":
                error_msg = status_data.get('error_message', 'Unknown error')
                raise Exception(f"Job failed: {error_msg}")
            elif current_status in ["CANCELLED", "REVOKED"]:
                raise Exception(f"Job was cancelled: {current_status}")
                
            time.sleep(10)  # Wait 10 seconds before next poll
            
        raise Exception(f"Job did not complete within {max_wait_time} seconds")
        
    def validate_outputs(self, output_urls: list) -> bool:
        """Step 5: Validate processed outputs"""
        self.log("Step 5: Validating processed outputs...")
        
        if not output_urls:
            raise Exception("No output URLs received")
            
        self.log(f"Found {len(output_urls)} processed video segments")
        
        for i, url in enumerate(output_urls):
            self.log(f"  Segment {i+1}: {url}")
            
            # Try to access each URL to verify it exists
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    self.log(f"  ✓ Segment {i+1} is accessible")
                else:
                    self.log(f"  ⚠ Segment {i+1} returned status {response.status_code}", "WARN")
            except Exception as e:
                self.log(f"  ⚠ Could not verify segment {i+1}: {e}", "WARN")
                
        self.log("✓ Output validation completed")
        return True
        
    def run_test(self) -> bool:
        """Run the complete end-to-end test"""
        try:
            self.log("=== Starting Sprint 2 End-to-End Validation ===")
            
            # Check prerequisites
            if not self.check_prerequisites():
                return False
                
            # Get file information
            file_info = self.get_file_info(self.test_video_path)
            self.log(f"Test file: {file_info['filename']} ({file_info['file_size']} bytes)")
            
            # Step 1: Initiate upload
            upload_data = self.initiate_upload(file_info)
            
            # Step 2: Upload to S3
            self.upload_to_s3(
                upload_data['presigned_url'], 
                self.test_video_path, 
                file_info['content_type']
            )
            
            # Step 3: Complete upload
            complete_result = self.complete_upload(upload_data['s3_key'], upload_data['job_id'])
            
            # Use the job ID returned from complete upload (which is now the Celery task ID)
            celery_job_id = complete_result['job_id']
            self.log(f"Using Celery job ID for tracking: {celery_job_id}")
            
            # Step 4: Poll until completion
            final_status = self.poll_job_status(celery_job_id)
            
            # Step 5: Validate outputs
            output_urls = final_status.get('output_urls', [])
            self.validate_outputs(output_urls)
            
            self.log("=== Sprint 2 End-to-End Validation PASSED ===")
            self.log(f"Successfully processed video into {len(output_urls)} segments")
            
            return True
            
        except Exception as e:
            self.log(f"=== Sprint 2 End-to-End Validation FAILED ===", "ERROR")
            self.log(f"Error: {e}", "ERROR")
            return False


def create_test_video_if_needed():
    """Create a simple test video if none exists"""
    if os.path.exists(TEST_VIDEO_PATH):
        return True
        
    print(f"Test video not found at: {TEST_VIDEO_PATH}")
    print("\nYou can:")
    print("1. Place any video file at the path above")
    print("2. Update TEST_VIDEO_PATH in this script")
    print("3. Run this command to create a simple test video:")
    print(f"   ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=30 -pix_fmt yuv420p {TEST_VIDEO_PATH}")
    
    return False


def main():
    """Main function"""
    print("Sprint 2 End-to-End Validation Tool")
    print("=" * 50)
    
    # Check if test video exists
    if not create_test_video_if_needed():
        return False
        
    # Run the validation
    validator = Sprint2E2EValidator(API_BASE_URL, TEST_VIDEO_PATH)
    success = validator.run_test()
    
    if success:
        print("\n🎉 All tests passed! Sprint 2 is working end-to-end.")
        print("\nNext steps:")
        print("- Clean up test/debug files")
        print("- Prepare for Sprint 3 implementation")
        print("- Consider frontend integration")
    else:
        print("\n❌ Tests failed. Please check the logs and fix issues.")
        
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
