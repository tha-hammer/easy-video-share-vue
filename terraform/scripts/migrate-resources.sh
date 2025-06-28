#!/bin/bash
# Resource Migration Script: Complex → Simple
# This script helps migrate from complex (162 resources) to simple configuration

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/../backups"
DATE_STAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}🔄 Resource Migration: Complex → Simple${NC}"
echo -e "${YELLOW}⚠️  This will transition from 162 resources to ~20 resources${NC}"
echo ""

# Function to prompt for confirmation
confirm() {
    local message="$1"
    local default="${2:-n}"
    
    echo -e "${YELLOW}$message${NC}"
    read -p "Continue? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Operation cancelled${NC}"
        exit 1
    fi
}

# Function to backup state
backup_state() {
    local workspace="$1"
    local description="$2"
    
    echo -e "${BLUE}📦 Backing up $workspace workspace...${NC}"
    terraform workspace select "$workspace"
    terraform state pull > "$BACKUP_DIR/state-$workspace-$description-$DATE_STAMP.json"
    terraform state list > "$BACKUP_DIR/resources-$workspace-$description-$DATE_STAMP.txt"
    echo -e "${GREEN}✅ Backup saved: $BACKUP_DIR/state-$workspace-$description-$DATE_STAMP.json${NC}"
}

# Function to get resource identifier
get_resource_id() {
    local resource_type="$1"
    local resource_name="$2"
    
    terraform state show "$resource_name" 2>/dev/null | grep -E "^[[:space:]]*id[[:space:]]*=" | sed 's/.*= *"\([^"]*\)".*/\1/' | head -1
}

# Function to import critical resources
import_critical_resources() {
    echo -e "${BLUE}📥 Importing critical resources to main-simple workspace...${NC}"
    
    terraform workspace select main-simple
    
    # Get resource IDs from complex workspace first
    terraform workspace select complex-features
    
    local cognito_pool_id=$(get_resource_id "aws_cognito_user_pool" "aws_cognito_user_pool.video_app_users")
    local s3_bucket_name=$(get_resource_id "aws_s3_bucket" "aws_s3_bucket.video_bucket")
    local dynamodb_table_name=$(get_resource_id "aws_dynamodb_table" "aws_dynamodb_table.video_metadata")
    
    echo "Found resource IDs:"
    echo "  Cognito Pool: $cognito_pool_id"
    echo "  S3 Bucket: $s3_bucket_name"
    echo "  DynamoDB Table: $dynamodb_table_name"
    
    # Switch back to main-simple for imports
    terraform workspace select main-simple
    
    # Import critical resources
    if [ -n "$cognito_pool_id" ]; then
        echo -e "${BLUE}Importing Cognito User Pool...${NC}"
        terraform import aws_cognito_user_pool.video_app_users "$cognito_pool_id" || echo "Import failed - resource may already exist"
    fi
    
    if [ -n "$s3_bucket_name" ]; then
        echo -e "${BLUE}Importing S3 Video Bucket...${NC}"
        terraform import aws_s3_bucket.video_bucket "$s3_bucket_name" || echo "Import failed - resource may already exist"
    fi
    
    if [ -n "$dynamodb_table_name" ]; then
        echo -e "${BLUE}Importing DynamoDB Table...${NC}"
        terraform import aws_dynamodb_table.video_metadata "$dynamodb_table_name" || echo "Import failed - resource may already exist"
    fi
}

# Function to destroy AI/Audio features selectively
destroy_ai_features() {
    echo -e "${BLUE}🗑️  Destroying AI/Audio features from complex-features workspace...${NC}"
    terraform workspace select complex-features
    
    # AI Video features
    local ai_resources=(
        "aws_lambda_function.ai_video_processor"
        "aws_lambda_layer_version.ai_video_layer"
        "aws_iam_role_policy.ai_video_lambda_policy"
        "aws_secretsmanager_secret.ai_video_secrets"
        "aws_secretsmanager_secret_version.ai_video_secrets"
    )
    
    # Audio features
    local audio_resources=(
        "aws_s3_bucket.audio_bucket"
        "aws_lambda_function.transcription_processor"
        "aws_iam_role.transcription_processor_role"
        "aws_iam_role_policy.transcription_processor_policy"
        "aws_cloudwatch_event_rule.transcribe_job_state_change"
        "aws_cloudwatch_event_target.transcribe_lambda_target"
    )
    
    # WebSocket features
    local websocket_resources=(
        "aws_apigatewayv2_api.websocket_api"
        "aws_apigatewayv2_deployment.websocket_deployment"
        "aws_apigatewayv2_stage.websocket_stage"
        "aws_lambda_function.websocket_handler"
        "aws_dynamodb_table.websocket_connections"
    )
    
    # Destroy AI resources
    echo -e "${YELLOW}Destroying AI Video resources...${NC}"
    for resource in "${ai_resources[@]}"; do
        if terraform state list | grep -q "$resource"; then
            echo "Destroying $resource"
            terraform destroy -target="$resource" -auto-approve || echo "Failed to destroy $resource (may not exist)"
        fi
    done
    
    # Destroy Audio resources
    echo -e "${YELLOW}Destroying Audio processing resources...${NC}"
    for resource in "${audio_resources[@]}"; do
        if terraform state list | grep -q "$resource"; then
            echo "Destroying $resource"
            terraform destroy -target="$resource" -auto-approve || echo "Failed to destroy $resource (may not exist)"
        fi
    done
    
    # Destroy WebSocket resources
    echo -e "${YELLOW}Destroying WebSocket resources...${NC}"
    for resource in "${websocket_resources[@]}"; do
        if terraform state list | grep -q "$resource"; then
            echo "Destroying $resource"
            terraform destroy -target="$resource" -auto-approve || echo "Failed to destroy $resource (may not exist)"
        fi
    done
}

# Function to remove complex API endpoints
destroy_complex_api() {
    echo -e "${BLUE}🗑️  Destroying complex API endpoints...${NC}"
    terraform workspace select complex-features
    
    # AI Video API endpoints
    local ai_api_resources=(
        "aws_api_gateway_resource.ai_video_resource"
        "aws_api_gateway_resource.ai_video_id_resource"
        "aws_api_gateway_method.ai_video_get"
        "aws_api_gateway_method.ai_video_post"
        "aws_api_gateway_integration.ai_video_get_integration"
        "aws_api_gateway_integration.ai_video_post_integration"
    )
    
    # Audio API endpoints  
    local audio_api_resources=(
        "aws_api_gateway_resource.audio_resource"
        "aws_api_gateway_resource.audio_upload_url_resource"
        "aws_api_gateway_method.audio_get"
        "aws_api_gateway_method.audio_post"
        "aws_api_gateway_integration.audio_get_integration"
        "aws_api_gateway_integration.audio_post_integration"
    )
    
    echo -e "${YELLOW}Destroying AI API endpoints...${NC}"
    for resource in "${ai_api_resources[@]}"; do
        if terraform state list | grep -q "$resource"; then
            echo "Destroying $resource"
            terraform destroy -target="$resource" -auto-approve || echo "Failed to destroy $resource"
        fi
    done
    
    echo -e "${YELLOW}Destroying Audio API endpoints...${NC}"
    for resource in "${audio_api_resources[@]}"; do
        if terraform state list | grep -q "$resource"; then
            echo "Destroying $resource"
            terraform destroy -target="$resource" -auto-approve || echo "Failed to destroy $resource"
        fi
    done
}

# Function to deploy simple configuration
deploy_simple_config() {
    echo -e "${BLUE}🚀 Deploying simple configuration...${NC}"
    terraform workspace select main-simple
    
    # Ensure we're using the simple main.tf
    echo -e "${YELLOW}Verifying main.tf is the simple version...${NC}"
    if grep -q "ai_video" main.tf; then
        echo -e "${RED}❌ main.tf appears to contain complex configuration${NC}"
        echo "Please ensure main.tf contains only the simple configuration"
        exit 1
    fi
    
    # Plan and apply
    echo -e "${BLUE}Planning simple configuration...${NC}"
    terraform plan -out="simple-migration-$DATE_STAMP.tfplan"
    
    echo -e "${YELLOW}Review the plan above. Does it look correct?${NC}"
    confirm "Apply the simple configuration?"
    
    terraform apply "simple-migration-$DATE_STAMP.tfplan"
}

# Function to verify migration
verify_migration() {
    echo -e "${BLUE}🔍 Verifying migration...${NC}"
    
    terraform workspace select main-simple
    
    # Count resources
    local resource_count=$(terraform state list | wc -l)
    echo "Resources in main-simple: $resource_count"
    
    # Check critical resources exist
    echo -e "${BLUE}Checking critical resources...${NC}"
    
    if terraform state list | grep -q "aws_cognito_user_pool.video_app_users"; then
        echo -e "${GREEN}✅ Cognito User Pool exists${NC}"
    else
        echo -e "${RED}❌ Cognito User Pool missing${NC}"
    fi
    
    if terraform state list | grep -q "aws_s3_bucket.video_bucket"; then
        echo -e "${GREEN}✅ S3 Video Bucket exists${NC}"
    else
        echo -e "${RED}❌ S3 Video Bucket missing${NC}"
    fi
    
    if terraform state list | grep -q "aws_dynamodb_table.video_metadata"; then
        echo -e "${GREEN}✅ DynamoDB Table exists${NC}"
    else
        echo -e "${RED}❌ DynamoDB Table missing${NC}"
    fi
    
    # Check AI features are gone
    terraform workspace select complex-features
    local complex_count=$(terraform state list | wc -l)
    echo "Resources remaining in complex-features: $complex_count"
    
    if [ "$complex_count" -lt 50 ]; then
        echo -e "${GREEN}✅ Complex features successfully reduced${NC}"
    else
        echo -e "${YELLOW}⚠️  Many resources still in complex workspace${NC}"
    fi
}

# Main execution flow
main() {
    echo -e "${BLUE}Starting Resource Migration Process${NC}"
    echo ""
    
    # Check prerequisites
    if ! command -v terraform >/dev/null 2>&1; then
        echo -e "${RED}❌ Terraform not found${NC}"
        exit 1
    fi
    
    # Verify workspaces exist
    if ! terraform workspace list | grep -q "complex-features"; then
        echo -e "${RED}❌ complex-features workspace not found${NC}"
        exit 1
    fi
    
    if ! terraform workspace list | grep -q "main-simple"; then
        echo -e "${RED}❌ main-simple workspace not found${NC}"
        exit 1
    fi
    
    # Phase 1: Backup everything
    echo -e "${BLUE}=== Phase 1: Backup Current State ===${NC}"
    confirm "Backup current state of both workspaces?"
    backup_state "complex-features" "pre-migration"
    backup_state "main-simple" "pre-migration"
    
    # Phase 2: Import critical resources
    echo -e "${BLUE}=== Phase 2: Import Critical Resources ===${NC}"
    confirm "Import critical resources (Cognito, S3, DynamoDB) to main-simple?"
    import_critical_resources
    
    # Phase 3: Selective destruction
    echo -e "${BLUE}=== Phase 3: Destroy AI/Audio Features ===${NC}"
    confirm "Destroy AI video and audio processing features?"
    destroy_ai_features
    
    echo -e "${BLUE}=== Phase 3b: Destroy Complex API Endpoints ===${NC}"
    confirm "Destroy complex API endpoints?"
    destroy_complex_api
    
    # Phase 4: Deploy simple configuration
    echo -e "${BLUE}=== Phase 4: Deploy Simple Configuration ===${NC}"
    confirm "Deploy the simple configuration?"
    deploy_simple_config
    
    # Phase 5: Verification
    echo -e "${BLUE}=== Phase 5: Verification ===${NC}"
    verify_migration
    
    echo ""
    echo -e "${GREEN}🎉 Migration completed!${NC}"
    echo "Backups saved in: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Test your application with the simple configuration"
    echo "2. Verify users can log in and access videos"
    echo "3. Clean up remaining complex workspace resources if needed"
}

# Handle script arguments
case "${1:-}" in
    "backup-only")
        backup_state "complex-features" "manual"
        backup_state "main-simple" "manual"
        ;;
    "import-only")
        import_critical_resources
        ;;
    "destroy-only")
        destroy_ai_features
        destroy_complex_api
        ;;
    "verify-only")
        verify_migration
        ;;
    *)
        main
        ;;
esac
