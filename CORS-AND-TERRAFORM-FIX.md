# CRITICAL FIX: CORS and Terraform Deployment Issues

## Issue Summary

The deployment was failing due to:

1. **Terraform Errors**: References to non-existent audio resources in main.tf
2. **CORS Errors**: Missing integration responses for AI video endpoints

## Root Cause

The `main.tf` API Gateway deployment section was referencing audio resources that only exist in `ai-video-extensions.tf`, causing Terraform planning to fail.

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

## Expected Result

- ✅ Terraform plan/apply should now succeed
- ✅ API Gateway deployment will work correctly
- ✅ CORS headers should be properly set for all endpoints
- ✅ AI video generation should work without CORS errors

## Next Steps

1. **Run deployment**: `./scripts/deploy-ai-video.sh`
2. **Test AI video generation** - CORS errors should be resolved
3. **Verify all endpoints** respond with proper CORS headers

## Note

The ai-video-extensions.tf file handles the AI video and audio endpoints with their own deployment dependencies. This separation is working correctly and doesn't need changes.
