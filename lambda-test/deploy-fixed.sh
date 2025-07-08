#!/bin/bash

# Deploy Fixed Lambda function with proper configuration for video processing
FUNCTION_NAME="easy-video-share-video-processor-test"
ROLE_ARN="arn:aws:iam::571960159088:role/easy-video-share-lambda-execution-role"

echo "=== DEPLOYING FIXED LAMBDA FUNCTION ==="

echo "STEP 1: Installing Python dependencies..."
pip install -r requirements.txt -t .

echo "STEP 2: Creating deployment package with fixed function..."
"C:/Program Files/7-Zip/7z.exe" a function.zip lambda_function_fixed.py redis/

echo "STEP 3: Cleaning up dependency files..."
rm -rf redis/

echo "STEP 4: Checking if function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    echo "Function exists, updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip
    
    echo "Updating function configuration for video processing..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240
else
    echo "Function doesn't exist, creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function_fixed.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240
fi

echo "STEP 5: Testing function with basic event..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test": "hello"}' \
    basic-response.json

echo "Basic test response:"
cat basic-response.json
echo ""

echo "STEP 6: Testing function with full integration event..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://test-event.json \
    integration-response.json

echo "Integration test response:"
cat integration-response.json
echo ""

echo "=== DEPLOYMENT COMPLETE ==="
echo "Function: $FUNCTION_NAME"
echo "Handler: lambda_function_fixed.lambda_handler"
echo "Timeout: 900 seconds (15 minutes)"
echo "Memory: 3008 MB"
echo "Storage: 10 GB"
echo ""
echo "Check CloudWatch logs for detailed execution information:"
echo "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$FUNCTION_NAME" 