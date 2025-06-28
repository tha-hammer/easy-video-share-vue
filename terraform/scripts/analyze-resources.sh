#!/bin/bash
# Resource Analysis Script - Analyze current complex state before migration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Resource Analysis: Current Complex State${NC}"
echo ""

# Function to count resources by category
analyze_resources() {
    local workspace="$1"
    terraform workspace select "$workspace"
    
    echo -e "${CYAN}=== Workspace: $workspace ===${NC}"
    
    # Total count
    local total=$(terraform state list | wc -l)
    echo -e "${BLUE}Total Resources: $total${NC}"
    echo ""
    
    # Critical resources (must keep)
    echo -e "${GREEN}🟢 CRITICAL RESOURCES (Must Keep/Import):${NC}"
    local critical_resources=(
        "cognito_user_pool"
        "cognito_user_group" 
        "cognito_user_pool_client"
        "s3_bucket.video_bucket"
        "dynamodb_table.video_metadata"
    )
    
    local critical_count=0
    for pattern in "${critical_resources[@]}"; do
        local matches=$(terraform state list | grep "$pattern" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "  ${GREEN}✅ $pattern: $matches resources${NC}"
            terraform state list | grep "$pattern" | sed 's/^/    - /'
            critical_count=$((critical_count + matches))
        fi
    done
    echo -e "${GREEN}Critical Resources Total: $critical_count${NC}"
    echo ""
    
    # AI Video features (safe to destroy)
    echo -e "${RED}🔴 AI VIDEO FEATURES (Safe to Destroy):${NC}"
    local ai_patterns=(
        "ai_video"
        "lambda_layer"
        "secretsmanager"
    )
    
    local ai_count=0
    for pattern in "${ai_patterns[@]}"; do
        local matches=$(terraform state list | grep "$pattern" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "  ${RED}❌ $pattern: $matches resources${NC}"
            terraform state list | grep "$pattern" | sed 's/^/    - /'
            ai_count=$((ai_count + matches))
        fi
    done
    echo -e "${RED}AI Features Total: $ai_count${NC}"
    echo ""
    
    # Audio features (safe to destroy)
    echo -e "${RED}🔴 AUDIO FEATURES (Safe to Destroy):${NC}"
    local audio_patterns=(
        "audio_bucket"
        "transcription"
        "transcribe"
    )
    
    local audio_count=0
    for pattern in "${audio_patterns[@]}"; do
        local matches=$(terraform state list | grep "$pattern" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "  ${RED}❌ $pattern: $matches resources${NC}"
            terraform state list | grep "$pattern" | sed 's/^/    - /'
            audio_count=$((audio_count + matches))
        fi
    done
    echo -e "${RED}Audio Features Total: $audio_count${NC}"
    echo ""
    
    # WebSocket features (safe to destroy)
    echo -e "${RED}🔴 WEBSOCKET FEATURES (Safe to Destroy):${NC}"
    local websocket_patterns=(
        "apigatewayv2"
        "websocket"
    )
    
    local websocket_count=0
    for pattern in "${websocket_patterns[@]}"; do
        local matches=$(terraform state list | grep "$pattern" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "  ${RED}❌ $pattern: $matches resources${NC}"
            terraform state list | grep "$pattern" | sed 's/^/    - /'
            websocket_count=$((websocket_count + matches))
        fi
    done
    echo -e "${RED}WebSocket Features Total: $websocket_count${NC}"
    echo ""
    
    # Core API Gateway (need to simplify)
    echo -e "${YELLOW}🟡 CORE API (Need to Simplify):${NC}"
    local api_patterns=(
        "api_gateway_rest_api"
        "api_gateway_resource"
        "api_gateway_method"
        "api_gateway_integration"
        "lambda_function"
        "iam_role"
    )
    
    local api_count=0
    for pattern in "${api_patterns[@]}"; do
        local matches=$(terraform state list | grep "$pattern" | grep -v -E "(ai_video|audio|websocket|transcription)" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "  ${YELLOW}🔧 $pattern: $matches resources${NC}"
            api_count=$((api_count + matches))
        fi
    done
    echo -e "${YELLOW}Core API Resources Total: $api_count${NC}"
    echo ""
    
    # Summary
    echo -e "${CYAN}=== MIGRATION SUMMARY ===${NC}"
    echo -e "${GREEN}Resources to Import: $critical_count${NC}"
    echo -e "${RED}Resources to Destroy: $((ai_count + audio_count + websocket_count))${NC}"
    echo -e "${YELLOW}Resources to Recreate (simplified): $api_count${NC}"
    echo -e "${BLUE}Total Resources: $total${NC}"
    echo ""
    
    local remaining=$((critical_count + api_count / 2))  # Estimate simplified API resources
    echo -e "${GREEN}Estimated Simple State Resources: ~$remaining${NC}"
    echo -e "${RED}Resources to be Removed: ~$((total - remaining))${NC}"
    echo ""
}

# Function to show critical resource details
show_critical_details() {
    echo -e "${BLUE}🔍 Critical Resource Details${NC}"
    terraform workspace select complex-features
    
    # Show resource IDs for import
    echo -e "${CYAN}Resource IDs needed for import:${NC}"
    
    if terraform state list | grep -q "aws_cognito_user_pool.video_app_users"; then
        local pool_id=$(terraform state show aws_cognito_user_pool.video_app_users | grep "id " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo -e "  ${GREEN}Cognito Pool ID: $pool_id${NC}"
    fi
    
    if terraform state list | grep -q "aws_s3_bucket.video_bucket"; then
        local bucket_name=$(terraform state show aws_s3_bucket.video_bucket | grep "bucket " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo -e "  ${GREEN}S3 Bucket Name: $bucket_name${NC}"
    fi
    
    if terraform state list | grep -q "aws_dynamodb_table.video_metadata"; then
        local table_name=$(terraform state show aws_dynamodb_table.video_metadata | grep "name " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo -e "  ${GREEN}DynamoDB Table: $table_name${NC}"
    fi
    echo ""
}

# Function to generate migration commands
generate_commands() {
    echo -e "${BLUE}📋 Generated Migration Commands${NC}"
    echo ""
    
    echo -e "${CYAN}# 1. Backup current state${NC}"
    echo "terraform workspace select complex-features"
    echo "terraform state pull > backups/complex-pre-migration-\$(date +%Y%m%d-%H%M%S).json"
    echo ""
    
    echo -e "${CYAN}# 2. Import critical resources to main-simple${NC}"
    if terraform state list | grep -q "aws_cognito_user_pool.video_app_users"; then
        local pool_id=$(terraform state show aws_cognito_user_pool.video_app_users | grep "id " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo "terraform workspace select main-simple"
        echo "terraform import aws_cognito_user_pool.video_app_users '$pool_id'"
    fi
    
    if terraform state list | grep -q "aws_s3_bucket.video_bucket"; then
        local bucket_name=$(terraform state show aws_s3_bucket.video_bucket | grep "bucket " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo "terraform import aws_s3_bucket.video_bucket '$bucket_name'"
    fi
    
    if terraform state list | grep -q "aws_dynamodb_table.video_metadata"; then
        local table_name=$(terraform state show aws_dynamodb_table.video_metadata | grep "name " | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')
        echo "terraform import aws_dynamodb_table.video_metadata '$table_name'"
    fi
    echo ""
    
    echo -e "${CYAN}# 3. Destroy AI features (run from complex-features workspace)${NC}"
    echo "terraform workspace select complex-features"
    terraform state list | grep -E "(ai_video|lambda_layer|secretsmanager)" | while read resource; do
        echo "terraform destroy -target='$resource' -auto-approve"
    done
    echo ""
    
    echo -e "${CYAN}# 4. Deploy simple configuration${NC}"
    echo "terraform workspace select main-simple"
    echo "terraform plan"
    echo "terraform apply"
    echo ""
}

# Function to show risks and warnings
show_risks() {
    echo -e "${RED}⚠️  MIGRATION RISKS AND WARNINGS${NC}"
    echo ""
    
    echo -e "${RED}🔴 HIGH RISK:${NC}"
    echo "  - User account data (Cognito User Pool)"
    echo "  - Video files (S3 bucket)"
    echo "  - Video metadata (DynamoDB table)"
    echo ""
    
    echo -e "${YELLOW}🟡 MEDIUM RISK:${NC}"
    echo "  - API downtime during transition"
    echo "  - Lambda function changes"
    echo "  - IAM permission changes"
    echo ""
    
    echo -e "${GREEN}🟢 LOW RISK:${NC}"
    echo "  - AI video features (intentionally removing)"
    echo "  - Audio processing (intentionally removing)"
    echo "  - WebSocket features (intentionally removing)"
    echo ""
    
    echo -e "${BLUE}💡 MITIGATION STRATEGIES:${NC}"
    echo "  1. Backup everything before starting"
    echo "  2. Import critical resources first"
    echo "  3. Test each phase before proceeding"
    echo "  4. Keep complex workspace as backup"
    echo "  5. Have rollback plan ready"
    echo ""
}

# Main execution
main() {
    # Check prerequisites
    if ! command -v terraform >/dev/null 2>&1; then
        echo -e "${RED}❌ Terraform not found${NC}"
        exit 1
    fi
    
    # Analyze both workspaces
    if terraform workspace list | grep -q "complex-features"; then
        analyze_resources "complex-features"
    else
        echo -e "${RED}❌ complex-features workspace not found${NC}"
    fi
    
    if terraform workspace list | grep -q "main-simple"; then
        analyze_resources "main-simple"
    else
        echo -e "${YELLOW}⚠️  main-simple workspace not found (will be populated during migration)${NC}"
    fi
    
    # Show critical details
    show_critical_details
    
    # Show risks
    show_risks
    
    # Generate commands
    generate_commands
    
    echo -e "${GREEN}✅ Analysis complete!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Review the analysis above"
    echo "2. Run: ./scripts/migrate-resources.sh"
    echo "3. Or run phases individually with backup-only, import-only, etc."
}

# Handle arguments
case "${1:-}" in
    "critical-only")
        show_critical_details
        ;;
    "risks-only")
        show_risks
        ;;
    "commands-only")
        generate_commands
        ;;
    *)
        main
        ;;
esac
