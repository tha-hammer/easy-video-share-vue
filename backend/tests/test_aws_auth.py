#!/usr/bin/env python3
"""
AWS Authentication Test and Fix Script
Tests AWS credentials and provides guidance for fixing authentication issues
"""
import boto3
from botocore.exceptions import TokenRetrievalError, ProfileNotFound, NoCredentialsError
from config import settings

def test_aws_authentication():
    """Test AWS authentication with different methods"""
    print("🔐 AWS Authentication Test")
    print("=" * 40)
    
    # Test 1: SSO Profile
    print(f"1. Testing SSO Profile: {settings.AWS_PROFILE}")
    try:
        session = boto3.Session(profile_name=settings.AWS_PROFILE)
        sts_client = session.client('sts')
        response = sts_client.get_caller_identity()
        
        print("✅ SSO authentication successful!")
        print(f"   Account: {response.get('Account')}")
        print(f"   User: {response.get('Arn')}")
        
        # Test S3 access
        s3_client = session.client('s3', region_name=settings.AWS_REGION)
        s3_client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
        print(f"✅ S3 bucket access successful: {settings.AWS_BUCKET_NAME}")
        
        return True
        
    except TokenRetrievalError:
        print("❌ SSO token has expired or is invalid")
        print(f"   Run: aws sso login --profile {settings.AWS_PROFILE}")
        
    except ProfileNotFound:
        print(f"❌ SSO profile not found: {settings.AWS_PROFILE}")
        print("   Check your ~/.aws/config file")
        
    except Exception as e:
        print(f"❌ SSO authentication failed: {e}")
    
    # Test 2: Environment Variables / Default Credentials
    print("\n2. Testing Environment Variables / Default Credentials")
    try:
        client = boto3.client('sts', region_name=settings.AWS_REGION)
        response = client.get_caller_identity()
        
        print("✅ Default credentials authentication successful!")
        print(f"   Account: {response.get('Account')}")
        print(f"   User: {response.get('Arn')}")
        
        # Test S3 access
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        s3_client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
        print(f"✅ S3 bucket access successful: {settings.AWS_BUCKET_NAME}")
        
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        
    except Exception as e:
        print(f"❌ Default credentials failed: {e}")
    
    return False

def provide_fix_instructions():
    """Provide instructions for fixing AWS authentication"""
    print("\n🛠️  How to Fix AWS Authentication:")
    print("=" * 40)
    
    print("\n📋 Option 1: Refresh SSO Login (Recommended)")
    print(f"   aws sso login --profile {settings.AWS_PROFILE}")
    print("   aws sts get-caller-identity --profile " + settings.AWS_PROFILE)
    
    print("\n📋 Option 2: Use Environment Variables")
    print("   $env:AWS_ACCESS_KEY_ID=\"your-access-key\"")
    print("   $env:AWS_SECRET_ACCESS_KEY=\"your-secret-key\"")
    print("   $env:AWS_DEFAULT_REGION=\"us-east-1\"")
    
    print("\n📋 Option 3: Configure Default Profile")
    print("   aws configure")
    print("   (Enter your access key, secret key, and region)")

def main():
    """Main test function"""
    success = test_aws_authentication()
    
    if not success:
        provide_fix_instructions()
        print("\n❌ AWS authentication test failed")
        print("Fix the authentication issue and run this test again.")
        return 1
    else:
        print("\n✅ AWS authentication is working correctly!")
        print("You can now run the Sprint 2 tests:")
        print("   python test_sprint_2.py")
        return 0

if __name__ == "__main__":
    exit(main())
