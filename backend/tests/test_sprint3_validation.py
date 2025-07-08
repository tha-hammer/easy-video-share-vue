#!/usr/bin/env python3
"""
Sprint 3 Validation Test Script

This script validates the Sprint 3 implementation:
1. Tests the analyze-duration endpoint with various cutting options
2. Validates that the new complete-upload endpoint accepts cutting options and text strategy
3. Verifies the video duration analysis functionality

Requirements:
- Backend API running (python main.py)
- Test video file uploaded to S3 or available for testing
- AWS credentials configured
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

class Sprint3Validator:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_health_check(self) -> bool:
        """Test API health"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("✓ API is running and healthy")
                return True
            else:
                self.log(f"API health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Cannot connect to API: {e}", "ERROR")
            return False
    
    def test_analyze_duration_fixed(self, s3_key: str) -> bool:
        """Test analyze-duration endpoint with fixed cutting options"""
        self.log("Testing analyze-duration with fixed cutting options...")
        
        payload = {
            "s3_key": s3_key,
            "cutting_options": {
                "type": "fixed",
                "duration_seconds": 30
            }
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/video/analyze-duration", 
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✓ Fixed cutting analysis successful:")
                self.log(f"  Total duration: {result['total_duration']:.2f}s")
                self.log(f"  Number of segments: {result['num_segments']}")
                self.log(f"  Segment durations: {result['segment_durations']}")
                return True
            else:
                self.log(f"Fixed cutting analysis failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Fixed cutting analysis error: {e}", "ERROR")
            return False
    
    def test_analyze_duration_random(self, s3_key: str) -> bool:
        """Test analyze-duration endpoint with random cutting options"""
        self.log("Testing analyze-duration with random cutting options...")
        
        payload = {
            "s3_key": s3_key,
            "cutting_options": {
                "type": "random",
                "min_duration": 15,
                "max_duration": 45
            }
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/video/analyze-duration", 
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✓ Random cutting analysis successful:")
                self.log(f"  Total duration: {result['total_duration']:.2f}s")
                self.log(f"  Number of segments: {result['num_segments']}")
                self.log(f"  Segment durations: {result['segment_durations']}")
                return True
            else:
                self.log(f"Random cutting analysis failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Random cutting analysis error: {e}", "ERROR")
            return False
    
    def test_analyze_duration_invalid_s3_key(self) -> bool:
        """Test analyze-duration endpoint with invalid S3 key"""
        self.log("Testing analyze-duration with invalid S3 key...")
        
        payload = {
            "s3_key": "nonexistent/video.mp4",
            "cutting_options": {
                "type": "fixed",
                "duration_seconds": 30
            }
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/video/analyze-duration", 
                json=payload
            )
            
            if response.status_code == 404:
                self.log("✓ Correctly returned 404 for invalid S3 key")
                return True
            else:
                self.log(f"Expected 404 for invalid S3 key, got: {response.status_code}", "ERROR")
                self.log(f"Response body: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Invalid S3 key test error: {e}", "ERROR")
            return False
    
    def test_complete_upload_with_cutting_options(self, s3_key: str, job_id: str) -> bool:
        """Test complete-upload endpoint with cutting options and text strategy"""
        self.log("Testing complete-upload with cutting options and text strategy...")
        
        payload = {
            "s3_key": s3_key,
            "job_id": job_id,
            "cutting_options": {
                "type": "fixed",
                "duration_seconds": 20
            },
            "text_strategy": "one_for_all"
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/upload/complete", 
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                celery_job_id = result['job_id']
                self.log(f"✓ Complete upload with options successful:")
                self.log(f"  Original Job ID: {job_id}")
                self.log(f"  Celery Job ID: {celery_job_id}")
                self.log(f"  Status: {result['status']}")
                
                # Optional: Check job status briefly to ensure it's actually processing
                self.log("Checking if job is actually queued...")
                status_response = self.session.get(f"{self.api_base_url}/jobs/{celery_job_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    self.log(f"  Job status check: {status_data.get('status', 'UNKNOWN')}")
                
                return True
            else:
                self.log(f"Complete upload failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Complete upload test error: {e}", "ERROR")
            return False
    
    def run_tests(self, test_s3_key: str = None) -> bool:
        """Run all Sprint 3 validation tests"""
        self.log("=== Starting Sprint 3 Validation Tests ===")
        
        # Test 1: Health check
        if not self.test_health_check():
            return False
        
        # Test 2: Analyze duration endpoints (requires valid S3 key)
        if not self.test_analyze_duration_fixed(test_s3_key):
            return False
        if not self.test_analyze_duration_random(test_s3_key):
            return False
        
        # Test 3: Error handling
        if not self.test_analyze_duration_invalid_s3_key():
            return False
        
        # Test 4: Complete upload with options (using real data)
        import uuid
        real_job_id = str(uuid.uuid4())
        self.log("Testing complete upload with real S3 key and cutting options...")
        if not self.test_complete_upload_with_cutting_options(test_s3_key, real_job_id):
            return False
        
        self.log("=== Sprint 3 Validation Tests Completed ===")
        return True


def main():
    """Main function"""
    print("Sprint 3 Validation Tool")
    print("=" * 50)
    print()
    print("This script tests the Sprint 3 implementation:")
    print("1. Video duration analysis with cutting options")
    print("2. Updated complete-upload endpoint with new parameters")
    print("3. Error handling for invalid inputs")
    print()
    
    # Get test S3 key from user
    test_s3_key = input("Enter a valid S3 key for testing (REQUIRED for complete testing): ").strip()
    if not test_s3_key:
        print("ERROR: S3 key is required for production testing!")
        print("Please provide a real S3 key of an uploaded video file.")
        return
    
    print()
    
    # Run validation
    validator = Sprint3Validator(API_BASE_URL)
    validator.run_tests(test_s3_key)


if __name__ == "__main__":
    main()
