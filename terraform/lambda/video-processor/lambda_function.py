import json
import boto3
import tempfile
import os
import logging
import subprocess
import shutil
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Optional
import uuid

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_decimals_to_floats(obj):
    """Convert Decimal values to float for processing"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_floats(item) for item in obj]
    else:
        return obj

def lambda_handler(event, context):
    """
    Enhanced Lambda handler for two-phase video processing
    """
    logger.info("=== VIDEO PROCESSING LAMBDA STARTED ===")
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Determine processing type
        processing_type = event.get('processing_type', 'full_video_processing')
        
        if processing_type == 'segments_without_text':
            return process_segments_without_text(event, context)
        elif processing_type == 'apply_text_overlays':
            return apply_text_overlays_to_segments(event, context)
        elif processing_type == 'generate_thumbnail':
            return generate_thumbnail(event, context)
        elif processing_type == 'full_video_processing':
            return process_full_video(event, context)
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
            
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        if 'job_id' in event:
            update_job_status(event['job_id'], "FAILED", "failed", 0.0, error_message=str(e))

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': event.get('job_id')
            })
        }

def process_segments_without_text(event, context):
    """
    Phase 1: Process video segments WITHOUT text overlays
    """
    logger.info("=== PROCESSING SEGMENTS WITHOUT TEXT OVERLAYS ===")
    
    try:
        video_s3_key = event['video_s3_key']
        segments = event['segments']
        video_id = event['video_id']
        job_id = event.get('job_id', f"job_{video_id}_{int(time.time())}")
        
        # Download original video
        local_video = download_from_s3(video_s3_key)
        
        processed_segments = []
        temp_storage_paths = []
        
        # Update job status
        update_job_status(job_id, "PROCESSING", "processing_segments", 10.0)
        
        total_segments = len(segments)
        for i, segment in enumerate(segments):
            logger.info(f"Processing segment {i+1}/{total_segments}")
            
            start_time = segment['start']
            duration = segment['end'] - segment['start']
            
            # Process segment without text
            temp_output = f"/tmp/segment_{i}_{video_id}.mp4"
            
            success = process_video_segment(local_video, temp_output, start_time, duration)
            
            if not success:
                logger.error(f"Failed to process segment {i+1}")
                continue
            
            # Check remaining execution time
            remaining_time = context.get_remaining_time_in_millis()
            
            if remaining_time < 60000:  # Less than 1 minute remaining
                # Upload to S3 for later processing
                s3_key = f"temp-segments/{video_id}/segment_{i}.mp4"
                upload_url = upload_to_s3(temp_output, s3_key)
                
                processed_segments.append({
                    'segment_id': f"seg_{video_id}_{i+1:03d}",
                    'segment_number': i + 1,
                    'start_time': start_time,
                    'duration': duration,
                    'storage_type': 's3',
                    'location': s3_key,
                    'temp_segment_path': None,
                    'raw_segment_ready': True,
                    'thumbnail_generated': False
                })
                
                # Clean up temp file
                os.remove(temp_output)
            else:
                # Keep in Lambda temp storage
                processed_segments.append({
                    'segment_id': f"seg_{video_id}_{i+1:03d}",
                    'segment_number': i + 1,
                    'start_time': start_time,
                    'duration': duration,
                    'storage_type': 'lambda_temp',
                    'location': None,
                    'temp_segment_path': temp_output,
                    'raw_segment_ready': True,
                    'thumbnail_generated': False
                })
                temp_storage_paths.append(temp_output)
            
            # Update progress
            progress = 10.0 + (i + 1) / total_segments * 80.0
            update_job_status(job_id, "PROCESSING", "processing_segments", progress)
        
        # Update DynamoDB with segment status
        update_segments_in_dynamodb(video_id, processed_segments)
        
        # Final status update
        update_job_status(job_id, "SEGMENTS_READY", "segments_ready", 90.0)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Segments processed successfully',
                'job_id': job_id,
                'segments': processed_segments,
                'temp_storage_count': len(temp_storage_paths),
                's3_storage_count': len([s for s in processed_segments if s['storage_type'] == 's3'])
            })
        }
        
    except Exception as e:
        logger.error(f"Error in segment processing: {str(e)}")
        raise e

def apply_text_overlays_to_segments(event, context):
    """
    Phase 2: Apply text overlays to processed segments
    """
    logger.info("=== APPLYING TEXT OVERLAYS TO SEGMENTS ===")
    
    try:
        video_id = event['video_id']
        text_overlays = convert_decimals_to_floats(event['text_overlays'])  # From Fabric.js, convert Decimals to floats
        job_id = event.get('job_id', f"job_{video_id}_{int(time.time())}")
        
        # Get video metadata to access existing segments from output_s3_urls
        dynamodb = boto3.resource('dynamodb')
        video_table = dynamodb.Table('easy-video-share-video-metadata')
        
        video_response = video_table.get_item(Key={'video_id': video_id})
        video_item = video_response.get('Item')
        
        if not video_item:
            raise Exception(f"Video {video_id} not found in database")
        
        # Get existing processed segments from output_s3_urls
        output_s3_urls = video_item.get('output_s3_urls', [])
        if not output_s3_urls:
            raise Exception(f"No processed segments found for video {video_id}")
        
        processed_segments = []
        
        update_job_status(job_id, "PROCESSING", "applying_text_overlays", 10.0)
        
        # Process each segment that has text overlays
        segments_with_overlays = {}
        for overlay in text_overlays:
            segment_id = overlay['segment_id']
            if segment_id not in segments_with_overlays:
                segments_with_overlays[segment_id] = []
            segments_with_overlays[segment_id].append(overlay)
        
        total_segments = len(segments_with_overlays)
        for i, (segment_id, segment_overlays) in enumerate(segments_with_overlays.items()):
            logger.info(f"Processing segment {segment_id} with {len(segment_overlays)} overlays")
            
            # Parse segment_id to get segment number: seg_{video_id}_{segment_number:03d}
            try:
                # Remove "seg_" prefix and video_id to get segment number
                segment_suffix = segment_id.replace(f"seg_{video_id}_", "")
                segment_number = int(segment_suffix)
                
                # Get the corresponding S3 URL (1-based indexing)
                if segment_number < 1 or segment_number > len(output_s3_urls):
                    logger.error(f"Invalid segment number {segment_number} for segment {segment_id}")
                    continue
                
                input_s3_key = output_s3_urls[segment_number - 1]  # Convert to 0-based index
                logger.info(f"Processing segment {segment_id} from S3 key: {input_s3_key}")
                
            except (ValueError, IndexError) as e:
                logger.error(f"Failed to parse segment ID {segment_id}: {e}")
                continue
            
            # Download the segment from S3
            input_path = download_from_s3(input_s3_key)
            
            # Apply text overlays
            output_path = f"/tmp/final_segment_{segment_id}.mp4"
            # Get segment duration from the overlay data (all overlays for a segment should have the same duration)
            segment_duration = float(segment_overlays[0].get('segment_duration', 30.0)) if segment_overlays else 30.0
            success = apply_text_overlays_ffmpeg(input_path, output_path, segment_overlays, segment_duration)
            
            if success:
                # Upload final segment with text overlays
                final_s3_key = f"processed/{video_id}/segment_{segment_number:03d}_with_text.mp4"
                final_url = upload_to_s3(output_path, final_s3_key)
                
                processed_segments.append({
                    'segment_id': segment_id,
                    'segment_number': segment_number,
                    'original_s3_key': input_s3_key,
                    'final_s3_key': final_s3_key,
                    'final_url': final_url,
                    'text_overlays_applied': True,
                    'overlay_count': len(segment_overlays)
                })
                
                logger.info(f"Successfully processed segment {segment_id} with text overlays")
                
                # Clean up temp files
                os.remove(output_path)
                if os.path.exists(input_path):
                    os.remove(input_path)
            else:
                logger.error(f"Failed to apply text overlays to segment {segment_id}")
            
            # Update progress
            progress = 10.0 + (i + 1) / total_segments * 80.0
            update_job_status(job_id, "PROCESSING", "applying_text_overlays", progress)
        
        # Final status update with output URLs
        final_s3_urls = [segment['final_s3_key'] for segment in processed_segments if segment.get('final_s3_key')]
        update_job_status(job_id, "COMPLETED", "text_overlays_applied", 100.0, output_s3_keys=final_s3_urls)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Text overlays applied successfully',
                'job_id': job_id,
                'processed_segments': processed_segments
            })
        }
        
    except Exception as e:
        logger.error(f"Error applying text overlays: {str(e)}")
        raise e

def generate_thumbnail(event, context):
    """
    Generate thumbnail from segment for text overlay design
    """
    logger.info("=== GENERATING SEGMENT THUMBNAIL ===")
    
    try:
        segment_id = event['segment_id']
        video_id = event['video_id']
        
        # Get segment info from DynamoDB
        segment_info = get_segment_from_dynamodb(segment_id)
        
        if not segment_info:
            raise Exception(f"Segment {segment_id} not found")
        
        # Get video path
        if segment_info['storage_type'] == 'lambda_temp':
            video_path = segment_info['temp_segment_path']
        else:
            video_path = download_from_s3(segment_info['location'])
        
        # Generate thumbnail at midpoint
        thumbnail_path = f"/tmp/thumbnail_{segment_id}.jpg"
        
        ffmpeg_path, ffprobe_path = find_ffmpeg_binaries()
        if not ffmpeg_path:
            raise Exception("FFmpeg not found")
        
        # Extract frame at midpoint
        midpoint = segment_info['duration'] / 2
        cmd = [
            ffmpeg_path, '-i', video_path,
            '-ss', str(midpoint),
            '-vframes', '1',
            '-q:v', '2',
            '-y', thumbnail_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Thumbnail generation failed: {result.stderr}")
        
        # Upload thumbnail to S3
        thumbnail_s3_key = f"thumbnails/{video_id}/segment_{segment_info['segment_number']}.jpg"
        thumbnail_url = upload_to_s3(thumbnail_path, thumbnail_s3_key)
        
        # Update segment metadata
        update_segment_thumbnail_in_dynamodb(segment_id, thumbnail_s3_key)
        
        # Clean up temp file
        os.remove(thumbnail_path)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'thumbnail_url': thumbnail_url,
                'segment_id': segment_id,
                'thumbnail_s3_key': thumbnail_s3_key
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        raise e

def process_full_video(event, context):
    """
    Original full video processing functionality (for backward compatibility)
    """
    logger.info("=== PROCESSING FULL VIDEO (LEGACY) ===")
    
    # Extract parameters from event
    s3_bucket = event.get('s3_bucket')
    s3_key = event.get('s3_key')
    job_id = event.get('job_id')
    cutting_options = event.get('cutting_options')
    text_input = event.get('text_input')
    user_id = event.get('user_id', 'anonymous')
    segment_duration = event.get('segment_duration', 30)

    if not all([s3_bucket, s3_key, job_id]):
        raise ValueError("Missing required parameters: s3_bucket, s3_key, job_id")

    # Update job status to PROCESSING
    update_job_status(job_id, "PROCESSING", "downloading_video", 5.0)

    # Process video
    result = process_video(s3_bucket, s3_key, job_id, cutting_options, text_input, user_id, segment_duration)

    # Update job status to COMPLETED
    update_job_status(job_id, "COMPLETED", "completed", 100.0, 
                     output_s3_keys=result['output_s3_keys'],
                     segments_created=len(result['output_s3_keys']),
                     processing_duration=result['processing_duration'])

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Video processing completed successfully',
            'job_id': job_id,
            'segments_created': len(result['output_s3_keys']),
            'processing_duration': result['processing_duration']
        })
    }

def apply_text_overlays_ffmpeg(input_path: str, output_path: str, text_overlays: List[dict], segment_duration: float = 30.0) -> bool:
    """
    Apply text overlays using FFmpeg with proper filter chaining
    """
    logger.info(f"Applying {len(text_overlays)} text overlays")
    
    try:
        if not text_overlays:
            # No text overlays, just copy file
            shutil.copy2(input_path, output_path)
            return True
        
        ffmpeg_path, _ = find_ffmpeg_binaries()
        if not ffmpeg_path:
            raise Exception("FFmpeg not found")
        
        # Build filter complex for multiple text overlays
        filters = []
        for i, overlay in enumerate(text_overlays):
            # Convert overlay to FFmpeg drawtext filter
            filter_str = convert_overlay_to_ffmpeg(overlay, segment_duration)
            if i == 0:
                filters.append(f"[0:v]{filter_str}[v{i+1}]")
            else:
                filters.append(f"[v{i}]{filter_str}[v{i+1}]")
        
        # Use the last video stream as output
        final_output = f"[v{len(text_overlays)}]"
        
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-filter_complex', ';'.join(filters),
            '-map', final_output,
            '-map', '0:a',
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg text overlay failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying text overlays: {str(e)}")
        return False

def convert_overlay_to_ffmpeg(overlay: dict, segment_duration: float = 30.0) -> str:
    """
    Convert text overlay object to FFmpeg drawtext filter
    """
    # Extract overlay properties
    text = overlay.get('text', '').replace("'", "\\'").replace(":", "\\:")
    x = overlay.get('x', 0)
    y = overlay.get('y', 0)
    font_size = overlay.get('fontSize', 24)
    color = overlay.get('color', '#ffffff')
    
    # Build drawtext filter
    filter_parts = [
        f"drawtext=text='{text}'",
        f"x={x}",
        f"y={y}",
        f"fontsize={font_size}",
        f"fontcolor={color}",
        f"enable='between(t,0,{segment_duration})'"
    ]
    
    return ':'.join(filter_parts)

def download_from_s3(s3_key: str) -> str:
    """
    Download file from S3 to local temp directory
    """
    logger.info(f"Downloading from S3: {s3_key}")
    
    s3_client = boto3.client('s3')
    local_path = f"/tmp/{os.path.basename(s3_key)}"
    
    try:
        s3_client.download_file(
            Bucket=os.environ.get('S3_BUCKET', 'easy-video-share-bucket'),
            Key=s3_key,
            Filename=local_path
        )
        logger.info(f"Downloaded to: {local_path}")
        return local_path
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}")
        raise e

def upload_to_s3(local_path: str, s3_key: str) -> str:
    """
    Upload file to S3 and return presigned URL
    """
    logger.info(f"Uploading to S3: {s3_key}")
    
    s3_client = boto3.client('s3')
    bucket = os.environ.get('S3_BUCKET', 'easy-video-share-bucket')
    
    try:
        s3_client.upload_file(local_path, bucket, s3_key)
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        logger.info(f"Uploaded successfully, URL: {url}")
        return url
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise e

def update_segments_in_dynamodb(video_id: str, segments: List[dict]):
    """
    Update segment metadata in DynamoDB
    """
    logger.info(f"Updating segments in DynamoDB for video: {video_id}")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-segments')
        
        for segment in segments:
            table.put_item(Item={
                'video_id': video_id,
                'segment_id': segment['segment_id'],
                'segment_number': segment['segment_number'],
                'start_time': Decimal(str(segment['start_time'])),
                'duration': Decimal(str(segment['duration'])),
                'storage_type': segment['storage_type'],
                'location': segment.get('location'),
                'temp_segment_path': segment.get('temp_segment_path'),
                'raw_segment_ready': segment['raw_segment_ready'],
                'thumbnail_generated': segment['thumbnail_generated'],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"Updated {len(segments)} segments in DynamoDB")
        
    except Exception as e:
        logger.error(f"Error updating segments in DynamoDB: {str(e)}")
        raise e

def get_segments_from_dynamodb(video_id: str) -> List[dict]:
    """
    Get segments from DynamoDB for a video
    """
    logger.info(f"Getting segments from DynamoDB for video: {video_id}")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-segments')
        
        response = table.scan(
            FilterExpression='video_id = :video_id',
            ExpressionAttributeValues={':video_id': video_id}
        )
        
        segments = response.get('Items', [])
        logger.info(f"Found {len(segments)} segments")
        return segments
        
    except Exception as e:
        logger.error(f"Error getting segments from DynamoDB: {str(e)}")
        raise e

def get_segment_from_dynamodb(segment_id: str) -> Optional[dict]:
    """
    Get a specific segment from DynamoDB
    This function gets segments from the video-metadata table (output_s3_urls)
    and can also check the video-segments table for additional text overlay data.
    """
    logger.info(f"Getting segment from DynamoDB: {segment_id}")
    
    # Parse segment_id to extract video_id and segment number
    # Format: seg_{video_id}_{segment_number:03d}
    if not segment_id.startswith("seg_"):
        logger.error(f"Invalid segment ID format: {segment_id}")
        return None
    
    # Remove "seg_" prefix
    segment_id_without_prefix = segment_id[4:]
    
    # Find the last underscore to separate video_id from segment_number
    last_underscore_index = segment_id_without_prefix.rfind("_")
    if last_underscore_index == -1:
        logger.error(f"Invalid segment ID format: {segment_id}")
        return None
    
    video_id = segment_id_without_prefix[:last_underscore_index]
    segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
    
    try:
        segment_number = int(segment_number_str)
    except ValueError:
        logger.error(f"Invalid segment number format: {segment_number_str}")
        return None
    
    logger.info(f"Parsed segment ID: video_id='{video_id}', segment_number={segment_number}")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE', 'easy-video-share-video-metadata')
        video_metadata_table = dynamodb.Table(table_name)
        
        logger.info(f"Using DynamoDB table: {table_name}")
        
        # Get the video record to find the segment from output_s3_urls
        logger.info(f"Querying DynamoDB for video_id: {video_id}")
        video_resp = video_metadata_table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            logger.error(f"Video not found in table {table_name}: {video_id}")
            return None
        
        logger.info(f"Video found. Status: {video_item.get('status')}, Title: {video_item.get('title')}")
        
        # Get the output_s3_urls array
        output_s3_urls = video_item.get("output_s3_urls", [])
        if not output_s3_urls:
            logger.error(f"No output_s3_urls found for video: {video_id}")
            return None
        
        logger.info(f"Found {len(output_s3_urls)} segments in output_s3_urls")
        
        # Check if segment number is valid
        if segment_number < 1 or segment_number > len(output_s3_urls):
            logger.error(f"Invalid segment number: {segment_number}, max: {len(output_s3_urls)}, available range: 1-{len(output_s3_urls)}")
            return None
        
        # Get the s3_key for this segment
        s3_key = output_s3_urls[segment_number - 1]  # Convert to 0-based index
        
        # Extract filename from s3_key
        filename = s3_key.split("/")[-1] if s3_key else None
        
        # Check if there's additional data in the video-segments table
        additional_data = {}
        actual_duration = 30.0  # Default fallback
        try:
            segments_table = dynamodb.Table('easy-video-share-video-segments')
            response = segments_table.get_item(Key={'segment_id': segment_id})
            segment_item = response.get('Item')
            
            if segment_item:
                logger.info(f"Found additional data in video-segments table: {segment_id}")
                # Convert Decimals to floats for text overlays
                raw_text_overlays = segment_item.get('text_overlays', [])
                converted_text_overlays = convert_decimals_to_floats(raw_text_overlays)
                
                additional_data = {
                    'thumbnail_url': segment_item.get('thumbnail_url'),
                    'text_overlays': converted_text_overlays,
                    'download_count': segment_item.get('download_count', 0),
                    'social_media_usage': segment_item.get('social_media_usage', [])
                }
                # Get actual duration from video-segments table
                if 'duration' in segment_item:
                    actual_duration = float(segment_item['duration'])
                    logger.info(f"Found actual duration for {segment_id}: {actual_duration}s")
        except Exception as e:
            logger.warning(f"Error querying video-segments table for additional data: {str(e)}")
            # Continue without additional data
        
        # Create segment data
        segment_data = {
            'segment_id': segment_id,
            'video_id': video_id,
            'user_id': video_item.get("user_id", ""),
            'segment_type': 'PROCESSED',
            'segment_number': segment_number,
            's3_key': s3_key,
            'location': s3_key,  # Add location field for Lambda compatibility
            'storage_type': 's3',  # Add storage_type field for Lambda compatibility
            'duration': actual_duration,  # Use actual duration from video-segments table
            'file_size': 0,    # Default size, could be enhanced to get from S3
            'content_type': "video/mp4",
            'title': f"{video_item.get('title', 'Video')} - Part {segment_number}",
            'description': f"Processed segment {segment_number} of {len(output_s3_urls)}",
            'tags': video_item.get("tags", []),
            'created_at': video_item.get("created_at", ""),
            'updated_at': video_item.get("updated_at", ""),
            'filename': filename,
            'download_count': additional_data.get('download_count', 0),
            'social_media_usage': additional_data.get('social_media_usage', []),
            'thumbnail_url': additional_data.get('thumbnail_url')
        }
        
        logger.info(f"Created segment from output_s3_urls with additional data: {segment_id}")
        return segment_data
        
    except Exception as e:
        logger.error(f"Error getting segment from DynamoDB: {str(e)}")
        raise e

def update_segment_thumbnail_in_dynamodb(segment_id: str, thumbnail_s3_key: str):
    """
    Update segment thumbnail info in DynamoDB
    """
    logger.info(f"Updating thumbnail for segment: {segment_id}")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-segments')
        
        table.update_item(
            Key={'segment_id': segment_id},
            UpdateExpression='SET thumbnail_s3_key = :thumbnail_s3_key, thumbnail_generated = :thumbnail_generated',
            ExpressionAttributeValues={
                ':thumbnail_s3_key': thumbnail_s3_key,
                ':thumbnail_generated': True
            }
        )
        
        logger.info(f"Updated thumbnail for segment: {segment_id}")
        
    except Exception as e:
        logger.error(f"Error updating segment thumbnail: {str(e)}")
        raise e

def process_video_segment(input_path: str, output_path: str, start_time: float, duration: float) -> bool:
    """
    Process a single video segment without text overlays
    """
    logger.info(f"Processing segment: {start_time}s for {duration}s")
    
    try:
        ffmpeg_path, _ = find_ffmpeg_binaries()
        if not ffmpeg_path:
            raise Exception("FFmpeg not found")
        
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30',
            '-c:a', 'aac', '-b:a', '64k',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg segment processing failed: {result.stderr}")
            return False
        
        logger.info(f"Segment processed successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing segment: {str(e)}")
        return False

def find_ffmpeg_binaries():
    """
    Find FFmpeg and FFprobe binaries in the Lambda environment
    """
    logger.info("=== SEARCHING FOR FFMPEG BINARIES ===")
    
    # Common paths where FFmpeg might be installed
    search_paths = [
        '/opt/bin/',
        '/opt/ffmpeg/bin/',
        '/usr/bin/',
        '/usr/local/bin/',
        '/var/task/bin/',
        '/var/task/ffmpeg/bin/'
    ]
    
    ffmpeg_path = None
    ffprobe_path = None
    
    # First check if they're in PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    ffprobe_in_path = shutil.which('ffprobe')
    
    if ffmpeg_in_path:
        ffmpeg_path = ffmpeg_in_path
        logger.info(f"Found ffmpeg in PATH: {ffmpeg_path}")
    
    if ffprobe_in_path:
        ffprobe_path = ffprobe_in_path
        logger.info(f"Found ffprobe in PATH: {ffprobe_path}")
    
    # Search in common directories
    for search_path in search_paths:
        logger.info(f"Searching in: {search_path}")
        try:
            if os.path.exists(search_path):
                contents = os.listdir(search_path)
                logger.info(f"Contents of {search_path}: {contents}")
                
                if ffmpeg_path is None and 'ffmpeg' in contents:
                    ffmpeg_path = os.path.join(search_path, 'ffmpeg')
                    logger.info(f"Found ffmpeg at: {ffmpeg_path}")
                
                if ffprobe_path is None and 'ffprobe' in contents:
                    ffprobe_path = os.path.join(search_path, 'ffprobe')
                    logger.info(f"Found ffprobe at: {ffprobe_path}")
        except Exception as e:
            logger.warning(f"Cannot access {search_path}: {e}")
    
    # Test if binaries are executable
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ FFmpeg is working: {ffmpeg_path}")
            else:
                logger.error(f"❌ FFmpeg test failed: {result.stderr}")
                ffmpeg_path = None
        except Exception as e:
            logger.error(f"❌ FFmpeg test exception: {e}")
            ffmpeg_path = None
    
    if ffprobe_path and os.path.exists(ffprobe_path):
        try:
            result = subprocess.run([ffprobe_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ FFprobe is working: {ffprobe_path}")
            else:
                logger.error(f"❌ FFprobe test failed: {result.stderr}")
                ffprobe_path = None
        except Exception as e:
            logger.error(f"❌ FFprobe test exception: {e}")
            ffprobe_path = None
    
    return ffmpeg_path, ffprobe_path

def get_video_duration(video_path, ffprobe_path=None, ffmpeg_path=None):
    """
    Get video duration using ffprobe or ffmpeg fallback
    """
    logger.info(f"Getting duration for: {video_path}")
    
    # Try ffprobe first (faster)
    if ffprobe_path:
        try:
            cmd = [ffprobe_path, '-v', 'quiet', '-show_entries', 'format=duration', 
                   '-of', 'csv=p=0', video_path]
            logger.info(f"Running ffprobe: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"✅ Duration via ffprobe: {duration}s")
                return duration
            else:
                logger.warning(f"FFprobe failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"FFprobe exception: {e}")
    
    # Fallback to ffmpeg
    if ffmpeg_path:
        try:
            cmd = [ffmpeg_path, '-i', video_path, '-t', '0.1', '-f', 'null', '-']
            logger.info(f"Running ffmpeg for duration: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # Parse duration from stderr output
                import re
                duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
                if duration_match:
                    hours, minutes, seconds = duration_match.groups()
                    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    logger.info(f"✅ Duration via ffmpeg: {duration}s")
                    return duration
                else:
                    logger.error("Could not parse duration from ffmpeg output")
            else:
                logger.error(f"FFmpeg duration check failed: {result.stderr}")
        except Exception as e:
            logger.error(f"FFmpeg duration exception: {e}")
    
    raise Exception("Could not determine video duration")

def update_job_status(job_id, status, stage, progress, output_s3_keys=None, segments_created=None, processing_duration=None, error_message=None):
    """
    Update job status in DynamoDB
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        update_expression = 'SET #status = :status, processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at'
        expression_values = {
            ':status': status,
            ':stage': stage,
            ':progress': Decimal(str(progress)),
            ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
        if output_s3_keys:
            update_expression += ', output_s3_urls = :outputs'
            expression_values[':outputs'] = output_s3_keys
        
        if segments_created is not None:
            update_expression += ', segments_created = :segments'
            expression_values[':segments'] = segments_created
        
        if processing_duration is not None:
            update_expression += ', metadata.processing_duration = :proc_duration'
            expression_values[':proc_duration'] = Decimal(str(processing_duration))
        
        if error_message:
            update_expression += ', error_message = :error'
            expression_values[':error'] = error_message
        
        table.update_item(
            Key={'video_id': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expression_values
        )
        
        logger.info(f"✅ Job status updated: {job_id} -> {status}")
        
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")
        # Don't raise exception - continue processing even if DB update fails

def process_video(s3_bucket, s3_key, job_id, cutting_options, text_input, user_id, segment_duration):
    """
    Main video processing logic
    """
    logger.info("=== STARTING VIDEO PROCESSING ===")
    
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    
    # Find FFmpeg binaries
    ffmpeg_path, ffprobe_path = find_ffmpeg_binaries()
    if not ffmpeg_path:
        raise Exception("FFmpeg not found in Lambda environment")
    
    processing_start_time = datetime.utcnow()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Download video from S3
        input_video_path = os.path.join(temp_dir, 'input_video.mov')
        logger.info(f"Downloading video: {s3_bucket}/{s3_key}")
        s3_client.download_file(s3_bucket, s3_key, input_video_path)
        input_file_size = os.path.getsize(input_video_path)
        logger.info(f"Downloaded video: {input_file_size} bytes")
        
        # Get video duration
        total_duration = get_video_duration(input_video_path, ffprobe_path, ffmpeg_path)
        logger.info(f"Video duration: {total_duration}s")
        
        # Calculate segments
        max_segments = int(total_duration / segment_duration)
        if max_segments < 1:
            max_segments = 1
            segment_duration = total_duration
        
        # Limit segments for production (adjust as needed)
        if max_segments > 10:
            max_segments = 10
            segment_duration = total_duration / max_segments
        
        logger.info(f"Will create {max_segments} segments of {segment_duration:.1f}s each")
        
        # Process video segments
        output_s3_keys = []
        
        for i in range(max_segments):
            start_time = i * segment_duration
            if start_time >= total_duration:
                break
            
            logger.info(f"Processing segment {i+1}/{max_segments} starting at {start_time:.1f}s")
            
            segment_path = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
            
            # Process segment
            if process_video_segment(input_video_path, segment_path, start_time, segment_duration):
                # Upload segment to S3
                segment_s3_key = f"processed/{job_id}/segment_{i:03d}.mp4"
                logger.info(f"Uploading to S3: {segment_s3_key}")
                s3_client.upload_file(segment_path, s3_bucket, segment_s3_key)
                output_s3_keys.append(segment_s3_key)
                logger.info(f"✅ Segment {i+1} completed")
            else:
                logger.error(f"❌ Segment {i+1} failed")
        
        processing_end_time = datetime.utcnow()
        processing_duration = (processing_end_time - processing_start_time).total_seconds()
        
        logger.info(f"=== VIDEO PROCESSING COMPLETED ===")
        logger.info(f"Created {len(output_s3_keys)} segments in {processing_duration:.1f}s")
        
        return {
            'output_s3_keys': output_s3_keys,
            'processing_duration': processing_duration
        } 