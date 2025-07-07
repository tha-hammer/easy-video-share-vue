#!/bin/bash

# Deploy Lambda function with dependencies
FUNCTION_NAME="easy-video-share-video-processor-test"
ROLE_ARN="arn:aws:iam::571960159088:role/easy-video-share-lambda-execution-role"

echo "Installing Python dependencies..."
pip install -r requirements.txt -t .

echo "Creating deployment package..."
"C:/Program Files/7-Zip/7z.exe" a function.zip lambda_function.py redis/

echo "Cleaning up dependency files..."
rm -rf redis/

echo "Checking if function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    echo "Function exists, updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip
    
    echo "Updating function configuration..."
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
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240
fi

echo "Testing function..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://test-event.json \
    response.json

echo "Response:"
cat response.json
echo ""

echo "Done! Function deployed with dependencies and proper configuration."