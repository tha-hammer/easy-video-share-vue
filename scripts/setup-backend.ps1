# Easy Video Share Backend - Development Setup Script
# Run this script to set up the backend development environment

Write-Host "Setting up Easy Video Share Backend..." -ForegroundColor Green

# Navigate to backend directory
Set-Location -Path "backend"

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Environment file .env not found. Please configure your environment variables." -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and fill in your AWS and Google AI credentials." -ForegroundColor Yellow
}

Write-Host "Backend setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start development:" -ForegroundColor Cyan
Write-Host "1. Start Redis server: redis-server" -ForegroundColor White
Write-Host "2. Start API server: python run_server.py" -ForegroundColor White
Write-Host "3. Start worker (new terminal): celery -A backend.tasks worker --loglevel=info" -ForegroundColor White

# Return to original directory
Set-Location -Path ".."
