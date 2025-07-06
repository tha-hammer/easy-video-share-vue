import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Simple test Lambda handler for Phase 1A testing
    """
    logger.info(f"Test Lambda invoked with event: {event}")
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Lambda Video Processor Test!',
            'event': event,
            'function_name': context.function_name,
            'function_version': context.function_version
        })
    } 