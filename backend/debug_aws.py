#!/usr/bin/env python3
"""
Debug AWS credentials being used by boto3
"""

import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def debug_aws_credentials():
    """Debug what AWS credentials boto3 is actually using"""
    print("🔍 Debugging AWS Credentials...")
    
    try:
        # Create session to check credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            print(f"✅ AWS Credentials found:")
            print(f"   Access Key: {credentials.access_key[:10]}...")
            print(f"   Secret Key: {credentials.secret_key[:10] if credentials.secret_key else 'None'}...")
            print(f"   Token: {'Yes' if credentials.token else 'No'}")
        else:
            print("❌ No AWS credentials found")
            return False
            
        # Test S3 access
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Try to list buckets to verify credentials work
        print("\n🔍 Testing S3 access...")
        response = s3_client.list_buckets()
        print("✅ S3 access successful")
        
        # Check if our bucket exists
        bucket_name = "easy-video-share-silmari-dev"
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        
        if bucket_name in buckets:
            print(f"✅ Bucket '{bucket_name}' found")
            
            # Check bucket region
            try:
                bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
                region = bucket_location['LocationConstraint'] or 'us-east-1'
                print(f"📍 Bucket region: {region}")
            except Exception as e:
                print(f"⚠️  Could not determine bucket region: {e}")
        else:
            print(f"❌ Bucket '{bucket_name}' not found")
            print(f"Available buckets: {buckets}")
            return False
            
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials configured")
        print("Run: aws configure")
        return False
    except ClientError as e:
        print(f"❌ AWS access error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    debug_aws_credentials()
