# Start Redis Docker service for development
Write-Host "Starting Redis service..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Start Redis with Docker Compose
docker-compose up -d redis

if ($LASTEXITCODE -eq 0) {
    Write-Host "Redis started successfully!" -ForegroundColor Green
    Write-Host "Redis is available at: redis://localhost:6379" -ForegroundColor Cyan
    
    # Test Redis connection
    Write-Host "Testing Redis connection..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    try {
        $testResult = docker exec easy-video-share-redis redis-cli ping
        if ($testResult -eq "PONG") {
            Write-Host "✅ Redis connection test successful!" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis connection test failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Could not test Redis connection" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to start Redis" -ForegroundColor Red
    exit 1
}
