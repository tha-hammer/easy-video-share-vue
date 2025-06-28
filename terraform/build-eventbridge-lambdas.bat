@echo off
echo 🔨 Building EventBridge Lambda functions...

REM Change to terraform directory
cd /d "%~dp0"

REM Create transcription processor ZIP
echo 📦 Creating transcription-processor.zip...
cd lambda
powershell -Command "Compress-Archive -Path 'transcription-processor.js' -DestinationPath '../transcription_processor.zip' -Force"
cd ..

REM Create websocket handler ZIP  
echo 📦 Creating websocket-handler.zip...
cd lambda
powershell -Command "Compress-Archive -Path 'websocket-handler.js' -DestinationPath '../websocket_handler.zip' -Force"
cd ..

echo ✅ EventBridge Lambda functions built successfully!
echo 📁 Files created:
echo    - transcription_processor.zip
echo    - websocket_handler.zip
pause
