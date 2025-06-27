#!/usr/bin/env python3
"""
Script to delete corrupted audio database records
"""

import boto3
import json

# Configuration
AWS_REGION = 'us-east-1'
DYNAMODB_TABLE = 'easy-video-share-video-metadata'

def delete_corrupted_audio():
    """Delete the corrupted audio database record"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # The corrupted audio ID
    corrupted_audio_id = "a4185468-0041-703d-bc96-b2163fdc7695_1750936999098_3ij216e8v"
    
    print(f"🗑️ Deleting corrupted audio record:")
    print(f"   Audio ID: {corrupted_audio_id}")
    
    try:
        # First, check if the record exists
        response = table.get_item(
            Key={'video_id': corrupted_audio_id}
        )
        
        if 'Item' not in response:
            print(f"❌ Audio record not found - nothing to delete")
            return
        
        item = response['Item']
        print(f"\n📋 Found audio record to delete:")
        print(f"   Title: {item.get('title', 'N/A')}")
        print(f"   Filename: {item.get('filename', 'N/A')}")
        print(f"   Bucket Location: {item.get('bucket_location', 'N/A')}")
        print(f"   Media Type: {item.get('media_type', 'N/A')}")
        print(f"   Created At: {item.get('created_at', 'N/A')}")
        
        # Confirm deletion
        confirm = input(f"\n❓ Are you sure you want to delete this record? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Deletion cancelled")
            return
        
        # Delete the record
        delete_response = table.delete_item(
            Key={'video_id': corrupted_audio_id}
        )
        
        print(f"✅ Audio record deleted successfully!")
        print(f"   Deleted Audio ID: {corrupted_audio_id}")
        
    except Exception as e:
        print(f"❌ Error deleting audio record: {str(e)}")

def list_all_audio_records():
    """List all audio records to see what else might be corrupted"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"\n🔍 Listing all audio records in database:")
    
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
        
        for i, record in enumerate(audio_records, 1):
            print(f"\n{i}. Audio ID: {record.get('video_id', 'N/A')}")
            print(f"   Title: {record.get('title', 'N/A')}")
            print(f"   Filename: {record.get('filename', 'N/A')}")
            print(f"   Bucket Location: {record.get('bucket_location', 'N/A')}")
            print(f"   Created At: {record.get('created_at', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error listing audio records: {str(e)}")

if __name__ == "__main__":
    print("🗑️ Audio Record Cleanup Script")
    print("=" * 50)
    
    # Delete the corrupted record
    delete_corrupted_audio()
    
    # List all remaining audio records
    list_all_audio_records() 