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
        
        # Default hello world test
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hello from Lambda!',
                'event_received': event,
                'test_status': 'SUCCESS',
                'available_tests': ['s3_operations', 'ffmpeg_test']
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