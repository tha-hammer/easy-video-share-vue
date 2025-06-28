#!/bin/bash
# Environment Management Utility
# Manage multiple Terraform environments and configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/environments.yaml"

echo "🎛️  Terraform Environment Manager"
echo ""

# Function to list all configured environments
list_environments() {
    echo "📋 Configured Environments:"
    echo ""
    
    if [ -f "$CONFIG_FILE" ] && command -v yq >/dev/null 2>&1; then
        while IFS= read -r line; do
            local env_name=$(echo "$line" | cut -d'|' -f1)
            local workspace=$(echo "$line" | cut -d'|' -f2)
            local config_type=$(echo "$line" | cut -d'|' -f3)
            local description=$(echo "$line" | cut -d'|' -f4)
            
            echo "🏷️  Environment: $env_name"
            echo "   Workspace: $workspace"
            echo "   Type: $config_type"
            echo "   Description: $description"
            
            # Check if workspace exists
            if terraform workspace list 2>/dev/null | grep -q "\\b$workspace\\b"; then
                echo "   Status: ✅ Workspace exists"
            else
                echo "   Status: ❌ Workspace missing"
            fi
            echo ""
        done < <(yq eval '.environments | to_entries | .[] | .key + "|" + .value.workspace + "|" + .value.config_type + "|" + .value.description' "$CONFIG_FILE" 2>/dev/null)
    else
        echo "⚠️  Configuration file not found or yq not installed"
        echo "Showing current Terraform workspaces:"
        terraform workspace list
    fi
}

# Function to create missing workspaces
create_missing_workspaces() {
    echo "🔧 Creating Missing Workspaces..."
    echo ""
    
    local created_count=0
    
    if [ -f "$CONFIG_FILE" ] && command -v yq >/dev/null 2>&1; then
        while IFS= read -r workspace; do
            if ! terraform workspace list 2>/dev/null | grep -q "\\b$workspace\\b"; then
                echo "🆕 Creating workspace: $workspace"
                terraform workspace new "$workspace" >/dev/null 2>&1
                echo "✅ Created workspace: $workspace"
                ((created_count++))
            else
                echo "✅ Workspace already exists: $workspace"
            fi
        done < <(yq eval '.environments | to_entries | .[].value.workspace' "$CONFIG_FILE" 2>/dev/null | sort -u)
    else
        echo "❌ Cannot read configuration file. Creating standard workspaces..."
        local standard_workspaces=("main-simple" "ai-video-features" "audio-processing" "development" "staging" "experimental")
        
        for workspace in "${standard_workspaces[@]}"; do
            if ! terraform workspace list 2>/dev/null | grep -q "\\b$workspace\\b"; then
                echo "🆕 Creating workspace: $workspace"
                terraform workspace new "$workspace" >/dev/null 2>&1
                echo "✅ Created workspace: $workspace"
                ((created_count++))
            fi
        done
    fi
    
    echo ""
    echo "📊 Summary: Created $created_count new workspaces"
}

# Function to show environment status
show_status() {
    local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    local current_workspace=$(terraform workspace show 2>/dev/null || echo "unknown")
    
    echo "📊 Current Status:"
    echo "   Git Branch: $current_branch"
    echo "   Terraform Workspace: $current_workspace"
    echo ""
    
    # Check resource counts in main.tf
    if [ -f "main.tf" ]; then
        local ai_count=$(grep -c "ai_video\|AI.*video" main.tf 2>/dev/null || echo "0")
        local audio_count=$(grep -c "audio_bucket\|transcription" main.tf 2>/dev/null || echo "0")
        local websocket_count=$(grep -c "websocket\|apigatewayv2" main.tf 2>/dev/null || echo "0")
        local total_resources=$(grep -c "^resource " main.tf 2>/dev/null || echo "0")
        
        echo "📁 Configuration Analysis (main.tf):"
        echo "   Total Resources: $total_resources"
        echo "   AI Video Resources: $ai_count"
        echo "   Audio Resources: $audio_count"
        echo "   WebSocket Resources: $websocket_count"
        echo ""
        
        # Determine configuration complexity
        local complexity="simple"
        if [ "$ai_count" -gt 0 ] || [ "$audio_count" -gt 0 ] || [ "$websocket_count" -gt 0 ]; then
            complexity="complex"
        fi
        echo "   Configuration Complexity: $complexity"
    else
        echo "❌ main.tf not found"
    fi
    
    echo ""
    
    # Check for state drift
    echo "🔍 Checking for state drift..."
    if terraform plan -detailed-exitcode >/dev/null 2>&1; then
        echo "✅ No changes needed - infrastructure matches configuration"
    else
        local exit_code=$?
        if [ $exit_code -eq 2 ]; then
            echo "⚠️  Changes detected - run 'terraform plan' to see details"
        else
            echo "❌ Error checking plan - run 'terraform plan' manually"
        fi
    fi
}

# Function to backup current state
backup_state() {
    local workspace=$(terraform workspace show)
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="./backups"
    
    mkdir -p "$backup_dir"
    
    echo "💾 Backing up state for workspace: $workspace"
    
    if terraform state pull > "$backup_dir/terraform_${workspace}_${timestamp}.tfstate"; then
        echo "✅ State backed up to: $backup_dir/terraform_${workspace}_${timestamp}.tfstate"
    else
        echo "❌ Failed to backup state"
        return 1
    fi
}

# Function to cleanup unused workspaces
cleanup_workspaces() {
    echo "🧹 Cleanup Unused Workspaces"
    echo ""
    echo "⚠️  This will show workspaces that appear to be empty or unused."
    echo "You should manually verify before deleting any workspace."
    echo ""
    
    local current_workspace=$(terraform workspace show)
    
    while IFS= read -r workspace; do
        if [ "$workspace" != "$current_workspace" ] && [ "$workspace" != "default" ]; then
            echo "Checking workspace: $workspace"
            terraform workspace select "$workspace" >/dev/null 2>&1
            
            # Check if workspace has any resources
            local resource_count=$(terraform state list 2>/dev/null | wc -l)
            
            if [ "$resource_count" -eq 0 ]; then
                echo "  📊 $workspace: Empty ($resource_count resources)"
                echo "  🗑️  Consider deleting with: terraform workspace delete $workspace"
            else
                echo "  📊 $workspace: $resource_count resources"
            fi
        fi
    done < <(terraform workspace list | grep -v "^*" | sed 's/^ *//')
    
    # Return to original workspace
    terraform workspace select "$current_workspace" >/dev/null 2>&1
    echo ""
    echo "✅ Returned to workspace: $current_workspace"
}

# Function to show cost estimates
show_cost_info() {
    echo "💰 Cost Information"
    echo ""
    
    if [ -f "$CONFIG_FILE" ] && command -v yq >/dev/null 2>&1; then
        echo "Cost tiers by workspace:"
        while IFS= read -r line; do
            local workspace=$(echo "$line" | cut -d'|' -f1)
            local cost_tier=$(echo "$line" | cut -d'|' -f2)
            
            case "$cost_tier" in
                "low") cost_icon="💚" ;;
                "medium") cost_icon="💛" ;;
                "high") cost_icon="❤️" ;;
                *) cost_icon="❓" ;;
            esac
            
            echo "  $cost_icon $workspace: $cost_tier cost"
        done < <(yq eval '.workspaces | to_entries | .[] | .key + "|" + .value.cost_tier' "$CONFIG_FILE" 2>/dev/null)
    else
        echo "⚠️  Cost information requires configuration file and yq"
    fi
    
    echo ""
    echo "💡 Tip: Use 'terraform destroy' to clean up unused expensive resources"
}

# Main menu
case "${1:-menu}" in
    "list"|"ls")
        list_environments
        ;;
    "status"|"info")
        show_status
        ;;
    "create-workspaces"|"setup")
        create_missing_workspaces
        ;;
    "backup")
        backup_state
        ;;
    "cleanup")
        cleanup_workspaces
        ;;
    "cost")
        show_cost_info
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  list, ls           - List all configured environments"
        echo "  status, info       - Show current environment status"
        echo "  setup              - Create missing workspaces"
        echo "  backup             - Backup current workspace state"
        echo "  cleanup            - Show unused workspaces"
        echo "  cost               - Show cost information"
        echo "  help               - Show this help"
        echo ""
        ;;
    "menu"|*)
        echo "What would you like to do?"
        echo ""
        echo "1) List all environments"
        echo "2) Show current status"
        echo "3) Create missing workspaces"
        echo "4) Backup current state"
        echo "5) Check for unused workspaces"
        echo "6) Show cost information"
        echo "7) Exit"
        echo ""
        read -p "Choose option (1-7): " choice
        
        case $choice in
            1) list_environments ;;
            2) show_status ;;
            3) create_missing_workspaces ;;
            4) backup_state ;;
            5) cleanup_workspaces ;;
            6) show_cost_info ;;
            7) echo "👋 Goodbye!"; exit 0 ;;
            *) echo "❌ Invalid choice" ;;
        esac
        ;;
esac

echo ""
echo "✅ Environment management complete!"
