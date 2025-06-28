# Easy Video Share Backend - Development Server Script
# Starts the FastAPI development server

Write-Host "Starting Easy Video Share Backend API Server..." -ForegroundColor Green

# Navigate to backend directory
Set-Location -Path "backend"

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
}

# Start the server
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python run_server.py

# Return to original directory
Set-Location -Path ".."
