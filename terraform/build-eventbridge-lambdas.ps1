#!/usr/bin/env pwsh

# Build script for EventBridge Lambda functions (Windows PowerShell)

Write-Host "🔨 Building EventBridge Lambda functions..." -ForegroundColor Green

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Create transcription processor ZIP
Write-Host "📦 Creating transcription-processor.zip..." -ForegroundColor Yellow
$transcriptionFiles = @(
    "lambda/transcription-processor.js"
)

if (Test-Path "transcription_processor.zip") {
    Remove-Item "transcription_processor.zip" -Force
}

Compress-Archive -Path $transcriptionFiles -DestinationPath "transcription_processor.zip" -CompressionLevel Optimal

# Create websocket handler ZIP  
Write-Host "📦 Creating websocket-handler.zip..." -ForegroundColor Yellow
$websocketFiles = @(
    "lambda/websocket-handler.js"
)

if (Test-Path "websocket_handler.zip") {
    Remove-Item "websocket_handler.zip" -Force
}

Compress-Archive -Path $websocketFiles -DestinationPath "websocket_handler.zip" -CompressionLevel Optimal

Write-Host "✅ EventBridge Lambda functions built successfully!" -ForegroundColor Green
Write-Host "📁 Files created:" -ForegroundColor Cyan
Write-Host "   - transcription_processor.zip" -ForegroundColor White
Write-Host "   - websocket_handler.zip" -ForegroundColor White

# Verify the files were created
if (Test-Path "transcription_processor.zip") {
    $size1 = (Get-Item "transcription_processor.zip").Length
    Write-Host "   ✓ transcription_processor.zip ($size1 bytes)" -ForegroundColor Green
} else {
    Write-Host "   ❌ transcription_processor.zip not created" -ForegroundColor Red
}

if (Test-Path "websocket_handler.zip") {
    $size2 = (Get-Item "websocket_handler.zip").Length
    Write-Host "   ✓ websocket_handler.zip ($size2 bytes)" -ForegroundColor Green
} else {
    Write-Host "   ❌ websocket_handler.zip not created" -ForegroundColor Red
}
