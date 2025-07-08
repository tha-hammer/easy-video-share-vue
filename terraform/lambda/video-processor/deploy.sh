#!/bin/bash

# Deploy Production Lambda Video Processor
FUNCTION_NAME="easy-video-share-video-processor"
ROLE_ARN="arn:aws:iam::571960159088:role/easy-video-share-lambda-execution-role"

echo "=== DEPLOYING PRODUCTION LAMBDA VIDEO PROCESSOR ==="

echo "STEP 1: Installing Python dependencies..."
pip install -r requirements.txt -t .

echo "STEP 2: Creating production deployment package..."
"C:/Program Files/7-Zip/7z.exe" a production-lambda.zip lambda_function.py utils/ redis/

echo "STEP 3: Cleaning up dependency files..."
rm -rf redis/

echo "STEP 4: Checking if production function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    echo "Production function exists, updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://production-lambda.zip
    
    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240
else
    echo "Production function doesn't exist, creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://production-lambda.zip \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240 \
        --environment Variables='{"ENVIRONMENT":"production"}'
fi

echo "STEP 5: Testing production function..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_type":"hello","message":"Production deployment test"}' \
    production-test-response.json

echo "Production test response:"
cat production-test-response.json
echo ""

echo "=== PRODUCTION DEPLOYMENT COMPLETE ==="
echo "Function: $FUNCTION_NAME"
echo "Handler: lambda_function.lambda_handler"
echo "Timeout: 900 seconds (15 minutes)"
echo "Memory: 3008 MB"
echo "Storage: 10 GB"
echo "Environment: production"
echo ""
echo "Next steps:"
echo "1. Update Railway environment variables:"
echo "   - USE_LAMBDA_PROCESSING=true"
echo "   - LAMBDA_FUNCTION_NAME=$FUNCTION_NAME"
echo "2. Test Railway integration"
echo "3. Monitor CloudWatch logs" 