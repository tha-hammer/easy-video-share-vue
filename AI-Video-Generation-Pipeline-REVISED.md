# 🎬 **AI-Powered Short-Form Video Generation Pipeline - REVISED PLAN**

## **Critical Issues Identified in Original Plan**

### ❌ **Infrastructure Misalignment**

- Original plan proposed completely new DynamoDB tables, ignoring existing `video_metadata` table
- Planned separate ECS/Fargate cluster, overlooking existing Lambda-based architecture
- Ignored existing Cognito authentication and API Gateway structure
- Proposed new S3 bucket structure conflicting with existing setup

### ❌ **Technology Stack Conflicts**

- Kling AI integration not viable (limited API availability, pricing uncertainty)
- Over-engineered Python video processing in containers vs. simple Lambda approach
- Complex EventBridge orchestration when existing API Gateway patterns work well
- Ignored existing IAM roles and permissions structure

### ❌ **Operational Complexity**

- Proposed 4-5 new Lambda functions vs. extending existing ones
- Complex multi-table data model vs. leveraging existing video_metadata structure
- Separate authentication patterns vs. using existing Cognito integration

---

## 🔄 **REVISED SOLUTION: Vertex AI with Veo 2 Integration**

### **Core Architecture Changes**

```
Audio Upload → Transcription → Scene Planning → Vertex AI Veo 2 → Final Video
     ↓              ↓              ↓              ↓            ↓
Existing S3 → AWS Transcribe → OpenAI GPT-4 → Google Veo 2 → Existing Lambda
```

### **Technology Stack**

- **Frontend**: Vue.js 3 + TypeScript + Metronic UI (existing)
- **Backend**: Existing AWS Lambda + API Gateway + DynamoDB
- **AI Services**: Google Cloud Vertex AI (Veo 2), OpenAI GPT-4
- **Video Processing**: In-Lambda FFmpeg processing (no containers)
- **Storage**: Existing S3 bucket with new folder structure
- **Authentication**: Existing AWS Cognito

---

## 📊 **Revised Data Model (Extending Existing)**

### **Extended video_metadata Table**

```typescript
interface VideoMetadata {
  // Existing fields
  video_id: string
  user_id: string
  user_email: string
  title: string
  filename: string
  bucket_location: string
  upload_date: string
  file_size?: number
  content_type?: string
  duration?: number
  created_at: string
  updated_at: string

  // NEW AI Video Generation fields
  ai_project_type?: 'standard' | 'ai_generated'
  ai_generation_status?: 'processing' | 'completed' | 'failed'
  ai_generation_data?: {
    // Audio processing
    audio_transcription?: {
      full_text: string
      segments: TranscriptSegment[]
      confidence: number
      language_code: string
    }

    // Scene planning
    scene_beats?: {
      overall_theme: string
      scenes: SceneBeat[]
      target_duration: number
    }

    // Vertex AI generation
    vertex_ai_tasks?: {
      task_id: string
      status: 'pending' | 'processing' | 'completed' | 'failed'
      video_url?: string
      prompt: string
      created_at: string
    }[]

    // Processing metadata
    processing_steps?: ProcessingStep[]
    final_video_url?: string
    generation_time?: number
    cost_breakdown?: {
      transcription: number
      scene_generation: number
      video_generation: number
      total: number
    }
  }
}

interface TranscriptSegment {
  start_time: number
  end_time: number
  text: string
  confidence: number
}

interface SceneBeat {
  sequence: number
  start_time: number
  end_time: number
  duration: number
  audio_text: string
  scene_description: string
  vertex_ai_prompt: string
  visual_style: string
}

interface ProcessingStep {
  step: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
}
```

---

## 🔧 **Terraform Infrastructure Extensions**

### **Minimal Infrastructure Additions**

```hcl
# terraform/ai-video-extensions.tf

# Add Google Cloud Service Account key to Secrets Manager
resource "aws_secretsmanager_secret" "ai_video_secrets" {
  name        = "${var.project_name}-ai-video-secrets"
  description = "API keys and secrets for AI video generation"

  tags = {
    Name        = "AI Video Secrets"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "ai_video_secrets" {
  secret_id = aws_secretsmanager_secret.ai_video_secrets.id
  secret_string = jsonencode({
    google_cloud_credentials = var.google_cloud_credentials_json
    openai_api_key          = var.openai_api_key
    vertex_ai_project_id    = var.vertex_ai_project_id
    vertex_ai_location      = var.vertex_ai_location
  })
}

# Extend existing Lambda function with AI capabilities
resource "aws_lambda_layer_version" "ai_video_layer" {
  filename   = "ai_video_layer.zip"
  layer_name = "${var.project_name}-ai-video-layer"

  compatible_runtimes = ["nodejs18.x"]

  description = "AI video generation dependencies (Google Cloud SDK, FFmpeg)"
}

# Update existing Lambda function to include new layer
resource "aws_lambda_function" "ai_video_processor" {
  filename         = "ai_video_lambda.zip"
  function_name    = "${var.project_name}-ai-video-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "ai-video.handler"
  runtime         = "nodejs18.x"
  timeout         = 900  # 15 minutes for AI processing
  memory_size     = 2048 # Increased for video processing

  layers = [aws_lambda_layer_version.ai_video_layer.arn]

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.video_metadata.name
      SECRETS_MANAGER_ARN = aws_secretsmanager_secret.ai_video_secrets.arn
      S3_BUCKET = aws_s3_bucket.video_bucket.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_policy,
    aws_cloudwatch_log_group.ai_video_logs,
  ]
}

# CloudWatch Log Group for AI video processing
resource "aws_cloudwatch_log_group" "ai_video_logs" {
  name              = "/aws/lambda/${var.project_name}-ai-video-processor"
  retention_in_days = 14

  tags = {
    Name        = "AI Video Processing Logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Add new API Gateway routes for AI video processing
resource "aws_api_gateway_resource" "ai_video_resource" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  parent_id   = aws_api_gateway_rest_api.video_api.root_resource_id
  path_part   = "ai-video"
}

resource "aws_api_gateway_method" "ai_video_post" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "ai_video_post_integration" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "ai_video_api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_video_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.video_api.execution_arn}/*/*"
}

# Update IAM role policy to include Secrets Manager access
resource "aws_iam_role_policy" "ai_video_lambda_policy" {
  name = "${var.project_name}-ai-video-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.ai_video_secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.video_bucket.arn}/ai-generated/*",
          "${aws_s3_bucket.video_bucket.arn}/ai-temp/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### **New Variables**

```hcl
# terraform/variables.tf (additions)

variable "google_cloud_credentials_json" {
  description = "Google Cloud service account credentials JSON"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for scene generation"
  type        = string
  sensitive   = true
}

variable "vertex_ai_project_id" {
  description = "Google Cloud project ID for Vertex AI"
  type        = string
}

variable "vertex_ai_location" {
  description = "Google Cloud location for Vertex AI"
  type        = string
  default     = "us-central1"
}
```

---

## 💰 **Revised Cost Analysis**

### **Monthly Cost Estimates (100 videos/month)**

**AWS Services:**

- **DynamoDB**: ~$5 (reusing existing table)
- **Lambda**: ~$15-25 (extended processing time)
- **S3 Storage**: ~$10-15 (reusing existing bucket)
- **AWS Transcribe**: ~$15-25 (audio transcription)
- **Secrets Manager**: ~$2 (API key storage)

**Google Cloud Services:**

- **Vertex AI Veo 2**: ~$40-80 (video generation - estimated)
- **Cloud Storage**: ~$5 (temporary storage)

**External APIs:**

- **OpenAI GPT-4**: ~$10-20 (scene planning)

**Total Estimated Monthly Cost: $102-177** (significantly lower than original plan)

---

## 🚀 **Implementation Timeline**

### **Phase 1: Infrastructure Setup (Week 1)**

- Add Google Cloud credentials to Secrets Manager
- Create Lambda layer with Google Cloud SDK
- Update existing Lambda function for AI processing
- Add new API Gateway routes

### **Phase 2: Backend Implementation (Week 1-2)**

- Implement AI video processing Lambda
- Add Vertex AI Veo 2 integration
- Test transcription and scene planning

### **Phase 3: Frontend Integration (Week 2)**

- Create AI video generation component
- Integrate with existing video management
- Add progress tracking and status display

### **Phase 4: Testing & Optimization (Week 3)**

- End-to-end testing
- Performance optimization
- Error handling and edge cases

---

## ✅ **Key Advantages of Revised Plan**

1. **Infrastructure Reuse**: Leverages existing DynamoDB, S3, Lambda, and Cognito setup
2. **Simplified Architecture**: Single Lambda function vs. multiple containers
3. **Cost Effective**: 40-50% lower estimated costs
4. **Faster Implementation**: Builds on existing patterns and code
5. **Better Integration**: Seamless with current video management workflow
6. **Scalable**: Uses proven AWS serverless architecture
7. **Modern AI**: Vertex AI Veo 2 is Google's latest text-to-video model

---

## 🔧 **Next Steps**

1. **Set up Google Cloud project** and enable Vertex AI
2. **Create service account** with Vertex AI permissions
3. **Add secrets to AWS Secrets Manager**
4. **Update terraform configuration** with new resources
5. **Implement and test Lambda function**
6. **Create Vue.js frontend components**
7. **Deploy and test end-to-end workflow**

This revised plan addresses all the flaws in the original approach while providing a more practical, cost-effective, and maintainable solution for AI video generation.
