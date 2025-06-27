#!/usr/bin/env python3
"""
Script to fix existing audio records in DynamoDB that have incorrect bucket_location values.
The issue is that bucket_location is missing the userId prefix in the path.
"""

import boto3
import json
from datetime import datetime

# Configuration
AWS_REGION = 'us-east-1'
DYNAMODB_TABLE = 'easy-video-share-video-metadata'  # Correct table name

def fix_audio_bucket_locations():
    """Fix bucket_location values for existing audio records"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"🔍 Scanning table {DYNAMODB_TABLE} for audio records...")
    
    # Scan for audio records (media_type = 'audio')
    scan_kwargs = {
        'FilterExpression': 'media_type = :mediaType',
        'ExpressionAttributeValues': {
            ':mediaType': 'audio'
        }
    }
    
    fixed_count = 0
    error_count = 0
    
    try:
        # Scan the table
        response = table.scan(**scan_kwargs)
        
        for item in response.get('Items', []):
            try:
                # Check if this is an audio record
                if item.get('media_type') != 'audio':
                    continue
                
                current_bucket_location = item.get('bucket_location', '')
                user_id = item.get('user_id', '')
                audio_id = item.get('video_id', '')  # audio_id is stored in video_id field
                
                print(f"\n📋 Processing audio record:")
                print(f"   Audio ID: {audio_id}")
                print(f"   User ID: {user_id}")
                print(f"   Current bucket_location: {current_bucket_location}")
                
                # Check if bucket_location already has the correct format
                if current_bucket_location.startswith(f'audio/{user_id}/'):
                    print(f"   ✅ Already correct format - skipping")
                    continue
                
                # Check if it's in the wrong format (missing userId)
                if current_bucket_location.startswith('audio/') and '/' in current_bucket_location[6:]:
                    # Extract the audioId and filename from the wrong format
                    # Wrong format: audio/audioId/filename
                    # Correct format: audio/userId/audioId/filename
                    parts = current_bucket_location.split('/')
                    if len(parts) >= 3:
                        audio_id_part = parts[1]
                        filename_part = '/'.join(parts[2:])
                        
                        # Construct the correct bucket_location
                        correct_bucket_location = f'audio/{user_id}/{audio_id_part}/{filename_part}'
                        
                        print(f"   🔧 Fixing bucket_location:")
                        print(f"      From: {current_bucket_location}")
                        print(f"      To:   {correct_bucket_location}")
                        
                        # Update the record
                        update_response = table.update_item(
                            Key={'video_id': audio_id},
                            UpdateExpression='SET bucket_location = :bucket_location, updated_at = :updated_at',
                            ExpressionAttributeValues={
                                ':bucket_location': correct_bucket_location,
                                ':updated_at': datetime.utcnow().isoformat() + 'Z'
                            }
                        )
                        
                        print(f"   ✅ Updated successfully")
                        fixed_count += 1
                    else:
                        print(f"   ❌ Invalid bucket_location format - cannot parse")
                        error_count += 1
                else:
                    print(f"   ❌ Unexpected bucket_location format - skipping")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing record: {str(e)}")
                error_count += 1
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            
            for item in response.get('Items', []):
                try:
                    # Same processing logic as above
                    if item.get('media_type') != 'audio':
                        continue
                    
                    current_bucket_location = item.get('bucket_location', '')
                    user_id = item.get('user_id', '')
                    audio_id = item.get('video_id', '')
                    
                    print(f"\n📋 Processing audio record:")
                    print(f"   Audio ID: {audio_id}")
                    print(f"   User ID: {user_id}")
                    print(f"   Current bucket_location: {current_bucket_location}")
                    
                    if current_bucket_location.startswith(f'audio/{user_id}/'):
                        print(f"   ✅ Already correct format - skipping")
                        continue
                    
                    if current_bucket_location.startswith('audio/') and '/' in current_bucket_location[6:]:
                        parts = current_bucket_location.split('/')
                        if len(parts) >= 3:
                            audio_id_part = parts[1]
                            filename_part = '/'.join(parts[2:])
                            correct_bucket_location = f'audio/{user_id}/{audio_id_part}/{filename_part}'
                            
                            print(f"   🔧 Fixing bucket_location:")
                            print(f"      From: {current_bucket_location}")
                            print(f"      To:   {correct_bucket_location}")
                            
                            table.update_item(
                                Key={'video_id': audio_id},
                                UpdateExpression='SET bucket_location = :bucket_location, updated_at = :updated_at',
                                ExpressionAttributeValues={
                                    ':bucket_location': correct_bucket_location,
                                    ':updated_at': datetime.utcnow().isoformat() + 'Z'
                                }
                            )
                            
                            print(f"   ✅ Updated successfully")
                            fixed_count += 1
                        else:
                            print(f"   ❌ Invalid bucket_location format - cannot parse")
                            error_count += 1
                    else:
                        print(f"   ❌ Unexpected bucket_location format - skipping")
                        error_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Error processing record: {str(e)}")
                    error_count += 1
    
    except Exception as e:
        print(f"❌ Error scanning table: {str(e)}")
        return
    
    print(f"\n🎉 Database fix completed!")
    print(f"   ✅ Fixed records: {fixed_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📊 Total processed: {fixed_count + error_count}")

if __name__ == "__main__":
    print("🔧 Audio Bucket Location Fix Script")
    print("=" * 50)
    
    # Confirm before running
    response = input("This will update existing audio records in the database. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        exit(0)
    
    fix_audio_bucket_locations() 