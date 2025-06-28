#!/usr/bin/env python3
"""
Celery worker startup script for video processing tasks
"""

from tasks import celery_app

if __name__ == "__main__":
    # Start Celery worker with proper configuration
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=1',
        '--pool=solo'  # Use solo pool for Windows compatibility
    ])
