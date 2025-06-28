# Easy Video Share Backend - Celery Worker Script
# Starts the Celery worker for background video processing

Write-Host "Starting Easy Video Share Celery Worker..." -ForegroundColor Green

# Navigate to backend directory
Set-Location -Path "backend"

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
}

# Start the worker
Write-Host "Starting Celery worker for video processing tasks..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the worker" -ForegroundColor Yellow
Write-Host ""

celery -A backend.tasks worker --loglevel=info --pool=solo

# Return to original directory
Set-Location -Path ".."
