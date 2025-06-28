#!/bin/bash
# Emergency backup and workspace setup script

set -e

echo "🔄 Starting Terraform State Management Setup..."

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo "❌ Error: main.tf not found. Please run from terraform directory."
    exit 1
fi

# Create backups directory
mkdir -p backups

# Backup current state
echo "📦 Backing up current state..."
BACKUP_FILE="backups/state-backup-$(date +%Y%m%d-%H%M%S).json"
terraform state pull > "$BACKUP_FILE"
echo "✅ State backed up to: $BACKUP_FILE"

# Show current state summary
echo "📊 Current deployed resources:"
echo "Total resources: $(terraform state list | wc -l)"
echo "AI Video features: $(terraform state list | grep -E "(ai_video|audio|transcription|websocket)" | wc -l)"
echo "Core features: $(terraform state list | grep -E "(video_bucket|dynamodb|cognito)" | wc -l)"

# Create workspaces
echo "🏗️  Setting up workspaces..."

# Create complex workspace and move current state there
if ! terraform workspace list | grep -q "complex-features"; then
    terraform workspace new complex-features
    echo "✅ Created 'complex-features' workspace"
else
    echo "ℹ️  'complex-features' workspace already exists"
fi

# Create simple workspace for main branch  
if ! terraform workspace list | grep -q "main-simple"; then
    terraform workspace new main-simple
    echo "✅ Created 'main-simple' workspace"
else
    echo "ℹ️  'main-simple' workspace already exists"
fi

# Switch to complex workspace (current state should go here)
terraform workspace select complex-features
echo "✅ Switched to 'complex-features' workspace"

# Backup old_main.tf if it exists
if [ -f "old_main.tf" ]; then
    cp old_main.tf "backups/old_main-$(date +%Y%m%d-%H%M%S).tf"
    echo "✅ Backed up old_main.tf"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Verify current state: terraform plan"
echo "2. Switch to simple workspace: terraform workspace select main-simple"
echo "3. Run: ./scripts/setup-simple-config.sh"
echo ""
echo "Current workspace: $(terraform workspace show)"
echo "Backup location: $BACKUP_FILE"
