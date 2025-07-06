# Branch-Specific Terraform Resource Management Plan

## Current Situation Analysis

### **Problem**:

- **Deployed State**: Complex configuration (AI video, audio, transcription, WebSocket)
- **Current Branch**: `main` (simple configuration)
- **Git Branch**: Contains simplified `main.tf`
- **Risk**: Terraform plan/apply on main branch would destroy complex resources

## 1. Current Deployed Resources (Complex Configuration)

### Core Resources (Keep in Both Branches)

```
✅ KEEP - Core Infrastructure:
- aws_s3_bucket.video_bucket
- aws_dynamodb_table.video_metadata
- aws_cognito_user_pool.video_app_users
- aws_cognito_user_pool_client.video_app_client
- aws_cognito_user_group.admin_group
- aws_cognito_user_group.user_group
- aws_api_gateway_rest_api.video_api
- aws_lambda_function.video_metadata_api
- aws_lambda_function.admin_api
- Basic video CRUD API endpoints
```

### Complex Features (Branch-Specific)

```
🔄 BRANCH-SPECIFIC - AI/Audio Features:
- aws_s3_bucket.audio_bucket (+ all related configs)
- aws_lambda_function.ai_video_processor
- aws_lambda_function.transcription_processor
- aws_lambda_function.websocket_handler
- aws_lambda_layer_version.ai_video_layer
- aws_apigatewayv2_api.websocket_api (+ all WebSocket resources)
- aws_cloudwatch_event_rule.transcribe_job_state_change
- aws_secretsmanager_secret.ai_video_secrets
- All AI video and audio API endpoints
```

### CI/CD Resources (Keep in Both)

```
✅ KEEP - CI/CD:
- aws_iam_openid_connect_provider.github
- aws_iam_role.github_actions
- local_file.frontend_deployment_script
```

## 2. Recommended Strategy: Terraform Workspaces + Conditional Resources

### Step 1: Setup Workspace Structure

aws sts get-caller-identity --profile AdministratorAccess-571960159088
$env:AWS_PROFILE = "AdministratorAccess-571960159088" OR for Git Bash
export AWS_PROFILE=AdministratorAccess-571960159088

```bash
# Create workspaces
terraform workspace new main-simple
terraform workspace new feature-complex

# Current state goes to complex workspace
terraform workspace select feature-complex
```

### Step 2: Create Branch-Aware Configuration

#### A. Main Configuration with Conditionals

```hcl
# variables.tf
variable "enable_ai_features" {
  description = "Enable AI video processing features"
  type        = bool
  default     = false
}

variable "branch_name" {
  description = "Git branch name for resource naming"
  type        = string
  default     = "main"
}
```

#### B. Conditional Resource Creation

```hcl
# AI Video Resources (only when enabled)
resource "aws_s3_bucket" "audio_bucket" {
  count  = var.enable_ai_features ? 1 : 0
  bucket = "${var.project_name}-audio-${var.environment}"
}

resource "aws_lambda_function" "ai_video_processor" {
  count = var.enable_ai_features ? 1 : 0
  # ... configuration
}
```

### Step 3: Environment-Specific tfvars

#### terraform/environments/main.tfvars

```hcl
enable_ai_features = false
branch_name = "main"
project_name = "easy-video-share"
environment = "main"
```

#### terraform/environments/complex.tfvars

```hcl
enable_ai_features = true
branch_name = "feature-ai-video"
project_name = "easy-video-share"
environment = "dev"
```

## 3. Migration Implementation Plan

### Phase 1: Backup Current State

```bash
# Backup current complex state
terraform state pull > backup-complex-state-$(date +%Y%m%d).json
```

### Phase 2: Setup Workspaces

```bash
# Create and move current state to complex workspace
terraform workspace new feature-complex
terraform workspace select feature-complex

# Create simple workspace for main branch
terraform workspace new main-simple
terraform workspace select main-simple
```

### Phase 3: Resource State Migration

```bash
# For shared resources, import them to simple workspace
terraform workspace select main-simple

# Import core resources that exist in both configurations
terraform import aws_s3_bucket.video_bucket existing-bucket-name
terraform import aws_dynamodb_table.video_metadata existing-table-name
terraform import aws_cognito_user_pool.video_app_users existing-pool-id
# ... continue for all shared resources
```

### Phase 4: Branch Switching Scripts

#### scripts/switch-to-main.sh

```bash
#!/bin/bash
echo "Switching to main branch configuration..."
git checkout main
cd terraform
terraform workspace select main-simple
terraform plan -var-file="environments/main.tfvars"
```

#### scripts/switch-to-complex.sh

```bash
#!/bin/bash
echo "Switching to complex branch configuration..."
git checkout feature/ai-video  # or appropriate branch
cd terraform
terraform workspace select feature-complex
terraform plan -var-file="environments/complex.tfvars"
```

## 4. Alternative Strategy: Separate Terraform Directories

### Directory Structure

```
terraform/
├── core/                    # Shared resources
│   ├── main.tf             # S3, DynamoDB, Cognito, basic API
│   ├── variables.tf
│   └── outputs.tf
├── environments/
│   ├── main/               # Simple configuration
│   │   ├── main.tf        # References core + minimal additions
│   │   └── terraform.tfvars
│   └── complex/            # Complex configuration
│       ├── main.tf        # References core + AI features
│       ├── ai-features.tf # AI video, audio, transcription
│       └── terraform.tfvars
└── modules/
    ├── ai-video/          # Reusable AI video module
    └── websocket/         # Reusable WebSocket module
```

## 5. Immediate Action Plan

### Option A: Quick Fix (Recommended for now)

```bash
# 1. Backup current state
terraform state pull > backup-$(date +%Y%m%d-%H%M).json

# 2. Create workspace for complex config
terraform workspace new complex-current
terraform workspace select complex-current

# 3. Copy old_main.tf to main.tf temporarily to match state
cp old_main.tf main.tf

# 4. Verify state matches
terraform plan  # Should show no changes

# 5. Create simple workspace
terraform workspace new main-simple
terraform workspace select main-simple

# 6. Reset main.tf to simple version (current main branch content)
git checkout main.tf

# 7. Plan simple config (will show what would be destroyed/created)
terraform plan
```

### Option B: Gradual Migration

```bash
# 1. Add conditionals to current configuration
# 2. Set enable_ai_features = true for current state
# 3. Gradually transition by changing variable values
# 4. Test both configurations work
```

## 6. Team Workflow

### Developer Workflow

```bash
# When switching branches
./scripts/switch-terraform-env.sh $(git branch --show-current)

# Before any terraform operations
echo "Current workspace: $(terraform workspace show)"
echo "Current branch: $(git branch --show-current)"
```

### Safety Checks

```bash
# Pre-apply safety script
#!/bin/bash
WORKSPACE=$(terraform workspace show)
BRANCH=$(git branch --show-current)

echo "Terraform Workspace: $WORKSPACE"
echo "Git Branch: $BRANCH"

if [[ "$WORKSPACE" == "main-simple" && "$BRANCH" != "main" ]]; then
    echo "❌ WARNING: Workspace/branch mismatch!"
    exit 1
fi

terraform plan
```

## 7. Rollback Plan

### If Migration Goes Wrong

```bash
# Restore from backup
terraform workspace select complex-current
terraform state push backup-YYYYMMDD-HHMM.json
terraform apply  # Restore to working state
```

## Next Steps

1. **Choose Strategy**: Workspaces (recommended) vs Separate Directories
2. **Test Migration**: Start with workspace creation and state backup
3. **Implement Gradually**: Don't rush - test each step
4. **Document Decisions**: Keep team informed of chosen approach
5. **Automate Switching**: Create scripts for seamless branch transitions

## Risk Mitigation

- ✅ Always backup state before major changes
- ✅ Use `terraform plan` extensively before `apply`
- ✅ Test in development environment first
- ✅ Keep old configurations until new approach is proven
- ✅ Document all steps for team knowledge sharing
