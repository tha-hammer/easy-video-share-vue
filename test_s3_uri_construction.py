#!/usr/bin/env python3
"""
Test script to verify S3 URI construction with the current database record
"""

import boto3
import json

# Configuration
AWS_REGION = 'us-east-1'
DYNAMODB_TABLE = 'easy-video-share-video-metadata'
AUDIO_BUCKET = 'easy-video-share-silmari-dev-audio'

def test_s3_uri_construction():
    """Test the exact S3 URI construction that the Lambda would use"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # The specific audio ID that's failing
    audio_id = "a4185468-0041-703d-bc96-b2163fdc7695_1750936999098_3ij216e8v"
    user_id = "a4185468-0041-703d-bc96-b2163fdc7695"
    
    print(f"🔍 Testing S3 URI construction for audio: {audio_id}")
    
    try:
        # Get the audio metadata (same as Lambda does)
        response = table.get_item(
            Key={'video_id': audio_id}
        )
        
        if 'Item' not in response:
            print(f"❌ Audio record not found!")
            return
        
        audio_metadata = response['Item']
        
        print(f"\n📋 Audio metadata retrieved:")
        print(f"   Bucket Location: {audio_metadata.get('bucket_location', 'N/A')}")
        print(f"   Content Type: {audio_metadata.get('content_type', 'N/A')}")
        
        # Simulate the Lambda's S3 URI construction
        bucket_location = audio_metadata.get('bucket_location', '')
        
        # This is what the Lambda should be doing (from the fixed code)
        file_uri = f"s3://{AUDIO_BUCKET}/{bucket_location}"
        
        print(f"\n🔧 S3 URI Construction:")
        print(f"   Audio Bucket: {AUDIO_BUCKET}")
        print(f"   Bucket Location: {bucket_location}")
        print(f"   Final S3 URI: {file_uri}")
        
        # Check if the file actually exists in S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        try:
            # Try to get the object metadata
            s3_response = s3_client.head_object(
                Bucket=AUDIO_BUCKET,
                Key=bucket_location
            )
            print(f"\n✅ File EXISTS in S3!")
            print(f"   Size: {s3_response.get('ContentLength', 'N/A')} bytes")
            print(f"   Content Type: {s3_response.get('ContentType', 'N/A')}")
            print(f"   Last Modified: {s3_response.get('LastModified', 'N/A')}")
        except s3_client.exceptions.NoSuchKey:
            print(f"\n❌ File DOES NOT EXIST in S3!")
            print(f"   Bucket: {AUDIO_BUCKET}")
            print(f"   Key: {bucket_location}")
        except Exception as e:
            print(f"\n❌ Error checking S3: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_s3_uri_construction() 