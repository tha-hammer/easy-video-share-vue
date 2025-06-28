#!/bi



n/bash

# Build script for EventBridge Lambda functions

echo "🔨 Building EventBridge Lambda functions..."

# Change to terraform directory
cd "$(dirname "$0")"

# Create transcription processor ZIP
echo "📦 Creating transcription-processor.zip..."
cd lambda
zip -r ../transcription_processor.zip transcription-processor.js
cd ..

# Create websocket handler ZIP  
echo "📦 Creating websocket-handler.zip..."
cd lambda
zip -r ../websocket_handler.zip websocket-handler.js
cd ..

echo "✅ EventBridge Lambda functions built successfully!"
echo "📁 Files created:"
echo "   - transcription_processor.zip"
echo "   - websocket_handler.zip"
