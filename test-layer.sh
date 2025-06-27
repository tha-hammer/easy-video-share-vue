#!/bin/bash

echo "🧪 Testing Lambda layer creation..."

# Set up directories
LAMBDA_LAYER_DIR="temp-layer-test"
LAMBDA_LAYER_ZIP="terraform/ai_video_layer.zip"

# Clean up
if [ -d "$LAMBDA_LAYER_DIR" ]; then
    rm -rf "$LAMBDA_LAYER_DIR"
fi

# Create layer directory structure
mkdir -p "$LAMBDA_LAYER_DIR/nodejs"

# Create package.json
cat > "$LAMBDA_LAYER_DIR/nodejs/package.json" << 'EOF'
{
  "name": "ai-video-layer",
  "version": "1.0.0",
  "description": "AI Video Generation Dependencies",
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.450.0",
    "@aws-sdk/client-s3": "^3.450.0",
    "@aws-sdk/client-secrets-manager": "^3.450.0",
    "@aws-sdk/client-transcribe": "^3.450.0",
    "@aws-sdk/lib-dynamodb": "^3.450.0",
    "google-auth-library": "^9.0.0",
    "@google-cloud/vertexai": "^0.1.0",
    "openai": "^4.20.0"
  }
}
EOF

# Install dependencies
echo "📦 Installing dependencies..."
cd "$LAMBDA_LAYER_DIR/nodejs"
npm install --production
cd ../..

# Create ZIP
echo "📦 Creating ZIP..."
cd "$LAMBDA_LAYER_DIR"
powershell -Command "Compress-Archive -Path 'nodejs' -DestinationPath '../$LAMBDA_LAYER_ZIP' -Force"
cd ..

# Verify structure
echo "🔍 Verifying structure..."
# Use unzip -l to list ZIP contents without extracting
LAYER_CONTENTS=$(unzip -l "$LAMBDA_LAYER_ZIP" | tail -n +4 | head -n -2 | awk '{print $4}')

echo "📁 ZIP contents \(first 10 entries\):"
echo "$LAYER_CONTENTS" | head -10

if echo "$LAYER_CONTENTS" | grep -q "^nodejs/$" && echo "$LAYER_CONTENTS" | grep -q "^nodejs/node_modules/$" && echo "$LAYER_CONTENTS" | grep -q "^nodejs/node_modules/google-auth-library/"; then
    echo "✅ SUCCESS: google-auth-library found!"
    echo "   Total entries: $(echo "$LAYER_CONTENTS" | wc -l)"
else
    echo "❌ FAILED: google-auth-library not found!"
    echo "   Expected: nodejs/node_modules/google-auth-library"
    echo "   Found entries:"
    echo "$LAYER_CONTENTS" | head -20
fi

rm -rf "$LAMBDA_LAYER_DIR"

echo "🧪 Test complete!" 