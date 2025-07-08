import json
import boto3
import tempfile
import os
import logging
import subprocess
import shutil
import re
from datetime import datetime, timezone
from decimal import Decimal

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Fixed Lambda handler with better FFmpeg handling and timeout management
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

def process_video_segment(input_path, output_path, start_time, duration, ffmpeg_path):
    """
    Process a single video segment with optimized settings
    """
    logger.info(f"Processing segment: {start_time}s to {start_time + duration}s")
    
    # Use optimized settings for faster processing
    cmd = [
        ffmpeg_path, '-i', input_path,
        '-ss', str(start_time), '-t', str(duration),
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30',  # Faster, lower quality
        '-c:a', 'aac', '-b:a', '64k',  # Lower audio bitrate
        '-movflags', '+faststart',  # Optimize for streaming
        '-y', output_path
    ]
    
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    
    # Use longer timeout for video processing
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minutes per segment
    
    if result.returncode == 0 and os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        logger.info(f"✅ Segment created: {output_path} ({file_size} bytes)")
        return True
    else:
        logger.error(f"❌ FFmpeg failed: return code {result.returncode}")
        logger.error(f"FFmpeg stderr: {result.stderr}")
        return False

def test_full_integration(event, context=None):
    """
    Fixed full integration test with better error handling
    """
    logger.info("=== FULL INTEGRATION STARTED ===")
    
    try:
        logger.info("STEP 1: Initializing AWS clients...")
        s3_client = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        logger.info("STEP 1: ✅ AWS clients initialized")
        
        logger.info("STEP 2: Finding FFmpeg binaries...")
        ffmpeg_path, ffprobe_path = find_ffmpeg_binaries()
        
        if not ffmpeg_path:
            raise Exception("FFmpeg not found in Lambda environment")
        
        logger.info("STEP 2: ✅ FFmpeg binaries found")
        
        logger.info("STEP 3: Getting parameters from event...")
        bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
        input_video_key = event.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
        job_id = event.get('job_id', f"lambda-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
        user_id = event.get('user_id', 'lambda-test-user')
        segment_duration = event.get('segment_duration', 30)
        logger.info(f"STEP 3: ✅ Parameters: bucket={bucket}, job_id={job_id}, video={input_video_key}")
        
        processing_start_time = datetime.utcnow()
        logger.info(f"STEP 4: Starting processing at {processing_start_time}")
        
        logger.info("STEP 5: Creating temp directory...")
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"STEP 5: ✅ Temp directory created: {temp_dir}")
            
            logger.info("STEP 6: Creating DynamoDB job record...")
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
            logger.info("STEP 6: ✅ DynamoDB job record created")
            
            logger.info("STEP 7: Updating status to PROCESSING...")
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
            logger.info("STEP 7: ✅ Status updated to PROCESSING")
            
            logger.info(f"STEP 8: Downloading video from S3: {bucket}/{input_video_key}")
            input_video_path = os.path.join(temp_dir, 'input_video.mov')
            s3_client.download_file(bucket, input_video_key, input_video_path)
            input_file_size = os.path.getsize(input_video_path)
            logger.info(f"STEP 8: ✅ Downloaded video: {input_file_size} bytes")
            
            logger.info("STEP 9: Getting video duration...")
            total_duration = get_video_duration(input_video_path, ffprobe_path, ffmpeg_path)
            logger.info(f"STEP 9: ✅ Video duration: {total_duration}s")
            
            logger.info("STEP 10: Calculating segments...")
            max_segments = int(total_duration / segment_duration)
            if max_segments < 1:
                max_segments = 1
                segment_duration = total_duration
            
            # Limit segments for testing to avoid timeouts
            if max_segments > 3:
                max_segments = 3
                segment_duration = total_duration / max_segments
            
            logger.info(f"STEP 10: ✅ Will create {max_segments} segments of {segment_duration:.1f}s each")
            
            logger.info("STEP 11: Processing video segments...")
            output_s3_keys = []
            
            for i in range(max_segments):
                start_time = i * segment_duration
                if start_time >= total_duration:
                    break
                
                logger.info(f"STEP 11.{i+1}: Processing segment {i+1}/{max_segments} starting at {start_time:.1f}s")
                
                segment_path = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
                
                # Process segment with fixed function
                if process_video_segment(input_video_path, segment_path, start_time, segment_duration, ffmpeg_path):
                    # Upload segment to S3
                    segment_s3_key = f"processed/{job_id}/segment_{i:03d}.mp4"
                    logger.info(f"STEP 11.{i+1}: Uploading to S3: {segment_s3_key}")
                    s3_client.upload_file(segment_path, bucket, segment_s3_key)
                    output_s3_keys.append(segment_s3_key)
                    logger.info(f"STEP 11.{i+1}: ✅ Segment {i+1} completed")
                else:
                    logger.error(f"STEP 11.{i+1}: ❌ Segment {i+1} failed")
            
            logger.info("STEP 12: Marking job as completed...")
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
            logger.info(f"STEP 12: ✅ Job completed! Created {len(output_s3_keys)} segments in {processing_duration:.1f}s")
            
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