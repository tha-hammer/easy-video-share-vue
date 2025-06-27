#!/usr/bin/env python3
"""
Script to check if the remaining audio record has a corresponding S3 file
"""

import boto3
import json

# Configuration
AWS_REGION = 'us-east-1'
S3_BUCKET = 'easy-video-share-silmari-dev'

def check_remaining_audio():
    """Check if the remaining audio record has a corresponding S3 file"""
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    # The remaining audio record details
    audio_id = "a4185468-0041-703d-bc96-b2163fdc7695_1750947518611_mfuznzfnx"
    bucket_location = "audio/a4185468-0041-703d-bc96-b2163fdc7695/a4185468-0041-703d-bc96-b2163fdc7695_1750947518611_mfuznzfnx/ElevenLabs_2025-05-07T20_13_27_Elicia My Bride_ivc_sp100_s50_sb75_se0_b_m2.mp3"
    
    print(f"🔍 Checking remaining audio record:")
    print(f"   Audio ID: {audio_id}")
    print(f"   Bucket Location: {bucket_location}")
    print(f"   S3 Bucket: {S3_BUCKET}")
    
    try:
        # Check if the file exists in S3
        response = s3_client.head_object(
            Bucket=S3_BUCKET,
            Key=bucket_location
        )
        
        print(f"\n✅ S3 file EXISTS!")
        print(f"   Content Length: {response.get('ContentLength', 'N/A')} bytes")
        print(f"   Content Type: {response.get('ContentType', 'N/A')}")
        print(f"   Last Modified: {response.get('LastModified', 'N/A')}")
        print(f"   ETag: {response.get('ETag', 'N/A')}")
        
        # This audio file is valid and can be used for AI video generation
        
    except s3_client.exceptions.NoSuchKey:
        print(f"\n❌ S3 file DOES NOT EXIST!")
        print(f"   The database record points to a non-existent S3 file")
        print(f"   This record should also be deleted")
        
        # Ask if user wants to delete this record too
        confirm = input(f"\n❓ Do you want to delete this corrupted record too? (y/N): ")
        if confirm.lower() == 'y':
            delete_corrupted_record(audio_id)
        
    except Exception as e:
        print(f"\n❌ Error checking S3 file: {str(e)}")

def delete_corrupted_record(audio_id):
    """Delete a corrupted audio record from DynamoDB"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table('easy-video-share-video-metadata')
    
    try:
        delete_response = table.delete_item(
            Key={'video_id': audio_id}
        )
        print(f"✅ Audio record deleted successfully!")
        print(f"   Deleted Audio ID: {audio_id}")
        
    except Exception as e:
        print(f"❌ Error deleting audio record: {str(e)}")

def list_s3_audio_files():
    """List all audio files in S3 to see what actually exists"""
    
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    print(f"\n🔍 Listing all audio files in S3 bucket:")
    print(f"   S3 Bucket: {S3_BUCKET}")
    
    try:
        # List all objects in the audio/ prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=S3_BUCKET,
            Prefix='audio/'
        )
        
        audio_files = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac')):
                        audio_files.append(obj)
        
        print(f"\n📋 Found {len(audio_files)} audio files in S3:")
        
        for i, obj in enumerate(audio_files, 1):
            print(f"\n{i}. S3 Key: {obj['Key']}")
            print(f"   Size: {obj['Size']} bytes")
            print(f"   Last Modified: {obj['LastModified']}")
            
    except Exception as e:
        print(f"❌ Error listing S3 files: {str(e)}")

if __name__ == "__main__":
    print("🔍 Audio File Validation Script")
    print("=" * 50)
    
    # Check the remaining audio record
    check_remaining_audio()
    
    # List all S3 audio files
    list_s3_audio_files() 