#!/bin/bash

# Deploy Enhanced Lambda Video Processor with Text Overlay Support
FUNCTION_NAME="easy-video-share-video-processor"
ROLE_ARN="arn:aws:iam::571960159088:role/easy-video-share-lambda-execution-role"

echo "=== DEPLOYING ENHANCED LAMBDA VIDEO PROCESSOR ==="
echo "Features: Two-phase processing, text overlays, thumbnail generation"

echo "STEP 1: Installing Python dependencies..."
pip install -r requirements.txt -t .

echo "STEP 2: Creating enhanced deployment package..."
# Include all necessary files for the enhanced lambda function
"C:/Program Files/7-Zip/7z.exe" a enhanced-lambda.zip lambda_function.py utils/ redis/ boto3/

echo "STEP 3: Cleaning up dependency files..."
rm -rf redis/ boto3/

echo "STEP 4: Checking if enhanced function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME 2>/dev/null; then
    echo "Enhanced function exists, updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://enhanced-lambda.zip
    
    echo "Updating function configuration for enhanced processing..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240 \
        --environment Variables='{ENVIRONMENT=production,S3_BUCKET=easy-video-share-bucket,DYNAMODB_TABLE_NAME=easy-video-share-video-metadata}'
else
    echo "Enhanced function doesn't exist, creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://enhanced-lambda.zip \
        --timeout 900 \
        --memory-size 3008 \
        --ephemeral-storage Size=10240 \
        --environment Variables='{ENVIRONMENT=production,S3_BUCKET=easy-video-share-bucket,DYNAMODB_TABLE_NAME=easy-video-share-video-metadata}'
fi

echo "STEP 5: Creating/updating DynamoDB table for video segments..."
aws dynamodb describe-table --table-name easy-video-share-video-segments 2>/dev/null || {
    echo "Creating video segments table..."
    aws dynamodb create-table \
        --table-name easy-video-share-video-segments \
        --attribute-definitions \
            AttributeName=segment_id,AttributeType=S \
            AttributeName=video_id,AttributeType=S \
            AttributeName=segment_number,AttributeType=N \
            AttributeName=created_at,AttributeType=S \
        --key-schema \
            AttributeName=segment_id,KeyType=HASH \
        --global-secondary-indexes \
            'IndexName=VideoIndex,KeySchema=[{AttributeName=video_id,KeyType=HASH},{AttributeName=segment_number,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
            'IndexName=CreatedAtIndex,KeySchema=[{AttributeName=video_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
        --billing-mode PAY_PER_REQUEST
}

echo "STEP 6: Deployment complete - test manually via AWS Console"
echo "Go to: https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/$FUNCTION_NAME"
echo ""

echo "=== ENHANCED DEPLOYMENT COMPLETE ==="
echo "Function: $FUNCTION_NAME"
echo "Handler: lambda_function.lambda_handler"
echo "Timeout: 900 seconds (15 minutes)"
echo "Memory: 3008 MB"
echo "Storage: 10 GB"
echo "Environment: production"
echo ""
echo "Enhanced Features:"
echo "✅ Two-phase processing (segments without text → text overlay application)"
echo "✅ Thumbnail generation for text overlay design"
echo "✅ Smart timeout handling with S3 temp storage"
echo "✅ DynamoDB segment metadata storage"
echo "✅ FFmpeg text overlay processing"
echo ""
echo "Processing Types Supported:"
echo "- full_video_processing (legacy compatibility)"
echo "- segments_without_text (Phase 1)"
echo "- apply_text_overlays (Phase 2)"
echo "- generate_thumbnail (thumbnails for design)"
echo ""
echo "Next steps:"
echo "1. Update Railway environment variables:"
echo "   - USE_LAMBDA_PROCESSING=true"
echo "   - LAMBDA_FUNCTION_NAME=$FUNCTION_NAME"
echo "2. Test Railway integration with enhanced endpoints"
echo "3. Test text overlay workflow end-to-end"
echo "4. Monitor CloudWatch logs for enhanced processing" 