# Easy Video Share Backend - Celery Worker Script
# Starts the Celery worker for background video processing

Write-Host "Starting Easy Video Share Celery Worker..." -ForegroundColor Green

# Check if Redis is running
try {
    $redisStatus = docker ps --filter "name=easy-video-share-redis" --format "table {{.Status}}"
    if (-not ($redisStatus -like "*Up*")) {
        Write-Host "❌ Redis container is not running" -ForegroundColor Red
        Write-Host "Starting Redis first..." -ForegroundColor Yellow
        & ".\scripts\start-redis.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to start Redis. Exiting." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Could not check Redis status. Make sure Docker is running." -ForegroundColor Red
    exit 1
}

# Navigate to backend directory
Set-Location -Path "backend"

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  No virtual environment found. Using system Python." -ForegroundColor Yellow
}

# Test Redis connection
Write-Host "Testing Redis connection..." -ForegroundColor Yellow
python test_redis_connection.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Redis connection test failed" -ForegroundColor Red
    exit 1
}

# Start the worker
Write-Host "Starting Celery worker for video processing tasks..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the worker" -ForegroundColor Yellow
Write-Host ""

celery -A tasks worker --loglevel=info --pool=solo

# Return to original directory
Set-Location -Path ".."
