# Terraform Workspace Management - MIGRATION COMPLETE ✅

## Current Status

**✅ MIGRATION SUCCESSFUL**: Complex configuration has been migrated to simple configuration.

**Current Production State**:

- **`main-simple` workspace**: 44 resources (ACTIVE - use for development)
- **`default` workspace**: 162 resources (LEGACY - can be cleaned up)

## Quick Start

### 1. Use Simple Configuration (Recommended)

```bash
$env:AWS_PROFILE = "AdministratorAccess-571960159088"
cd terraform
terraform workspace select main-simple
terraform plan    # Should show no changes
terraform apply   # If needed
```

### 2. Optional Cleanup (Legacy Resources)

```bash
# Review what legacy resources can be cleaned up
terraform workspace select default
./scripts/analyze-default-resources.sh

# Selectively destroy complex features (optional)
terraform destroy -target=aws_lambda_function.ai_video_processor
terraform destroy -target=aws_s3_bucket.audio_bucket
```

## ✅ Migration Results

| Metric              | Before            | After         | Change           |
| ------------------- | ----------------- | ------------- | ---------------- |
| **Total Resources** | 162               | 44            | -73%             |
| **Configuration**   | Complex           | Simple        | Simplified       |
| **Features**        | AI + Audio + Core | Core Only     | AI/Audio Removed |
| **Workspace**       | `default`         | `main-simple` | Migrated         |

### ✅ Preserved (Critical Data)

- User accounts (Cognito User Pool)
- Video files (S3 bucket)
- Video metadata (DynamoDB table)
- Core API functionality

### ✅ Removed (Complex Features)

- AI video generation
- Audio processing
- WebSocket real-time features
- Complex Lambda layers
- EventBridge automation

## Current Workspace Strategy

| Workspace          | Status        | Resources | Purpose             |
| ------------------ | ------------- | --------- | ------------------- |
| `main-simple`      | 🟢 **ACTIVE** | 44        | Current development |
| `default`          | 🟡 **LEGACY** | 162       | Can be cleaned up   |
| `complex-features` | ⚪ **EMPTY**  | 0         | Not used            |

## Resource Categories

### 🟢 Shared Resources (Both Configurations)

- S3 video bucket
- DynamoDB video metadata table
- Cognito user pools
- Basic video CRUD API
- IAM roles for core functionality

### 🔵 Complex-Only Resources

- S3 audio bucket
- AI video processing Lambda
- Transcription processor
- WebSocket API for real-time updates
- EventBridge rules
- AI video layer and secrets

## Commands Reference

### Workspace Management

```bash
# List workspaces
terraform workspace list

# Show current workspace
terraform workspace show

# Switch workspace
terraform workspace select <workspace-name>

# Create new workspace
terraform workspace new <workspace-name>
```

### State Management

```bash
# Backup state
terraform state pull > backup-$(date +%Y%m%d).json

# List resources
terraform state list

# Show specific resource
terraform state show <resource-name>

# Move resource between workspaces
terraform state mv <source> <destination>
```

### Safety Checks

```bash
# Always plan before apply
terraform plan

# Plan with specific var file
terraform plan -var-file="environments/main.tfvars"

# Apply with confirmation
terraform apply
```

## Current File Structure (Post-Migration)

```
terraform/
├── main.tf                                    # Simple configuration (active)
├── variables.tf                               # Updated with all required variables
├── terraform.tfvars                           # Configuration values
├── old_main.tf                               # Complex configuration backup
├── RESOURCE-TRANSITION-STRATEGY.md           # Migration strategy (completed)
├── scripts/
│   ├── analyze-default-resources.sh          # ✅ Analyze legacy resources
│   ├── migrate-default-to-simple.sh          # ✅ Migration (completed)
│   ├── manage-environments.sh                # ✅ Environment management
│   ├── switch-environment.sh                 # ✅ Workspace switcher
│   ├── simple-analyze.sh                     # ✅ Alternative analyzer
│   └── emergency-setup.sh                    # ⚠️  Emergency only
├── backups/                                  # State backups from migration
│   ├── default-workspace-pre-migration-*.json
│   └── default-workspace-export-*.json
└── analysis/                                 # Migration analysis files
    ├── critical-resource-ids.txt
    └── all-resources-default.txt
```

## Safety Guidelines (Post-Migration)

1. **Use main-simple for development**

   ```bash
   terraform workspace select main-simple
   ```

2. **Verify workspace before operations**

   ```bash
   echo "Workspace: $(terraform workspace show)"
   terraform state list | wc -l  # Should show ~44 resources
   ```

3. **Backup before major changes**
   ```bash
   terraform state pull > backup-$(date +%Y%m%d-%H%M%S).json
   ```

## Legacy Resource Cleanup (Optional)

The `default` workspace still contains 162 resources that can be cleaned up:

```bash
# Switch to legacy workspace
terraform workspace select default

# See what can be safely destroyed
./scripts/analyze-default-resources.sh

# Example cleanup commands (run individually)
terraform destroy -target=aws_lambda_function.ai_video_processor
terraform destroy -target=aws_s3_bucket.audio_bucket
terraform destroy -target=aws_lambda_layer_version.ai_video_layer

# Return to active workspace
terraform workspace select main-simple
```

## Team Workflow (Updated)

### Developer Checklist (Simplified)

For daily development:

1. Use main-simple workspace: `terraform workspace select main-simple`
2. Review plan: `terraform plan`
3. Apply if needed: `terraform apply`

### No More Branch Switching Complexity

Since migration is complete, you can focus on the simple configuration without complex workspace switching.

## Emergency Procedures (Updated)

If something goes wrong with main-simple:

1. Check backups: `ls backups/`
2. Find latest: `ls -la backups/default-workspace-pre-migration-*`
3. Can restore from default workspace if needed
4. All critical data is preserved in both workspaces

## Success Metrics ✅

Your migration achieved:

- **73% resource reduction** (162 → 44)
- **100% data preservation** (users, videos, metadata)
- **Eliminated complexity** (AI, audio, WebSocket features)
- **Working simple configuration** ready for production

## 📋 Script Guide - Updated for Post-Migration

### 🎯 **Primary Scripts** (Ready to Use)

**1. `analyze-default-resources.sh` - ANALYZE LEGACY RESOURCES**

- **Purpose**: Analyze the 162 legacy resources in `default` workspace
- **Usage**: `./scripts/analyze-default-resources.sh`
- **Output**: Categorizes resources as AI, audio, core, etc.
- **When to use**: To decide what legacy resources to clean up

**2. `migrate-default-to-simple.sh` - MIGRATION COMPLETE ✅**

- **Status**: ✅ **Already completed successfully**
- **Purpose**: Was used to migrate from complex → simple configuration
- **Result**: Created working `main-simple` workspace with 44 resources
- **Note**: No need to run again unless rolling back

### 🔧 **Utility Scripts**

**3. `manage-environments.sh` - ENVIRONMENT MANAGEMENT**

- **Purpose**: General workspace management and status checking
- **Usage**: `./scripts/manage-environments.sh status`
- **Features**: Lists workspaces, shows resource counts, backup state

**4. `switch-environment.sh` - WORKSPACE SWITCHER**

- **Purpose**: Switch between workspaces
- **Usage**: `./scripts/switch-environment.sh main-simple`
- **Note**: Mainly use `main-simple` for development now

### ⚠️ **Legacy/Obsolete Scripts**

**5. `setup-simple-config.sh` - OBSOLETE**

- **Status**: ❌ No longer needed (migration complete)

**6. `emergency-setup.sh` - EMERGENCY ONLY**

- **Purpose**: Emergency recovery procedures
- **When to use**: Only if something goes catastrophically wrong

**7. `simple-analyze.sh` - ALTERNATIVE ANALYZER**

- **Purpose**: Simpler version of resource analyzer
- **Usage**: Alternative to `analyze-default-resources.sh`

## 🚀 **Recommended Daily Workflow**

```bash
# Standard development workflow (post-migration)
cd terraform
terraform workspace select main-simple
terraform plan
terraform apply   # if needed
```

## 🧹 **Optional Cleanup of Legacy Resources**

```bash
# See what legacy resources exist
terraform workspace select default
./scripts/analyze-default-resources.sh

# Selectively destroy complex features (optional)
terraform destroy -target=aws_lambda_function.ai_video_processor
terraform destroy -target=aws_s3_bucket.audio_bucket
terraform destroy -target=aws_lambda_layer_version.ai_video_layer
```

## ✅ **Migration Success Verification**

Your migration was successful! Evidence:

1. **`main-simple` workspace**: 44 resources (vs 162 original)
2. **All critical data preserved**: Users, videos, metadata intact
3. **Complex features removed**: No more AI, audio, WebSocket complexity
4. **Working configuration**: `terraform plan` shows no changes needed

**You can now focus on `main-simple` workspace for all development.**
