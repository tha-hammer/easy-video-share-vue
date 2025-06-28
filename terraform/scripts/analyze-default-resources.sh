#!/bin/bash
# Corrected Resource Analysis Script - Analyzes DEFAULT workspace
# Since we discovered the 162 resources are in 'default', not 'complex-features'

set -e

echo "🔍 Resource Analysis: Default Workspace (Actual Current State)"
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
echo "=== ACTUAL DEPLOYED STATE: Default Workspace ==="

# Get total count
TOTAL_RESOURCES=$(terraform state list | wc -l)
echo "Total Resources: $TOTAL_RESOURCES"

# Save full resource list
terraform state list > analysis/all-resources-default.txt
echo "📄 Full resource list saved to: analysis/all-resources-default.txt"

echo ""
echo "🟢 CRITICAL RESOURCES (Must Keep/Import to main-simple):"

# Critical resources that contain data
CRITICAL_RESOURCES=(
    "aws_cognito_user_pool.video_app_users"
    "aws_cognito_user_group.admin_group" 
    "aws_cognito_user_group.user_group"
    "aws_cognito_user_pool_client.video_app_client"
    "aws_s3_bucket.video_bucket"
    "aws_dynamodb_table.video_metadata"
)

echo "" > analysis/critical-resources.txt
critical_count=0

for resource in "${CRITICAL_RESOURCES[@]}"; do
    if terraform state list | grep -q "^$resource$"; then
        echo "✅ $resource"
        echo "$resource" >> analysis/critical-resources.txt
        ((critical_count++))
        
        # Get the actual resource ID for import commands
        echo "   ID: $(terraform state show "$resource" | grep "^# " | head -1 | sed 's/^# //')"
    else
        echo "❌ $resource (NOT FOUND)"
    fi
done

echo "Critical Resources Total: $critical_count"
echo ""

echo "🔴 AI VIDEO FEATURES (Safe to Destroy):"
ai_resources=(
    "aws_lambda_function.ai_video_processor"
    "aws_lambda_layer_version.ai_video_layer"
    "aws_secretsmanager_secret.ai_video_secrets"
    "aws_secretsmanager_secret_version.ai_video_secrets"
)

echo "" > analysis/ai-resources-to-destroy.txt
ai_count=0

for resource in "${ai_resources[@]}"; do
    if terraform state list | grep -q "$resource"; then
        echo "🔴 $resource"
        echo "$resource" >> analysis/ai-resources-to-destroy.txt
        ((ai_count++))
    fi
done

# Find all AI-related resources with broader search
terraform state list | grep -i -E "(ai_video|ai-video)" >> analysis/ai-resources-to-destroy.txt

echo "AI Resources to Destroy: $ai_count"
echo ""

echo "🔵 AUDIO PROCESSING FEATURES (Safe to Destroy):"
audio_resources=(
    "aws_s3_bucket.audio_bucket"
    "aws_lambda_function.transcription_processor"
    "aws_cloudwatch_event_rule.transcribe_job_state_change"
    "aws_iam_role.transcription_processor_role"
)

echo "" > analysis/audio-resources-to-destroy.txt
audio_count=0

for resource in "${audio_resources[@]}"; do
    if terraform state list | grep -q "$resource"; then
        echo "🔵 $resource" 
        echo "$resource" >> analysis/audio-resources-to-destroy.txt
        ((audio_count++))
    fi
done

# Find all audio-related resources
terraform state list | grep -i -E "(audio|transcription)" >> analysis/audio-resources-to-destroy.txt

echo "Audio Resources to Destroy: $audio_count"
echo ""

echo "🟡 WEBSOCKET FEATURES (Safe to Destroy):"
websocket_count=$(terraform state list | grep -c "apigatewayv2" || echo "0")
terraform state list | grep "apigatewayv2" > analysis/websocket-resources-to-destroy.txt
terraform state list | grep "websocket" >> analysis/websocket-resources-to-destroy.txt

echo "WebSocket Resources to Destroy: $websocket_count"
echo ""

echo "🟠 API GATEWAY COMPLEX ENDPOINTS (May Need Simplification):"
# Count complex API resources
api_count=$(terraform state list | grep -c "api_gateway" || echo "0")
terraform state list | grep "api_gateway" > analysis/api-gateway-resources.txt

echo "API Gateway Resources: $api_count"
echo ""

# Generate import commands for critical resources
echo "📋 IMPORT COMMANDS FOR CRITICAL RESOURCES:"
echo "# Run these commands in main-simple workspace after ensuring main.tf is simple"
echo ""

# Extract actual resource IDs
if terraform state list | grep -q "aws_cognito_user_pool.video_app_users"; then
    USER_POOL_ID=$(terraform state show aws_cognito_user_pool.video_app_users | grep "id.*=" | head -1 | sed 's/.*= "\(.*\)"/\1/')
    echo "terraform import aws_cognito_user_pool.video_app_users $USER_POOL_ID"
fi

if terraform state list | grep -q "aws_s3_bucket.video_bucket"; then
    BUCKET_NAME=$(terraform state show aws_s3_bucket.video_bucket | grep "bucket.*=" | head -1 | sed 's/.*= "\(.*\)"/\1/')
    echo "terraform import aws_s3_bucket.video_bucket $BUCKET_NAME"
fi

if terraform state list | grep -q "aws_dynamodb_table.video_metadata"; then
    TABLE_NAME=$(terraform state show aws_dynamodb_table.video_metadata | grep "name.*=" | head -1 | sed 's/.*= "\(.*\)"/\1/')
    echo "terraform import aws_dynamodb_table.video_metadata $TABLE_NAME"
fi

echo ""
echo "💾 BACKUP COMMANDS:"
echo "# Run these NOW before making any changes"
echo "terraform state pull > backups/default-workspace-backup-\$(date +%Y%m%d-%H%M%S).json"
echo "terraform show -json > backups/default-workspace-full-\$(date +%Y%m%d-%H%M%S).json"

echo ""
echo "📊 SUMMARY:"
echo "  Total Resources in DEFAULT: $TOTAL_RESOURCES"
echo "  Critical (keep): $critical_count"
echo "  AI Features (destroy): $ai_count"
echo "  Audio Features (destroy): $audio_count" 
echo "  WebSocket (destroy): $websocket_count"
echo "  API Gateway (review): $api_count"

estimated_remaining=$((critical_count + 10))  # Estimate ~10 core API resources to keep
echo "  Estimated Simple Config: ~$estimated_remaining resources"

echo ""
echo "✅ Analysis complete! Check the 'analysis/' directory for detailed resource lists."
echo ""
echo "🚨 NEXT STEPS:"
echo "1. Review analysis/critical-resources.txt"
echo "2. Backup state: terraform state pull > backups/backup-\$(date +%Y%m%d).json"
echo "3. Test import commands in main-simple workspace"
echo "4. Begin selective destruction in default workspace"

# Return to original workspace
terraform workspace select "$CURRENT_WS"
echo ""
echo "🔄 Returned to workspace: $CURRENT_WS"
