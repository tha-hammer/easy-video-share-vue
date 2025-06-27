output "bucket_name" {
  description = "Name of the created S3 bucket"
  value       = aws_s3_bucket.video_bucket.bucket
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.video_bucket.arn
}

output "bucket_website_endpoint" {
  description = "Website endpoint for the S3 bucket"
  value       = aws_s3_bucket_website_configuration.video_bucket_website.website_endpoint
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.video_bucket.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.video_bucket.bucket_regional_domain_name
}

# Audio Bucket Outputs
output "audio_bucket_name" {
  description = "Name of the created S3 audio bucket"
  value       = aws_s3_bucket.audio_bucket.bucket
}

output "audio_bucket_arn" {
  description = "ARN of the created S3 audio bucket"
  value       = aws_s3_bucket.audio_bucket.arn
}

output "audio_bucket_domain_name" {
  description = "Domain name of the S3 audio bucket"
  value       = aws_s3_bucket.audio_bucket.bucket_domain_name
}

# REMOVED: Access keys for security (use IAM roles instead)
# output "app_user_access_key_id" {
#   description = "Access key ID for the application user"
#   value       = aws_iam_access_key.video_app_user_key.id
# }

# output "app_user_secret_access_key" {
#   description = "Secret access key for the application user"
#   value       = aws_iam_access_key.video_app_user_key.secret
#   sensitive   = true
# }

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for video metadata"
  value       = aws_dynamodb_table.video_metadata.name
}

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "api_videos_endpoint" {
  description = "Full API endpoint for video operations"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/videos"
}

# Admin API Endpoints
output "api_admin_users_endpoint" {
  description = "Full API endpoint for admin user operations"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/admin/users"
}

output "api_admin_videos_endpoint" {
  description = "Full API endpoint for admin video operations"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/admin/videos"
}

# Cognito Configuration
output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.video_app_users.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.video_app_client.id
}

output "cognito_user_pool_domain" {
  description = "Cognito User Pool Domain"
  value       = aws_cognito_user_pool.video_app_users.domain
}

output "cognito_region" {
  description = "AWS region for Cognito"
  value       = var.aws_region
}

output "aws_region" {
  description = "AWS region where resources are created"
  value       = var.aws_region
}

# Audio API Endpoints
output "api_audio_endpoint" {
  description = "Full API endpoint for audio operations"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/audio"
}

output "api_audio_upload_endpoint" {
  description = "Full API endpoint for audio upload URL generation"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/audio/upload-url"
}

# AI Video Lambda Function
output "ai_video_lambda_function_name" {
  description = "Name of the AI video processing Lambda function"
  value       = aws_lambda_function.ai_video_processor.function_name
}

# AI Video API Endpoints
output "api_ai_video_endpoint" {
  description = "Full API endpoint for AI video operations"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}/ai-video"
} 