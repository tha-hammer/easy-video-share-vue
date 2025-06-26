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

# AI Video Generation Variables
variable "google_cloud_credentials_json" {
  description = "Google Cloud service account credentials JSON"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key for scene generation"
  type        = string
  sensitive   = true
  default     = ""
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