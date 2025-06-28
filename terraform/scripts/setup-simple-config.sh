#!/bin/bash
# Setup simple configuration for main branch

set -e

echo "🔧 Setting up simple configuration for main branch..."

# Ensure we're in main-simple workspace
CURRENT_WORKSPACE=$(terraform workspace show)
if [ "$CURRENT_WORKSPACE" != "main-simple" ]; then
    echo "Switching to main-simple workspace..."
    terraform workspace select main-simple
fi

# Check if main.tf is the simple version
echo "📋 Checking main.tf configuration..."

# Count AI-related resources in current main.tf
AI_RESOURCES=$(grep -c "ai_video\|audio_bucket\|transcription\|websocket" main.tf || echo "0")

if [ "$AI_RESOURCES" -gt "0" ]; then
    echo "⚠️  Current main.tf contains complex features ($AI_RESOURCES AI resources found)"
    echo "This suggests main.tf is still the complex version."
    echo ""
    echo "Options:"
    echo "1. Copy simple main.tf from git: git checkout HEAD -- main.tf"
    echo "2. Manually edit main.tf to remove AI features"
    echo "3. Use the current complex config and rename workspace"
    echo ""
    echo "What would you like to do?"
    echo "1) Copy simple main.tf from git"
    echo "2) Continue with complex config (rename workspace)"
    echo "3) Exit and handle manually"
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "Copying simple main.tf from git..."
            git checkout HEAD -- main.tf
            echo "✅ Restored simple main.tf"
            ;;
        2)
            echo "Renaming workspace to reflect complex config..."
            terraform workspace select default
            terraform workspace delete main-simple
            terraform workspace new complex-current
            terraform workspace select complex-current
            echo "✅ Renamed workspace to 'complex-current'"
            echo "You may want to run the emergency setup again for proper organization"
            exit 0
            ;;
        3)
            echo "Exiting for manual handling..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
fi

# Initialize terraform for this workspace
echo "🚀 Initializing terraform for simple configuration..."
terraform init

# Show what would be created/destroyed
echo "📊 Planning simple configuration..."
terraform plan -out=simple.plan

echo ""
echo "📋 Plan Summary:"
terraform show -json simple.plan | jq -r '
.resource_changes[] | 
select(.change.actions[] | contains("create") or contains("destroy")) |
"\(.change.actions[0]): \(.address)"
' 2>/dev/null || echo "Plan details available with: terraform show simple.plan"

echo ""
echo "⚠️  IMPORTANT: Review the plan carefully!"
echo ""
echo "The plan above shows what will happen if you apply the simple configuration."
echo "Resources marked as 'destroy' will be DELETED from AWS."
echo ""
echo "Safe to apply? This will:"
echo "✅ Keep: Core video sharing infrastructure"  
echo "❌ Remove: AI video processing, audio features, transcription, WebSocket"
echo ""
echo "Do you want to apply this configuration? (y/N)"
read -p "Apply simple config: " apply_choice

if [[ "$apply_choice" =~ ^[Yy]$ ]]; then
    echo "🚀 Applying simple configuration..."
    terraform apply simple.plan
    echo "✅ Simple configuration applied successfully!"
else
    echo "⏸️  Configuration not applied. Plan saved as simple.plan"
    echo "You can apply later with: terraform apply simple.plan"
fi

echo ""
echo "✅ Simple configuration setup complete!"
echo "Current workspace: $(terraform workspace show)"
echo "You can switch between configurations using:"
echo "  terraform workspace select complex-features  # For full features"
echo "  terraform workspace select main-simple       # For simple config"
