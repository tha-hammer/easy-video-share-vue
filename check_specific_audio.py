#!/usr/bin/env python3
"""
Script to check a specific audio record in DynamoDB
"""

import boto3
import json

# Configuration
AWS_REGION = 'us-east-1'
DYNAMODB_TABLE = 'easy-video-share-video-metadata'

def check_specific_audio():
    """Check the specific audio record that's failing"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # The specific audio ID that's failing
    audio_id = "a4185468-0041-703d-bc96-b2163fdc7695_1750936999098_3ij216e8v"
    user_id = "a4185468-0041-703d-bc96-b2163fdc7695"
    
    print(f"🔍 Checking specific audio record:")
    print(f"   Audio ID: {audio_id}")
    print(f"   User ID: {user_id}")
    
    try:
        # Get the specific item
        response = table.get_item(
            Key={'video_id': audio_id}
        )
        
        if 'Item' not in response:
            print(f"❌ Audio record not found!")
            return
        
        item = response['Item']
        
        print(f"\n📋 Audio record found:")
        print(f"   Title: {item.get('title', 'N/A')}")
        print(f"   Filename: {item.get('filename', 'N/A')}")
        print(f"   Bucket Location: {item.get('bucket_location', 'N/A')}")
        print(f"   Media Type: {item.get('media_type', 'N/A')}")
        print(f"   User ID: {item.get('user_id', 'N/A')}")
        print(f"   Created At: {item.get('created_at', 'N/A')}")
        print(f"   Updated At: {item.get('updated_at', 'N/A')}")
        
        # Check if bucket_location is correct
        bucket_location = item.get('bucket_location', '')
        if bucket_location.startswith(f'audio/{user_id}/'):
            print(f"\n✅ Bucket location is CORRECT format")
        elif bucket_location.startswith('audio/') and '/' in bucket_location[6:]:
            print(f"\n❌ Bucket location is WRONG format (missing userId prefix)")
            print(f"   Current: {bucket_location}")
            
            # Show what it should be
            parts = bucket_location.split('/')
            if len(parts) >= 3:
                audio_id_part = parts[1]
                filename_part = '/'.join(parts[2:])
                correct_format = f'audio/{user_id}/{audio_id_part}/{filename_part}'
                print(f"   Should be: {correct_format}")
        else:
            print(f"\n❓ Unexpected bucket_location format: {bucket_location}")
            
    except Exception as e:
        print(f"❌ Error checking audio record: {str(e)}")

if __name__ == "__main__":
    check_specific_audio() 