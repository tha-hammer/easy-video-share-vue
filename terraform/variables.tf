variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for video storage"
  type        = string
  validation {
    condition     = length(var.bucket_name) > 3 && length(var.bucket_name) < 64
    error_message = "Bucket name must be between 3 and 63 characters."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "easy-video-share"
}

# Cognito Configuration
variable "cognito_domain_prefix" {
  description = "Prefix for Cognito domain"
  type        = string
}

# Optional: Admin user configuration
variable "admin_user_email" {
  description = "Admin user email"
  type        = string
  default     = ""
}

variable "admin_user_password" {
  description = "Admin user password"
  type        = string
  default     = ""
  sensitive   = true
}

# Google Cloud Configuration (for compatibility)
variable "google_cloud_project_id" {
  description = "Google Cloud project ID"
  type        = string
  default     = ""
}

variable "google_cloud_location" {
  description = "Google Cloud location"
  type        = string
  default     = "us-central1"
}

variable "google_cloud_service_account_email" {
  description = "Google Cloud service account email"
  type        = string
  default     = ""
}

# Workload Identity Federation
variable "workload_identity_pool_id" {
  description = "Workload identity pool ID"
  type        = string
  default     = ""
}

variable "workload_identity_provider_id" {
  description = "Workload identity provider ID"
  type        = string
  default     = ""
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = ""
}

# OpenAI Configuration
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  default     = ""
  sensitive   = true
}

# CI/CD configuration
variable "github_repository" {
  description = "GitHub repository"
  type        = string
  default     = ""
}

# Legacy configuration (for backward compatibility)
variable "vertex_ai_project_id" {
  description = "Vertex AI project ID"
  type        = string
  default     = ""
}

variable "vertex_ai_location" {
  description = "Vertex AI location"
  type        = string
  default     = "us-central1"
}

variable "google_cloud_credentials_json" {
  description = "Google Cloud credentials JSON"
  type        = string
  default     = ""
  sensitive   = true
}