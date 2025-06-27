#!/usr/bin/env python3
"""
Script to check what files actually exist in the S3 audio bucket
"""

import boto3

# Configuration
AWS_REGION = 'us-east-1'
AUDIO_BUCKET = 'easy-video-share-silmari-dev-audio'

def check_s3_files():
    """Check what files actually exist in the S3 audio bucket"""
    
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    print(f"🔍 Checking S3 audio bucket: {AUDIO_BUCKET}")
    
    try:
        # List all objects in the audio bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=AUDIO_BUCKET)
        
        all_files = []
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    all_files.append(obj['Key'])
        
        print(f"\n📋 Found {len(all_files)} files in S3 audio bucket:")
        
        # Look for files related to the failing audio ID
        target_audio_id = "a4185468-0041-703d-bc96-b2163fdc7695_1750936999098_3ij216e8v"
        target_filename = "bdaaUNRFWHJ5eCVy6mgkT_output.mp3"
        
        print(f"\n🔍 Looking for files related to audio ID: {target_audio_id}")
        print(f"🔍 Looking for filename: {target_filename}")
        
        matching_files = []
        for file_key in all_files:
            if target_audio_id in file_key or target_filename in file_key:
                matching_files.append(file_key)
        
        if matching_files:
            print(f"\n✅ Found {len(matching_files)} matching files:")
            for file_key in matching_files:
                print(f"   📁 {file_key}")
        else:
            print(f"\n❌ No files found matching the audio ID or filename")
            
        # Show all files in the audio directory
        print(f"\n📁 All files in audio/ directory:")
        audio_files = [f for f in all_files if f.startswith('audio/')]
        for file_key in audio_files:
            print(f"   📁 {file_key}")
            
    except Exception as e:
        print(f"❌ Error checking S3: {str(e)}")

if __name__ == "__main__":
    check_s3_files() 