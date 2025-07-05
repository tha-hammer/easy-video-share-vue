#!/usr/bin/env python3
"""
Script to fix video_id mismatch in segments.
This script updates segments that have the wrong video_id to match the video being viewed in the frontend.
"""

import boto3
from decimal import Decimal
import json

# AWS Configuration
AWS_REGION = 'us-east-1'
TABLE_NAME = 'easy-video-share-video-metadata'

def fix_segment_video_ids():
    """
    Fix segments that have video_id '59f20d7b-23ad-48ff-a8f4-cfa3c280f7eb' 
    to use video_id '5e910883-ebc9-4d44-91a9-162eff750d46'
    """
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
    
    # The video_id that segments currently have
    old_video_id = '59f20d7b-23ad-48ff-a8f4-cfa3c280f7eb'
    
    # The video_id that the frontend is expecting
    new_video_id = '5e910883-ebc9-4d44-91a9-162eff750d46'
    
    print(f"🔧 Fixing segments: {old_video_id} -> {new_video_id}")
    
    try:
        # Query segments with the old video_id
        response = table.query(
            IndexName='video_id-segment_type-index',
            KeyConditionExpression='video_id = :vid',
            ExpressionAttributeValues={
                ':vid': old_video_id
            }
        )
        
        segments = response.get('Items', [])
        print(f"📊 Found {len(segments)} segments to update")
        
        if not segments:
            print("❌ No segments found with the old video_id")
            return
        
        # Update each segment
        updated_count = 0
        for segment in segments:
            segment_id = segment['segment_id']
            
            try:
                # Update the video_id
                table.update_item(
                    Key={'segment_id': segment_id},
                    UpdateExpression='SET video_id = :new_vid',
                    ExpressionAttributeValues={
                        ':new_vid': new_video_id
                    }
                )
                
                print(f"✅ Updated segment {segment_id}")
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Failed to update segment {segment_id}: {e}")
        
        print(f"🎉 Successfully updated {updated_count} segments")
        
        # Verify the fix
        print("\n🔍 Verifying the fix...")
        verify_response = table.query(
            IndexName='video_id-segment_type-index',
            KeyConditionExpression='video_id = :vid',
            ExpressionAttributeValues={
                ':vid': new_video_id
            }
        )
        
        verified_segments = verify_response.get('Items', [])
        print(f"✅ Found {len(verified_segments)} segments with the new video_id")
        
        # Check if old segments still exist
        old_response = table.query(
            IndexName='video_id-segment_type-index',
            KeyConditionExpression='video_id = :vid',
            ExpressionAttributeValues={
                ':vid': old_video_id
            }
        )
        
        old_segments = old_response.get('Items', [])
        print(f"📊 {len(old_segments)} segments still have the old video_id")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_segment_video_ids() 