import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Diagnostic function to check FFmpeg layer contents
    """
    logger.info("=== DIAGNOSTIC STARTED ===")
    
    try:
        # Check /opt/bin/ contents
        logger.info("Checking /opt/bin/ directory...")
        try:
            opt_bin_contents = os.listdir('/opt/bin/')
            logger.info(f"/opt/bin/ contents: {opt_bin_contents}")
        except Exception as e:
            logger.info(f"Cannot access /opt/bin/: {e}")
        
        # Check /opt/ contents  
        logger.info("Checking /opt/ directory...")
        try:
            opt_contents = os.listdir('/opt/')
            logger.info(f"/opt/ contents: {opt_contents}")
        except Exception as e:
            logger.info(f"Cannot access /opt/: {e}")
            
        # Check if ffmpeg exists
        ffmpeg_paths = ['/opt/bin/ffmpeg', '/usr/bin/ffmpeg']
        for path in ffmpeg_paths:
            if os.path.exists(path):
                logger.info(f"Found ffmpeg at: {path}")
            else:
                logger.info(f"ffmpeg not found at: {path}")
        
        # Check environment PATH
        path_env = os.environ.get('PATH', '')
        logger.info(f"PATH environment: {path_env}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Diagnostic complete - check logs',
                'status': 'success'
            })
        }
        
    except Exception as e:
        logger.error(f"Diagnostic error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }