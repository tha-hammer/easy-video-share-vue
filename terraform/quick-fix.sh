#!/bin/bash

# Quick fix for Lambda environment variables - follows deploy.sh pattern
# Removes AWS_REGION (reserved) and adds the missing DynamoDB table names

echo "🚀 Quick Lambda environment fix..."

aws lambda update-function-configuration \
  --function-name "easy-video-share-video-processor" \
  --region "us-east-1" \
  --environment Variables='{ENVIRONMENT=production,DYNAMODB_TABLE=easy-video-share-video-metadata,VIDEO_SEGMENTS_TABLE=easy-video-share-video-segments,S3_BUCKET=easy-video-share-silmari-dev}'

echo "✅ Lambda environment updated successfully!"
echo ""
echo "📊 Environment variables set:"
echo "  • ENVIRONMENT=production"
echo "  • DYNAMODB_TABLE=easy-video-share-video-metadata"
echo "  • VIDEO_SEGMENTS_TABLE=easy-video-share-video-segments"
echo "  • S3_BUCKET=easy-video-share-silmari-dev"
echo ""
echo "🔧 Test the fix:"
echo "aws lambda invoke --function-name easy-video-share-video-processor --region us-east-1 --payload '{\"action\":\"generate_thumbnail\",\"segment_id\":\"seg_76fabf52-c283-47ed-b8da-87b780dc4a84_032\"}' response.json" 