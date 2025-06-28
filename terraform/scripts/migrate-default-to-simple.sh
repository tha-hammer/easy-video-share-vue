#!/bin/bash
# Migration Script: Default → Main-Simple
# Safely migrates from complex default workspace to simple main-simple workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="../backups"
ANALYSIS_DIR="../analysis"

echo "🚀 Migration Script: Default → Main-Simple"
echo "⚠️  This will migrate from complex (default) to simple (main-simple) configuration"
echo ""

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$ANALYSIS_DIR"

# Safety check
read -p "Have you run the analysis script and reviewed the resource lists? (y/n): " analyzed
if [ "$analyzed" != "y" ]; then
    echo "❌ Please run './scripts/analyze-default-resources.sh' first"
    exit 1
fi

echo ""
echo "📋 Migration Overview:"
echo "  Source: default workspace (162 resources)"
echo "  Target: main-simple workspace (simple config)"
echo "  Strategy: Import critical → Destroy complex → Deploy simple"
echo ""

read -p "Continue with migration? (y/n): " continue_migration
if [ "$continue_migration" != "y" ]; then
    echo "Migration cancelled."
    exit 0
fi

# Phase 1: Backup everything
echo ""
echo "🛡️  Phase 1: Backup Current State"
echo "=================================="

terraform workspace select default

timestamp=$(date +"%Y%m%d-%H%M%S")
backup_file="$BACKUP_DIR/default-workspace-pre-migration-$timestamp.json"
state_export="$BACKUP_DIR/default-workspace-export-$timestamp.json"

echo "📦 Backing up default workspace state..."
terraform state pull > "$backup_file"
echo "✅ State backed up to: $backup_file"

echo "📄 Exporting full state details..."
terraform show -json > "$state_export"
echo "✅ Full state exported to: $state_export"

# Phase 2: Extract Critical Resource IDs
echo ""
echo "🔍 Phase 2: Extract Critical Resource Information"
echo "================================================"

echo "📋 Extracting resource IDs for import..."

# Function to extract resource ID safely
get_resource_id() {
    local resource_name="$1"
    if terraform state list | grep -q "^$resource_name$"; then
        terraform state show "$resource_name" | grep -E "^\s*id\s*=" | head -1 | sed 's/.*= "\(.*\)"/\1/'
    else
        echo ""
    fi
}

# Extract critical resource IDs
USER_POOL_ID=$(get_resource_id "aws_cognito_user_pool.video_app_users")
BUCKET_NAME=$(get_resource_id "aws_s3_bucket.video_bucket") 
TABLE_NAME=$(get_resource_id "aws_dynamodb_table.video_metadata")
API_GATEWAY_ID=$(get_resource_id "aws_api_gateway_rest_api.video_api")

echo "Critical Resource IDs:"
echo "  Cognito User Pool: $USER_POOL_ID"
echo "  S3 Video Bucket: $BUCKET_NAME"  
echo "  DynamoDB Table: $TABLE_NAME"
echo "  API Gateway: $API_GATEWAY_ID"

# Save to file for reference
cat > "$ANALYSIS_DIR/critical-resource-ids.txt" << EOF
# Critical Resource IDs for Import
USER_POOL_ID=$USER_POOL_ID
BUCKET_NAME=$BUCKET_NAME
TABLE_NAME=$TABLE_NAME
API_GATEWAY_ID=$API_GATEWAY_ID
EOF

# Verify critical resources exist
echo ""
echo "🔍 Verifying critical resources exist in AWS..."

if [ -n "$USER_POOL_ID" ]; then
    if aws cognito-idp describe-user-pool --user-pool-id "$USER_POOL_ID" >/dev/null 2>&1; then
        echo "✅ Cognito User Pool exists"
    else
        echo "❌ Cognito User Pool verification failed"
        exit 1
    fi
fi

if [ -n "$BUCKET_NAME" ]; then
    if aws s3 ls "s3://$BUCKET_NAME" >/dev/null 2>&1; then
        echo "✅ S3 Video Bucket exists and is accessible"
    else
        echo "❌ S3 Video Bucket verification failed"
        exit 1
    fi
fi

if [ -n "$TABLE_NAME" ]; then
    if aws dynamodb describe-table --table-name "$TABLE_NAME" >/dev/null 2>&1; then
        echo "✅ DynamoDB Table exists"
    else
        echo "❌ DynamoDB Table verification failed"
        exit 1
    fi
fi

echo ""
read -p "All critical resources verified. Continue to import phase? (y/n): " continue_import
if [ "$continue_import" != "y" ]; then
    echo "Migration paused. You can resume later."
    exit 0
fi

# Phase 3: Setup Simple Workspace
echo ""
echo "🔧 Phase 3: Setup Simple Workspace"
echo "=================================="

terraform workspace select main-simple

echo "📄 Ensuring main.tf is the simple version..."
if [ -f "old_main.tf" ] && [ -f "main.tf" ]; then
    # Check if current main.tf is complex
    complex_indicators=$(grep -c "ai_video\|audio_bucket\|websocket" main.tf || echo "0")
    if [ "$complex_indicators" -gt "0" ]; then
        echo "⚠️  Current main.tf appears to be complex ($complex_indicators complex resources)"
        echo "🔄 Restoring simple main.tf from git..."
        git checkout HEAD -- main.tf || {
            echo "❌ Failed to restore simple main.tf from git"
            echo "💡 You may need to manually ensure main.tf contains only simple resources"
            read -p "Continue anyway? (y/n): " continue_anyway
            if [ "$continue_anyway" != "y" ]; then
                exit 1
            fi
        }
    fi
fi

# Phase 4: Import Critical Resources
echo ""
echo "📥 Phase 4: Import Critical Resources"
echo "===================================="

echo "🔄 Importing critical resources to main-simple workspace..."

import_status=0

# Import Cognito User Pool
if [ -n "$USER_POOL_ID" ]; then
    echo "📥 Importing Cognito User Pool..."
    if terraform import aws_cognito_user_pool.video_app_users "$USER_POOL_ID"; then
        echo "✅ Cognito User Pool imported"
    else
        echo "❌ Failed to import Cognito User Pool"
        import_status=1
    fi
fi

# Import S3 Bucket
if [ -n "$BUCKET_NAME" ]; then
    echo "📥 Importing S3 Video Bucket..."
    if terraform import aws_s3_bucket.video_bucket "$BUCKET_NAME"; then
        echo "✅ S3 Video Bucket imported"
    else
        echo "❌ Failed to import S3 Video Bucket" 
        import_status=1
    fi
fi

# Import DynamoDB Table
if [ -n "$TABLE_NAME" ]; then
    echo "📥 Importing DynamoDB Table..."
    if terraform import aws_dynamodb_table.video_metadata "$TABLE_NAME"; then
        echo "✅ DynamoDB Table imported"
    else
        echo "❌ Failed to import DynamoDB Table"
        import_status=1
    fi
fi

if [ $import_status -ne 0 ]; then
    echo ""
    echo "❌ Some imports failed. Please review and fix before continuing."
    echo "💡 You can re-run this script or import manually using:"
    echo "   terraform import aws_cognito_user_pool.video_app_users $USER_POOL_ID"
    echo "   terraform import aws_s3_bucket.video_bucket $BUCKET_NAME"
    echo "   terraform import aws_dynamodb_table.video_metadata $TABLE_NAME"
    exit 1
fi

# Test imported configuration
echo ""
echo "🧪 Testing imported configuration..."
terraform plan -out=import-test.plan

plan_changes=$(terraform show -no-color import-test.plan | grep -c "Plan:" || echo "0")
echo "Terraform plan shows $plan_changes change sets"

if [ "$plan_changes" -gt "10" ]; then
    echo "⚠️  Plan shows many changes ($plan_changes). This may indicate configuration mismatch."
    echo "💡 Review the plan carefully:"
    terraform show import-test.plan
    echo ""
    read -p "Continue despite many planned changes? (y/n): " continue_despite_changes
    if [ "$continue_despite_changes" != "y" ]; then
        echo "Migration paused. Review configuration and try again."
        exit 1
    fi
fi

echo "✅ Import phase complete!"

# Phase 5: Deploy Simple Configuration
echo ""
echo "🚀 Phase 5: Deploy Simple Configuration" 
echo "======================================="

echo "🔄 Applying simple configuration..."
read -p "Apply the simple configuration now? (y/n): " apply_simple
if [ "$apply_simple" = "y" ]; then
    terraform apply import-test.plan
    echo "✅ Simple configuration applied!"
else
    echo "⏸️  Apply skipped. You can apply later with: terraform apply import-test.plan"
fi

# Phase 6: Optional Cleanup
echo ""
echo "🧹 Phase 6: Cleanup Complex Resources (Optional)"
echo "================================================"

echo "⚠️  Now you can clean up the complex resources from the default workspace."
echo "💡 This is optional and can be done later."
echo ""

read -p "Clean up complex resources from default workspace now? (y/n): " cleanup_now
if [ "$cleanup_now" = "y" ]; then
    echo "🔄 Switching to default workspace for cleanup..."
    terraform workspace select default
    
    echo "🔍 Available cleanup targets:"
    echo "  - AI Video resources (aws_lambda_function.ai_video_processor, etc.)"
    echo "  - Audio resources (aws_s3_bucket.audio_bucket, etc.)"
    echo "  - WebSocket API (aws_apigatewayv2_api.websocket_api, etc.)"
    echo ""
    echo "💡 You can use targeted destroys like:"
    echo "   terraform destroy -target=aws_lambda_function.ai_video_processor"
    echo "   terraform destroy -target=aws_s3_bucket.audio_bucket"
    echo ""
    echo "⚠️  Be careful not to destroy critical resources!"
    
    read -p "Destroy AI video resources? (y/n): " destroy_ai
    if [ "$destroy_ai" = "y" ]; then
        terraform destroy -target=aws_lambda_function.ai_video_processor || echo "Resource not found or already destroyed"
        terraform destroy -target=aws_lambda_layer_version.ai_video_layer || echo "Resource not found or already destroyed"
    fi
    
    read -p "Destroy audio bucket? (y/n): " destroy_audio
    if [ "$destroy_audio" = "y" ]; then
        terraform destroy -target=aws_s3_bucket.audio_bucket || echo "Resource not found or already destroyed"
    fi
fi

# Final Summary
echo ""
echo "🎉 Migration Summary"
echo "==================="
echo "✅ Backed up default workspace state"
echo "✅ Extracted critical resource IDs" 
echo "✅ Imported critical resources to main-simple workspace"
echo "✅ Deployed simple configuration"

terraform workspace select main-simple
simple_resource_count=$(terraform state list | wc -l)

echo ""
echo "📊 Final State:"
echo "  main-simple workspace: $simple_resource_count resources"
echo "  Backup location: $backup_file"
echo "  Resource IDs: $ANALYSIS_DIR/critical-resource-ids.txt"

echo ""
echo "🚀 Next Steps:"
echo "1. Test your application to ensure core functionality works"
echo "2. Optionally clean up remaining complex resources from default workspace"
echo "3. Update your deployment scripts to use main-simple workspace"
echo "4. Consider setting main-simple as your default workspace"

echo ""
echo "✅ Migration complete!"
