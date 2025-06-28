# Redis Setup Script for Windows
# This script helps install Redis for Windows

Write-Host "Setting up Redis for Easy Video Share Backend..." -ForegroundColor Green

# Check if Redis is already installed
try {
    $redisVersion = redis-server --version
    Write-Host "Redis is already installed: $redisVersion" -ForegroundColor Green
    Write-Host "Starting Redis server..." -ForegroundColor Yellow
    Start-Process -FilePath "redis-server" -WindowStyle Hidden
    Write-Host "Redis server started in background" -ForegroundColor Green
} catch {
    Write-Host "Redis not found. Installing Redis..." -ForegroundColor Yellow
    
    # Check if Chocolatey is installed
    try {
        choco --version | Out-Null
        Write-Host "Installing Redis via Chocolatey..." -ForegroundColor Yellow
        choco install redis-64 -y
        Write-Host "Redis installed successfully!" -ForegroundColor Green
        Write-Host "Starting Redis server..." -ForegroundColor Yellow
        Start-Process -FilePath "redis-server" -WindowStyle Hidden
        Write-Host "Redis server started in background" -ForegroundColor Green
    } catch {
        Write-Host "Chocolatey not found. Please install Redis manually:" -ForegroundColor Red
        Write-Host "1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Red
        Write-Host "2. Or install Chocolatey first: https://chocolatey.org/install" -ForegroundColor Red
        Write-Host "3. Then run: choco install redis-64" -ForegroundColor Red
        
        # Alternative: Download and extract Redis
        Write-Host "" -ForegroundColor Yellow
        Write-Host "Alternative: Using Redis from releases..." -ForegroundColor Yellow
        $redisUrl = "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip"
        $redisZip = "Redis-x64-3.0.504.zip"
        $redisDir = "redis"
        
        if (-not (Test-Path $redisDir)) {
            Write-Host "Downloading Redis..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $redisUrl -OutFile $redisZip
            Expand-Archive -Path $redisZip -DestinationPath $redisDir
            Remove-Item $redisZip
            Write-Host "Redis downloaded and extracted to $redisDir" -ForegroundColor Green
        }
        
        Write-Host "Starting Redis server from local directory..." -ForegroundColor Yellow
        Start-Process -FilePath "$redisDir\redis-server.exe" -WindowStyle Hidden
        Write-Host "Redis server started!" -ForegroundColor Green
    }
}

# Test Redis connection
Start-Sleep -Seconds 2
try {
    redis-cli ping
    Write-Host "✅ Redis is running and responding to ping!" -ForegroundColor Green
} catch {
    Write-Host "❌ Redis connection test failed. Please check Redis installation." -ForegroundColor Red
}
