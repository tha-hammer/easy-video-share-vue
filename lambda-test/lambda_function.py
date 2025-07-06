import json

def lambda_handler(event, context):
    """
    Simple test Lambda function for Phase 1A testing
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from Lambda!',
            'event_received': event,
            'test_status': 'SUCCESS'
        })
    }