# Verify FFmpeg installation for MoviePy
Write-Host "Checking FFmpeg installation..." -ForegroundColor Green

try {
    $ffmpegVersion = ffmpeg -version 2>$null
    if ($ffmpegVersion) {
        Write-Host "✅ FFmpeg is installed and accessible" -ForegroundColor Green
        $versionLine = ($ffmpegVersion -split "`n")[0]
        Write-Host "Version: $versionLine" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "❌ FFmpeg is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install FFmpeg on Windows:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor White
    Write-Host "2. Extract to C:\ffmpeg" -ForegroundColor White
    Write-Host "3. Add C:\ffmpeg\bin to your PATH environment variable" -ForegroundColor White
    Write-Host "4. Restart your terminal/IDE" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative - Install via chocolatey:" -ForegroundColor Yellow
    Write-Host "choco install ffmpeg" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative - Install via winget:" -ForegroundColor Yellow
    Write-Host "winget install Gyan.FFmpeg" -ForegroundColor White
    exit 1
}

# Test Redis connection for Celery
Write-Host ""
Write-Host "Testing Redis connection for Celery..." -ForegroundColor Green

try {
    # Test if Redis container is running
    $redisStatus = docker ps --filter "name=easy-video-share-redis" --format "table {{.Status}}"
    if ($redisStatus -like "*Up*") {
        Write-Host "✅ Redis container is running" -ForegroundColor Green
        
        # Test Redis connectivity
        $redisPing = docker exec easy-video-share-redis redis-cli ping 2>$null
        if ($redisPing -eq "PONG") {
            Write-Host "✅ Redis connectivity test successful" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis not responding to ping" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Redis container is not running" -ForegroundColor Red
        Write-Host "Run: .\scripts\start-redis.ps1" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Could not check Redis status" -ForegroundColor Red
    Write-Host "Make sure Docker is running and Redis container exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Environment setup verification complete!" -ForegroundColor Green
