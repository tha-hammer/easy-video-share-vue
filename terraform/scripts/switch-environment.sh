#!/bin/bash
# Smart branch and workspace switcher

set -e

# Get current git branch
CURRENT_BRANCH=$(git branch --show-current)
CURRENT_WORKSPACE=$(terraform workspace show)

echo "🔄 Smart Terraform Environment Switcher"
echo "Current Git Branch: $CURRENT_BRANCH"
echo "Current Terraform Workspace: $CURRENT_WORKSPACE"
echo ""

# Define workspace mapping
case "$CURRENT_BRANCH" in
    "main")
        TARGET_WORKSPACE="main-simple"
        CONFIG_TYPE="Simple"
        ;;
    "feature/ai-video"|"complex"|"ai-features")
        TARGET_WORKSPACE="complex-features"
        CONFIG_TYPE="Complex (AI Features)"
        ;;
    *)
        echo "⚠️  Unknown branch pattern: $CURRENT_BRANCH"
        echo "Available workspaces:"
        terraform workspace list
        echo ""
        echo "Please choose a workspace:"
        echo "1) main-simple (core video sharing)"
        echo "2) complex-features (AI video processing)"
        echo "3) Stay in current workspace"
        read -p "Choose option (1-3): " choice
        
        case $choice in
            1) TARGET_WORKSPACE="main-simple"; CONFIG_TYPE="Simple" ;;
            2) TARGET_WORKSPACE="complex-features"; CONFIG_TYPE="Complex" ;;
            3) 
                echo "Staying in current workspace: $CURRENT_WORKSPACE"
                terraform plan
                exit 0
                ;;
            *) echo "Invalid choice"; exit 1 ;;
        esac
        ;;
esac

# Check if target workspace exists
if ! terraform workspace list | grep -q "$TARGET_WORKSPACE"; then
    echo "❌ Error: Workspace '$TARGET_WORKSPACE' does not exist!"
    echo "Available workspaces:"
    terraform workspace list
    echo ""
    echo "Run ./scripts/emergency-setup.sh first to create workspaces"
    exit 1
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

# Verify configuration matches workspace
echo ""
echo "🔍 Verifying configuration..."

# Check for AI resources in main.tf
AI_RESOURCES=$(grep -c "ai_video\|audio_bucket\|transcription\|websocket" main.tf || echo "0")

case "$TARGET_WORKSPACE" in
    "main-simple")
        if [ "$AI_RESOURCES" -gt "0" ]; then
            echo "⚠️  WARNING: main.tf contains AI resources but you're in simple workspace!"
            echo "This could cause unexpected behavior."
            echo ""
            echo "Options:"
            echo "1) Switch to complex workspace"
            echo "2) Replace main.tf with simple version from git"
            echo "3) Continue anyway (not recommended)"
            read -p "Choose option (1-3): " fix_choice
            
            case $fix_choice in
                1) 
                    terraform workspace select complex-features
                    echo "✅ Switched to complex workspace to match configuration"
                    ;;
                2)
                    git checkout HEAD -- main.tf
                    echo "✅ Restored simple main.tf from git"
                    ;;
                3)
                    echo "⚠️  Continuing with mismatched configuration..."
                    ;;
            esac
        else
            echo "✅ Configuration matches workspace (simple)"
        fi
        ;;
    "complex-features")
        if [ "$AI_RESOURCES" -eq "0" ]; then
            echo "⚠️  WARNING: main.tf is simple but you're in complex workspace!"
            echo "You may need to restore the complex configuration."
            echo ""
            echo "If you have old_main.tf, you can:"
            echo "  cp old_main.tf main.tf"
        else
            echo "✅ Configuration matches workspace (complex)"
        fi
        ;;
esac

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
