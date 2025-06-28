# Resource Transition Strategy: Complex → Simple

## Current Situation Analysis - CORRECTED

**ACTUAL Current Cloud State**: 162 resources deployed in **`default` workspace**
**Target State**: Simple core functionality (main-simple workspace)
**Empty Workspaces**: `complex-features` and `main-simple` are both empty
**Challenge**: Move resources from `default` → `main-simple` (keep critical) and destroy non-essential

## 🚨 QUICK REFERENCE - Corrected Situation

**The Real State**:

- ✅ **162 resources** are in `default` workspace (your current production)
- ❌ `complex-features` workspace is **empty** (created by emergency script)
- ❌ `main-simple` workspace is **empty** (target for simple config)

**Next Actions**:

1. **Analyze first**: `./scripts/analyze-default-resources.sh`
2. **Backup everything**: `terraform workspace select default && terraform state pull > backups/backup-$(date +%Y%m%d).json`
3. **Migrate safely**: `./scripts/migrate-default-to-simple.sh`

**Critical Resources to Preserve** (contain your data):

- `aws_cognito_user_pool.video_app_users` (all user accounts)
- `aws_s3_bucket.video_bucket` (all videos)
- `aws_dynamodb_table.video_metadata` (all video metadata)

**Safe to Destroy** (AI features you want to remove):

- `aws_lambda_function.ai_video_processor`
- `aws_s3_bucket.audio_bucket`
- `aws_lambda_function.transcription_processor`
- `aws_apigatewayv2_api.websocket_api`
- All `ai_video_*` and `audio_*` resources

## ⚠️ CRITICAL DISCOVERY

The resources are NOT in `complex-features` workspace as initially thought. They are in the `default` workspace. This means:

1. **Default workspace** = Your current production state (162 resources)
2. **Complex-features workspace** = Empty (created by emergency script)
3. **Main-simple workspace** = Empty (target for simple config)

## New Migration Strategy

**Source**: `default` workspace (162 resources)
**Target**: `main-simple` workspace (simple config)
**Method**: State move + selective destroy

## Resource Categories & Decisions

### 🟢 KEEP & IMPORT (Core Business Critical)

_These resources are essential and should be preserved_

| Resource Type                                   | Count | Reason                                     | Action                |
| ----------------------------------------------- | ----- | ------------------------------------------ | --------------------- |
| `aws_cognito_user_pool.video_app_users`         | 1     | **CRITICAL** - Contains all user accounts  | Import to main-simple |
| `aws_cognito_user_group.admin_group`            | 1     | **CRITICAL** - User management             | Import to main-simple |
| `aws_cognito_user_group.user_group`             | 1     | **CRITICAL** - User management             | Import to main-simple |
| `aws_cognito_user_pool_client.video_app_client` | 1     | **CRITICAL** - Frontend authentication     | Import to main-simple |
| `aws_s3_bucket.video_bucket`                    | 1     | **CRITICAL** - Contains all videos         | Import to main-simple |
| `aws_s3_bucket_*` (video bucket config)         | ~6    | **IMPORTANT** - Video bucket configuration | Import to main-simple |
| `aws_dynamodb_table.video_metadata`             | 1     | **CRITICAL** - All video metadata          | Import to main-simple |
| `aws_iam_role.lambda_execution_role`            | 1     | **NEEDED** - Core Lambda permissions       | Import to main-simple |

**Total to Import: ~12 resources**

### 🔴 DESTROY (AI/Complex Features Only)

_These can be safely removed for simple configuration_

| Resource Category     | Estimated Count | Examples                                                                            | Impact         |
| --------------------- | --------------- | ----------------------------------------------------------------------------------- | -------------- |
| AI Video Processing   | 15              | `aws_lambda_function.ai_video_processor`, `aws_lambda_layer_version.ai_video_layer` | Safe to remove |
| Audio Processing      | 10              | `aws_s3_bucket.audio_bucket`, audio-related API endpoints                           | Safe to remove |
| Transcription         | 8               | `aws_lambda_function.transcription_processor`, EventBridge rules                    | Safe to remove |
| WebSocket API         | 12              | `aws_apigatewayv2_api.websocket_api`, WebSocket routes                              | Safe to remove |
| Complex API Endpoints | 25              | AI video endpoints, audio endpoints                                                 | Safe to remove |
| Secrets Manager       | 2               | `aws_secretsmanager_secret.ai_video_secrets`                                        | Safe to remove |

**Total to Destroy: ~72 resources**

### 🔄 RECREATE (Replace Complex with Simple)

_These exist but need simpler versions_

| Resource Type            | Current             | Simple Version Needed            | Reason                       |
| ------------------------ | ------------------- | -------------------------------- | ---------------------------- |
| API Gateway Methods      | 30+ complex         | 6 simple (videos CRUD + OPTIONS) | Simpler API surface          |
| API Gateway Integrations | 25+                 | 6                                | Match simple methods         |
| Lambda Functions         | 5 complex           | 2 simple                         | Remove AI/audio features     |
| IAM Policies             | Complex permissions | Basic permissions                | Principle of least privilege |

**Total to Recreate: ~66 resources**

### 🔍 DECISION MATRIX

Use this matrix to decide on any unclear resources:

| Criteria                         | Keep/Import | Destroy | Recreate |
| -------------------------------- | ----------- | ------- | -------- |
| Contains user data?              | ✅          | ❌      | ❌       |
| Required for core video sharing? | ✅          | ❌      | 🤔       |
| AI/ML specific?                  | ❌          | ✅      | ❌       |
| Audio processing specific?       | ❌          | ✅      | ❌       |
| Complex permissions?             | ❌          | ❌      | ✅       |
| Simple equivalent needed?        | ❌          | ❌      | ✅       |

## Migration Execution Plan - CORRECTED

### Phase 1: Backup & Preparation (CRITICAL)

```bash
# 1. Backup everything from DEFAULT workspace
cd terraform
terraform workspace select default
terraform state pull > backups/pre-migration-default-$(date +%Y%m%d-%H%M%S).json

# 2. Export critical data identifiers
terraform show -json > backups/default-state-$(date +%Y%m%d-%H%M%S).json

# 3. Document current resource IDs for critical resources
terraform state list | grep -E "(cognito|dynamodb|s3_bucket\.video)" > backups/critical-resource-ids.txt

# 4. List all resources for analysis
terraform state list > backups/all-current-resources.txt
```

### Phase 2: Analysis and Resource Categorization

```bash
# Switch to default workspace to analyze what we have
terraform workspace select default

# Get detailed info about critical resources
terraform state show aws_cognito_user_pool.video_app_users
terraform state show aws_s3_bucket.video_bucket
terraform state show aws_dynamodb_table.video_metadata
```

### Phase 3: Import Critical Resources to Simple Workspace

```bash
# Switch to target simple workspace
terraform workspace select main-simple

# Ensure main.tf is the SIMPLE version (from main branch)
git checkout main -- main.tf

# Import critical resources one by one (get actual IDs from Phase 2)
# Example commands (replace with actual resource IDs):
terraform import aws_cognito_user_pool.video_app_users us-east-1_XXXXXXXXX
terraform import aws_s3_bucket.video_bucket your-actual-bucket-name
terraform import aws_dynamodb_table.video_metadata your-actual-table-name

# Test that imports worked
terraform plan  # Should show minimal changes
```

### Phase 4: Selective Destruction in Default Workspace

```bash
# Switch back to default workspace for cleanup
terraform workspace select default

# Destroy AI features first (least critical)
terraform destroy -target=aws_lambda_function.ai_video_processor
terraform destroy -target=aws_lambda_layer_version.ai_video_layer
terraform destroy -target=aws_secretsmanager_secret.ai_video_secrets

# Destroy audio features
terraform destroy -target=aws_s3_bucket.audio_bucket
terraform destroy -target=aws_lambda_function.transcription_processor

# Destroy WebSocket API
terraform destroy -target=aws_apigatewayv2_api.websocket_api

# Continue destroying non-essential resources...
```

### Phase 5: Deploy Simple Configuration

```bash
# Switch to simple workspace
terraform workspace select main-simple

# Apply simple configuration (should only create what's missing)
terraform plan   # Review carefully - should be minimal changes
terraform apply  # Only if plan looks correct
```

## Resource-by-Resource Decision Guide

### Immediate KEEP (Import to simple)

```bash
# These contain data or are business critical
aws_cognito_user_pool.video_app_users          # ALL USER ACCOUNTS
aws_cognito_user_group.admin_group              # User roles
aws_cognito_user_group.user_group               # User roles
aws_cognito_user_pool_client.video_app_client   # Frontend auth
aws_s3_bucket.video_bucket                      # ALL VIDEOS
aws_dynamodb_table.video_metadata               # ALL VIDEO METADATA
aws_s3_bucket_versioning.video_bucket_versioning
aws_s3_bucket_public_access_block.video_bucket_pab
aws_s3_bucket_policy.video_bucket_policy
aws_s3_bucket_website_configuration.video_bucket_website
aws_s3_bucket_cors_configuration.video_bucket_cors
aws_s3_bucket_server_side_encryption_configuration.video_bucket_encryption
```

### Immediate DESTROY (AI/Audio features)

```bash
# Audio bucket and all related resources
aws_s3_bucket.audio_bucket
aws_s3_bucket_*audio_bucket*

# AI Video processing
aws_lambda_function.ai_video_processor
aws_lambda_layer_version.ai_video_layer
aws_iam_role_policy.ai_video_lambda_policy

# Transcription
aws_lambda_function.transcription_processor
aws_iam_role.transcription_processor_role
aws_cloudwatch_event_rule.transcribe_job_state_change

# WebSocket
aws_apigatewayv2_api.websocket_api
aws_apigatewayv2_*

# Secrets
aws_secretsmanager_secret.ai_video_secrets
aws_secretsmanager_secret_version.ai_video_secrets
```

### REPLACE (Complex → Simple versions)

```bash
# API Gateway - keep the base API but simplify endpoints
aws_api_gateway_rest_api.video_api              # KEEP structure
aws_api_gateway_resource.videos_resource         # KEEP
aws_api_gateway_resource.admin_*                 # KEEP admin features

# Remove complex endpoints
aws_api_gateway_resource.ai_video_*              # DESTROY
aws_api_gateway_resource.audio_*                 # DESTROY

# Simplify Lambda functions
aws_lambda_function.video_metadata_api           # KEEP but simplify
aws_lambda_function.admin_api                    # KEEP
```

## Safety Commands

### Pre-Migration Verification

```bash
# Verify critical resources exist
aws cognito-idp describe-user-pool --user-pool-id $(terraform output cognito_user_pool_id)
aws s3 ls s3://$(terraform output video_bucket_name)
aws dynamodb describe-table --table-name $(terraform output dynamodb_table_name)
```

### Emergency Rollback

If something goes wrong:

```bash
# 1. Stop all operations immediately
# 2. Restore state to DEFAULT workspace (where original resources were)
terraform workspace select default
terraform state push backups/pre-migration-default-YYYYMMDD-HHMMSS.json

# 3. Verify restoration
terraform state list | wc -l  # Should show 162 resources
terraform plan  # Should show no changes

# 4. If simple workspace has issues, clean it up
terraform workspace select main-simple
terraform destroy  # Remove any partially created resources
```

## Risk Assessment

| Risk Level    | Impact              | Mitigation                                               |
| ------------- | ------------------- | -------------------------------------------------------- |
| 🔴 **HIGH**   | Lose user accounts  | Import Cognito resources first, verify before proceeding |
| 🔴 **HIGH**   | Lose video files    | Import S3 bucket, never destroy, verify access           |
| 🔴 **HIGH**   | Lose video metadata | Import DynamoDB table, backup data separately            |
| 🟡 **MEDIUM** | API downtime        | Deploy simple API before destroying complex              |
| 🟢 **LOW**    | Lose AI features    | Expected - these are being removed intentionally         |

## Success Criteria

After migration, you should have:

1. ✅ All users can still log in
2. ✅ All videos are still accessible
3. ✅ Video metadata is preserved
4. ✅ Basic video CRUD operations work
5. ✅ Admin functions work
6. ✅ No AI/audio features (as intended)
7. ✅ Reduced resource count (~15-20 resources instead of 162)

## Next Steps

1. **Review this plan carefully**
2. **Backup everything** (Phase 1)
3. **Start with importing critical resources** (Phase 2)
4. **Test each phase before proceeding**
5. **Have rollback plan ready**

Do you want me to create scripts to automate parts of this migration?
