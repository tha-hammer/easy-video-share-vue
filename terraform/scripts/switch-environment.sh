#!/bin/bash
# Adaptive Terraform Environment Switcher
# Supports unlimited environments via configuration file

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/environments.yaml"
CACHE_FILE="/tmp/terraform-env-cache.json"

# Get current git branch
CURRENT_BRANCH=$(git branch --show-current)
CURRENT_WORKSPACE=$(terraform workspace show)

echo "🔄 Adaptive Terraform Environment Switcher"
echo "Current Git Branch: $CURRENT_BRANCH"
echo "Current Terraform Workspace: $CURRENT_WORKSPACE"
echo ""

# Function to parse YAML (simple parser for our use case)
parse_yaml() {
    local yaml_file="$1"
    local key_path="$2"
    
    # Use yq if available, otherwise fallback to manual parsing
    if command -v yq >/dev/null 2>&1; then
        yq eval "$key_path" "$yaml_file" 2>/dev/null || echo ""
    else
        # Simple grep-based parsing for basic YAML
        grep -A 20 "^environments:" "$yaml_file" | grep -A 5 "  $CURRENT_BRANCH:" | grep "workspace:" | sed 's/.*workspace: *"\?\([^"]*\)"\?.*/\1/' | head -1
    fi
}

# Function to get environment config
get_environment_config() {
    local branch="$1"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "❌ Configuration file not found: $CONFIG_FILE"
        echo "Using fallback configuration..."
        return 1
    fi
    
    # Try exact branch match first
    local workspace=$(parse_yaml "$CONFIG_FILE" ".environments.$branch.workspace")
    local config_type=$(parse_yaml "$CONFIG_FILE" ".environments.$branch.config_type")
    local description=$(parse_yaml "$CONFIG_FILE" ".environments.$branch.description")
    
    if [ -n "$workspace" ] && [ "$workspace" != "null" ]; then
        echo "$workspace|$config_type|$description"
        return 0
    fi
    
    # Try pattern matching
    local patterns=("main" "feature/ai-*" "feature/audio*" "develop*" "staging*" "experimental/*" "hotfix/*")
    local environments=("main" "feature/ai-video" "feature/audio-only" "develop" "staging" "experimental/*" "main")
    
    for i in "${!patterns[@]}"; do
        local pattern="${patterns[$i]}"
        if [[ "$branch" == $pattern ]]; then
            local env="${environments[$i]}"
            workspace=$(parse_yaml "$CONFIG_FILE" ".environments.$env.workspace")
            config_type=$(parse_yaml "$CONFIG_FILE" ".environments.$env.config_type")
            description=$(parse_yaml "$CONFIG_FILE" ".environments.$env.description")
            
            if [ -n "$workspace" ] && [ "$workspace" != "null" ]; then
                echo "$workspace|$config_type|$description"
                return 0
            fi
        fi
    done
    
    return 1
}

# Function to show interactive environment selection
show_environment_menu() {
    echo "🎯 Available Environments:"
    echo ""
    
    local counter=1
    local workspaces=()
    local descriptions=()
    
    # Parse all available environments
    if [ -f "$CONFIG_FILE" ]; then
        # If we have yq, use it for better parsing
        if command -v yq >/dev/null 2>&1; then
            while IFS= read -r line; do
                local env_name=$(echo "$line" | cut -d'|' -f1)
                local workspace=$(echo "$line" | cut -d'|' -f2)
                local config_type=$(echo "$line" | cut -d'|' -f3)
                local description=$(echo "$line" | cut -d'|' -f4)
                
                workspaces+=("$workspace")
                descriptions+=("$config_type - $description")
                echo "$counter) $workspace"
                echo "   └─ $config_type - $description"
                echo ""
                ((counter++))
            done < <(yq eval '.environments | to_entries | .[] | .key + "|" + .value.workspace + "|" + .value.config_type + "|" + .value.description' "$CONFIG_FILE" 2>/dev/null | head -10)
        fi
    fi
    
    # Fallback menu if YAML parsing fails
    if [ ${#workspaces[@]} -eq 0 ]; then
        workspaces=("main-simple" "ai-video-features" "audio-processing" "development" "staging" "experimental")
        descriptions=("Simple Core - Basic video sharing" 
                     "AI Video Processing - Full AI pipeline" 
                     "Audio Processing - Audio transcription only"
                     "Development - All features enabled"
                     "Staging - Production-like environment"
                     "Experimental - Bleeding edge features")
        
        for i in "${!workspaces[@]}"; do
            echo "$((i+1))) ${workspaces[$i]}"
            echo "   └─ ${descriptions[$i]}"
            echo ""
        done
    fi
    
    echo "$counter) Stay in current workspace ($CURRENT_WORKSPACE)"
    echo ""
    
    read -p "Choose environment (1-$counter): " choice
    
    if [ "$choice" -eq "$counter" ]; then
        echo "Staying in current workspace: $CURRENT_WORKSPACE"
        return 1
    elif [ "$choice" -ge 1 ] && [ "$choice" -lt "$counter" ]; then
        local index=$((choice-1))
        TARGET_WORKSPACE="${workspaces[$index]}"
        CONFIG_TYPE="${descriptions[$index]}"
        return 0
    else
        echo "❌ Invalid choice"
        exit 1
    fi
}

# Get environment configuration
echo "🔍 Analyzing branch pattern..."
if config_result=$(get_environment_config "$CURRENT_BRANCH"); then
    IFS='|' read -r TARGET_WORKSPACE CONFIG_TYPE DESCRIPTION <<< "$config_result"
    echo "✅ Found configuration for branch '$CURRENT_BRANCH'"
    echo "   Workspace: $TARGET_WORKSPACE"
    echo "   Type: $CONFIG_TYPE"
    echo "   Description: $DESCRIPTION"
else
    echo "⚠️  No automatic configuration found for branch: $CURRENT_BRANCH"
    echo ""
    if ! show_environment_menu; then
        terraform plan
        exit 0
    fi
fi

echo ""

# Create workspace if it doesn't exist
if ! terraform workspace list | grep -q "\\b$TARGET_WORKSPACE\\b"; then
    echo "🆕 Creating new workspace: $TARGET_WORKSPACE"
    terraform workspace new "$TARGET_WORKSPACE"
    echo "✅ Created workspace: $TARGET_WORKSPACE"
fi

# Switch workspace if needed
if [ "$CURRENT_WORKSPACE" != "$TARGET_WORKSPACE" ]; then
    echo "🔄 Switching from '$CURRENT_WORKSPACE' to '$TARGET_WORKSPACE'..."
    terraform workspace select "$TARGET_WORKSPACE"
    echo "✅ Switched to workspace: $TARGET_WORKSPACE"
else
    echo "✅ Already in correct workspace: $TARGET_WORKSPACE"
fi

echo ""
echo "📋 Environment Info:"
echo "Configuration Type: $CONFIG_TYPE"
echo "Terraform Workspace: $(terraform workspace show)"
echo "Git Branch: $CURRENT_BRANCH"

# Enhanced configuration verification
echo ""
echo "🔍 Verifying configuration..."

# Function to check for feature resources
check_feature_resources() {
    local feature="$1"
    local count=0
    
    case "$feature" in
        "ai_video")
            count=$(grep -c "ai_video\|AI.*video" main.tf 2>/dev/null || echo "0")
            ;;
        "audio")
            count=$(grep -c "audio_bucket\|transcription" main.tf 2>/dev/null || echo "0")
            ;;
        "websocket")
            count=$(grep -c "websocket\|apigatewayv2" main.tf 2>/dev/null || echo "0")
            ;;
        "eventbridge")
            count=$(grep -c "cloudwatch_event\|eventbridge" main.tf 2>/dev/null || echo "0")
            ;;
        *)
            count=$(grep -c "$feature" main.tf 2>/dev/null || echo "0")
            ;;
    esac
    
    echo "$count"
}

# Get feature counts
AI_RESOURCES=$(check_feature_resources "ai_video")
AUDIO_RESOURCES=$(check_feature_resources "audio")
WEBSOCKET_RESOURCES=$(check_feature_resources "websocket")
EVENTBRIDGE_RESOURCES=$(check_feature_resources "eventbridge")

echo "Resource Analysis:"
echo "  AI Video Resources: $AI_RESOURCES"
echo "  Audio Resources: $AUDIO_RESOURCES"
echo "  WebSocket Resources: $WEBSOCKET_RESOURCES"
echo "  EventBridge Resources: $EVENTBRIDGE_RESOURCES"

# Smart configuration validation
TOTAL_COMPLEX_RESOURCES=$((AI_RESOURCES + AUDIO_RESOURCES + WEBSOCKET_RESOURCES + EVENTBRIDGE_RESOURCES))

# Determine expected complexity based on workspace
case "$TARGET_WORKSPACE" in
    "main-simple")
        EXPECTED_COMPLEXITY="simple"
        EXPECTED_COMPLEX_COUNT=0
        ;;
    "ai-video-features"|"development"|"staging")
        EXPECTED_COMPLEXITY="complex"
        EXPECTED_COMPLEX_COUNT=5  # Minimum expected complex resources
        ;;
    "audio-processing")
        EXPECTED_COMPLEXITY="audio-only"
        EXPECTED_COMPLEX_COUNT=2  # Audio + transcription
        ;;
    "experimental")
        EXPECTED_COMPLEXITY="any"
        EXPECTED_COMPLEX_COUNT=0  # No expectations
        ;;
    *)
        EXPECTED_COMPLEXITY="unknown"
        EXPECTED_COMPLEX_COUNT=0
        ;;
esac

# Configuration mismatch detection and resolution
if [ "$EXPECTED_COMPLEXITY" != "any" ] && [ "$EXPECTED_COMPLEXITY" != "unknown" ]; then
    if [ "$EXPECTED_COMPLEXITY" = "simple" ] && [ "$TOTAL_COMPLEX_RESOURCES" -gt 0 ]; then
        echo ""
        echo "⚠️  CONFIGURATION MISMATCH DETECTED!"
        echo "Workspace '$TARGET_WORKSPACE' expects simple configuration but main.tf has $TOTAL_COMPLEX_RESOURCES complex resources."
        echo ""
        echo "Resolution options:"
        echo "1) Switch to a complex workspace (ai-video-features, development)"
        echo "2) Restore simple main.tf from git (git checkout HEAD -- main.tf)"
        echo "3) Use old_main.tf as reference to switch to complex config"
        echo "4) Continue anyway (may cause terraform errors)"
        read -p "Choose option (1-4): " fix_choice
        
        case $fix_choice in
            1)
                echo "Available complex workspaces:"
                terraform workspace list | grep -E "(ai-video|development|staging|complex)" || echo "  No complex workspaces found"
                echo ""
                read -p "Enter workspace name: " new_workspace
                if terraform workspace list | grep -q "\\b$new_workspace\\b"; then
                    terraform workspace select "$new_workspace"
                    echo "✅ Switched to complex workspace: $new_workspace"
                else
                    echo "❌ Workspace not found: $new_workspace"
                fi
                ;;
            2)
                git checkout HEAD -- main.tf
                echo "✅ Restored simple main.tf from git"
                ;;
            3)
                if [ -f "old_main.tf" ]; then
                    echo "Available configurations:"
                    echo "  current main.tf: $TOTAL_COMPLEX_RESOURCES complex resources"
                    echo "  old_main.tf: $(check_feature_resources "ai_video" < old_main.tf) AI resources"
                    echo ""
                    read -p "Copy old_main.tf to main.tf? (y/n): " copy_choice
                    if [ "$copy_choice" = "y" ]; then
                        cp old_main.tf main.tf
                        echo "✅ Copied old_main.tf to main.tf"
                    fi
                else
                    echo "❌ old_main.tf not found"
                fi
                ;;
            4)
                echo "⚠️  Continuing with mismatched configuration..."
                ;;
        esac
        
    elif [ "$EXPECTED_COMPLEXITY" != "simple" ] && [ "$TOTAL_COMPLEX_RESOURCES" -lt "$EXPECTED_COMPLEX_COUNT" ]; then
        echo ""
        echo "⚠️  CONFIGURATION MISMATCH DETECTED!"
        echo "Workspace '$TARGET_WORKSPACE' expects complex configuration but main.tf only has $TOTAL_COMPLEX_RESOURCES complex resources."
        echo ""
        if [ -f "old_main.tf" ]; then
            OLD_COMPLEX_COUNT=$(grep -c "ai_video\|audio_bucket\|websocket" old_main.tf 2>/dev/null || echo "0")
            echo "Found old_main.tf with $OLD_COMPLEX_COUNT complex resources."
            echo ""
            read -p "Restore complex configuration from old_main.tf? (y/n): " restore_choice
            if [ "$restore_choice" = "y" ]; then
                cp old_main.tf main.tf
                echo "✅ Restored complex configuration"
            fi
        else
            echo "Consider switching to a simpler workspace or adding required resources."
        fi
    else
        echo "✅ Configuration matches workspace expectations"
    fi
fi

# Run terraform plan
echo ""
echo "🚀 Running terraform plan..."
terraform plan

echo ""
echo "✅ Environment switch complete!"
echo ""
echo "Summary:"
echo "  Git Branch: $CURRENT_BRANCH"
echo "  Terraform Workspace: $(terraform workspace show)"
echo "  Configuration Type: $CONFIG_TYPE"
echo "  AI Resources in main.tf: $AI_RESOURCES"
