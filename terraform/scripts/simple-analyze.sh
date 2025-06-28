#!/bin/bash
# Simple Resource Analysis Script - Analyzes DEFAULT workspace
# More robust version that completes the analysis

set -e

echo "🔍 Simple Resource Analysis: Default Workspace"
echo ""

# Ensure we're analyzing the correct workspace
CURRENT_WS=$(terraform workspace show)
echo "Current workspace: $CURRENT_WS"

# Switch to default where the actual resources are
echo "🔄 Switching to DEFAULT workspace..."
terraform workspace select default

# Create analysis directory
mkdir -p analysis

echo ""
echo "=== ANALYZING DEFAULT WORKSPACE ==="

# Get total count and save all resources
terraform state list > analysis/all-resources-default.txt
TOTAL_RESOURCES=$(wc -l < analysis/all-resources-default.txt)
echo "Total Resources: $TOTAL_RESOURCES"

echo ""
echo "🔍 Looking for CRITICAL resources (must preserve)..."

# Check each critical resource individually
echo "Checking for Cognito User Pool..."
if grep -q "aws_cognito_user_pool.video_app_users" analysis/all-resources-default.txt; then
    echo "✅ aws_cognito_user_pool.video_app_users FOUND"
    echo "aws_cognito_user_pool.video_app_users" > analysis/critical-resources.txt
else
    echo "❌ aws_cognito_user_pool.video_app_users NOT FOUND"
    echo "" > analysis/critical-resources.txt
fi

echo "Checking for S3 Video Bucket..."
if grep -q "aws_s3_bucket.video_bucket" analysis/all-resources-default.txt; then
    echo "✅ aws_s3_bucket.video_bucket FOUND"
    echo "aws_s3_bucket.video_bucket" >> analysis/critical-resources.txt
else
    echo "❌ aws_s3_bucket.video_bucket NOT FOUND"
fi

echo "Checking for DynamoDB Table..."
if grep -q "aws_dynamodb_table.video_metadata" analysis/all-resources-default.txt; then
    echo "✅ aws_dynamodb_table.video_metadata FOUND"
    echo "aws_dynamodb_table.video_metadata" >> analysis/critical-resources.txt
else
    echo "❌ aws_dynamodb_table.video_metadata NOT FOUND"
fi

echo "Checking for Cognito Groups..."
if grep -q "aws_cognito_user_group" analysis/all-resources-default.txt; then
    echo "✅ Found Cognito User Groups:"
    grep "aws_cognito_user_group" analysis/all-resources-default.txt | sed 's/^/    /'
    grep "aws_cognito_user_group" analysis/all-resources-default.txt >> analysis/critical-resources.txt
else
    echo "❌ No Cognito User Groups found"
fi

echo "Checking for Cognito User Pool Client..."
if grep -q "aws_cognito_user_pool_client" analysis/all-resources-default.txt; then
    echo "✅ Found Cognito User Pool Client:"
    grep "aws_cognito_user_pool_client" analysis/all-resources-default.txt | sed 's/^/    /'
    grep "aws_cognito_user_pool_client" analysis/all-resources-default.txt >> analysis/critical-resources.txt
else
    echo "❌ No Cognito User Pool Client found"
fi

# Count critical resources
CRITICAL_COUNT=$(wc -l < analysis/critical-resources.txt)
echo ""
echo "📊 Critical Resources Found: $CRITICAL_COUNT"

echo ""
echo "🔴 Looking for AI/COMPLEX resources (safe to destroy)..."

# Find AI video resources
echo "AI Video Resources:" > analysis/ai-resources.txt
grep -i "ai_video\|ai-video" analysis/all-resources-default.txt >> analysis/ai-resources.txt || echo "None found"
AI_COUNT=$(grep -c "aws_" analysis/ai-resources.txt || echo "0")

# Find audio resources
echo "Audio Resources:" > analysis/audio-resources.txt
grep -i "audio\|transcription" analysis/all-resources-default.txt >> analysis/audio-resources.txt || echo "None found"
AUDIO_COUNT=$(grep -c "aws_" analysis/audio-resources.txt || echo "0")

# Find WebSocket resources
echo "WebSocket Resources:" > analysis/websocket-resources.txt
grep -i "websocket\|apigatewayv2" analysis/all-resources-default.txt >> analysis/websocket-resources.txt || echo "None found"
WEBSOCKET_COUNT=$(grep -c "aws_" analysis/websocket-resources.txt || echo "0")

# Find Secrets Manager
echo "Secrets Manager:" > analysis/secrets-resources.txt
grep -i "secretsmanager" analysis/all-resources-default.txt >> analysis/secrets-resources.txt || echo "None found"
SECRETS_COUNT=$(grep -c "aws_" analysis/secrets-resources.txt || echo "0")

# Find EventBridge/CloudWatch Events
echo "EventBridge/CloudWatch:" > analysis/eventbridge-resources.txt
grep -i "cloudwatch_event\|eventbridge" analysis/all-resources-default.txt >> analysis/eventbridge-resources.txt || echo "None found"
EVENTBRIDGE_COUNT=$(grep -c "aws_" analysis/eventbridge-resources.txt || echo "0")

echo "📊 Complex Feature Counts:"
echo "  AI Video: $AI_COUNT"
echo "  Audio: $AUDIO_COUNT"
echo "  WebSocket: $WEBSOCKET_COUNT"
echo "  Secrets: $SECRETS_COUNT"
echo "  EventBridge: $EVENTBRIDGE_COUNT"

COMPLEX_TOTAL=$((AI_COUNT + AUDIO_COUNT + WEBSOCKET_COUNT + SECRETS_COUNT + EVENTBRIDGE_COUNT))
echo "  Total Complex: $COMPLEX_TOTAL"

echo ""
echo "📋 RESOURCE CATEGORIES:"

# Show top-level resource types
echo "Resource Type Summary:" > analysis/resource-summary.txt
echo "=====================" >> analysis/resource-summary.txt
cut -d. -f1 analysis/all-resources-default.txt | sort | uniq -c | sort -nr >> analysis/resource-summary.txt

echo "Top 10 Resource Types:"
head -10 analysis/resource-summary.txt | tail -9

echo ""
echo "🎯 IMPORT COMMANDS NEEDED:"
echo ""

# Generate import commands for found critical resources
if grep -q "aws_cognito_user_pool.video_app_users" analysis/critical-resources.txt; then
    echo "# Get User Pool ID first:"
    echo "terraform workspace select default"
    echo "terraform state show aws_cognito_user_pool.video_app_users | grep 'id.*='"
    echo ""
    echo "# Then import to main-simple:"
    echo "terraform workspace select main-simple"
    echo "terraform import aws_cognito_user_pool.video_app_users [USER_POOL_ID]"
    echo ""
fi

if grep -q "aws_s3_bucket.video_bucket" analysis/critical-resources.txt; then
    echo "# Get S3 Bucket name:"
    echo "terraform workspace select default"
    echo "terraform state show aws_s3_bucket.video_bucket | grep 'bucket.*='"
    echo ""
    echo "# Then import:"
    echo "terraform import aws_s3_bucket.video_bucket [BUCKET_NAME]"
    echo ""
fi

if grep -q "aws_dynamodb_table.video_metadata" analysis/critical-resources.txt; then
    echo "# Get DynamoDB table name:"
    echo "terraform workspace select default"
    echo "terraform state show aws_dynamodb_table.video_metadata | grep 'name.*='"
    echo ""
    echo "# Then import:"
    echo "terraform import aws_dynamodb_table.video_metadata [TABLE_NAME]"
    echo ""
fi

echo ""
echo "🛡️  BACKUP COMMANDS:"
echo "terraform workspace select default"
echo "terraform state pull > backups/backup-\$(date +%Y%m%d-%H%M%S).json"

echo ""
echo "📁 Analysis files created:"
echo "  analysis/all-resources-default.txt - All 162 resources"
echo "  analysis/critical-resources.txt - Critical resources to preserve"
echo "  analysis/ai-resources.txt - AI features to destroy"
echo "  analysis/audio-resources.txt - Audio features to destroy"
echo "  analysis/websocket-resources.txt - WebSocket features to destroy"
echo "  analysis/resource-summary.txt - Resource type breakdown"

echo ""
echo "✅ Analysis complete!"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Review critical-resources.txt to see what will be preserved"
echo "2. Backup your state: terraform state pull > backups/backup-\$(date +%Y%m%d).json"
echo "3. Get resource IDs for import commands above"
echo "4. Run migration: ./scripts/migrate-default-to-simple.sh"

# Return to original workspace
terraform workspace select "$CURRENT_WS"
echo ""
echo "🔄 Returned to workspace: $CURRENT_WS"
