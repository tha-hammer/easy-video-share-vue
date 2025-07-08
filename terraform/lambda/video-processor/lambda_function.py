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

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Production Lambda handler for video processing
    """
    logger.info("=== VIDEO PROCESSING LAMBDA STARTED ===")
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    
    try:
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

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        if 'job_id' in locals():
            update_job_status(job_id, "FAILED", "failed", 0.0, error_message=str(e))

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': job_id if 'job_id' in locals() else None
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
            if process_video_segment(input_video_path, segment_path, start_time, segment_duration, ffmpeg_path):
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