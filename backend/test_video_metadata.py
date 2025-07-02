#!/usr/bin/env python3
"""
Test script to check video metadata in DynamoDB
"""
import os
import sys
from dynamodb_service import list_videos, get_job_status

def test_video_metadata():
    """Test and display video metadata from DynamoDB"""
    print("🔍 Testing Video Metadata in DynamoDB")
    print("=" * 50)
    
    # List all videos
    print("\n1. Listing all videos from DynamoDB:")
    videos = list_videos()
    print(f"Found {len(videos)} videos")
    
    for i, video in enumerate(videos):
        print(f"\n--- Video {i+1} ---")
        print(f"video_id: {video.get('video_id')}")
        print(f"title: {video.get('title')}")
        print(f"filename: {video.get('filename')}")
        print(f"file_size: {video.get('file_size')}")
        print(f"user_email: {video.get('user_email')}")
        print(f"bucket_location: {video.get('bucket_location')}")
        print(f"status: {video.get('status')}")
        print(f"duration: {video.get('duration')}")
        print(f"output_s3_urls: {video.get('output_s3_urls')}")
        print(f"error_message: {video.get('error_message')}")
    
    # Test individual job status
    if videos:
        print(f"\n2. Testing individual job status for first video:")
        first_video = videos[0]
        job_id = first_video.get('video_id')
        if job_id:
            job_status = get_job_status(job_id)
            print(f"Job status for {job_id}:")
            print(job_status)

if __name__ == "__main__":
    test_video_metadata() 