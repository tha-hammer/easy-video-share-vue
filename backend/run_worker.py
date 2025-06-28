#!/usr/bin/env python3
"""
Celery worker startup script for video processing tasks
"""

from backend.tasks import celery_app

if __name__ == "__main__":
    celery_app.start()
