#!/usr/bin/env python3
"""
Sprint 2 Complete Validation Suite

This script provides a comprehensive validation of Sprint 2 implementation,
including infrastructure setup, service validation, and end-to-end testing.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

class Sprint2Validator:
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent
        self.test_video_path = self.backend_dir / "test_video.mp4"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        symbols = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "❌", "WARNING": "⚠"}
        symbol = symbols.get(level, "•")
        print(f"[{timestamp}] {symbol} {message}")
        
    def check_dependencies(self) -> bool:
        """Check all required dependencies"""
        self.log("Checking dependencies...", "INFO")
        
        dependencies = [
            ("Python", ["python", "--version"]),
            ("FFmpeg", ["ffmpeg", "-version"]),
            ("Redis (python package)", ["python", "-c", "import redis; print('Redis package OK')"]),
            ("Celery", ["python", "-c", "import celery; print('Celery package OK')"]),
            ("FastAPI", ["python", "-c", "import fastapi; print('FastAPI package OK')"]),
        ]
        
        all_good = True
        for name, cmd in dependencies:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log(f"{name}: Available", "SUCCESS")
                else:
                    self.log(f"{name}: Command failed", "ERROR")
                    all_good = False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log(f"{name}: Not found", "ERROR")
                all_good = False
                
        return all_good
    
    def check_redis_service(self) -> bool:
        """Check if Redis service is running"""
        self.log("Checking Redis service...", "INFO")
        
        try:
            result = subprocess.run([
                "python", "-c", 
                "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("Redis service: Running", "SUCCESS")
                return True
            else:
                self.log("Redis service: Not responding", "ERROR")
                return False
        except Exception as e:
            self.log(f"Redis service: Error - {e}", "ERROR")
            return False
            
    def check_aws_credentials(self) -> bool:
        """Check AWS credentials"""
        self.log("Checking AWS credentials...", "INFO")
        
        try:
            result = subprocess.run([
                "python", "-c",
                "import boto3; s3 = boto3.client('s3', region_name='us-east-1'); s3.list_buckets(); print('AWS OK')"
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.log("AWS credentials: Valid", "SUCCESS")
                return True
            else:
                self.log("AWS credentials: Invalid or not configured", "ERROR")
                return False
        except Exception as e:
            self.log(f"AWS credentials: Error - {e}", "ERROR")
            return False
            
    def create_test_video(self) -> bool:
        """Create test video if it doesn't exist"""
        if self.test_video_path.exists():
            self.log(f"Test video already exists: {self.test_video_path}", "SUCCESS")
            return True
            
        self.log("Creating test video...", "INFO")
        
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            result = subprocess.run([
                "python", "create_test_video.py"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and self.test_video_path.exists():
                self.log("Test video created successfully", "SUCCESS")
                return True
            else:
                self.log(f"Failed to create test video: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error creating test video: {e}", "ERROR")
            return False
            
    def start_services(self) -> bool:
        """Start required services"""
        self.log("Starting services...", "INFO")
        
        # Start Redis if not running
        if not self.check_redis_service():
            self.log("Starting Redis...", "INFO")
            try:
                redis_script = self.project_root / "scripts" / "start-redis.ps1"
                if redis_script.exists():
                    subprocess.run(["powershell", "-File", str(redis_script)], 
                                 capture_output=True, timeout=30)
                    time.sleep(3)
                    
                    if self.check_redis_service():
                        self.log("Redis started successfully", "SUCCESS")
                    else:
                        self.log("Failed to start Redis", "ERROR")
                        return False
                else:
                    self.log("Redis start script not found", "ERROR")
                    return False
            except Exception as e:
                self.log(f"Error starting Redis: {e}", "ERROR")
                return False
        
        return True
        
    def run_infrastructure_tests(self) -> bool:
        """Run infrastructure validation tests"""
        self.log("Running infrastructure tests...", "INFO")
        
        test_scripts = [
            "test_redis_connection.py",
            "test_aws_auth.py", 
            "diagnose_ffmpeg.py"
        ]
        
        all_passed = True
        for script in test_scripts:
            script_path = self.backend_dir / script
            if script_path.exists():
                try:
                    self.log(f"Running {script}...", "INFO")
                    result = subprocess.run([
                        "python", str(script_path)
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        self.log(f"{script}: PASSED", "SUCCESS")
                    else:
                        self.log(f"{script}: FAILED - {result.stderr}", "ERROR")
                        all_passed = False
                except Exception as e:
                    self.log(f"{script}: ERROR - {e}", "ERROR")
                    all_passed = False
            else:
                self.log(f"{script}: Not found", "WARNING")
                
        return all_passed
        
    def run_video_processing_test(self) -> bool:
        """Run video processing validation"""
        self.log("Running video processing test...", "INFO")
        
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            result = subprocess.run([
                "python", "-c", f"""
import sys
sys.path.append('.')
from video_processor import split_and_overlay_hardcoded, validate_video_file

# Validate test video
if not validate_video_file('{self.test_video_path}'):
    print('Test video validation failed')
    sys.exit(1)

print('Test video is valid')

# Test processing (dry run)
try:
    output_prefix = 'test_output'
    outputs = split_and_overlay_hardcoded('{self.test_video_path}', output_prefix)
    print(f'Processing test successful - would create {{len(outputs)}} segments')
except Exception as e:
    print(f'Processing test failed: {{e}}')
    sys.exit(1)
"""
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log("Video processing test: PASSED", "SUCCESS")
                return True
            else:
                self.log(f"Video processing test: FAILED - {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Video processing test: ERROR - {e}", "ERROR")
            return False
            
    def run_validation_suite(self) -> bool:
        """Run the complete validation suite"""
        self.log("=" * 60, "INFO")
        self.log("Starting Sprint 2 Complete Validation", "INFO") 
        self.log("=" * 60, "INFO")
        
        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Check AWS Credentials", self.check_aws_credentials),
            ("Create Test Video", self.create_test_video),
            ("Start Services", self.start_services),
            ("Run Infrastructure Tests", self.run_infrastructure_tests),
            ("Run Video Processing Test", self.run_video_processing_test),
        ]
        
        for step_name, step_func in steps:
            self.log(f"\n--- {step_name} ---", "INFO")
            
            if not step_func():
                self.log(f"❌ {step_name} FAILED", "ERROR")
                self.log("Validation stopped due to failure", "ERROR")
                return False
            else:
                self.log(f"✓ {step_name} PASSED", "SUCCESS")
                
        self.log("\n" + "=" * 60, "INFO")
        self.log("🎉 ALL VALIDATION STEPS PASSED!", "SUCCESS")
        self.log("Sprint 2 infrastructure is ready for end-to-end testing", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        return True
        
    def show_next_steps(self):
        """Show next steps after validation"""
        print("\n🚀 Next Steps:")
        print("1. Start all services:")
        print("   powershell -File scripts/start-sprint2-services.ps1")
        print("\n2. Run end-to-end test:")
        print("   python backend/test_sprint2_e2e.py")
        print("\n3. View API documentation:")
        print("   http://localhost:8000/docs")
        print("\n4. Clean up test files when done:")
        print("   python backend/cleanup_test_files.py")


def main():
    """Main function"""
    validator = Sprint2Validator()
    
    try:
        success = validator.run_validation_suite()
        
        if success:
            validator.show_next_steps()
            return True
        else:
            print("\n❌ Validation failed. Please fix the issues and try again.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠ Validation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during validation: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
