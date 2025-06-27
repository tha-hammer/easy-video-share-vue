# CRITICAL FIX: CORS and Terraform Deployment Issues

## Issue Summary

The deployment was failing due to:

1. **Terraform Errors**: References to non-existent audio resources in main.tf
2. **CORS Errors**: Missing integration responses for AI video endpoints
3. **AWS Authentication Error**: Invalid access keys being used

## Root Cause

The `main.tf` API Gateway deployment section was referencing audio resources that only exist in `ai-video-extensions.tf`, causing Terraform planning to fail.

AWS CLI was configured with disabled access keys, but Terraform was still trying to use the old (now invalid) access keys.

## Fix Applied

### ✅ **1. Removed Invalid Resource References**

Removed these non-existent references from `main.tf` deployment:

```
- aws_api_gateway_integration.audio_post_integration
- aws_api_gateway_integration.audio_get_integration
- aws_api_gateway_integration.audio_options_integration
- aws_api_gateway_integration.audio_upload_url_post_integration
- aws_api_gateway_integration.audio_upload_url_options_integration
- aws_api_gateway_integration_response.audio_post_integration_response
- aws_api_gateway_integration_response.audio_get_integration_response
- aws_api_gateway_integration_response.audio_options_integration_response
- aws_api_gateway_integration_response.audio_upload_url_post_integration_response
- aws_api_gateway_integration_response.audio_upload_url_options_integration_response
```

### ✅ **2. Fixed Deployment Dependencies**

Updated deployment to only reference resources that exist in `main.tf`:

- Videos endpoints ✅
- Admin endpoints ✅
- Integration responses ✅
- Added note that audio/AI video resources are in ai-video-extensions.tf

### ✅ **3. Fixed AWS Authentication Error**

Removed old invalid access keys and set up AWS SSO or IAM role authentication.

## Expected Result

- ✅ Terraform plan/apply should now succeed
- ✅ API Gateway deployment will work correctly
- ✅ CORS headers should be properly set for all endpoints
- ✅ AI video generation should work without CORS errors
- ✅ AWS authentication errors should be resolved

## Next Steps

1. **Run deployment**: `./scripts/deploy-ai-video.sh`
2. **Test AI video generation** - CORS errors should be resolved
3. **Verify all endpoints** respond with proper CORS headers
4. **Ensure AWS authentication is working** by running `aws sts get-caller-identity`

## Note

The ai-video-extensions.tf file handles the AI video and audio endpoints with their own deployment dependencies. This separation is working correctly and doesn't need changes.

## 🚨 **ADDITIONAL ISSUE: AWS Authentication Error**

### Problem

After disabling access keys for security, Terraform is still trying to use the old (now invalid) access keys:

```
Error: InvalidClientTokenId: The security token included in the request is invalid.
```

### Root Cause

AWS CLI is configured with disabled access keys:

```
access_key     ****************GQR4 shared-credentials-file
secret_key     ****************CRbX shared-credentials-file
```

### ✅ **SOLUTION: Use PowerUserAccess Profile**

You have an AWS profile `PowerUserAccess-571960159088` with appropriate permissions. Let's use that instead of the disabled default credentials:

#### Step 1: Set AWS Profile for Terraform

```powershell
# Set the AWS profile environment variable
$env:AWS_PROFILE = "PowerUserAccess-571960159088"
```

#### Step 2: Verify Authentication Works

```powershell
aws sts get-caller-identity
```

#### Step 3: Run Terraform with the Profile

```powershell
# Now run terraform commands
cd terraform
terraform plan
terraform apply
```

#### Alternative: Set Profile in Provider (Optional)

You can also update the Terraform provider to always use this profile:

```hcl
provider "aws" {
  region  = var.aws_region
  profile = "PowerUserAccess-571960159088"
}
```

#### Make Profile Permanent (Optional)

Add to your PowerShell profile:

```powershell
# Add this to your PowerShell profile
$env:AWS_PROFILE = "PowerUserAccess-571960159088"
```

#### For Git Bash / Linux / macOS:

```bash
# Set the AWS profile environment variable
export AWS_PROFILE="PowerUserAccess-571960159088"

# Verify it's set
echo $AWS_PROFILE

# Then run terraform
cd terraform
terraform plan
terraform apply
```

#### Make Profile Permanent in Git Bash:

```bash
# Add to your ~/.bashrc or ~/.bash_profile
echo 'export AWS_PROFILE="PowerUserAccess-571960159088"' >> ~/.bashrc
source ~/.bashrc
```

## 🚨 **NEW ISSUE: IAM Permissions Error**

### Problem

The PowerUserAccess role doesn't have sufficient IAM permissions:

```
Error: AccessDenied: User is not authorized to perform: iam:GetUser on resource: user easy-video-share-app-user
Error: AccessDenied: User is not authorized to perform: iam:GetRole on resource: role easy-video-share-lambda-execution-role
```

### Root Cause

PowerUserAccess policy typically excludes IAM operations for security. The Terraform state is trying to read existing IAM resources.

### ✅ **SOLUTIONS (Choose One):**

#### Option 1: Use Administrator Profile (Recommended)

```bash
# Switch to a profile with full admin permissions
export AWS_PROFILE="video-app"  # or another admin profile
aws sts get-caller-identity
```

#### Option 2: Import Existing Resources to Skip Creation

```bash
# If resources already exist, import them to Terraform state
cd terraform
terraform import aws_iam_user.video_app_user easy-video-share-app-user
terraform import aws_iam_role.lambda_execution_role easy-video-share-lambda-execution-role
```

#### Option 3: Remove Legacy IAM User (Recommended for Security)

Since we're not using access keys anymore, we can remove the legacy IAM user:

**In main.tf, comment out or remove these resources:**

```hcl
# Comment out these legacy resources
# resource "aws_iam_user" "video_app_user" { ... }
# resource "aws_iam_user_policy" "video_app_user_policy" { ... }
```

#### Option 4: Request Additional IAM Permissions

Ask your AWS administrator to add these permissions to your PowerUserAccess role:

- `iam:GetUser`
- `iam:GetRole`
- `iam:ListRoles`
- `iam:ListUsers`

#### ✅ **RECOMMENDED SOLUTION: Remove Only Legacy IAM User**

Based on your Terraform state, you have both legacy (user) and needed (role) IAM resources:

**Legacy (can be removed):**

- `aws_iam_user.video_app_user`
- `aws_iam_user_policy.video_app_user_policy`

**Still needed (keep):**

- `aws_iam_role.lambda_execution_role`
- `aws_iam_role_policy.lambda_policy`
- `aws_iam_role_policy.ai_video_lambda_policy`

**Steps to fix:**

1. **Remove legacy IAM user from Terraform state (but keep in AWS for now):**

```bash
cd terraform
terraform state rm aws_iam_user.video_app_user
terraform state rm aws_iam_user_policy.video_app_user_policy
```

2. **Comment out the legacy resources in main.tf:**

```hcl
# Legacy IAM user - removed for security (no longer using access keys)
# resource "aws_iam_user" "video_app_user" { ... }
# resource "aws_iam_user_policy" "video_app_user_policy" { ... }
```

3. **Try terraform apply again:**

```bash
terraform plan  # Should only show IAM role operations
terraform apply
```

This approach:

- ✅ Removes the problematic IAM user resources that need `iam:GetUser` permission
- ✅ Keeps the Lambda execution role that's actually needed
- ✅ Uses your PowerUserAccess profile (which might have role permissions)
- ✅ Maintains security by not using access keys

## 🚨 **NEW ERRORS: CloudWatch Log Group + IAM User Tag Issues**

### Error 1: CloudWatch Log Group Already Exists

```
Error: ResourceAlreadyExistsException: The specified log group already exists
```

**Fix:** Import the existing log group to Terraform state:

```bash
cd terraform
terraform import aws_cloudwatch_log_group.ai_video_logs /aws/lambda/easy-video-share-ai-video-processor
```

### Error 2: IAM User Tag Validation Error

```
Error: ValidationError: 1 validation error detected: Value at 'tags.3.member.value' failed to satisfy constraint
```

**Root Cause:** Invalid characters in IAM user tag values (probably parentheses in tag)

**Fix:** Update the IAM user tags in main.tf to remove invalid characters:

```hcl
resource "aws_iam_user" "video_app_user" {
  name = "${var.project_name}-app-user"

  tags = {
    Name        = "Legacy App User - Consider Removing"  # Remove parentheses
    Environment = var.environment
    Project     = var.project_name
  }
}
```

### Complete Fix Steps:

```bash
# 1. Import the existing log group
cd terraform
terraform import aws_cloudwatch_log_group.ai_video_logs /aws/lambda/easy-video-share-ai-video-processor

# 2. Update the IAM user tag in main.tf (remove parentheses)
# 3. Try terraform apply again
terraform plan
terraform apply
```
