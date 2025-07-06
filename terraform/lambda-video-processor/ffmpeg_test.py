import json
import subprocess
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Test Lambda function to verify FFmpeg layer functionality
    """
    try:
        logger.info(f"FFmpeg test Lambda invoked with event: {event}")
        
        # Test FFmpeg availability and version
        result = subprocess.run(
            ['/opt/bin/ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Extract version info
            version_line = result.stdout.split('\n')[0]
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'FFmpeg test successful!',
                    'ffmpeg_available': True,
                    'version': version_line,
                    'event': event,
                    'function_name': context.function_name,
                    'function_version': context.function_version
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'FFmpeg test failed',
                    'ffmpeg_available': False,
                    'error': result.stderr,
                    'event': event
                })
            }
            
    except subprocess.TimeoutExpired:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'FFmpeg test timed out',
                'ffmpeg_available': False,
                'error': 'FFmpeg command timed out after 10 seconds'
            })
        }
    except Exception as e:
        logger.error(f"Error in FFmpeg test: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'FFmpeg test failed with exception',
                'ffmpeg_available': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
        } 