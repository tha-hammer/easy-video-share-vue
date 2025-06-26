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
  description = "Cognito domain prefix for hosted UI"
  type        = string
  default     = "easy-video-share"
  validation {
    condition     = length(var.cognito_domain_prefix) > 3 && length(var.cognito_domain_prefix) < 64
    error_message = "Cognito domain prefix must be between 3 and 63 characters."
  }
}

# Google Cloud Configuration (Modern Authentication)
variable "google_cloud_project_id" {
  description = "Google Cloud Project ID for Vertex AI"
  type        = string
  default     = ""
}

variable "google_cloud_location" {
  description = "Google Cloud location for Vertex AI (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "google_cloud_service_account_email" {
  description = "Google Cloud Service Account email for Vertex AI"
  type        = string
  default     = ""
}

# OpenAI Configuration
variable "openai_api_key" {
  description = "OpenAI API key for AI video generation"
  type        = string
  default     = ""
  sensitive   = true
}

# Legacy JSON key support (optional, for backward compatibility)
variable "google_cloud_credentials_json" {
  description = "Google Cloud service account JSON credentials (legacy, prefer ADC)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "vertex_ai_project_id" {
  description = "Google Cloud project ID for Vertex AI"
  type        = string
  default     = ""
}

variable "vertex_ai_location" {
  description = "Google Cloud location for Vertex AI"
  type        = string
  default     = "us-central1"
}

variable "audio_bucket_name" {
  description = "Name of the S3 bucket for audio file storage (AI Shorts)"
  type        = string
  default     = ""
  validation {
    condition     = var.audio_bucket_name == "" || (length(var.audio_bucket_name) > 3 && length(var.audio_bucket_name) < 64)
    error_message = "Audio bucket name must be between 3 and 63 characters or empty to auto-generate."
  }
}

# Workload Identity Federation Configuration
variable "workload_identity_pool_id" {
  description = "Workload Identity Pool ID for AWS to Google Cloud federation"
  type        = string
  default     = "easy-video-share"
}

variable "workload_identity_provider_id" {
  description = "Workload Identity Provider ID for AWS"
  type        = string
  default     = "easy-video-share"
}

variable "aws_account_id" {
  description = "AWS Account ID for Workload Identity Federation"
  type        = string
  default     = "571960159088"
} 