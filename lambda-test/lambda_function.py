import json
import boto3
import tempfile
import os
import logging

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Phase 4: Clean integration test with step-by-step logging
    """
    logger.info("=== LAMBDA HANDLER STARTED ===")
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    logger.info(f"Event test_type value: '{event.get('test_type')}'")
    
    try:
        # Check if this is a full integration test
        if event.get('test_type') == 'full_integration':
            logger.info("*** ENTERING FULL INTEGRATION TEST ***")
            return test_full_integration(event, context)
        
        logger.info("*** RETURNING DEFAULT RESPONSE ***")
        # Default hello world test
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hello from Lambda!',
                'event_received': event,
                'test_status': 'SUCCESS',
                'available_tests': ['full_integration']
            })
        }
    except Exception as e:
        logger.error(f"*** HANDLER ERROR: {str(e)} ***")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_full_integration(event, context=None):
    """
    Phase 4: Full integration test with detailed step logging
    """
    logger.info("=== FULL INTEGRATION STARTED ===")
    
    try:
        logger.info("STEP 1: Importing modules...")
        import subprocess
        import uuid
        from datetime import datetime, timezone
        from decimal import Decimal
        import redis
        logger.info("STEP 1: ✅ All imports successful")
        
        logger.info("STEP 2: Initializing AWS clients...")
        s3_client = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        logger.info("STEP 2: ✅ AWS clients initialized")
        
        logger.info("STEP 3: Setting up Redis connection...")
        try:
            redis_client = redis.StrictRedis(
                host='redis-14117.c265.us-east-1-2.ec2.redns.redis-cloud.com', 
                port=14117, 
                username='default',
                password='MNQmxGqbUGtAhKhQgH0fvxWvSG90qUvd',
                decode_responses=True, 
                socket_timeout=5, 
                socket_connect_timeout=5
            )
            redis_client.ping()
            logger.info("STEP 3: ✅ Redis connection successful")
        except Exception as e:
            logger.warning(f"STEP 3: ⚠️ Redis connection failed: {e}. Continuing without Redis.")
            redis_client = None
        
        logger.info("STEP 4: Getting parameters from event...")
        bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
        input_video_key = event.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
        job_id = event.get('job_id', f"lambda-integration-{uuid.uuid4()}")
        user_id = event.get('user_id', 'lambda-test-user')
        segment_duration = event.get('segment_duration', 30)
        logger.info(f"STEP 4: ✅ Parameters: bucket={bucket}, job_id={job_id}, video={input_video_key}")
        
        processing_start_time = datetime.utcnow()
        logger.info(f"STEP 5: Starting processing at {processing_start_time}")
        
        logger.info("STEP 6: Creating temp directory...")
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"STEP 6: ✅ Temp directory created: {temp_dir}")
            
            logger.info("STEP 7: Creating DynamoDB job record...")
            timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            
            table.put_item(Item={
                'video_id': job_id,
                'user_id': user_id,
                'filename': input_video_key.split('/')[-1],
                'original_s3_key': input_video_key,
                'upload_date': timestamp,
                'created_at': timestamp,
                'updated_at': timestamp,
                'status': 'QUEUED',
                'processing_stage': 'queued',
                'progress_percentage': Decimal('0.0'),
                'metadata': {
                    'test_mode': True,
                    'lambda_processing': True
                }
            })
            logger.info("STEP 7: ✅ DynamoDB job record created")
            
            logger.info("STEP 8: Updating status to PROCESSING...")
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PROCESSING',
                    ':stage': 'downloading_video',
                    ':progress': Decimal('5.0'),
                    ':updated_at': timestamp
                }
            )
            logger.info("STEP 8: ✅ Status updated to PROCESSING")
            
            logger.info(f"STEP 9: Downloading video from S3: {bucket}/{input_video_key}")
            input_video_path = os.path.join(temp_dir, 'input_video.mov')
            s3_client.download_file(bucket, input_video_key, input_video_path)
            input_file_size = os.path.getsize(input_video_path)
            logger.info(f"STEP 9: ✅ Downloaded video: {input_file_size} bytes")
            
            logger.info("STEP 10: Getting video duration...")
            # Test if ffprobe exists
            ffprobe_paths = ['/opt/bin/ffprobe', '/usr/bin/ffprobe']
            ffprobe_cmd = None
            
            for path in ffprobe_paths:
                if os.path.exists(path):
                    ffprobe_cmd = path
                    logger.info(f"STEP 10: Found ffprobe at {path}")
                    break
            
            if ffprobe_cmd:
                duration_cmd = [ffprobe_cmd, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_video_path]
                logger.info(f"STEP 10: Running ffprobe command: {' '.join(duration_cmd)}")
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
                total_duration = float(duration_result.stdout.strip())
                logger.info(f"STEP 10: ✅ Video duration: {total_duration}s")
            else:
                logger.error("STEP 10: ❌ No ffprobe found!")
                raise Exception("ffprobe not found")
            
            logger.info("STEP 11: Calculating segments...")
            max_segments = int(total_duration / segment_duration)
            if max_segments < 1:
                max_segments = 1
                segment_duration = total_duration
            # Limit to 5 segments for testing
            if max_segments > 5:
                max_segments = 5
                segment_duration = total_duration / max_segments
            
            logger.info(f"STEP 11: ✅ Will create {max_segments} segments of {segment_duration:.1f}s each")
            
            logger.info("STEP 12: Processing video segments...")
            output_s3_keys = []
            
            for i in range(max_segments):
                start_time = i * segment_duration
                if start_time >= total_duration:
                    break
                
                logger.info(f"STEP 12.{i+1}: Processing segment {i+1}/{max_segments} starting at {start_time:.1f}s")
                
                segment_path = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
                
                # Cut segment with high quality for social media
                cut_cmd = [
                    '/opt/bin/ffmpeg', '-i', input_video_path,
                    '-ss', str(start_time), '-t', str(segment_duration),
                    '-c:v', 'libx264', '-crf', '23', '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart',
                    '-y', segment_path
                ]
                
                logger.info(f"STEP 12.{i+1}: Running FFmpeg command")
                cut_result = subprocess.run(cut_cmd, capture_output=True, text=True, timeout=120)
                
                if cut_result.returncode == 0 and os.path.exists(segment_path):
                    # Upload segment to S3
                    segment_s3_key = f"processed/{job_id}/segment_{i:03d}.mp4"
                    logger.info(f"STEP 12.{i+1}: Uploading to S3: {segment_s3_key}")
                    s3_client.upload_file(segment_path, bucket, segment_s3_key)
                    output_s3_keys.append(segment_s3_key)
                    logger.info(f"STEP 12.{i+1}: ✅ Segment {i+1} completed")
                else:
                    logger.error(f"STEP 12.{i+1}: ❌ FFmpeg failed with return code {cut_result.returncode}")
                    logger.error(f"FFmpeg stderr: {cut_result.stderr}")
            
            logger.info("STEP 13: Marking job as completed...")
            processing_end_time = datetime.utcnow()
            processing_duration = (processing_end_time - processing_start_time).total_seconds()
            
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, progress_percentage = :progress, output_s3_urls = :outputs, segments_created = :segments, metadata.processing_duration = :proc_duration, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':stage': 'completed',
                    ':progress': Decimal('100.0'),
                    ':outputs': output_s3_keys,
                    ':segments': len(output_s3_keys),
                    ':proc_duration': Decimal(str(processing_duration)),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            logger.info(f"STEP 13: ✅ Job completed! Created {len(output_s3_keys)} segments in {processing_duration:.1f}s")
            
            logger.info("=== FULL INTEGRATION COMPLETED SUCCESSFULLY ===")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_type': 'full_integration',
                    'job_id': job_id,
                    'processing_summary': {
                        'segments_created': len(output_s3_keys),
                        'processing_duration_seconds': processing_duration,
                        'output_s3_keys': output_s3_keys
                    },
                    'test_status': 'SUCCESS',
                    'message': f'Successfully processed {len(output_s3_keys)} segments in {processing_duration:.1f} seconds'
                })
            }
        
    except Exception as e:
        logger.error(f"=== FULL INTEGRATION FAILED ===")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Try to mark job as failed in database
        try:
            if 'table' in locals() and 'job_id' in locals():
                table.update_item(
                    Key={'video_id': job_id},
                    UpdateExpression='SET #status = :status, processing_stage = :stage, error_message = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'FAILED',
                        ':stage': 'failed',
                        ':error': str(e),
                        ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
            else:
                logger.error("Cannot update job status - table or job_id not initialized")
        except Exception as db_error:
            logger.error(f"Failed to update job status to FAILED: {db_error}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'full_integration',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }