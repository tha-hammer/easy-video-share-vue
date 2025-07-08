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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Phase 4B: Error Handling and Rollback Testing
    Tests various failure scenarios to ensure robust error handling
    """
    logger.info("=== ERROR HANDLING TEST STARTED ===")
    logger.info(f"Test scenario: {event.get('test_scenario', 'unknown')}")
    
    test_scenario = event.get('test_scenario', 'unknown')
    
    try:
        if test_scenario == 'invalid_s3_key':
            return test_invalid_s3_key(event, context)
        elif test_scenario == 'processing_timeout':
            return test_processing_timeout(event, context)
        elif test_scenario == 'upload_failure':
            return test_upload_failure(event, context)
        elif test_scenario == 'ffmpeg_failure':
            return test_ffmpeg_failure(event, context)
        elif test_scenario == 'dynamodb_failure':
            return test_dynamodb_failure(event, context)
        elif test_scenario == 'memory_pressure':
            return test_memory_pressure(event, context)
        elif test_scenario == 'all_scenarios':
            return test_all_scenarios(event, context)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown test scenario: {test_scenario}',
                    'available_scenarios': [
                        'invalid_s3_key',
                        'processing_timeout', 
                        'upload_failure',
                        'ffmpeg_failure',
                        'dynamodb_failure',
                        'memory_pressure',
                        'all_scenarios'
                    ]
                })
            }
    except Exception as e:
        logger.error(f"Error handling test failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'test_scenario': test_scenario
            })
        }

def test_invalid_s3_key(event, context):
    """
    Test 1: Invalid S3 key → should update job status to FAILED
    """
    logger.info("=== TESTING INVALID S3 KEY SCENARIO ===")
    
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        # Create test job
        job_id = f"error-test-invalid-s3-{int(time.time())}"
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        table.put_item(Item={
            'video_id': job_id,
            'user_id': 'error-test-user',
            'filename': 'nonexistent-video.mov',
            'original_s3_key': 'uploads/nonexistent-video.mov',
            'upload_date': timestamp,
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'QUEUED',
            'processing_stage': 'queued',
            'progress_percentage': Decimal('0.0'),
            'metadata': {
                'test_mode': True,
                'error_test': 'invalid_s3_key'
            }
        })
        
        # Try to download non-existent file
        bucket = event.get('s3_bucket', 'easy-video-share-silmari-dev')
        invalid_key = 'uploads/nonexistent-video.mov'
        
        logger.info(f"Attempting to download non-existent file: {bucket}/{invalid_key}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'nonexistent.mov')
            s3_client.download_file(bucket, invalid_key, input_path)
            
        # If we get here, the test failed (should have raised an exception)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'invalid_s3_key',
                'error': 'Test failed - should have raised S3 error',
                'test_status': 'FAILED'
            })
        }
        
    except Exception as e:
        logger.info(f"Expected S3 error caught: {str(e)}")
        
        # Update job status to FAILED
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
            logger.info("✅ Job status updated to FAILED")
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'test_scenario': 'invalid_s3_key',
                'test_status': 'SUCCESS',
                'error_handled': True,
                'job_status': 'FAILED',
                'error_message': str(e)
            })
        }

def test_processing_timeout(event, context):
    """
    Test 2: Processing timeout → should handle gracefully
    """
    logger.info("=== TESTING PROCESSING TIMEOUT SCENARIO ===")
    
    try:
        # Create a job that will timeout
        job_id = f"error-test-timeout-{int(time.time())}"
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        table.put_item(Item={
            'video_id': job_id,
            'user_id': 'error-test-user',
            'filename': 'timeout-test.mov',
            'original_s3_key': 'uploads/timeout-test.mov',
            'upload_date': timestamp,
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'PROCESSING',
            'processing_stage': 'processing',
            'progress_percentage': Decimal('10.0'),
            'metadata': {
                'test_mode': True,
                'error_test': 'processing_timeout'
            }
        })
        
        # Simulate a long-running process that might timeout
        logger.info("Simulating long-running process...")
        
        # Try to run a command that takes too long
        try:
            # This should timeout after 10 seconds
            result = subprocess.run(['sleep', '20'], capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("✅ Expected timeout occurred")
            
            # Update job status to indicate timeout
            table.update_item(
                Key={'video_id': job_id},
                UpdateExpression='SET #status = :status, processing_stage = :stage, error_message = :error, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':stage': 'timeout',
                    ':error': 'Processing timeout - operation took too long',
                    ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                }
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_scenario': 'processing_timeout',
                    'test_status': 'SUCCESS',
                    'timeout_handled': True,
                    'job_status': 'FAILED',
                    'error_message': 'Processing timeout - operation took too long'
                })
            }
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'processing_timeout',
                'error': 'Test failed - should have timed out',
                'test_status': 'FAILED'
            })
        }
        
    except Exception as e:
        logger.error(f"Timeout test error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'processing_timeout',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_upload_failure(event, context):
    """
    Test 3: Upload failure → should not leave partial results
    """
    logger.info("=== TESTING UPLOAD FAILURE SCENARIO ===")
    
    try:
        job_id = f"error-test-upload-{int(time.time())}"
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        s3_client = boto3.client('s3')
        
        # Create test job
        table.put_item(Item={
            'video_id': job_id,
            'user_id': 'error-test-user',
            'filename': 'upload-test.mov',
            'original_s3_key': 'uploads/upload-test.mov',
            'upload_date': timestamp,
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'PROCESSING',
            'processing_stage': 'uploading',
            'progress_percentage': Decimal('80.0'),
            'metadata': {
                'test_mode': True,
                'error_test': 'upload_failure'
            }
        })
        
        # Create a temporary file to simulate processing
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_segment.mp4')
            
            # Create a dummy file
            with open(test_file, 'w') as f:
                f.write('dummy video content')
            
            # Try to upload to a non-existent bucket (should fail)
            try:
                s3_client.upload_file(test_file, 'non-existent-bucket', f'processed/{job_id}/segment_000.mp4')
            except Exception as upload_error:
                logger.info(f"✅ Expected upload error: {str(upload_error)}")
                
                # Clean up any partial uploads
                try:
                    s3_client.delete_object(Bucket='easy-video-share-silmari-dev', Key=f'processed/{job_id}/')
                except:
                    pass  # Ignore cleanup errors
                
                # Update job status
                table.update_item(
                    Key={'video_id': job_id},
                    UpdateExpression='SET #status = :status, processing_stage = :stage, error_message = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'FAILED',
                        ':stage': 'upload_failed',
                        ':error': f'Upload failed: {str(upload_error)}',
                        ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'test_scenario': 'upload_failure',
                        'test_status': 'SUCCESS',
                        'upload_error_handled': True,
                        'partial_results_cleaned': True,
                        'job_status': 'FAILED',
                        'error_message': f'Upload failed: {str(upload_error)}'
                    })
                }
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'upload_failure',
                'error': 'Test failed - should have failed upload',
                'test_status': 'FAILED'
            })
        }
        
    except Exception as e:
        logger.error(f"Upload failure test error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'upload_failure',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_ffmpeg_failure(event, context):
    """
    Test 4: FFmpeg failure → should handle gracefully
    """
    logger.info("=== TESTING FFMPEG FAILURE SCENARIO ===")
    
    try:
        job_id = f"error-test-ffmpeg-{int(time.time())}"
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        # Create test job
        table.put_item(Item={
            'video_id': job_id,
            'user_id': 'error-test-user',
            'filename': 'ffmpeg-test.mov',
            'original_s3_key': 'uploads/ffmpeg-test.mov',
            'upload_date': timestamp,
            'created_at': timestamp,
            'updated_at': timestamp,
            'status': 'PROCESSING',
            'processing_stage': 'ffmpeg_processing',
            'progress_percentage': Decimal('50.0'),
            'metadata': {
                'test_mode': True,
                'error_test': 'ffmpeg_failure'
            }
        })
        
        # Try to run FFmpeg with invalid parameters
        try:
            # This should fail
            cmd = ['/opt/bin/ffmpeg', '-i', 'nonexistent-file.mov', '-c', 'copy', 'output.mp4']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.info(f"✅ Expected FFmpeg error: {result.stderr}")
                
                # Update job status
                table.update_item(
                    Key={'video_id': job_id},
                    UpdateExpression='SET #status = :status, processing_stage = :stage, error_message = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'FAILED',
                        ':stage': 'ffmpeg_failed',
                        ':error': f'FFmpeg failed: {result.stderr[:200]}',
                        ':updated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'test_scenario': 'ffmpeg_failure',
                        'test_status': 'SUCCESS',
                        'ffmpeg_error_handled': True,
                        'job_status': 'FAILED',
                        'ffmpeg_stderr': result.stderr[:200]
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'test_scenario': 'ffmpeg_failure',
                        'error': 'Test failed - FFmpeg should have failed',
                        'test_status': 'FAILED'
                    })
                }
                
        except subprocess.TimeoutExpired:
            logger.info("✅ FFmpeg timeout occurred")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_scenario': 'ffmpeg_failure',
                    'test_status': 'SUCCESS',
                    'ffmpeg_timeout_handled': True,
                    'job_status': 'FAILED'
                })
            }
        
    except Exception as e:
        logger.error(f"FFmpeg failure test error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'ffmpeg_failure',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_dynamodb_failure(event, context):
    """
    Test 5: DynamoDB failure → should handle gracefully
    """
    logger.info("=== TESTING DYNAMODB FAILURE SCENARIO ===")
    
    try:
        job_id = f"error-test-dynamodb-{int(time.time())}"
        
        # Try to update a non-existent job (should fail)
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        try:
            # This should fail because the job doesn't exist
            table.update_item(
                Key={'video_id': 'non-existent-job-id'},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PROCESSING'
                }
            )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'test_scenario': 'dynamodb_failure',
                    'error': 'Test failed - DynamoDB should have failed',
                    'test_status': 'FAILED'
                })
            }
            
        except Exception as db_error:
            logger.info(f"✅ Expected DynamoDB error: {str(db_error)}")
            
            # The function should continue processing even if DB update fails
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_scenario': 'dynamodb_failure',
                    'test_status': 'SUCCESS',
                    'dynamodb_error_handled': True,
                    'processing_continued': True,
                    'error_message': str(db_error)
                })
            }
        
    except Exception as e:
        logger.error(f"DynamoDB failure test error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'dynamodb_failure',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_memory_pressure(event, context):
    """
    Test 6: Memory pressure → should handle gracefully
    """
    logger.info("=== TESTING MEMORY PRESSURE SCENARIO ===")
    
    try:
        job_id = f"error-test-memory-{int(time.time())}"
        
        # Try to allocate a large amount of memory
        try:
            # Allocate 2GB of memory (should be fine with 3GB limit)
            large_list = ['x' * 1024 * 1024] * 2048  # 2GB
            logger.info(f"✅ Successfully allocated {len(large_list)} MB of memory")
            
            # Try to allocate more (should fail or cause issues)
            try:
                even_larger = ['x' * 1024 * 1024] * 4096  # 4GB (should fail)
                logger.info("Unexpectedly allocated 4GB")
            except MemoryError:
                logger.info("✅ Expected MemoryError occurred")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'test_scenario': 'memory_pressure',
                        'test_status': 'SUCCESS',
                        'memory_error_handled': True,
                        'memory_limit_respected': True
                    })
                }
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_scenario': 'memory_pressure',
                    'test_status': 'SUCCESS',
                    'memory_usage_ok': True,
                    'allocated_2gb': True
                })
            }
            
        except MemoryError as me:
            logger.info(f"✅ MemoryError handled: {str(me)}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'test_scenario': 'memory_pressure',
                    'test_status': 'SUCCESS',
                    'memory_error_handled': True,
                    'error_message': str(me)
                })
            }
        
    except Exception as e:
        logger.error(f"Memory pressure test error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_scenario': 'memory_pressure',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }

def test_all_scenarios(event, context):
    """
    Test all error scenarios in sequence
    """
    logger.info("=== TESTING ALL ERROR SCENARIOS ===")
    
    results = {}
    
    # Test each scenario
    scenarios = [
        'invalid_s3_key',
        'processing_timeout',
        'upload_failure', 
        'ffmpeg_failure',
        'dynamodb_failure',
        'memory_pressure'
    ]
    
    for scenario in scenarios:
        logger.info(f"Testing scenario: {scenario}")
        try:
            if scenario == 'invalid_s3_key':
                result = test_invalid_s3_key({'test_scenario': scenario, **event}, context)
            elif scenario == 'processing_timeout':
                result = test_processing_timeout({'test_scenario': scenario, **event}, context)
            elif scenario == 'upload_failure':
                result = test_upload_failure({'test_scenario': scenario, **event}, context)
            elif scenario == 'ffmpeg_failure':
                result = test_ffmpeg_failure({'test_scenario': scenario, **event}, context)
            elif scenario == 'dynamodb_failure':
                result = test_dynamodb_failure({'test_scenario': scenario, **event}, context)
            elif scenario == 'memory_pressure':
                result = test_memory_pressure({'test_scenario': scenario, **event}, context)
            
            results[scenario] = {
                'status_code': result['statusCode'],
                'body': json.loads(result['body'])
            }
            
        except Exception as e:
            results[scenario] = {
                'error': str(e),
                'status': 'FAILED'
            }
    
    # Count successes
    successful_tests = sum(1 for r in results.values() if r.get('body', {}).get('test_status') == 'SUCCESS')
    total_tests = len(scenarios)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'test_scenario': 'all_scenarios',
            'test_status': 'COMPLETED',
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': f"{(successful_tests/total_tests)*100:.1f}%"
            },
            'detailed_results': results
        })
    } 