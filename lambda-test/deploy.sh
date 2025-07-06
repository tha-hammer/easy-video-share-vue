#!/bin/bash

# Fast Lambda deployment script
# Run this from your main terminal (not WSL) where AWS CLI works

FUNCTION_NAME="easy-video-share-video-processor-test"
ROLE_ARN="arn:aws:iam::864074432175:role/lambda-execution-role"  # Update this with your actual role ARN

echo "Creating deployment package..."
cd lambda-test
zip -r function.zip lambda_function.py

echo "Checking if function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    echo "Function exists, updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip
else
    echo "Function doesn't exist, creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 60 \
        --memory-size 128
fi

echo "Testing function..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://test-event.json \
    response.json

echo "Response:"
cat response.json
echo ""

echo "Done! Function deployed and tested."