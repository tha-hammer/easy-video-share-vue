# Terraform Duplicate Resource Fix

## Issue

The deploy script failed with multiple "Duplicate resource" errors because AI video infrastructure was defined in both:

- `main.tf` (incorrectly added by me)
- `ai-video-extensions.tf` (existing file with proper definitions)

## Errors Fixed

Removed duplicate resources from `main.tf`:

- ❌ `aws_secretsmanager_secret.ai_video_secrets`
- ❌ `aws_secretsmanager_secret_version.ai_video_secrets`
- ❌ `aws_lambda_layer_version.ai_video_layer`
- ❌ `aws_lambda_function.ai_video_processor`
- ❌ `aws_cloudwatch_log_group.ai_video_logs`
- ❌ `aws_api_gateway_resource.ai_video_resource`
- ❌ `aws_api_gateway_method.ai_video_post`
- ❌ `aws_api_gateway_method.ai_video_get`
- ❌ `aws_api_gateway_method.ai_video_options`
- ❌ `aws_api_gateway_integration.ai_video_post_integration`
- ❌ `aws_api_gateway_integration.ai_video_get_integration`
- ❌ `aws_api_gateway_integration.ai_video_options_integration`
- ❌ `aws_lambda_permission.ai_video_api_gateway_lambda`

## Resolution

✅ **Replaced duplicate section with comment**: `# AI Video Infrastructure is defined in ai-video-extensions.tf`

## Verification

- All AI video resources properly defined in `ai-video-extensions.tf`
- All audio resources (referenced in deployment) exist in `ai-video-extensions.tf`
- Deploy script dependency references remain valid

## Status

✅ **FIXED**: Deploy script should now run without Terraform duplicate resource errors.

## Next Steps

1. Run deploy script: `./scripts/deploy-ai-video.sh`
2. Verify successful deployment
3. Test AI video generation workflow
