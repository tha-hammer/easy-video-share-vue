#!/bin/bash

# Deploy Error Handling Test Lambda Function
FUNCTION_NAME="easy-video-share-video-processor-test"
ROLE_ARN="arn:aws:iam::571960159088:role/easy-video-share-lambda-execution-role"

echo "=== DEPLOYING ERROR HANDLING TESTS ==="

echo "STEP 1: Installing Python dependencies..."
pip install -r requirements.txt -t .

echo "STEP 2: Creating deployment package with error test function..."
"C:/Program Files/7-Zip/7z.exe" a error-test.zip lambda_function_error_test.py redis/

echo "STEP 3: Cleaning up dependency files..."
rm -rf redis/

echo "STEP 4: Deploying error test function..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://error-test.zip

echo "STEP 5: Updating handler to error test function..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --handler lambda_function_error_test.lambda_handler

echo "STEP 6: Testing error scenarios..."

# Test 1: Invalid S3 Key
echo "Testing invalid S3 key scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"invalid_s3_key","s3_bucket":"easy-video-share-silmari-dev","s3_key":"uploads/nonexistent-video.mov","job_id":"error-test-invalid-s3","user_id":"error-test-user"}' \
    error-test-invalid-s3.json

echo "Invalid S3 key result:"
cat error-test-invalid-s3.json
echo ""

# Test 2: Processing Timeout
echo "Testing processing timeout scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"processing_timeout","s3_bucket":"easy-video-share-silmari-dev","s3_key":"uploads/timeout-test.mov","job_id":"error-test-timeout","user_id":"error-test-user"}' \
    error-test-timeout.json

echo "Processing timeout result:"
cat error-test-timeout.json
echo ""

# Test 3: Upload Failure
echo "Testing upload failure scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"upload_failure","s3_bucket":"non-existent-bucket","s3_key":"uploads/upload-test.mov","job_id":"error-test-upload","user_id":"error-test-user"}' \
    error-test-upload.json

echo "Upload failure result:"
cat error-test-upload.json
echo ""

# Test 4: FFmpeg Failure
echo "Testing FFmpeg failure scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"ffmpeg_failure","s3_bucket":"easy-video-share-silmari-dev","s3_key":"uploads/ffmpeg-test.mov","job_id":"error-test-ffmpeg","user_id":"error-test-user"}' \
    error-test-ffmpeg.json

echo "FFmpeg failure result:"
cat error-test-ffmpeg.json
echo ""

# Test 5: DynamoDB Failure
echo "Testing DynamoDB failure scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"dynamodb_failure","s3_bucket":"easy-video-share-silmari-dev","s3_key":"uploads/dynamodb-test.mov","job_id":"error-test-dynamodb","user_id":"error-test-user"}' \
    error-test-dynamodb.json

echo "DynamoDB failure result:"
cat error-test-dynamodb.json
echo ""

# Test 6: Memory Pressure
echo "Testing memory pressure scenario..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"test_scenario":"memory_pressure","s3_bucket":"easy-video-share-silmari-dev","s3_key":"uploads/memory-test.mov","job_id":"error-test-memory","user_id":"error-test-user"}' \
    error-test-memory.json

echo "Memory pressure result:"
cat error-test-memory.json
echo ""

echo "=== ERROR HANDLING TESTS COMPLETE ==="
echo ""
echo "Test Results Summary:"
echo "- Invalid S3 Key: $(cat error-test-invalid-s3.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo "- Processing Timeout: $(cat error-test-timeout.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo "- Upload Failure: $(cat error-test-upload.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo "- FFmpeg Failure: $(cat error-test-ffmpeg.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo "- DynamoDB Failure: $(cat error-test-dynamodb.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo "- Memory Pressure: $(cat error-test-memory.json | python -c 'import sys,json; print("PASS" if json.load(sys.stdin).get("body", {}).get("test_status") == "SUCCESS" else "FAIL")' 2>/dev/null || echo "UNKNOWN")"
echo ""
echo "Check CloudWatch logs for detailed error handling information:"
echo "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$FUNCTION_NAME" 