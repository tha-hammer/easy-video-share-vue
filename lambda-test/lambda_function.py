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
    Phase 4: Clean integration test
    """
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    try:
        # Check if this is a full integration test
        if event.get('test_type') == 'full_integration':
            logger.info("Starting full integration test")
            return test_full_integration(event, context)
        
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
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_full_integration(event, context=None):
    """
    Phase 4: Full integration test - Complete video processing workflow
    """
    import subprocess
    import uuid
    from datetime import datetime, timezone
    from decimal import Decimal
    import redis
    
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('easy-video-share-video-metadata')
    
    # Initialize Redis for progress updates (same as Railway)
    try:
        redis_client = redis.StrictRedis.from_url('redis://redis-production-a637.up.railway.app:6379', decode_responses=True, socket_timeout=5, socket_connect_timeout=5)
        # Test connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Progress updates will be disabled.")
        redis_client = None
    
    def publish_progress(stage, progress, additional_data=None):
        """Publish progress updates to Redis for real-time UI updates"""
        if redis_client is None:
            logger.debug(f"Redis disabled - progress: {stage} - {progress}%")
            return
            
        try:
            progress_data = {
                'job_id': job_id,
                'stage': stage,
                'progress': float(progress),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            if additional_data:
                progress_data.update(additional_data)
            
            # Publish to the same Redis channel pattern as Railway
            channel = f"job_progress_{job_id}"
            redis_client.publish(channel, json.dumps(progress_data))
            logger.info(f"Published progress to Redis: {stage} - {progress}%")
        except Exception as e:
            # Don't fail the job if Redis publishing fails
            logger.warning(f"Redis progress publishing failed: {e}")
    
    # Get parameters from event
    bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
    input_video_key = event.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
    job_id = event.get('job_id', f"lambda-integration-{uuid.uuid4()}")
    user_id = event.get('user_id', 'lambda-test-user')
    segment_duration = event.get('segment_duration', 30)  # 30 seconds for social media
    
    processing_start_time = datetime.utcnow()
    logger.info(f"Starting video processing for job_id: {job_id}")
    logger.info(f"Input video: s3://{bucket}/{input_video_key}")
    logger.info(f"Segment duration: {segment_duration}s")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temp directory: {temp_dir}")
            # === STEP 1: CREATE JOB RECORD (QUEUED) ===
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
            
            # Publish initial progress to Redis
            publish_progress('queued', 0.0, {'message': 'Job queued for processing'})
            
            # === STEP 2: UPDATE TO PROCESSING ===
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PROCESSING',
                    ':stage': 'downloading_video',
                    ':progress': Decimal('5.0'),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            # Publish progress to Redis
            publish_progress('downloading_video', 5.0, {'message': 'Starting video download from S3'})
            
            # === STEP 3: DOWNLOAD VIDEO FROM S3 ===
            input_video_path = os.path.join(temp_dir, 'input_video.mov')
            logger.info(f"Downloading video from S3: {bucket}/{input_video_key}")
            s3_client.download_file(bucket, input_video_key, input_video_path)
            input_file_size = os.path.getsize(input_video_path)
            logger.info(f"Downloaded video: {input_file_size} bytes")
            
            # === STEP 4: GET VIDEO DURATION ===
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':stage': 'analyzing_video',
                    ':progress': Decimal('15.0'),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            # Publish progress to Redis
            publish_progress('analyzing_video', 15.0, {'message': 'Analyzing video duration and properties', 'file_size': input_file_size})
            
            # Get video duration using ffprobe (we know this works)
            ffprobe_paths = ['/opt/bin/ffprobe', '/usr/bin/ffprobe']
            ffprobe_cmd = None
            
            for path in ffprobe_paths:
                if os.path.exists(path):
                    ffprobe_cmd = path
                    break
            
            if ffprobe_cmd:
                logger.info(f"Using ffprobe: {ffprobe_cmd}")
                duration_cmd = [ffprobe_cmd, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_video_path]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
                total_duration = float(duration_result.stdout.strip())
                logger.info(f"Video duration: {total_duration}s")
            else:
                logger.info("Using ffmpeg fallback for duration")
                # Fallback to ffmpeg method
                duration_cmd = ['/opt/bin/ffmpeg', '-i', input_video_path, '-t', '0.1', '-f', 'null', '-']
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=60)
                import re
                duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', duration_result.stderr)
                if duration_match:
                    hours, minutes, seconds = duration_match.groups()
                    total_duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    logger.info(f"Video duration: {total_duration}s")
                else:
                    logger.error("Could not parse duration from ffmpeg output")
                    raise Exception("Could not parse duration")
            
            # === STEP 5: CALCULATE SEGMENTS ===
            max_segments = int(total_duration / segment_duration)
            if max_segments < 1:
                max_segments = 1
                segment_duration = total_duration
            # Limit to 5 segments for testing
            if max_segments > 5:
                max_segments = 5
                segment_duration = total_duration / max_segments
            
            logger.info(f"Calculated segments: {max_segments} segments of {segment_duration:.1f}s each")
            
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at, metadata.#dur = :duration, metadata.segments_planned = :segments',
                ExpressionAttributeNames={'#dur': 'duration'},
                ExpressionAttributeValues={
                    ':stage': 'processing_segments',
                    ':progress': Decimal('25.0'),
                    ':duration': Decimal(str(total_duration)),
                    ':segments': max_segments,
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            # Publish progress to Redis
            publish_progress('processing_segments', 25.0, {
                'message': f'Starting segment processing: {max_segments} segments of {segment_duration:.1f}s each',
                'total_duration': total_duration,
                'segments_planned': max_segments,
                'segment_duration': segment_duration
            })
            
            # === STEP 6: PROCESS VIDEO SEGMENTS ===
            output_s3_keys = []
            
            for i in range(max_segments):
                start_time = i * segment_duration
                if start_time >= total_duration:
                    break
                
                logger.info(f"Processing segment {i+1}/{max_segments} starting at {start_time:.1f}s")
                
                # Update progress for each segment
                segment_progress = 25.0 + (i / max_segments) * 60.0  # 25% to 85%
                table.update_item(
                    Key={'video_id': job_id},
                    UpdateExpression='SET progress_percentage = :progress, metadata.current_segment = :current, updated_at = :updated_at',
                    ExpressionAttributeValues={
                        ':progress': Decimal(str(segment_progress)),
                        ':current': i + 1,
                        ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
                
                # Publish progress to Redis for each segment
                publish_progress('processing_segments', segment_progress, {
                    'message': f'Processing segment {i+1} of {max_segments}',
                    'current_segment': i + 1,
                    'total_segments': max_segments,
                    'segment_start_time': start_time
                })
                
                segment_path = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
                
                # Cut segment with high quality for social media
                cut_cmd = [
                    '/opt/bin/ffmpeg', '-i', input_video_path,
                    '-ss', str(start_time), '-t', str(segment_duration),
                    '-c:v', 'libx264', '-crf', '23', '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart',  # Optimize for web streaming
                    '-y', segment_path
                ]
                
                cut_result = subprocess.run(cut_cmd, capture_output=True, text=True, timeout=120)
                
                if cut_result.returncode == 0 and os.path.exists(segment_path):
                    # Upload segment to S3
                    segment_s3_key = f"processed/{job_id}/segment_{i:03d}.mp4"
                    logger.info(f"Uploading segment to S3: {segment_s3_key}")
                    s3_client.upload_file(segment_path, bucket, segment_s3_key)
                    output_s3_keys.append(segment_s3_key)
                    logger.info(f"Segment {i+1} uploaded successfully")
                    
                    # Publish segment completion to Redis
                    publish_progress('processing_segments', segment_progress, {
                        'message': f'Segment {i+1} uploaded successfully',
                        'current_segment': i + 1,
                        'total_segments': max_segments,
                        'segment_s3_key': segment_s3_key
                    })
                else:
                    logger.error(f"Failed to create segment {i+1}: FFmpeg returned {cut_result.returncode}")
                    logger.error(f"FFmpeg stderr: {cut_result.stderr}")
                    logger.error(f"FFmpeg stdout: {cut_result.stdout}")
            
            # === STEP 7: COMPLETE JOB ===
            processing_end_time = datetime.utcnow()
            processing_duration = (processing_end_time - processing_start_time).total_seconds()
            
            logger.info(f"Processing completed: {len(output_s3_keys)} segments in {processing_duration:.1f}s")
            logger.info(f"Output S3 keys: {output_s3_keys}")
            
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
            
            # Publish final completion to Redis
            publish_progress('completed', 100.0, {
                'message': f'Video processing completed successfully! Created {len(output_s3_keys)} segments in {processing_duration:.1f}s',
                'segments_created': len(output_s3_keys),
                'output_s3_keys': output_s3_keys,
                'processing_duration': processing_duration,
                'total_duration': total_duration
            })
            
            # === RETURN RESULTS ===
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_type': 'full_integration',
                    'job_id': job_id,
                    'processing_summary': {
                        'input_video': {
                            'bucket': bucket,
                            's3_key': input_video_key,
                            'file_size': input_file_size,
                            'duration': total_duration
                        },
                        'processing_results': {
                            'segments_created': len(output_s3_keys),
                            'segment_duration': segment_duration,
                            'output_s3_keys': output_s3_keys,
                            'processing_duration_seconds': processing_duration
                        }
                    },
                    'test_status': 'SUCCESS',
                    'message': f'Successfully processed {len(output_s3_keys)} segments in {processing_duration:.1f} seconds'
                })
            }
        
    except Exception as e:
        # Mark job as failed in database
        try:
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
            
            # Publish failure to Redis
            publish_progress('failed', 0.0, {
                'message': f'Video processing failed: {str(e)}',
                'error': str(e)
            })
        except:
            pass  # Don't fail on cleanup failure
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'full_integration',
                'job_id': job_id,
                'error': str(e),
                'test_status': 'FAILED'
            })
        }