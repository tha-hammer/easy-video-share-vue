"""
Lambda Integration Module for Railway Backend

This module handles the integration between Railway backend and AWS Lambda
for video processing, including feature flags and Lambda invocation.
"""

import boto3
import json
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

# Initialize AWS Lambda client
lambda_client = boto3.client('lambda')

def use_lambda_processing(request_data: Dict[str, Any]) -> bool:
    """
    Determine whether to use Lambda or Celery processing based on feature flags
    
    Args:
        request_data: The upload request data
        
    Returns:
        bool: True if Lambda processing should be used, False for Celery
    """
    # Check environment variable for global feature flag
    use_lambda = getattr(settings, 'USE_LAMBDA_PROCESSING', False)
    
    if not use_lambda:
        logger.info("Lambda processing disabled by feature flag")
        return False
    
    # Check file size - use Lambda for larger files
    file_size = request_data.get('file_size', 0)
    if file_size > 100 * 1024 * 1024:  # 100MB threshold
        logger.info(f"File size {file_size} bytes exceeds 100MB threshold, using Lambda")
        return True
    
    # Check user preference if available
    user_preference = request_data.get('user_id')
    if user_preference and hasattr(settings, 'LAMBDA_USERS') and user_preference in settings.LAMBDA_USERS:
        logger.info(f"User {user_preference} prefers Lambda processing")
        return True
    
    # Default to Celery for smaller files
    logger.info(f"File size {file_size} bytes under threshold, using Celery")
    return False

async def trigger_lambda_processing(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger AWS Lambda for video processing
    
    Args:
        request_data: The upload request data containing video processing parameters
        
    Returns:
        Dict containing Lambda invocation response
    """
    try:
        logger.info(f"Triggering Lambda processing for job {request_data.get('job_id')}")
        
        # Prepare payload for Lambda
        payload = {
            's3_bucket': settings.AWS_BUCKET_NAME,
            's3_key': request_data.get('s3_key'),
            'job_id': request_data.get('job_id'),
            'user_id': request_data.get('user_id', 'anonymous'),
            'segment_duration': request_data.get('segment_duration', 30),
            'cutting_options': request_data.get('cutting_options'),
            'text_input': request_data.get('text_input'),
            'source': 'railway'
        }
        
        # Get Lambda function name from settings
        function_name = getattr(settings, 'LAMBDA_FUNCTION_NAME', 'easy-video-share-video-processor')
        
        logger.info(f"Invoking Lambda function: {function_name}")
        logger.info(f"Payload: {json.dumps(payload, default=str)}")
        
        # Invoke Lambda function asynchronously
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Lambda invocation successful: {response}")
        
        return {
            'status': 'success',
            'lambda_response': response,
            'function_name': function_name,
            'invocation_type': 'async'
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger Lambda processing: {str(e)}")
        raise Exception(f"Lambda invocation failed: {str(e)}")

def get_lambda_function_status(function_name: str) -> Dict[str, Any]:
    """
    Get the status of a Lambda function
    
    Args:
        function_name: Name of the Lambda function
        
    Returns:
        Dict containing function status information
    """
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return {
            'status': 'available',
            'function_name': function_name,
            'runtime': response['Configuration']['Runtime'],
            'timeout': response['Configuration']['Timeout'],
            'memory_size': response['Configuration']['MemorySize'],
            'last_modified': response['Configuration']['LastModified']
        }
    except Exception as e:
        logger.error(f"Failed to get Lambda function status: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'function_name': function_name
        }

async def test_lambda_connectivity() -> Dict[str, Any]:
    """
    Test Lambda connectivity and configuration
    
    Returns:
        Dict containing test results
    """
    try:
        # Test basic Lambda client connectivity
        function_name = getattr(settings, 'LAMBDA_FUNCTION_NAME', 'easy-video-share-video-processor')
        
        # Get function status
        status = get_lambda_function_status(function_name)
        
        if status['status'] == 'available':
            return {
                'status': 'success',
                'message': 'Lambda connectivity test passed',
                'function_status': status
            }
        else:
            return {
                'status': 'error',
                'message': 'Lambda function not available',
                'function_status': status
            }
            
    except Exception as e:
        logger.error(f"Lambda connectivity test failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Lambda connectivity test failed: {str(e)}'
        }

# Configuration validation
def validate_lambda_config() -> Dict[str, Any]:
    """
    Validate Lambda configuration settings
    
    Returns:
        Dict containing validation results
    """
    validation_results = {
        'use_lambda_processing': getattr(settings, 'USE_LAMBDA_PROCESSING', False),
        'lambda_function_name': getattr(settings, 'LAMBDA_FUNCTION_NAME', 'easy-video-share-video-processor'),
        'aws_region': getattr(settings, 'AWS_REGION', 'us-east-1'),
        'aws_bucket_name': getattr(settings, 'AWS_BUCKET_NAME', ''),
        'missing_settings': []
    }
    
    # Check for required settings
    required_settings = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'AWS_BUCKET_NAME'
    ]
    
    for setting in required_settings:
        if not getattr(settings, setting, None):
            validation_results['missing_settings'].append(setting)
    
    validation_results['is_valid'] = len(validation_results['missing_settings']) == 0
    
    return validation_results 