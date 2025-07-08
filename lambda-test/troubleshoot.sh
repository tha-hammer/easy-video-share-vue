#!/bin/bash

# Troubleshooting script for Lambda FFmpeg timeout issues
FUNCTION_NAME="easy-video-share-video-processor-test"

echo "=== LAMBDA FFMPEG TROUBLESHOOTING ==="
echo ""

echo "STEP 1: Deploy diagnostic function..."
echo "Installing dependencies..."
pip install -r requirements.txt -t .

echo "Creating diagnostic package..."
"C:/Program Files/7-Zip/7z.exe" a diagnostic.zip lambda_function_diagnostic.py redis/

echo "Deploying diagnostic function..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://diagnostic.zip

echo "Running diagnostic..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test": "diagnostic"}' \
    diagnostic-response.json

echo "Diagnostic results:"
cat diagnostic-response.json | python -m json.tool
echo ""

echo "STEP 2: Check CloudWatch logs for detailed information..."
echo "Recent log events:"
aws logs describe-log-streams \
    --log-group-name "/aws/lambda/$FUNCTION_NAME" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text | xargs -I {} aws logs get-log-events \
    --log-group-name "/aws/lambda/$FUNCTION_NAME" \
    --log-stream-name {} \
    --start-time $(date -d '10 minutes ago' +%s)000 \
    --query 'events[*].message' \
    --output text

echo ""
echo "STEP 3: Deploy fixed function if diagnostic passes..."
read -p "Do you want to deploy the fixed function? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deploying fixed function..."
    bash deploy-fixed.sh
else
    echo "Skipping fixed function deployment."
fi

echo ""
echo "=== TROUBLESHOOTING COMPLETE ==="
echo ""
echo "Common issues and solutions:"
echo "1. FFmpeg not found: Check if FFmpeg layer is properly attached"
echo "2. Timeout issues: Increase Lambda timeout to 900 seconds"
echo "3. Memory issues: Increase Lambda memory to 3008 MB"
echo "4. Storage issues: Increase ephemeral storage to 10 GB"
echo "5. Permission issues: Check IAM role permissions"
echo ""
echo "Next steps:"
echo "- Check CloudWatch logs for detailed error messages"
echo "- Verify S3 bucket permissions"
echo "- Test with smaller video files first" 