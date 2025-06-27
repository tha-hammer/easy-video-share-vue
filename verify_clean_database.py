#!/usr/bin/env python3
"""
Script to verify the database is clean and ready for testing
"""

import boto3
import json

# Configuration
AWS_REGION = 'us-east-1'
DYNAMODB_TABLE = 'easy-video-share-video-metadata'

def verify_database_clean():
    """Verify that the database is clean and ready for testing"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"🔍 Verifying database is clean:")
    print(f"   Table: {DYNAMODB_TABLE}")
    print(f"   Region: {AWS_REGION}")
    
    try:
        # Scan for all audio records
        response = table.scan(
            FilterExpression='media_type = :mediaType',
            ExpressionAttributeValues={
                ':mediaType': 'audio'
            }
        )
        
        audio_records = response.get('Items', [])
        
        print(f"\n📋 Found {len(audio_records)} audio records:")
        
        if len(audio_records) == 0:
            print(f"✅ Database is clean! No audio records found.")
            print(f"   Ready for fresh audio upload and AI video generation testing.")
        else:
            print(f"⚠️  Found {len(audio_records)} audio records:")
            for i, record in enumerate(audio_records, 1):
                print(f"\n{i}. Audio ID: {record.get('video_id', 'N/A')}")
                print(f"   Title: {record.get('title', 'N/A')}")
                print(f"   Bucket Location: {record.get('bucket_location', 'N/A')}")
                print(f"   Created At: {record.get('created_at', 'N/A')}")
        
        # Also check for any AI video records
        ai_video_response = table.scan(
            FilterExpression='ai_project_type = :aiType',
            ExpressionAttributeValues={
                ':aiType': 'ai_generated'
            }
        )
        
        ai_video_records = ai_video_response.get('Items', [])
        print(f"\n📋 Found {len(ai_video_records)} AI video records:")
        
        if len(ai_video_records) == 0:
            print(f"✅ No AI video records found - clean slate for testing.")
        else:
            for i, record in enumerate(ai_video_records, 1):
                print(f"\n{i}. Video ID: {record.get('video_id', 'N/A')}")
                print(f"   Status: {record.get('ai_generation_status', 'N/A')}")
                print(f"   Created At: {record.get('created_at', 'N/A')}")
        
        return len(audio_records) == 0
        
    except Exception as e:
        print(f"❌ Error verifying database: {str(e)}")
        return False

def test_s3_bucket_access():
    """Test S3 bucket access to ensure everything is working"""
    
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    S3_BUCKET = 'easy-video-share-silmari-dev'
    
    print(f"\n🔍 Testing S3 bucket access:")
    print(f"   Bucket: {S3_BUCKET}")
    
    try:
        # Test bucket access
        response = s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ S3 bucket access successful!")
        
        # List audio directory
        audio_objects = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='audio/',
            MaxKeys=10
        )
        
        audio_count = len(audio_objects.get('Contents', []))
        print(f"📋 Found {audio_count} objects in audio/ directory")
        
        if audio_count == 0:
            print(f"✅ Audio directory is clean - ready for fresh uploads")
        else:
            print(f"⚠️  Audio directory contains {audio_count} objects")
            for obj in audio_objects.get('Contents', [])[:5]:  # Show first 5
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing S3 access: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Database Cleanup Verification")
    print("=" * 50)
    
    # Verify database is clean
    db_clean = verify_database_clean()
    
    # Test S3 access
    s3_working = test_s3_bucket_access()
    
    print(f"\n📊 Summary:")
    print(f"   Database Clean: {'✅ Yes' if db_clean else '❌ No'}")
    print(f"   S3 Access: {'✅ Working' if s3_working else '❌ Failed'}")
    
    if db_clean and s3_working:
        print(f"\n🎉 Ready for testing!")
        print(f"   You can now upload a fresh audio file and test AI video generation.")
        print(f"   The transcription should work properly without the corrupted database records.")
    else:
        print(f"\n⚠️  Some issues remain - please check the errors above.") 