import json
import boto3
import tempfile
import os

def lambda_handler(event, context):
    """
    Phase 2B: Test S3 download/upload operations
    """
    try:
        # Check if this is an S3 test
        if event.get('test_type') == 's3_operations':
            return test_s3_operations(event, context)
        
        # Check if this is an FFmpeg test
        if event.get('test_type') == 'ffmpeg_test':
            return test_ffmpeg_operations(event, context)
        
        # Check if this is a video cutting test
        if event.get('test_type') == 'video_cutting':
            return test_video_cutting(event, context)
        
        # Check if this is a DynamoDB test
        if event.get('test_type') == 'dynamodb_test':
            return test_dynamodb_operations(event, context)
        
        # Check if this is a full integration test
        if event.get('test_type') == 'full_integration':
            return test_full_integration(event, context)
        
        # Default hello world test
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hello from Lambda!',
                'event_received': event,
                'test_status': 'SUCCESS',
                'available_tests': ['s3_operations', 'ffmpeg_test', 'video_cutting', 'dynamodb_test', 'full_integration']
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

def test_s3_operations(event, context=None):
    """
    Test S3 download and upload operations
    """
    s3_client = boto3.client('s3')
    
    # Get bucket and key from event
    bucket = event.get('s3_bucket', 'easy-video-share-bucket')
    test_key = event.get('s3_key', 'uploads/test-file.txt')
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test 1: Try to download file
            local_path = os.path.join(temp_dir, 'downloaded_file.txt')
            
            try:
                s3_client.download_file(bucket, test_key, local_path)
                download_success = True
                file_size = os.path.getsize(local_path)
            except Exception as download_error:
                download_success = False
                file_size = 0
                download_error_msg = str(download_error)
            
            # Test 2: Try to upload a test file
            test_content = f"Lambda S3 test - {event.get('source', 'unknown')}"
            test_upload_path = os.path.join(temp_dir, 'test_upload.txt')
            
            with open(test_upload_path, 'w') as f:
                f.write(test_content)
            
            upload_key = f"lambda-tests/test-upload-{context.aws_request_id if context else 'test'}.txt"
            
            try:
                s3_client.upload_file(test_upload_path, bucket, upload_key)
                upload_success = True
            except Exception as upload_error:
                upload_success = False
                upload_error_msg = str(upload_error)
            
            # Return results
            result = {
                'test_type': 's3_operations',
                'bucket': bucket,
                'download_test': {
                    'success': download_success,
                    'test_key': test_key,
                    'file_size': file_size if download_success else 0
                },
                'upload_test': {
                    'success': upload_success,
                    'upload_key': upload_key if upload_success else None
                },
                'test_status': 'SUCCESS' if (download_success or upload_success) else 'PARTIAL_FAILURE'
            }
            
            # Add error details if needed
            if not download_success:
                result['download_test']['error'] = download_error_msg
            if not upload_success:
                result['upload_test']['error'] = upload_error_msg
                
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 's3_operations',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_ffmpeg_operations(event, context=None):
    """
    Phase 3A: Test FFmpeg availability and basic operations
    """
    import subprocess
    
    try:
        # Test 1: Check if FFmpeg is available
        try:
            result = subprocess.run(['/opt/bin/ffmpeg', '-version'], 
                                   capture_output=True, text=True, timeout=10)
            ffmpeg_available = result.returncode == 0
            ffmpeg_version = result.stdout.split('\n')[0] if result.stdout else "Unknown"
        except FileNotFoundError:
            ffmpeg_available = False
            ffmpeg_version = "FFmpeg not found at /opt/bin/ffmpeg"
        except Exception as e:
            ffmpeg_available = False
            ffmpeg_version = f"FFmpeg test failed: {str(e)}"
        
        # Test 2: Check if we can create a simple test video
        test_video_created = False
        test_video_error = None
        test_video_size = 0
        
        if ffmpeg_available:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_video_path = os.path.join(temp_dir, 'test.mp4')
                    
                    # Create a 5-second test video (solid color)
                    cmd = [
                        '/opt/bin/ffmpeg', '-f', 'lavfi', 
                        '-i', 'color=c=blue:size=320x240:duration=5',
                        '-c:v', 'libx264', '-t', '5', test_video_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and os.path.exists(test_video_path):
                        test_video_created = True
                        test_video_size = os.path.getsize(test_video_path)
                    else:
                        test_video_error = f"FFmpeg command failed: {result.stderr}"
                        
            except Exception as e:
                test_video_error = f"Video creation test failed: {str(e)}"
        
        # Return results
        result = {
            'test_type': 'ffmpeg_test',
            'ffmpeg_available': ffmpeg_available,
            'ffmpeg_version': ffmpeg_version,
            'video_creation_test': {
                'success': test_video_created,
                'file_size': test_video_size
            },
            'test_status': 'SUCCESS' if ffmpeg_available else 'FAILED'
        }
        
        if test_video_error:
            result['video_creation_test']['error'] = test_video_error
            
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'ffmpeg_test',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_video_cutting(event, context=None):
    """
    Phase 3B: Test video cutting with real S3 files
    """
    import subprocess
    
    s3_client = boto3.client('s3')
    
    # Get parameters from event
    bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
    video_key = event.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Download video from S3
            input_video_path = os.path.join(temp_dir, 'input_video.mov')
            
            try:
                s3_client.download_file(bucket, video_key, input_video_path)
                download_success = True
                input_file_size = os.path.getsize(input_video_path)
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'test_type': 'video_cutting',
                        'error': f'Failed to download video: {str(e)}',
                        'test_status': 'FAILED'
                    })
                }
            
            # Step 2: Get video duration using ffprobe
            try:
                # Try different ffprobe locations
                ffprobe_paths = ['/opt/bin/ffprobe', '/usr/bin/ffprobe', '/usr/local/bin/ffprobe']
                ffprobe_cmd = None
                
                for path in ffprobe_paths:
                    if os.path.exists(path):
                        ffprobe_cmd = path
                        break
                
                if ffprobe_cmd:
                    duration_cmd = [
                        ffprobe_cmd, '-v', 'quiet', 
                        '-show_entries', 'format=duration', 
                        '-of', 'csv=p=0', input_video_path
                    ]
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
                    total_duration = float(duration_result.stdout.strip())
                else:
                    # Fallback to ffmpeg method
                    duration_cmd = [
                        '/opt/bin/ffmpeg', '-i', input_video_path, 
                        '-t', '0.1', '-f', 'null', '-'
                    ]
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=60)
                    
                    # Parse duration from stderr
                    import re
                    duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', duration_result.stderr)
                    if duration_match:
                        hours, minutes, seconds = duration_match.groups()
                        total_duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    else:
                        raise Exception("Could not parse duration from ffmpeg output")
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'test_type': 'video_cutting',
                        'error': f'Failed to get video duration: {str(e)}',
                        'test_status': 'FAILED'
                    })
                }
            
            # Step 3: Cut video into 2 segments (10 seconds each or less if video is shorter)
            segment_duration = min(10, total_duration / 2)
            segments_created = []
            
            for i in range(2):
                start_time = i * segment_duration
                if start_time >= total_duration:
                    break
                    
                segment_path = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
                
                # Cut segment
                cut_cmd = [
                    '/opt/bin/ffmpeg', '-i', input_video_path,
                    '-ss', str(start_time), '-t', str(segment_duration),
                    '-c:v', 'libx264', '-c:a', 'aac', 
                    '-y', segment_path
                ]
                
                try:
                    cut_result = subprocess.run(cut_cmd, capture_output=True, text=True, timeout=120)
                    
                    if cut_result.returncode == 0 and os.path.exists(segment_path):
                        segment_size = os.path.getsize(segment_path)
                        
                        # Upload segment to S3
                        segment_s3_key = f"lambda-tests/segments/segment_{i:03d}_{context.aws_request_id if context else 'test'}.mp4"
                        s3_client.upload_file(segment_path, bucket, segment_s3_key)
                        
                        segments_created.append({
                            'segment_number': i,
                            'start_time': start_time,
                            'duration': segment_duration,
                            'file_size': segment_size,
                            's3_key': segment_s3_key
                        })
                    else:
                        segments_created.append({
                            'segment_number': i,
                            'error': f'FFmpeg failed: {cut_result.stderr}'
                        })
                        
                except Exception as e:
                    segments_created.append({
                        'segment_number': i,
                        'error': f'Segment creation failed: {str(e)}'
                    })
            
            # Return results
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_type': 'video_cutting',
                    'input_video': {
                        'bucket': bucket,
                        's3_key': video_key,
                        'file_size': input_file_size,
                        'duration': total_duration
                    },
                    'cutting_results': {
                        'segments_attempted': 2,
                        'segments_created': len([s for s in segments_created if 'error' not in s]),
                        'segment_duration': segment_duration,
                        'segments': segments_created
                    },
                    'test_status': 'SUCCESS' if any('error' not in s for s in segments_created) else 'FAILED'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'video_cutting',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_dynamodb_operations(event, context=None):
    """
    Phase 3C: Test DynamoDB job status updates
    """
    import uuid
    from datetime import datetime, timezone
    from decimal import Decimal
    
    dynamodb = boto3.resource('dynamodb')
    table_name = 'easy-video-share-video-metadata'
    table = dynamodb.Table(table_name)
    
    test_job_id = f"lambda-test-{uuid.uuid4()}"
    
    try:
        # Test 1: Create a test job entry
        create_success = False
        try:
            timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            
            # Create job entry similar to Railway processing
            table.put_item(Item={
                'video_id': test_job_id,
                'user_id': 'lambda-test-user',
                'filename': 'test-video.mov',
                'original_s3_key': 'test/video.mov',
                'upload_date': timestamp,
                'created_at': timestamp,
                'updated_at': timestamp,
                'status': 'QUEUED',
                'processing_stage': 'queued',
                'progress_percentage': Decimal('0.0'),
                'metadata': {
                    'duration': Decimal('360.0'),
                    'test_mode': True
                }
            })
            create_success = True
            
        except Exception as e:
            create_error = str(e)
        
        # Test 2: Update job status to PROCESSING
        processing_update_success = False
        try:
            table.update_item(
                Key={'video_id': test_job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PROCESSING',
                    ':stage': 'processing_video',
                    ':progress': Decimal('25.0'),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            processing_update_success = True
            
        except Exception as e:
            processing_update_error = str(e)
        
        # Test 3: Update job status to COMPLETED with results
        completion_update_success = False
        try:
            output_s3_keys = [
                f"lambda-tests/segments/segment_000_{test_job_id}.mp4",
                f"lambda-tests/segments/segment_001_{test_job_id}.mp4"
            ]
            
            table.update_item(
                Key={'video_id': test_job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, progress_percentage = :progress, output_s3_urls = :outputs, segments_created = :segments, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':stage': 'completed',
                    ':progress': Decimal('100.0'),
                    ':outputs': output_s3_keys,
                    ':segments': len(output_s3_keys),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            completion_update_success = True
            
        except Exception as e:
            completion_update_error = str(e)
        
        # Test 4: Read the final job record
        read_success = False
        final_record = None
        try:
            response = table.get_item(Key={'video_id': test_job_id})
            if 'Item' in response:
                final_record = response['Item']
                read_success = True
                # Convert Decimal types to float for JSON serialization
                if 'progress_percentage' in final_record:
                    final_record['progress_percentage'] = float(final_record['progress_percentage'])
                if 'metadata' in final_record and 'duration' in final_record['metadata']:
                    final_record['metadata']['duration'] = float(final_record['metadata']['duration'])
            else:
                read_error = "Job record not found"
                
        except Exception as e:
            read_error = str(e)
        
        # Test 5: Clean up - delete test record
        cleanup_success = False
        try:
            table.delete_item(Key={'video_id': test_job_id})
            cleanup_success = True
        except Exception as e:
            cleanup_error = str(e)
        
        # Compile results
        test_results = {
            'test_type': 'dynamodb_test',
            'test_job_id': test_job_id,
            'table_name': table_name,
            'operations': {
                'create_job': {
                    'success': create_success,
                    'error': create_error if not create_success else None
                },
                'update_processing': {
                    'success': processing_update_success,
                    'error': processing_update_error if not processing_update_success else None
                },
                'update_completed': {
                    'success': completion_update_success,
                    'error': completion_update_error if not completion_update_success else None
                },
                'read_record': {
                    'success': read_success,
                    'error': read_error if not read_success else None,
                    'final_record': final_record if read_success else None
                },
                'cleanup': {
                    'success': cleanup_success,
                    'error': cleanup_error if not cleanup_success else None
                }
            },
            'test_status': 'SUCCESS' if all([create_success, processing_update_success, completion_update_success, read_success]) else 'PARTIAL_SUCCESS'
        }
        
        # Convert Decimal objects to float for JSON serialization
        def decimal_to_float(obj):
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(v) for v in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        serializable_results = decimal_to_float(test_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps(serializable_results)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'dynamodb_test',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_full_integration(event, context=None):
    """
    Phase 4: Full integration test - Complete video processing workflow
    Simulates exactly what Railway currently does
    """
    import subprocess
    import uuid
    from datetime import datetime, timezone
    from decimal import Decimal
    
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('easy-video-share-video-metadata')
    
    # Get parameters from event
    bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
    input_video_key = event.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
    job_id = event.get('job_id', f"lambda-integration-{uuid.uuid4()}")
    user_id = event.get('user_id', 'lambda-test-user')
    
    # For social media, use 30-second segments minimum (as you requested)
    segment_duration = event.get('segment_duration', 30)
    
    processing_start_time = datetime.utcnow()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
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
            
            # === STEP 3: DOWNLOAD VIDEO FROM S3 ===
            input_video_path = os.path.join(temp_dir, 'input_video.mov')
            s3_client.download_file(bucket, input_video_key, input_video_path)
            input_file_size = os.path.getsize(input_video_path)
            
            # === STEP 4: UPDATE PROGRESS - ANALYZING ===
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':stage': 'analyzing_video',
                    ':progress': Decimal('15.0'),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            # === STEP 5: GET VIDEO DURATION ===
            ffprobe_paths = ['/opt/bin/ffprobe', '/usr/bin/ffprobe', '/usr/local/bin/ffprobe']
            ffprobe_cmd = None
            
            for path in ffprobe_paths:
                if os.path.exists(path):
                    ffprobe_cmd = path
                    break
            
            if ffprobe_cmd:
                duration_cmd = [ffprobe_cmd, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_video_path]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
                total_duration = float(duration_result.stdout.strip())
            else:
                # Fallback to ffmpeg
                duration_cmd = ['/opt/bin/ffmpeg', '-i', input_video_path, '-t', '0.1', '-f', 'null', '-']
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=60)
                import re
                duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', duration_result.stderr)
                if duration_match:
                    hours, minutes, seconds = duration_match.groups()
                    total_duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                else:
                    raise Exception("Could not parse duration")
            
            # === STEP 6: CALCULATE SEGMENTS (SOCIAL MEDIA OPTIMIZED) ===
            # For social media: minimum 30 seconds, maximum based on platform
            max_segments = int(total_duration / segment_duration)
            if max_segments < 1:
                max_segments = 1
                segment_duration = total_duration  # Use full video if shorter than min
            
            # Limit to reasonable number of segments
            if max_segments > 10:
                max_segments = 10
                segment_duration = total_duration / max_segments
            
            # === STEP 7: UPDATE PROGRESS - PROCESSING ===
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
            
            # === STEP 8: PROCESS VIDEO SEGMENTS ===
            output_s3_keys = []
            
            for i in range(max_segments):
                start_time = i * segment_duration
                if start_time >= total_duration:
                    break
                
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
                    s3_client.upload_file(segment_path, bucket, segment_s3_key)
                    output_s3_keys.append(segment_s3_key)
            
            # === STEP 9: UPDATE PROGRESS - UPLOADING ===
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET processing_stage = :stage, progress_percentage = :progress, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':stage': 'uploading_results',
                    ':progress': Decimal('90.0'),
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            # === STEP 10: COMPLETE JOB ===
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
                        },
                        'workflow_steps': [
                            'job_created', 'status_queued', 'status_processing',
                            'video_downloaded', 'duration_analyzed', 'segments_calculated',
                            'segments_processed', 'results_uploaded', 'job_completed'
                        ]
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