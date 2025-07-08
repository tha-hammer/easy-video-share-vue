import json
import logging

# Configure logging for CloudWatch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Minimal test to isolate the problem
    """
    logger.info("=== LAMBDA STARTED ===")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        logger.info("Testing imports...")
        import boto3
        logger.info("boto3 imported successfully")
        
        import redis
        logger.info("redis imported successfully")
        
        logger.info("Testing Redis connection...")
        redis_client = redis.StrictRedis(
            host='redis-14117.c265.us-east-1-2.ec2.redns.redis-cloud.com', 
            port=14117, 
            username='default',
            password='MNQmxGqbUGtAhKhQgH0fvxWvSG90qUvd',
            decode_responses=True, 
            socket_timeout=5, 
            socket_connect_timeout=5
        )
        redis_client.ping()
        logger.info("Redis connection successful!")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'All tests passed!',
                'imports': 'success',
                'redis': 'connected'
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }