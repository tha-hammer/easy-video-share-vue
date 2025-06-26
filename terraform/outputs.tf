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

output "app_user_access_key_id" {
  description = "Access key ID for the application user"
  value       = aws_iam_access_key.video_app_user_key.id
}

output "app_user_secret_access_key" {
  description = "Secret access key for the application user"
  value       = aws_iam_access_key.video_app_user_key.secret
  sensitive   = true
}

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

# =============================================================================
# Outputs
# =============================================================================

# S3 bucket
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.video_bucket.id
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.video_bucket.bucket_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.s3_distribution.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.s3_distribution.domain_name
}

# Cognito
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.users.id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.client.id
}

output "cognito_identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = aws_cognito_identity_pool.main.id
}

# API Gateway
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_deployment.main.invoke_url
}

# Lambda functions
output "lambda_function_name" {
  description = "Name of the main Lambda function"
  value       = aws_lambda_function.video_api.function_name
}

output "admin_lambda_function_name" {
  description = "Name of the admin Lambda function"
  value       = aws_lambda_function.admin_api.function_name
}

# DynamoDB tables
output "video_metadata_table_name" {
  description = "Name of the video metadata DynamoDB table"
  value       = aws_dynamodb_table.video_metadata.name
}

output "video_metadata_table_arn" {
  description = "ARN of the video metadata DynamoDB table"
  value       = aws_dynamodb_table.video_metadata.arn
}

# AI Video Generation Outputs (conditionally created)
output "ai_projects_table_name" {
  description = "Name of the AI projects DynamoDB table"
  value       = var.enable_ai_video_pipeline ? aws_dynamodb_table.ai_projects[0].name : null
}

output "video_assets_table_name" {
  description = "Name of the video assets DynamoDB table"
  value       = var.enable_ai_video_pipeline ? aws_dynamodb_table.video_assets[0].name : null
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.enable_ai_video_pipeline ? aws_ecs_cluster.video_processor[0].name : null
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = var.enable_ai_video_pipeline ? aws_ecr_repository.video_processor[0].repository_url : null
}

output "ai_video_bus_name" {
  description = "Name of the EventBridge bus for AI video processing"
  value       = var.enable_ai_video_pipeline ? aws_cloudwatch_event_bus.ai_video_bus[0].name : null
}

output "secrets_manager_secret_name" {
  description = "Name of the Secrets Manager secret containing API keys"
  value       = var.enable_ai_video_pipeline ? aws_secretsmanager_secret.ai_api_keys[0].name : null
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = var.enable_ai_video_pipeline ? aws_iam_role.ecs_task_execution_role[0].arn : null
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = var.enable_ai_video_pipeline ? aws_iam_role.ecs_task_role[0].arn : null
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = var.enable_ai_video_pipeline ? aws_security_group.ecs_tasks[0].id : null
}

output "ecs_subnet_ids" {
  description = "IDs of the ECS subnets"
  value = var.enable_ai_video_pipeline && var.create_vpc ? [
    aws_subnet.ecs_public_subnet_1[0].id,
    aws_subnet.ecs_public_subnet_2[0].id
  ] : null
}

output "ecs_vpc_id" {
  description = "ID of the ECS VPC"
  value = var.enable_ai_video_pipeline && var.create_vpc ? aws_vpc.ecs_vpc[0].id : var.vpc_id
} 