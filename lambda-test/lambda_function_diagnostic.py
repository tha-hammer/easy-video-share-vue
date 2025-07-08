import json
import os
import subprocess
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Diagnostic function to troubleshoot Lambda environment and FFmpeg issues
    """
    logger.info("=== LAMBDA DIAGNOSTIC STARTED ===")
    
    diagnostics = {
        'environment': {},
        'ffmpeg': {},
        'paths': {},
        'permissions': {},
        'test_results': {}
    }
    
    try:
        # Environment diagnostics
        logger.info("Checking environment...")
        diagnostics['environment'] = {
            'python_version': os.sys.version,
            'current_working_directory': os.getcwd(),
            'temp_directory': os.environ.get('TMPDIR', '/tmp'),
            'lambda_runtime': os.environ.get('AWS_LAMBDA_RUNTIME_API'),
            'memory_limit': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE'),
            'timeout': context.get_remaining_time_in_millis() if context else 'unknown'
        }
        
        # Path diagnostics
        logger.info("Checking file system...")
        paths_to_check = [
            '/opt/bin/',
            '/opt/ffmpeg/bin/',
            '/usr/bin/',
            '/usr/local/bin/',
            '/var/task/',
            '/tmp/'
        ]
        
        for path in paths_to_check:
            try:
                if os.path.exists(path):
                    contents = os.listdir(path)
                    diagnostics['paths'][path] = {
                        'exists': True,
                        'contents': contents[:10],  # First 10 items
                        'total_items': len(contents)
                    }
                else:
                    diagnostics['paths'][path] = {'exists': False}
            except Exception as e:
                diagnostics['paths'][path] = {'exists': True, 'error': str(e)}
        
        # FFmpeg diagnostics
        logger.info("Checking FFmpeg availability...")
        ffmpeg_paths = ['/opt/bin/ffmpeg', '/opt/ffmpeg/bin/ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']
        ffprobe_paths = ['/opt/bin/ffprobe', '/opt/ffmpeg/bin/ffprobe', '/usr/bin/ffprobe', '/usr/local/bin/ffprobe']
        
        # Check PATH
        ffmpeg_in_path = shutil.which('ffmpeg')
        ffprobe_in_path = shutil.which('ffprobe')
        
        if ffmpeg_in_path:
            ffmpeg_paths.insert(0, ffmpeg_in_path)
        if ffprobe_in_path:
            ffprobe_paths.insert(0, ffprobe_in_path)
        
        diagnostics['ffmpeg']['paths_checked'] = {
            'ffmpeg': ffmpeg_paths,
            'ffprobe': ffprobe_paths
        }
        
        # Test FFmpeg binaries
        for path in ffmpeg_paths:
            try:
                if os.path.exists(path):
                    result = subprocess.run([path, '-version'], 
                                          capture_output=True, text=True, timeout=10)
                    diagnostics['ffmpeg'][path] = {
                        'exists': True,
                        'executable': True,
                        'return_code': result.returncode,
                        'version_output': result.stdout[:200] if result.stdout else None,
                        'error_output': result.stderr[:200] if result.stderr else None
                    }
                else:
                    diagnostics['ffmpeg'][path] = {'exists': False}
            except subprocess.TimeoutExpired:
                diagnostics['ffmpeg'][path] = {'exists': True, 'executable': True, 'timeout': True}
            except Exception as e:
                diagnostics['ffmpeg'][path] = {'exists': True, 'executable': False, 'error': str(e)}
        
        # Test FFprobe binaries
        for path in ffprobe_paths:
            try:
                if os.path.exists(path):
                    result = subprocess.run([path, '-version'], 
                                          capture_output=True, text=True, timeout=10)
                    diagnostics['ffprobe'][path] = {
                        'exists': True,
                        'executable': True,
                        'return_code': result.returncode,
                        'version_output': result.stdout[:200] if result.stdout else None,
                        'error_output': result.stderr[:200] if result.stderr else None
                    }
                else:
                    diagnostics['ffprobe'][path] = {'exists': False}
            except subprocess.TimeoutExpired:
                diagnostics['ffprobe'][path] = {'exists': True, 'executable': True, 'timeout': True}
            except Exception as e:
                diagnostics['ffprobe'][path] = {'exists': True, 'executable': False, 'error': str(e)}
        
        # Permission diagnostics
        logger.info("Checking permissions...")
        try:
            # Test temp directory write
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write('test')
                temp_file = f.name
            
            os.unlink(temp_file)
            diagnostics['permissions']['temp_write'] = True
        except Exception as e:
            diagnostics['permissions']['temp_write'] = False
            diagnostics['permissions']['temp_write_error'] = str(e)
        
        # Test subprocess execution
        try:
            result = subprocess.run(['ls', '-la'], capture_output=True, text=True, timeout=5)
            diagnostics['permissions']['subprocess'] = True
            diagnostics['permissions']['subprocess_output'] = result.stdout[:200]
        except Exception as e:
            diagnostics['permissions']['subprocess'] = False
            diagnostics['permissions']['subprocess_error'] = str(e)
        
        # Simple FFmpeg test if available
        working_ffmpeg = None
        for path, info in diagnostics.get('ffmpeg', {}).items():
            if isinstance(info, dict) and info.get('executable'):
                working_ffmpeg = path
                break
        
        if working_ffmpeg:
            logger.info(f"Testing FFmpeg with: {working_ffmpeg}")
            try:
                # Create a simple test
                test_cmd = [working_ffmpeg, '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1', 
                           '-f', 'null', '-']
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
                diagnostics['test_results']['ffmpeg_simple_test'] = {
                    'success': result.returncode == 0,
                    'return_code': result.returncode,
                    'stderr': result.stderr[:200] if result.stderr else None
                }
            except Exception as e:
                diagnostics['test_results']['ffmpeg_simple_test'] = {
                    'success': False,
                    'error': str(e)
                }
        
        logger.info("=== DIAGNOSTIC COMPLETED ===")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'diagnostic_results': diagnostics,
                'summary': {
                    'ffmpeg_found': any(info.get('executable') for info in diagnostics.get('ffmpeg', {}).values() if isinstance(info, dict)),
                    'ffprobe_found': any(info.get('executable') for info in diagnostics.get('ffprobe', {}).values() if isinstance(info, dict)),
                    'temp_writable': diagnostics.get('permissions', {}).get('temp_write', False),
                    'subprocess_working': diagnostics.get('permissions', {}).get('subprocess', False)
                }
            }, indent=2)
        }
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'partial_diagnostics': diagnostics
            })
        }