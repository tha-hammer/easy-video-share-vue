#!/usr/bin/env python3
"""
Simple health check server for Celery worker
"""
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Check if Celery worker is running
            try:
                from tasks import celery_app
                # Try to inspect the worker
                inspect = celery_app.control.inspect()
                stats = inspect.stats()
                
                if stats:
                    self.wfile.write(b'{"status": "healthy", "message": "Celery worker is running"}')
                else:
                    self.wfile.write(b'{"status": "starting", "message": "Celery worker is starting up"}')
            except Exception as e:
                self.wfile.write(f'{{"status": "error", "message": "Celery worker error: {str(e)}"}}'.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

def start_health_server():
    """Start a simple HTTP server for health checks"""
    port = int(os.environ.get('PORT', 8001))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server starting on port {port}")
    
    def run_server():
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return server

if __name__ == '__main__':
    # Start health check server
    health_server = start_health_server()
    
    # Start Celery worker
    from tasks import celery_app
    celery_app.worker_main(['worker', '--loglevel=info', '--pool=solo']) 