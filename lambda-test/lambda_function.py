import json
import boto3
import tempfile
import os

def lambda_handler(event, context):
    """
    Phase 4: Clean integration test
    """
    try:
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
    Phase 4: Minimal integration test - Just create job to test basic functionality
    """
    import uuid
    from datetime import datetime, timezone
    from decimal import Decimal
    
    try:
        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('easy-video-share-video-metadata')
        
        # Get parameters from event
        job_id = event.get('job_id', f"lambda-integration-{uuid.uuid4()}")
        user_id = event.get('user_id', 'lambda-test-user')
        
        # === STEP 1: CREATE JOB RECORD (QUEUED) ===
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        table.put_item(Item={
            'video_id': job_id,
            'user_id': user_id,
            'filename': 'test-integration.mov',
            'original_s3_key': 'test/integration.mov',
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
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'test_type': 'full_integration',
                'job_id': job_id,
                'message': 'Successfully created test job in DynamoDB',
                'test_status': 'SUCCESS'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'test_type': 'full_integration',
                'error': str(e),
                'test_status': 'FAILED'
            })
        }