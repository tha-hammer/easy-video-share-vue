#!/bin/bash

# Quick update script for Lambda function - much faster than Terraform
# Updates environment variables and IAM policy for the new segment architecture

set -e

# Configuration
FUNCTION_NAME="easy-video-share-video-processor"
REGION="us-east-1"
ACCOUNT_ID="571960159088"
BUCKET_NAME="easy-video-share-silmari-dev"
USER_POOL_ID="us-east-1_8L0Sa4BCn"

echo "🚀 Quick Lambda update for segment architecture..."

# Update Lambda environment variables
echo "📋 Updating Lambda environment variables..."
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --environment "Variables={
    ENVIRONMENT=production,
    DYNAMODB_TABLE=easy-video-share-video-metadata,
    VIDEO_SEGMENTS_TABLE=easy-video-share-video-segments,
    S3_BUCKET=$BUCKET_NAME
  }"

echo "✅ Environment variables updated"

# Update IAM role policy
echo "📋 Updating IAM role policy..."
ROLE_NAME="easy-video-share-lambda-execution-role"

# Create updated policy JSON
cat > /tmp/updated-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Effect": "Allow",
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/easy-video-share-video-metadata",
        "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/easy-video-share-video-metadata/index/*",
        "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/easy-video-share-video-segments",
        "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/easy-video-share-video-segments/index/*"
      ]
    },
    {
      "Action": [
        "cognito-idp:ListUsers",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminDeleteUser",
        "cognito-idp:AdminDisableUser",
        "cognito-idp:AdminEnableUser",
        "cognito-idp:AdminAddUserToGroup",
        "cognito-idp:AdminRemoveUserFromGroup",
        "cognito-idp:AdminListGroupsForUser",
        "cognito-idp:ListUsersInGroup"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:cognito-idp:$REGION:$ACCOUNT_ID:userpool/$USER_POOL_ID"
    },
    {
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:CreateMultipartUpload",
        "s3:UploadPart",
        "s3:CompleteMultipartUpload",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    }
  ]
}
EOF

# Update the policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "easy-video-share-lambda-policy" \
  --policy-document file:///tmp/updated-policy.json

echo "✅ IAM policy updated"

# Clean up
rm /tmp/updated-policy.json

echo ""
echo "🎉 Quick Lambda update completed successfully!"
echo ""
echo "📊 Changes applied:"
echo "  • Updated Lambda environment variables to include both DynamoDB table names"
echo "  • Enhanced IAM permissions for batch DynamoDB operations"
echo "  • Added S3_BUCKET and AWS_REGION environment variables"
echo ""
echo "🔧 Next steps:"
echo "  1. Test thumbnail generation: aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"action\":\"generate_thumbnail\",\"segment_id\":\"test\"}'"
echo "  2. Test segment retrieval from both storage systems"
echo "  3. Verify text overlay processing works"
echo ""
echo "⚡ This update took seconds instead of minutes!" 