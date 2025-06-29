#!/usr/bin/env python3
"""
Celery Task Signature Verification
Debug script to check current task signatures and help with Celery worker restart
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_task_signature():
    """Check the current task signature"""
    print("🔍 Checking Celery Task Signature")
    print("=" * 40)
    
    try:
        from tasks import process_video_task
        import inspect
        
        # Get function signature
        sig = inspect.signature(process_video_task.run)
        print(f"✅ Current task signature: {sig}")
        
        # Check parameters
        params = list(sig.parameters.keys())
        print(f"📋 Parameters: {params}")
        
        required_params = ['s3_input_key', 'job_id', 'cutting_options', 'text_strategy', 'text_input']
        missing_params = [p for p in required_params if p not in params]
        
        if missing_params:
            print(f"❌ Missing parameters: {missing_params}")
            return False
        else:
            print("✅ All required parameters present")
            return True
            
    except Exception as e:
        print(f"❌ Error checking task signature: {str(e)}")
        return False

def print_restart_instructions():
    """Print Celery worker restart instructions"""
    print("\n🔄 Celery Worker Restart Instructions")
    print("=" * 45)
    print("The error suggests Celery worker is using an older task definition.")
    print("Follow these steps to fix:")
    print()
    print("1. Stop the current Celery worker (Ctrl+C)")
    print("2. Restart with fresh code:")
    print("   cd backend")
    print("   celery -A tasks worker --loglevel=info")
    print()
    print("3. Verify worker logs show the correct task signature")
    print("4. Re-run the manual test script")
    print()
    print("💡 Tip: Celery workers cache task definitions.")
    print("   Always restart after changing task signatures.")

def main():
    print("🛠️  Celery Task Debug Tool - Sprint 4.1")
    print("=" * 50)
    
    signature_ok = check_task_signature()
    print_restart_instructions()
    
    if signature_ok:
        print("\n✅ Task signature is correct in the code.")
        print("   The issue is likely a stale Celery worker.")
    else:
        print("\n❌ Task signature has issues in the code.")
        print("   Fix the task definition before restarting worker.")

if __name__ == "__main__":
    main()
