#!/bin/bash

echo "🧪 Testing Lambda layer attachment..."

# Get the Lambda function name
FUNCTION_NAME="easy-video-share-ai-video-processor"

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
FUNCTION_INFO=$(aws lambda get-function --function-name "$FUNCTION_NAME" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Lambda function not found: $FUNCTION_NAME"
    echo "   Please run the deployment script first"
    exit 1
fi

echo "✅ Lambda function found"

# Check if layers are attached
echo "🔍 Checking Lambda layers..."
LAYERS=$(echo "$FUNCTION_INFO" | jq -r '.Configuration.Layers[].Arn' 2>/dev/null)

if [ -z "$LAYERS" ]; then
    echo "❌ No layers attached to Lambda function!"
    echo "   This is why google-auth-library is missing"
    exit 1
fi

echo "✅ Layers attached:"
echo "$LAYERS" | while read -r layer; do
    echo "   - $layer"
done

# Test the function with a simple payload
echo "🧪 Testing Lambda function with simple payload..."
TEST_PAYLOAD='{"httpMethod":"GET","path":"/test","headers":{}}'

RESPONSE=$(aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload "$TEST_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    response.json 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Lambda function executed successfully"
    echo "📄 Response:"
    cat response.json
    rm -f response.json
else
    echo "❌ Lambda function execution failed"
    echo "📄 Error: $RESPONSE"
    if [ -f response.json ]; then
        echo "📄 Response body:"
        cat response.json
        rm -f response.json
    fi
fi

echo "🧪 Test complete!" 