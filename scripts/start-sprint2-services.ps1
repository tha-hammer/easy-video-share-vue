# Sprint 2 Service Startup Script
# This script starts all required services for Sprint 2 validation

Write-Host "Starting Sprint 2 Services..." -ForegroundColor Green

# Change to backend directory
$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $backendDir
Set-Location $backendDir

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Check if Redis is running, start if needed
Write-Host "`nChecking Redis status..." -ForegroundColor Cyan
try {
    python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis is running')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Redis is already running" -ForegroundColor Green
    } else {
        throw "Redis not responding"
    }
} catch {
    Write-Host "Starting Redis..." -ForegroundColor Yellow
    & "$projectRoot\scripts\start-redis.ps1"
    Start-Sleep -Seconds 3
}

# Start Celery worker in background
Write-Host "`nStarting Celery worker..." -ForegroundColor Cyan
$celeryJob = Start-Job -ScriptBlock {
    param($workingDir)
    Set-Location $workingDir
    python run_worker.py
} -ArgumentList $backendDir

Write-Host "✓ Celery worker started (Job ID: $($celeryJob.Id))" -ForegroundColor Green

# Start FastAPI server in background  
Write-Host "`nStarting FastAPI server..." -ForegroundColor Cyan
$apiJob = Start-Job -ScriptBlock {
    param($workingDir) 
    Set-Location $workingDir
    python main.py
} -ArgumentList $backendDir

Write-Host "✓ FastAPI server started (Job ID: $($apiJob.Id))" -ForegroundColor Green

# Wait for services to be ready
Write-Host "`nWaiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test API health
Write-Host "`nTesting API health..." -ForegroundColor Cyan
$maxRetries = 10
$retryCount = 0

do {
    $retryCount++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 5
        if ($response.status -eq "healthy") {
            Write-Host "✓ API is healthy and ready" -ForegroundColor Green
            break
        }
    } catch {
        if ($retryCount -lt $maxRetries) {
            Write-Host "Waiting for API... (attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        } else {
            Write-Host "❌ API failed to start properly" -ForegroundColor Red
            Write-Host "Check the API job output for errors:" -ForegroundColor Red
            Receive-Job -Job $apiJob
            break
        }
    }
} while ($retryCount -lt $maxRetries)

Write-Host "`n=== Sprint 2 Services Status ===" -ForegroundColor Magenta
Write-Host "Redis: Running"
Write-Host "Celery Worker: Job ID $($celeryJob.Id)"
Write-Host "FastAPI Server: Job ID $($apiJob.Id)"
Write-Host "API Endpoint: http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Run end-to-end test: python test_sprint2_e2e.py"
Write-Host "2. View API docs at: http://localhost:8000/docs"
Write-Host "3. To stop services, run: Stop-Job $($celeryJob.Id), $($apiJob.Id)"

Write-Host "`nServices are ready! 🚀" -ForegroundColor Green

# Keep script running and show job status
Write-Host "`nMonitoring services... (Press Ctrl+C to stop)" -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 30
        
        $celeryState = (Get-Job -Id $celeryJob.Id).State
        $apiState = (Get-Job -Id $apiJob.Id).State
        
        Write-Host "$(Get-Date -Format 'HH:mm:ss') - Celery: $celeryState, API: $apiState" -ForegroundColor DarkGray
        
        if ($celeryState -eq "Failed" -or $apiState -eq "Failed") {
            Write-Host "❌ One or more services have failed!" -ForegroundColor Red
            Write-Host "Celery Worker State: $celeryState"
            Write-Host "API Server State: $apiState"
            break
        }
    }
} catch {
    Write-Host "`nShutting down services..." -ForegroundColor Yellow
    Stop-Job -Job $celeryJob, $apiJob -PassThru | Remove-Job
    Write-Host "Services stopped." -ForegroundColor Green
}
