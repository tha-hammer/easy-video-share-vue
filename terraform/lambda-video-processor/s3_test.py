import json
import boto3
import tempfile
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Test Lambda function to verify S3 download/upload operations
    """
    try:
        logger.info(f"S3 test Lambda invoked with event: {event}")
        
        s3_client = boto3.client('s3')
        
        # Extract parameters from event
        s3_bucket = event.get('s3_bucket')
        s3_key = event.get('s3_key')
        
        if not s3_bucket or not s3_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Missing required parameters: s3_bucket and s3_key',
                    'event': event
                })
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test download
            input_path = os.path.join(temp_dir, 'test_input.mp4')
            logger.info(f"Downloading from s3://{s3_bucket}/{s3_key} to {input_path}")
            
            s3_client.download_file(s3_bucket, s3_key, input_path)
            
            # Verify file exists and get size
            if not os.path.exists(input_path):
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': 'File download failed - file not found',
                        's3_bucket': s3_bucket,
                        's3_key': s3_key
                    })
                }
            
            file_size = os.path.getsize(input_path)
            logger.info(f"Downloaded file size: {file_size} bytes")

            # Test upload (copy with different name)
            output_key = f"test_output/{s3_key.split('/')[-1]}"
            logger.info(f"Uploading to s3://{s3_bucket}/{output_key}")
            
            s3_client.upload_file(input_path, s3_bucket, output_key)
            
            # Verify upload by checking if file exists
            try:
                s3_client.head_object(Bucket=s3_bucket, Key=output_key)
                upload_success = True
            except Exception as e:
                upload_success = False
                logger.error(f"Upload verification failed: {str(e)}")

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'S3 test successful!',
                    'downloaded_size': file_size,
                    'uploaded_key': output_key,
                    'upload_success': upload_success,
                    's3_bucket': s3_bucket,
                    'original_key': s3_key,
                    'event': event,
                    'function_name': context.function_name,
                    'function_version': context.function_version
                })
            }

    except Exception as e:
        logger.error(f"Error in S3 test: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'S3 test failed with exception',
                'error': str(e),
                'error_type': type(e).__name__,
                'event': event
            })
        } 