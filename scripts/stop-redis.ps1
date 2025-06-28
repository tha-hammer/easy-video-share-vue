# Stop Redis Docker service
Write-Host "Stopping Redis service..." -ForegroundColor Yellow

docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "Redis stopped successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to stop Redis" -ForegroundColor Red
    exit 1
}
