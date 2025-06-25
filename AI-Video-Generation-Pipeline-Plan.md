# 🎬 **AI-Powered Short-Form Video Generation Pipeline**

## **Comprehensive Implementation Plan**

---

## 📋 **Executive Summary**

Transform audio uploads into professional vertical short-form videos (30-60s) for Instagram Reels and YouTube Shorts using AI-generated visuals. This plan extends the existing Vue.js video sharing application with sophisticated AI-powered content generation capabilities.

**Key Technologies**: Vue.js 3 + TypeScript, Metronic UI, AWS Infrastructure, Python Video Processing, Kling AI, LLM Integration

---

## 🏗️ **System Architecture Overview**

### **Pipeline Flow**

```
Audio Upload → Transcription → LLM Scene Planning → AI Asset Generation → Video Compilation → Final Output
```

### **Technology Stack**

- **Frontend**: Vue.js 3 + TypeScript + Metronic UI Components
- **Backend**: AWS Lambda + API Gateway + DynamoDB (Extended existing infrastructure)
- **AI Services**: Kling API (Video/Image), OpenAI/Anthropic (Scene Generation)
- **Video Processing**: Python + FFmpeg on ECS/Fargate
- **Storage**: AWS S3 with Transfer Acceleration
- **Authentication**: AWS Cognito (Existing system)

---

## 🎯 **Current Infrastructure Analysis**

### **Existing AWS Resources (terraform/main.tf)**

✅ **S3 Bucket**: `video_bucket` with Transfer Acceleration, CORS, Encryption  
✅ **DynamoDB**: `video_metadata` table with user_id GSI  
✅ **API Gateway**: REST API with Cognito authorization  
✅ **Lambda Functions**: Video metadata API, Admin API  
✅ **Cognito**: User Pool with admin/user groups  
✅ **IAM**: Application user with S3/DynamoDB permissions

### **Extensions Needed**

🔄 **New DynamoDB Tables**: Audio projects, transcripts, scene beats, generated assets  
🔄 **New Lambda Functions**: Transcription, scene generation, Kling integration, video compilation  
🔄 **ECS/Fargate**: Python video processing cluster  
🔄 **Secrets Manager**: API keys for external services  
🔄 **EventBridge**: Async processing orchestration

---

## 📊 **Data Models & Schema Design**

### **Core Entities**

```typescript
// Audio Project (Main entity)
interface AudioProject {
  project_id: string // PK: userId_timestamp_random
  user_id: string // GSI: User's Cognito sub
  title: string // User-defined project name
  audio_file_url: string // S3 object key
  audio_duration: number // Duration in seconds
  target_duration: number // Desired video length (30-60s)
  transcript_id?: string // FK to transcripts table
  status: ProjectStatus // Pipeline stage
  scene_beats_count?: number // Number of generated scenes
  final_video_url?: string // Compiled video S3 URL
  created_at: string // ISO timestamp
  updated_at: string // ISO timestamp
  metadata: {
    file_size: number
    content_type: string
    original_filename: string
  }
}

type ProjectStatus =
  | 'uploaded' // Audio file uploaded
  | 'transcribing' // AWS Transcribe processing
  | 'planning' // LLM generating scene beats
  | 'generating' // Kling AI creating assets
  | 'compiling' // Python video compilation
  | 'completed' // Final video ready
  | 'failed' // Error state

// Transcript Data
interface TranscriptData {
  transcript_id: string // PK
  project_id: string // FK to audio_projects
  full_text: string // Complete transcript
  segments: TranscriptSegment[] // Time-coded segments
  confidence: number // Overall confidence score
  language_code: string // Detected language
  created_at: string
}

interface TranscriptSegment {
  start_time: number // Seconds from start
  end_time: number // Seconds from start
  text: string // Segment text
  confidence: number // Segment confidence
  speaker_label?: string // Speaker identification
}

// Scene Beats (LLM Generated)
interface SceneBeat {
  beat_id: string // PK
  project_id: string // FK to audio_projects
  sequence_number: number // Scene order (1, 2, 3...)
  start_time: number // Audio timestamp start
  end_time: number // Audio timestamp end
  duration: number // Scene duration
  audio_segment: string // Selected transcript portion
  scene_description: string // LLM scene description
  visual_prompt: string // Optimized Kling prompt
  asset_type: 'video' | 'image' // Generation type
  transition_style: string // Transition effect
  generated_asset_id?: string // FK to generated_assets
  status: 'pending' | 'generated' | 'failed'
  created_at: string
}

// Generated Assets (Kling AI)
interface GeneratedAsset {
  asset_id: string // PK
  beat_id: string // FK to scene_beats
  kling_task_id: string // Kling API task ID
  asset_type: 'video' | 'image' // Asset type
  status: AssetStatus // Generation status
  asset_url?: string // S3 URL when complete
  prompt: string // Generation prompt used
  generation_params: {
    // Kling parameters
    duration?: number
    aspect_ratio: string
    quality: string
    style?: string
  }
  processing_time?: number // Generation duration
  error_message?: string // If failed
  created_at: string
  completed_at?: string
}

type AssetStatus =
  | 'pending' // Queued for generation
  | 'generating' // Kling processing
  | 'completed' // Asset ready
  | 'failed' // Generation failed
  | 'downloading' // Transferring to S3
```

---

## 🗄️ **Extended Terraform Infrastructure**

### **New DynamoDB Tables**

```hcl
# terraform/audio-generation-tables.tf

# Audio Projects Table
resource "aws_dynamodb_table" "audio_projects" {
  name           = "${var.project_name}-audio-projects"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "project_id"

  attribute {
    name = "project_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name     = "user-projects-index"
    hash_key = "user_id"
    range_key = "created_at"
  }

  global_secondary_index {
    name     = "status-index"
    hash_key = "status"
  }

  tags = {
    Name        = "Audio Projects"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Transcripts Table
resource "aws_dynamodb_table" "transcripts" {
  name           = "${var.project_name}-transcripts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "transcript_id"

  attribute {
    name = "transcript_id"
    type = "S"
  }

  attribute {
    name = "project_id"
    type = "S"
  }

  global_secondary_index {
    name     = "project-index"
    hash_key = "project_id"
  }

  tags = {
    Name        = "Audio Transcripts"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Scene Beats Table
resource "aws_dynamodb_table" "scene_beats" {
  name           = "${var.project_name}-scene-beats"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "project_id"
  range_key      = "sequence_number"

  attribute {
    name = "project_id"
    type = "S"
  }

  attribute {
    name = "sequence_number"
    type = "N"
  }

  attribute {
    name = "beat_id"
    type = "S"
  }

  global_secondary_index {
    name     = "beat-id-index"
    hash_key = "beat_id"
  }

  tags = {
    Name        = "Scene Beats"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Generated Assets Table
resource "aws_dynamodb_table" "generated_assets" {
  name           = "${var.project_name}-generated-assets"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "asset_id"

  attribute {
    name = "asset_id"
    type = "S"
  }

  attribute {
    name = "kling_task_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name     = "kling-task-index"
    hash_key = "kling_task_id"
  }

  global_secondary_index {
    name     = "status-index"
    hash_key = "status"
  }

  tags = {
    Name        = "Generated Assets"
    Environment = var.environment
    Project     = var.project_name
  }
}
```

### **Secrets Management**

```hcl
# terraform/secrets.tf
resource "aws_secretsmanager_secret" "ai_api_keys" {
  name        = "${var.project_name}-ai-api-keys"
  description = "API keys for AI services"

  tags = {
    Name        = "AI API Keys"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "ai_api_keys" {
  secret_id = aws_secretsmanager_secret.ai_api_keys.id
  secret_string = jsonencode({
    kling_api_key   = var.kling_api_key
    openai_api_key  = var.openai_api_key
  })
}

# Update variables.tf
variable "kling_api_key" {
  description = "Kling AI API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}
```

### **New Lambda Functions**

```hcl
# terraform/audio-generation-lambdas.tf

# Audio Transcription Lambda
resource "aws_lambda_function" "audio_transcription" {
  filename         = "audio_transcription_lambda.zip"
  function_name    = "${var.project_name}-audio-transcription"
  role            = aws_iam_role.audio_transcription_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      PROJECTS_TABLE = aws_dynamodb_table.audio_projects.name
      TRANSCRIPTS_TABLE = aws_dynamodb_table.transcripts.name
      S3_BUCKET = aws_s3_bucket.video_bucket.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.audio_transcription_policy,
    aws_cloudwatch_log_group.audio_transcription_logs,
  ]
}

# Scene Generation Lambda
resource "aws_lambda_function" "scene_generation" {
  filename         = "scene_generation_lambda.zip"
  function_name    = "${var.project_name}-scene-generation"
  role            = aws_iam_role.scene_generation_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 900  # 15 minutes for LLM processing
  memory_size     = 1024

  environment {
    variables = {
      PROJECTS_TABLE = aws_dynamodb_table.audio_projects.name
      TRANSCRIPTS_TABLE = aws_dynamodb_table.transcripts.name
      SCENE_BEATS_TABLE = aws_dynamodb_table.scene_beats.name
      SECRETS_MANAGER_ARN = aws_secretsmanager_secret.ai_api_keys.arn
    }
  }
}

# Kling Integration Lambda
resource "aws_lambda_function" "kling_integration" {
  filename         = "kling_integration_lambda.zip"
  function_name    = "${var.project_name}-kling-integration"
  role            = aws_iam_role.kling_integration_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      SCENE_BEATS_TABLE = aws_dynamodb_table.scene_beats.name
      GENERATED_ASSETS_TABLE = aws_dynamodb_table.generated_assets.name
      SECRETS_MANAGER_ARN = aws_secretsmanager_secret.ai_api_keys.arn
      S3_BUCKET = aws_s3_bucket.video_bucket.bucket
    }
  }
}

# Video Compilation Orchestrator Lambda
resource "aws_lambda_function" "video_compilation" {
  filename         = "video_compilation_lambda.zip"
  function_name    = "${var.project_name}-video-compilation"
  role            = aws_iam_role.video_compilation_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      PROJECTS_TABLE = aws_dynamodb_table.audio_projects.name
      ECS_CLUSTER_ARN = aws_ecs_cluster.video_processing.arn
      ECS_TASK_DEFINITION = aws_ecs_task_definition.video_processor.arn
      SUBNET_IDS = join(",", aws_subnet.private[*].id)
      SECURITY_GROUP_ID = aws_security_group.ecs_tasks.id
    }
  }
}
```

### **ECS/Fargate Video Processing Cluster**

```hcl
# terraform/ecs-video-processing.tf

# ECS Cluster for video processing
resource "aws_ecs_cluster" "video_processing" {
  name = "${var.project_name}-video-processing"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "Video Processing Cluster"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECR Repository for video processor image
resource "aws_ecr_repository" "video_processor" {
  name                 = "${var.project_name}-video-processor"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "Video Processor Repository"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Task Definition for video processing
resource "aws_ecs_task_definition" "video_processor" {
  family                   = "${var.project_name}-video-processor"
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = 4096   # 4 vCPU for video processing
  memory                  = 16384  # 16GB RAM for FFmpeg operations
  execution_role_arn      = aws_iam_role.ecs_execution_role.arn
  task_role_arn          = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "video-processor"
      image = "${aws_ecr_repository.video_processor.repository_url}:latest"

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = aws_s3_bucket.video_bucket.bucket },
        { name = "PROJECTS_TABLE", value = aws_dynamodb_table.audio_projects.name },
        { name = "SCENE_BEATS_TABLE", value = aws_dynamodb_table.scene_beats.name },
        { name = "GENERATED_ASSETS_TABLE", value = aws_dynamodb_table.generated_assets.name }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.video_processor.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "Video Processor Task"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "video_processor" {
  name              = "/ecs/${var.project_name}-video-processor"
  retention_in_days = 14

  tags = {
    Name        = "Video Processor Logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# VPC and Networking for ECS (if not exists)
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "private" {
  count = var.create_vpc ? 2 : 0

  vpc_id            = aws_vpc.main[0].id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-ecs-tasks"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-tasks-sg"
  }
}
```

### **EventBridge for Async Processing**

```hcl
# terraform/eventbridge.tf

# Custom Event Bus for AI video generation
resource "aws_cloudwatch_event_bus" "ai_video_generation" {
  name = "${var.project_name}-ai-video-generation"

  tags = {
    Name        = "AI Video Generation Event Bus"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Rule for audio transcription completion
resource "aws_cloudwatch_event_rule" "transcription_complete" {
  name        = "${var.project_name}-transcription-complete"
  description = "Trigger scene generation after transcription completes"
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name

  event_pattern = jsonencode({
    source      = ["easy-video-share.transcription"]
    detail-type = ["Transcription Complete"]
  })
}

# Target for scene generation
resource "aws_cloudwatch_event_target" "scene_generation_target" {
  rule           = aws_cloudwatch_event_rule.transcription_complete.name
  target_id      = "SceneGenerationTarget"
  arn            = aws_lambda_function.scene_generation.arn
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name
}

# Rule for scene generation completion
resource "aws_cloudwatch_event_rule" "scene_generation_complete" {
  name        = "${var.project_name}-scene-generation-complete"
  description = "Trigger Kling asset generation after scene planning"
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name

  event_pattern = jsonencode({
    source      = ["easy-video-share.scene-generation"]
    detail-type = ["Scene Generation Complete"]
  })
}

# Target for Kling integration
resource "aws_cloudwatch_event_target" "kling_integration_target" {
  rule           = aws_cloudwatch_event_rule.scene_generation_complete.name
  target_id      = "KlingIntegrationTarget"
  arn            = aws_lambda_function.kling_integration.arn
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name
}

# Rule for asset generation completion
resource "aws_cloudwatch_event_rule" "asset_generation_complete" {
  name        = "${var.project_name}-asset-generation-complete"
  description = "Trigger video compilation after all assets are ready"
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name

  event_pattern = jsonencode({
    source      = ["easy-video-share.asset-generation"]
    detail-type = ["All Assets Complete"]
  })
}

# Target for video compilation
resource "aws_cloudwatch_event_target" "video_compilation_target" {
  rule           = aws_cloudwatch_event_rule.asset_generation_complete.name
  target_id      = "VideoCompilationTarget"
  arn            = aws_lambda_function.video_compilation.arn
  event_bus_name = aws_cloudwatch_event_bus.ai_video_generation.name
}
```

---

## 🔧 **Lambda Function Implementations**

### **1. Audio Transcription Service**

```python
# terraform/lambdas/audio-transcription/index.py
import json
import boto3
import uuid
from datetime import datetime
import os

transcribe = boto3.client('transcribe')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
events = boto3.client('events')

def handler(event, context):
    """
    Initiates AWS Transcribe job for uploaded audio file
    Updates project status and creates transcript record
    """
    try:
        # Parse input
        project_id = event['project_id']
        audio_s3_key = event['audio_s3_key']

        # Get project details
        projects_table = dynamodb.Table(os.environ['PROJECTS_TABLE'])
        project = projects_table.get_item(Key={'project_id': project_id})['Item']

        # Start transcription job
        job_name = f"transcribe-{project_id}-{int(datetime.now().timestamp())}"
        transcript_id = str(uuid.uuid4())

        transcribe_response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={
                'MediaFileUri': f"s3://{os.environ['S3_BUCKET']}/{audio_s3_key}"
            },
            MediaFormat=detect_media_format(audio_s3_key),
            LanguageCode='en-US',  # Could be auto-detected
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 2,
                'ShowAlternatives': True,
                'MaxAlternatives': 2
            },
            JobExecutionSettings={
                'AllowDeferredExecution': False,
                'DataAccessRoleArn': context.invoked_function_arn
            }
        )

        # Create transcript record
        transcripts_table = dynamodb.Table(os.environ['TRANSCRIPTS_TABLE'])
        transcripts_table.put_item(
            Item={
                'transcript_id': transcript_id,
                'project_id': project_id,
                'transcribe_job_name': job_name,
                'status': 'transcribing',
                'created_at': datetime.now().isoformat()
            }
        )

        # Update project status
        projects_table.update_item(
            Key={'project_id': project_id},
            UpdateExpression='SET #status = :status, transcript_id = :transcript_id, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'transcribing',
                ':transcript_id': transcript_id,
                ':updated_at': datetime.now().isoformat()
            }
        )

        # Set up polling for transcription completion
        setup_transcription_polling(job_name, project_id, transcript_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'project_id': project_id,
                'transcript_id': transcript_id,
                'job_name': job_name,
                'status': 'transcribing'
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        # Update project status to failed
        projects_table.update_item(
            Key={'project_id': project_id},
            UpdateExpression='SET #status = :status, error_message = :error, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'failed',
                ':error': str(e),
                ':updated_at': datetime.now().isoformat()
            }
        )

        raise e

def detect_media_format(s3_key):
    """Detect media format from file extension"""
    extension = s3_key.split('.')[-1].lower()
    format_map = {
        'mp3': 'mp3',
        'wav': 'wav',
        'm4a': 'm4a',
        'aac': 'mp3',  # Transcribe treats AAC as MP3
        'ogg': 'ogg',
        'webm': 'webm'
    }
    return format_map.get(extension, 'mp3')

def setup_transcription_polling(job_name, project_id, transcript_id):
    """Set up CloudWatch Events rule to poll for transcription completion"""
    # This would set up a recurring Lambda to check transcription status
    # For simplicity, using a Step Function or EventBridge scheduled rule
    pass
```

### **2. Scene Generation Service (LLM Integration)**

```python
# terraform/lambdas/scene-generation/index.py
import json
import boto3
import openai
import uuid
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')
events = boto3.client('events')

def handler(event, context):
    """
    Generate scene beats using LLM based on transcript
    Creates detailed visual prompts for Kling AI generation
    """
    try:
        project_id = event['project_id']

        # Get API keys from Secrets Manager
        secrets = get_api_keys()
        openai.api_key = secrets['openai_api_key']

        # Get project and transcript data
        project = get_project_data(project_id)
        transcript = get_transcript_data(project['transcript_id'])

        # Generate scene beats using LLM
        scene_plan = generate_scene_plan(transcript, project['target_duration'])

        # Save scene beats to DynamoDB
        scene_beats = save_scene_beats(project_id, scene_plan)

        # Update project status
        update_project_status(project_id, 'planning', len(scene_beats))

        # Emit event for asset generation
        emit_scene_generation_complete_event(project_id, scene_beats)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'project_id': project_id,
                'scene_beats_count': len(scene_beats),
                'status': 'planning_complete'
            })
        }

    except Exception as e:
        print(f"Scene generation error: {str(e)}")
        update_project_status(project_id, 'failed', error=str(e))
        raise e

def generate_scene_plan(transcript, target_duration=45):
    """
    Use OpenAI GPT-4 to generate scene beats for short-form video
    """

    # Prepare transcript text with timestamps
    transcript_text = format_transcript_for_llm(transcript)

    prompt = f"""
    Create a {target_duration}-second vertical short-form video plan optimized for Instagram Reels and YouTube Shorts.

    TRANSCRIPT WITH TIMESTAMPS:
    {transcript_text}

    REQUIREMENTS:
    - Exactly {target_duration} seconds total duration
    - 3-5 dynamic visual scenes that keep viewers engaged
    - Each scene 8-15 seconds long
    - Mix of video and image generation for variety
    - Select the most engaging audio segments that tell a complete story
    - Optimize for vertical 9:16 format and mobile viewing
    - Create smooth narrative flow between scenes
    - Focus on the most interesting/valuable parts of the audio

    SCENE TYPES:
    - "video": For dynamic action, movement, or complex scenes
    - "image": For portraits, landscapes, static concepts, or text overlays

    VISUAL STYLE GUIDELINES:
    - High-quality, professional cinematography
    - Consistent visual theme throughout
    - Avoid copyrighted content or real people
    - Use descriptive, specific prompts for AI generation
    - Consider lighting, composition, and color palette

    OUTPUT FORMAT (JSON):
    {{
      "overall_theme": "Brief description of the video's visual theme and mood",
      "total_duration": {target_duration},
      "selected_audio_segments": [
        {{
          "start_time": 12.5,
          "end_time": 25.0,
          "text": "Selected transcript portion that will be used"
        }}
      ],
      "scenes": [
        {{
          "sequence": 1,
          "start_time": 0,
          "end_time": 12,
          "duration": 12,
          "audio_segment": "Exact text from transcript to sync with this scene",
          "scene_description": "Detailed description of what should be shown",
          "kling_prompt": "Optimized prompt for Kling AI generation (max 200 chars)",
          "asset_type": "video",
          "transition_style": "fade",
          "visual_notes": "Additional notes about composition, lighting, mood"
        }}
      ],
      "caption_style": "Description of how captions should be styled",
      "target_audience": "Instagram Reels / YouTube Shorts viewers",
      "engagement_hooks": ["Key moments designed to maintain attention"]
    }}

    Ensure the scene prompts are specific, creative, and optimized for AI video/image generation.
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=2000
        )

        scene_plan = json.loads(response.choices[0].message.content)

        # Validate and enhance the scene plan
        scene_plan = validate_and_enhance_scene_plan(scene_plan, target_duration)

        return scene_plan

    except Exception as e:
        print(f"LLM generation error: {str(e)}")
        raise e

def format_transcript_for_llm(transcript):
    """Format transcript with timestamps for LLM processing"""
    formatted_segments = []

    for segment in transcript['segments']:
        start_time = segment['start_time']
        end_time = segment['end_time']
        text = segment['text'].strip()

        formatted_segments.append(f"[{start_time:.1f}s - {end_time:.1f}s]: {text}")

    return "\n".join(formatted_segments)

def validate_and_enhance_scene_plan(scene_plan, target_duration):
    """Validate LLM output and enhance prompts for Kling AI"""

    # Ensure total duration matches target
    total_scene_duration = sum(scene['duration'] for scene in scene_plan['scenes'])
    if abs(total_scene_duration - target_duration) > 2:
        print(f"Warning: Scene duration mismatch. Target: {target_duration}, Actual: {total_scene_duration}")

    # Enhance Kling prompts with technical specifications
    for scene in scene_plan['scenes']:
        scene['kling_prompt'] = enhance_kling_prompt(scene['kling_prompt'], scene['asset_type'])
        scene['beat_id'] = str(uuid.uuid4())

    return scene_plan

def enhance_kling_prompt(prompt, asset_type):
    """Enhance prompts with Kling-specific optimization"""

    # Add technical specifications for Kling AI
    technical_suffix = ""

    if asset_type == "video":
        technical_suffix = " | 4K quality, smooth motion, cinematic lighting, vertical 9:16 aspect ratio"
    else:  # image
        technical_suffix = " | High resolution, professional photography, vertical composition, detailed"

    # Ensure prompt isn't too long for Kling API
    max_length = 200 - len(technical_suffix)
    if len(prompt) > max_length:
        prompt = prompt[:max_length-3] + "..."

    return prompt + technical_suffix

def save_scene_beats(project_id, scene_plan):
    """Save generated scene beats to DynamoDB"""

    scene_beats_table = dynamodb.Table(os.environ['SCENE_BEATS_TABLE'])
    scene_beats = []

    for scene in scene_plan['scenes']:
        beat_data = {
            'beat_id': scene['beat_id'],
            'project_id': project_id,
            'sequence_number': scene['sequence'],
            'start_time': scene['start_time'],
            'end_time': scene['end_time'],
            'duration': scene['duration'],
            'audio_segment': scene['audio_segment'],
            'scene_description': scene['scene_description'],
            'visual_prompt': scene['kling_prompt'],
            'asset_type': scene['asset_type'],
            'transition_style': scene['transition_style'],
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        scene_beats_table.put_item(Item=beat_data)
        scene_beats.append(beat_data)

    return scene_beats

def get_api_keys():
    """Retrieve API keys from AWS Secrets Manager"""
    try:
        response = secrets_manager.get_secret_value(
            SecretId=os.environ['SECRETS_MANAGER_ARN']
        )
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving API keys: {str(e)}")
        raise e

def get_project_data(project_id):
    """Get project data from DynamoDB"""
    projects_table = dynamodb.Table(os.environ['PROJECTS_TABLE'])
    response = projects_table.get_item(Key={'project_id': project_id})

    if 'Item' not in response:
        raise Exception(f"Project {project_id} not found")

    return response['Item']

def get_transcript_data(transcript_id):
    """Get transcript data from DynamoDB"""
    transcripts_table = dynamodb.Table(os.environ['TRANSCRIPTS_TABLE'])
    response = transcripts_table.get_item(Key={'transcript_id': transcript_id})

    if 'Item' not in response:
        raise Exception(f"Transcript {transcript_id} not found")

    return response['Item']
```

### **3. Kling AI Integration Service**

```python
# terraform/lambdas/kling-integration/index.py
import json
import boto3
import requests
import uuid
from datetime import datetime
import os
import time

dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')
s3 = boto3.client('s3')
events = boto3.client('events')

def handler(event, context):
    """
    Interface with Kling AI API for video/image generation
    Manages async generation and asset downloading
    """
    try:
        project_id = event['project_id']

        # Get API keys
        secrets = get_api_keys()
        kling_api_key = secrets['kling_api_key']

        # Get scene beats for project
        scene_beats = get_scene_beats(project_id)

        # Process each scene beat
        generated_assets = []
        for beat in scene_beats:
            if beat['status'] == 'pending':
                asset = generate_asset_for_beat(beat, kling_api_key)
                generated_assets.append(asset)

        # Start polling for completion
        setup_asset_polling(project_id, generated_assets)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'project_id': project_id,
                'assets_queued': len(generated_assets),
                'status': 'generating'
            })
        }

    except Exception as e:
        print(f"Kling integration error: {str(e)}")
        raise e

def generate_asset_for_beat(beat, kling_api_key):
    """Generate video or image asset using Kling AI API"""

    asset_id = str(uuid.uuid4())

    try:
        if beat['asset_type'] == 'video':
            task_id = generate_kling_video(beat['visual_prompt'], kling_api_key, beat['duration'])
        else:  # image
            task_id = generate_kling_image(beat['visual_prompt'], kling_api_key)

        # Create asset record
        asset_data = {
            'asset_id': asset_id,
            'beat_id': beat['beat_id'],
            'kling_task_id': task_id,
            'asset_type': beat['asset_type'],
            'status': 'generating',
            'prompt': beat['visual_prompt'],
            'generation_params': {
                'duration': beat.get('duration', 5) if beat['asset_type'] == 'video' else None,
                'aspect_ratio': '9:16',
                'quality': 'high'
            },
            'created_at': datetime.now().isoformat()
        }

        # Save to DynamoDB
        assets_table = dynamodb.Table(os.environ['GENERATED_ASSETS_TABLE'])
        assets_table.put_item(Item=asset_data)

        # Update scene beat status
        scene_beats_table = dynamodb.Table(os.environ['SCENE_BEATS_TABLE'])
        scene_beats_table.update_item(
            Key={
                'project_id': beat['project_id'],
                'sequence_number': beat['sequence_number']
            },
            UpdateExpression='SET generated_asset_id = :asset_id, #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':asset_id': asset_id,
                ':status': 'generating'
            }
        )

        return asset_data

    except Exception as e:
        print(f"Error generating asset for beat {beat['beat_id']}: {str(e)}")
        # Mark asset as failed
        asset_data = {
            'asset_id': asset_id,
            'beat_id': beat['beat_id'],
            'status': 'failed',
            'error_message': str(e),
            'created_at': datetime.now().isoformat()
        }

        assets_table = dynamodb.Table(os.environ['GENERATED_ASSETS_TABLE'])
        assets_table.put_item(Item=asset_data)

        raise e

def generate_kling_video(prompt, api_key, duration=5):
    """Call Kling AI text-to-video API"""

    url = "https://api.klingai.com/v1/videos/text2video"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "kling-v1",
        "prompt": prompt,
        "duration": min(duration, 10),  # Kling max duration
        "aspect_ratio": "9:16",
        "quality": "high",
        "fps": 30
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result["task_id"]

def generate_kling_image(prompt, api_key):
    """Call Kling AI text-to-image API"""

    url = "https://api.klingai.com/v1/images/generations"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "kling-v1",
        "prompt": prompt,
        "aspect_ratio": "9:16",
        "quality": "high",
        "style": "realistic"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result["task_id"]

def check_kling_status(task_id, api_key):
    """Check Kling AI generation status"""

    url = f"https://api.klingai.com/v1/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

def download_and_store_asset(asset_url, asset_id, asset_type):
    """Download generated asset from Kling and store in S3"""

    try:
        # Download asset from Kling
        response = requests.get(asset_url, stream=True)
        response.raise_for_status()

        # Determine file extension
        extension = '.mp4' if asset_type == 'video' else '.jpg'
        s3_key = f"ai-generated/{asset_id}{extension}"

        # Upload to S3
        s3.upload_fileobj(
            response.raw,
            os.environ['S3_BUCKET'],
            s3_key,
            ExtraArgs={
                'ContentType': 'video/mp4' if asset_type == 'video' else 'image/jpeg',
                'CacheControl': 'max-age=31536000'  # 1 year cache
            }
        )

        return f"s3://{os.environ['S3_BUCKET']}/{s3_key}"

    except Exception as e:
        print(f"Error downloading asset {asset_id}: {str(e)}")
        raise e

# Additional helper functions...
def get_api_keys():
    """Retrieve API keys from AWS Secrets Manager"""
    response = secrets_manager.get_secret_value(
        SecretId=os.environ['SECRETS_MANAGER_ARN']
    )
    return json.loads(response['SecretString'])

def get_scene_beats(project_id):
    """Get scene beats for project"""
    scene_beats_table = dynamodb.Table(os.environ['SCENE_BEATS_TABLE'])
    response = scene_beats_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('project_id').eq(project_id)
    )
    return response['Items']
```

---

## 🎨 **Vue.js Frontend Implementation (Metronic UI)**

### **New Route Structure**

```typescript
// src/router/index.ts - Add AI video generation routes
{
  path: '/ai-video',
  component: DefaultLayout,
  meta: { requiresAuth: true },
  children: [
    {
      path: '',
      name: 'AIVideoGenerator',
      component: () => import('@/views/ai-video/AIVideoGenerator.vue'),
      meta: {
        pageTitle: 'AI Video Generator',
        breadcrumbs: ['AI Tools', 'Video Generator']
      }
    },
    {
      path: 'project/:projectId',
      name: 'AIVideoProject',
      component: () => import('@/views/ai-video/AIVideoProject.vue'),
      meta: {
        pageTitle: 'AI Video Project',
        breadcrumbs: ['AI Tools', 'Video Generator', 'Project']
      }
    },
    {
      path: 'transcription/:projectId',
      name: 'TranscriptionEditor',
      component: () => import('@/views/ai-video/TranscriptionEditor.vue'),
      meta: {
        pageTitle: 'Edit Transcript',
        breadcrumbs: ['AI Tools', 'Video Generator', 'Transcript']
      }
    },
    {
      path: 'scene-editor/:projectId',
      name: 'SceneEditor',
      component: () => import('@/views/ai-video/SceneEditor.vue'),
      meta: {
        pageTitle: 'Scene Editor',
        breadcrumbs: ['AI Tools', 'Video Generator', 'Scenes']
      }
    },
    {
      path: 'compilation/:projectId',
      name: 'VideoCompilation',
      component: () => import('@/views/ai-video/VideoCompilation.vue'),
      meta: {
        pageTitle: 'Video Compilation',
        breadcrumbs: ['AI Tools', 'Video Generator', 'Compilation']
      }
    }
  ]
}
```

### **Main AI Video Generator Page**

```vue
<!-- src/views/ai-video/AIVideoGenerator.vue -->
<template>
  <div class="d-flex flex-column flex-column-fluid">
    <!-- Page Title -->
    <KTPageTitle :breadcrumbs="breadcrumbs" :description="pageDescription">
      AI Video Generator
    </KTPageTitle>

    <!-- Page Content -->
    <div id="kt_app_content" class="app-content flex-column-fluid">
      <div id="kt_app_content_container" class="app-container container-fluid">
        <!-- Project Creation Stepper -->
        <div class="card">
          <div class="card-body">
            <!-- Stepper Navigation -->
            <div
              class="stepper stepper-pills stepper-column d-flex flex-column flex-xl-row flex-row-fluid gap-10"
            >
              <!-- Stepper Nav -->
              <div
                class="card d-flex justify-content-center justify-content-xl-start flex-row-auto w-100 w-xl-300px w-xxl-400px"
              >
                <div class="card-body px-6 px-lg-10 px-xxl-15 py-20">
                  <div class="stepper-nav">
                    <!-- Step 1: Upload Audio -->
                    <div
                      class="stepper-item"
                      :class="{ current: currentStep === 1, completed: currentStep > 1 }"
                    >
                      <div class="stepper-wrapper">
                        <div class="stepper-icon w-40px h-40px">
                          <i class="ki-duotone ki-microphone-2 fs-2 stepper-check"></i>
                          <span class="stepper-number">1</span>
                        </div>
                        <div class="stepper-label">
                          <h3 class="stepper-title">Upload Audio</h3>
                          <div class="stepper-desc fw-semibold">
                            Select your audio file for processing
                          </div>
                        </div>
                      </div>
                      <div class="stepper-line h-40px"></div>
                    </div>

                    <!-- Step 2: Transcription -->
                    <div
                      class="stepper-item"
                      :class="{ current: currentStep === 2, completed: currentStep > 2 }"
                    >
                      <div class="stepper-wrapper">
                        <div class="stepper-icon w-40px h-40px">
                          <i class="ki-duotone ki-document fs-2 stepper-check"></i>
                          <span class="stepper-number">2</span>
                        </div>
                        <div class="stepper-label">
                          <h3 class="stepper-title">Review Transcript</h3>
                          <div class="stepper-desc fw-semibold">
                            Edit and refine the generated transcript
                          </div>
                        </div>
                      </div>
                      <div class="stepper-line h-40px"></div>
                    </div>

                    <!-- Step 3: Scene Planning -->
                    <div
                      class="stepper-item"
                      :class="{ current: currentStep === 3, completed: currentStep > 3 }"
                    >
                      <div class="stepper-wrapper">
                        <div class="stepper-icon w-40px h-40px">
                          <i class="ki-duotone ki-design-1 fs-2 stepper-check"></i>
                          <span class="stepper-number">3</span>
                        </div>
                        <div class="stepper-label">
                          <h3 class="stepper-title">Scene Planning</h3>
                          <div class="stepper-desc fw-semibold">
                            AI generates visual scene beats
                          </div>
                        </div>
                      </div>
                      <div class="stepper-line h-40px"></div>
                    </div>

                    <!-- Step 4: Asset Generation -->
                    <div
                      class="stepper-item"
                      :class="{ current: currentStep === 4, completed: currentStep > 4 }"
                    >
                      <div class="stepper-wrapper">
                        <div class="stepper-icon w-40px h-40px">
                          <i class="ki-duotone ki-picture fs-2 stepper-check"></i>
                          <span class="stepper-number">4</span>
                        </div>
                        <div class="stepper-label">
                          <h3 class="stepper-title">Generate Assets</h3>
                          <div class="stepper-desc fw-semibold">
                            Kling AI creates videos and images
                          </div>
                        </div>
                      </div>
                      <div class="stepper-line h-40px"></div>
                    </div>

                    <!-- Step 5: Compilation -->
                    <div
                      class="stepper-item"
                      :class="{ current: currentStep === 5, completed: currentStep > 5 }"
                    >
                      <div class="stepper-wrapper">
                        <div class="stepper-icon w-40px h-40px">
                          <i class="ki-duotone ki-media-play fs-2 stepper-check"></i>
                          <span class="stepper-number">5</span>
                        </div>
                        <div class="stepper-label">
                          <h3 class="stepper-title">Final Video</h3>
                          <div class="stepper-desc fw-semibold">
                            Compile and download your video
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Stepper Content -->
              <div class="flex-row-fluid py-lg-5 px-lg-15">
                <!-- Step 1: Audio Upload -->
                <div v-if="currentStep === 1" class="current" data-kt-stepper-element="content">
                  <div class="w-100">
                    <AIAudioUploader
                      @upload-complete="handleAudioUploaded"
                      @upload-progress="handleUploadProgress"
                      :is-uploading="isUploading"
                    />
                  </div>
                </div>

                <!-- Step 2: Transcription Review -->
                <div v-if="currentStep === 2" class="current" data-kt-stepper-element="content">
                  <div class="w-100">
                    <TranscriptionReviewer
                      :project="currentProject"
                      @transcription-approved="handleTranscriptionApproved"
                      @transcription-edited="handleTranscriptionEdited"
                    />
                  </div>
                </div>

                <!-- Step 3: Scene Planning -->
                <div v-if="currentStep === 3" class="current" data-kt-stepper-element="content">
                  <div class="w-100">
                    <ScenePlanningWidget
                      :project="currentProject"
                      @scene-generation-complete="handleSceneGenerationComplete"
                      @scene-beats-edited="handleSceneBeatsEdited"
                    />
                  </div>
                </div>

                <!-- Step 4: Asset Generation -->
                <div v-if="currentStep === 4" class="current" data-kt-stepper-element="content">
                  <div class="w-100">
                    <AssetGenerationMonitor
                      :project="currentProject"
                      @assets-ready="handleAssetsReady"
                    />
                  </div>
                </div>

                <!-- Step 5: Video Compilation -->
                <div v-if="currentStep === 5" class="current" data-kt-stepper-element="content">
                  <div class="w-100">
                    <VideoCompilationWidget
                      :project="currentProject"
                      @compilation-complete="handleCompilationComplete"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAIVideoStore } from '@/stores/aiVideo'
import type { AudioProject } from '@/types/aiVideo'

// Import Metronic components
import KTPageTitle from '@/layouts/default-layout/components/page-title/PageTitle.vue'

// Import AI Video components
import AIAudioUploader from '@/components/ai-video/AIAudioUploader.vue'
import TranscriptionReviewer from '@/components/ai-video/TranscriptionReviewer.vue'
import ScenePlanningWidget from '@/components/ai-video/ScenePlanningWidget.vue'
import AssetGenerationMonitor from '@/components/ai-video/AssetGenerationMonitor.vue'
import VideoCompilationWidget from '@/components/ai-video/VideoCompilationWidget.vue'

const route = useRoute()
const router = useRouter()
const aiVideoStore = useAIVideoStore()

// Component state
const currentStep = ref(1)
const currentProject = ref<AudioProject | null>(null)
const isUploading = ref(false)

// Computed properties
const breadcrumbs = computed(() => [
  { title: 'AI Tools', path: '/ai-video' },
  { title: 'Video Generator', path: '/ai-video' },
])

const pageDescription = computed(
  () => 'Transform audio into engaging short-form videos with AI-powered visual generation',
)

// Event handlers
const handleAudioUploaded = async (project: AudioProject) => {
  currentProject.value = project
  currentStep.value = 2

  // Start transcription process
  await aiVideoStore.startTranscription(project.project_id)
}

const handleUploadProgress = (progress: number) => {
  isUploading.value = progress < 100
}

const handleTranscriptionApproved = async () => {
  currentStep.value = 3

  // Start scene generation
  if (currentProject.value) {
    await aiVideoStore.generateSceneBeats(currentProject.value.project_id)
  }
}

const handleTranscriptionEdited = async (editedTranscript: any) => {
  if (currentProject.value) {
    await aiVideoStore.updateTranscript(currentProject.value.transcript_id, editedTranscript)
  }
}

const handleSceneGenerationComplete = () => {
  currentStep.value = 4
}

const handleSceneBeatsEdited = async (editedBeats: any[]) => {
  if (currentProject.value) {
    await aiVideoStore.updateSceneBeats(currentProject.value.project_id, editedBeats)
  }
}

const handleAssetsReady = () => {
  currentStep.value = 5
}

const handleCompilationComplete = (finalVideoUrl: string) => {
  // Navigate to project overview or success page
  router.push(`/ai-video/project/${currentProject.value?.project_id}`)
}

// Lifecycle
onMounted(async () => {
  // Check if we have a project ID in route params
  const projectId = route.params.projectId as string
  if (projectId) {
    currentProject.value = await aiVideoStore.getProject(projectId)

    // Determine current step based on project status
    if (currentProject.value) {
      switch (currentProject.value.status) {
        case 'uploaded':
          currentStep.value = 1
          break
        case 'transcribing':
        case 'transcribed':
          currentStep.value = 2
          break
        case 'planning':
          currentStep.value = 3
          break
        case 'generating':
          currentStep.value = 4
          break
        case 'compiling':
        case 'completed':
          currentStep.value = 5
          break
        default:
          currentStep.value = 1
      }
    }
  }
})

// Watch for project status changes
watch(
  () => currentProject.value?.status,
  (newStatus) => {
    if (newStatus === 'transcribing') {
      // Poll for transcription completion
      aiVideoStore.pollTranscriptionStatus(currentProject.value!.project_id)
    }
  },
)
</script>

<style scoped>
.stepper-item.current .stepper-icon {
  background-color: var(--bs-primary);
  color: white;
}

.stepper-item.completed .stepper-icon {
  background-color: var(--bs-success);
  color: white;
}

.stepper-item .stepper-icon {
  background-color: var(--bs-light);
  color: var(--bs-gray-600);
}
</style>
```

### **Audio Uploader Component (Metronic Styled)**

```vue
<!-- src/components/ai-video/AIAudioUploader.vue -->
<template>
  <div class="card mb-5 mb-xl-10">
    <div class="card-header border-0 cursor-pointer">
      <div class="card-title m-0">
        <h3 class="fw-bold m-0">Upload Audio File</h3>
      </div>
    </div>

    <div class="card-body">
      <div class="notice d-flex bg-light-info rounded border-info border border-dashed p-6 mb-9">
        <i class="ki-duotone ki-information-5 fs-2tx text-info me-4">
          <span class="path1"></span>
          <span class="path2"></span>
          <span class="path3"></span>
        </i>
        <div class="d-flex flex-stack flex-grow-1">
          <div class="fw-semibold">
            <h4 class="text-gray-900 fw-bold">Audio Requirements</h4>
            <div class="fs-6 text-gray-700">
              • Supported formats: MP3, WAV, M4A, AAC<br />
              • Maximum duration: 10 minutes<br />
              • Maximum file size: 100MB<br />
              • Clear audio quality recommended for best transcription
            </div>
          </div>
        </div>
      </div>

      <!-- Dropzone -->
      <div class="dropzone-wrapper">
        <div
          class="dropzone dropzone-queue"
          :class="{ 'dz-drag-hover': isDragOver }"
          @drop="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragenter.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @click="triggerFileInput"
        >
          <div class="dropzone-panel mb-4">
            <a class="dropzone-select btn btn-sm btn-primary me-2">Select files</a>
            <span class="dropzone-filename text-muted">or drag and drop your audio file here</span>
          </div>

          <div class="dropzone-items">
            <div class="dropzone-item" v-if="!selectedFile">
              <div class="dropzone-toolbar">
                <i class="ki-duotone ki-microphone-2 fs-2x text-primary">
                  <span class="path1"></span>
                  <span class="path2"></span>
                </i>
              </div>
              <div class="dropzone-content">
                <div class="text-dark fw-bold fs-6 mb-2">Drop audio files here</div>
                <div class="text-muted fs-7">Maximum file size: 100MB</div>
              </div>
            </div>

            <!-- Selected File Preview -->
            <div class="dropzone-item" v-if="selectedFile">
              <div class="dropzone-toolbar">
                <i class="ki-duotone ki-musical-note fs-3x text-success me-3">
                  <span class="path1"></span>
                  <span class="path2"></span>
                  <span class="path3"></span>
                </i>
              </div>
              <div class="dropzone-content flex-grow-1">
                <div class="fw-bold text-gray-900 fs-6">{{ selectedFile.name }}</div>
                <div class="text-muted fs-7 mb-2">
                  {{ formatFileSize(selectedFile.size) }} • {{ formatDuration(audioDuration) }}
                </div>

                <!-- Audio Preview -->
                <audio
                  ref="audioPreview"
                  controls
                  class="w-100 mb-3"
                  @loadedmetadata="handleAudioLoaded"
                  style="height: 40px;"
                >
                  <source :src="audioPreviewUrl" :type="selectedFile.type" />
                </audio>

                <!-- Project Configuration -->
                <div class="row g-3 mb-4">
                  <div class="col-md-6">
                    <label class="form-label required">Project Name</label>
                    <input
                      type="text"
                      class="form-control form-control-sm"
                      v-model="projectName"
                      placeholder="Enter project name"
                      required
                    />
                  </div>
                  <div class="col-md-6">
                    <label class="form-label required">Target Duration</label>
                    <select class="form-select form-select-sm" v-model="targetDuration">
                      <option value="30">30 seconds</option>
                      <option value="45" selected>45 seconds</option>
                      <option value="60">60 seconds</option>
                    </select>
                  </div>
                </div>

                <!-- Upload Progress -->
                <div v-if="isUploading" class="mb-3">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="fs-7 text-muted">Uploading...</span>
                    <span class="fs-7 text-muted">{{ Math.round(uploadProgress) }}%</span>
                  </div>
                  <div class="progress h-6px">
                    <div
                      class="progress-bar"
                      :style="{ width: `${uploadProgress}%` }"
                      :class="{ 'progress-bar-animated': isUploading }"
                    ></div>
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="d-flex justify-content-between">
                  <button
                    type="button"
                    class="btn btn-light btn-sm"
                    @click="removeFile"
                    :disabled="isUploading"
                  >
                    <i class="ki-duotone ki-trash fs-5">
                      <span class="path1"></span>
                      <span class="path2"></span>
                      <span class="path3"></span>
                      <span class="path4"></span>
                      <span class="path5"></span>
                    </i>
                    Remove
                  </button>

                  <button
                    type="button"
                    class="btn btn-primary btn-sm"
                    @click="startUpload"
                    :disabled="!canUpload || isUploading"
                  >
                    <span v-if="!isUploading">
                      <i class="ki-duotone ki-arrow-up fs-5 me-1">
                        <span class="path1"></span>
                        <span class="path2"></span>
                      </i>
                      Upload & Process
                    </span>
                    <span v-else>
                      <span class="spinner-border spinner-border-sm me-2"></span>
                      Processing...
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hidden file input -->
        <input
          ref="fileInput"
          type="file"
          accept="audio/*"
          style="display: none"
          @change="handleFileSelect"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useAIVideoStore } from '@/stores/aiVideo'
import { useVideoUpload } from '@/composables/useVideoUpload'
import type { AudioProject } from '@/types/aiVideo'

// Emits
const emit = defineEmits<{
  'upload-complete': [project: AudioProject]
  'upload-progress': [progress: number]
}>()

// Store and composables
const aiVideoStore = useAIVideoStore()
const { uploadVideo, uploadProgress } = useVideoUpload()

// Component state
const selectedFile = ref<File | null>(null)
const audioPreviewUrl = ref<string>('')
const audioDuration = ref<number>(0)
const isDragOver = ref(false)
const isUploading = ref(false)
const projectName = ref('')
const targetDuration = ref(45)

// Refs
const fileInput = ref<HTMLInputElement>()
const audioPreview = ref<HTMLAudioElement>()

// Computed
const canUpload = computed(
  () => selectedFile.value && projectName.value.trim().length > 0 && !isUploading.value,
)

const uploadProgress = computed(() => {
  if (!selectedFile.value) return 0
  const progress = uploadProgress.value.get(selectedFile.value.name)
  return progress?.percentage || 0
})

// Methods
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    setSelectedFile(input.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false

  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    setSelectedFile(event.dataTransfer.files[0])
  }
}

const setSelectedFile = (file: File) => {
  // Validate file type
  const validTypes = ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/aac', 'audio/ogg']
  if (!validTypes.includes(file.type)) {
    alert('Please select a valid audio file (MP3, WAV, M4A, AAC, OGG)')
    return
  }

  // Validate file size (100MB)
  if (file.size > 100 * 1024 * 1024) {
    alert('File size must be less than 100MB')
    return
  }

  selectedFile.value = file
  audioPreviewUrl.value = URL.createObjectURL(file)

  // Auto-generate project name from filename
  if (!projectName.value) {
    projectName.value = file.name.replace(/\.[^/.]+$/, '')
  }
}

const handleAudioLoaded = () => {
  if (audioPreview.value) {
    audioDuration.value = audioPreview.value.duration
  }
}

const removeFile = () => {
  if (audioPreviewUrl.value) {
    URL.revokeObjectURL(audioPreviewUrl.value)
  }

  selectedFile.value = null
  audioPreviewUrl.value = ''
  audioDuration.value = 0
  projectName.value = ''
}

const startUpload = async () => {
  if (!selectedFile.value || !canUpload.value) return

  try {
    isUploading.value = true

    // Create project record
    const project = await aiVideoStore.createProject({
      title: projectName.value,
      target_duration: targetDuration.value,
      audio_duration: audioDuration.value,
    })

    // Upload audio file
    const s3Key = `audio-projects/${project.project_id}/${selectedFile.value.name}`

    await uploadVideo(selectedFile.value, {
      video_id: project.project_id,
      title: projectName.value,
      filename: selectedFile.value.name,
      bucket_location: s3Key,
      user_id: project.user_id,
      user_email: project.user_email || '',
      upload_date: new Date().toISOString(),
      file_size: selectedFile.value.size,
      content_type: selectedFile.value.type,
      duration: audioDuration.value,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // Update project with audio file URL
    await aiVideoStore.updateProject(project.project_id, {
      audio_file_url: s3Key,
      status: 'uploaded',
    })

    emit('upload-complete', project)
  } catch (error) {
    console.error('Upload failed:', error)
    alert('Upload failed. Please try again.')
  } finally {
    isUploading.value = false
  }
}

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Cleanup
onUnmounted(() => {
  if (audioPreviewUrl.value) {
    URL.revokeObjectURL(audioPreviewUrl.value)
  }
})
</script>

<style scoped>
.dropzone {
  border: 2px dashed var(--bs-border-color);
  border-radius: var(--bs-border-radius);
  background-color: var(--bs-light);
  cursor: pointer;
  transition: all 0.3s ease;
}

.dropzone:hover,
.dropzone.dz-drag-hover {
  border-color: var(--bs-primary);
  background-color: var(--bs-primary-bg-subtle);
}

.dropzone-item {
  display: flex;
  align-items: flex-start;
  padding: 1.5rem;
  gap: 1rem;
}

.dropzone-content {
  flex-grow: 1;
}

.progress {
  background-color: var(--bs-light);
}

.progress-bar {
  background-color: var(--bs-primary);
}
</style>
```

---

## 🐍 **Python Video Processing Module (ECS/Fargate)**

### **Docker Container Setup**

```dockerfile
# terraform/video-processor/Dockerfile
FROM python:3.11-slim

# Install system dependencies for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    fonts-dejavu-core \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./

# Create directories for temporary processing
RUN mkdir -p /tmp/video-processing /tmp/assets

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
```

### **Python Requirements**

```txt
# terraform/video-processor/requirements.txt
boto3==1.34.0
ffmpeg-python==0.2.0
pillow==10.1.0
requests==2.31.0
python-dotenv==1.0.0
moviepy==1.0.3
opencv-python==4.8.1.78
numpy==1.24.4
pydub==0.25.1
```

### **Main Video Processing Pipeline**

```python
# terraform/video-processor/src/main.py
import os
import json
import boto3
import logging
from datetime import datetime
from video_compiler import VideoCompiler
from audio_processor import AudioProcessor
from caption_generator import CaptionGenerator
from asset_downloader import AssetDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIVideoProcessor:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')

        # Initialize processors
        self.video_compiler = VideoCompiler()
        self.audio_processor = AudioProcessor()
        self.caption_generator = CaptionGenerator()
        self.asset_downloader = AssetDownloader()

        # Environment variables
        self.bucket_name = os.environ['S3_BUCKET']
        self.projects_table = self.dynamodb.Table(os.environ['PROJECTS_TABLE'])
        self.scene_beats_table = self.dynamodb.Table(os.environ['SCENE_BEATS_TABLE'])
        self.generated_assets_table = self.dynamodb.Table(os.environ['GENERATED_ASSETS_TABLE'])

    def process_project(self, project_id: str):
        """Main entry point for video compilation"""

        try:
            logger.info(f"Starting video processing for project {project_id}")

            # Update project status
            self.update_project_status(project_id, 'compiling')

            # 1. Load project data
            project_data = self.load_project_data(project_id)
            scene_beats = self.load_scene_beats(project_id)
            generated_assets = self.load_generated_assets(project_id)

            # 2. Download all assets and audio
            local_assets = self.asset_downloader.download_all_assets(
                project_data, scene_beats, generated_assets
            )

            # 3. Process audio segments
            audio_segments = self.audio_processor.extract_audio_segments(
                local_assets['audio_file'], scene_beats
            )

            # 4. Generate captions
            captions = self.caption_generator.generate_captions(
                scene_beats, project_data['target_duration']
            )

            # 5. Compile final video
            final_video_path = self.video_compiler.compile_video(
                scene_beats, local_assets, audio_segments, captions, project_data
            )

            # 6. Upload final video to S3
            final_video_url = self.upload_final_video(project_id, final_video_path)

            # 7. Update project with completion
            self.update_project_status(project_id, 'completed', final_video_url)

            logger.info(f"Video processing completed for project {project_id}")

            return {
                'status': 'success',
                'final_video_url': final_video_url
            }

        except Exception as e:
            logger.error(f"Video processing failed for project {project_id}: {str(e)}")
            self.update_project_status(project_id, 'failed', error=str(e))
            raise e

        finally:
            # Cleanup temporary files
            self.cleanup_temp_files()

    def load_project_data(self, project_id: str):
        """Load project data from DynamoDB"""
        response = self.projects_table.get_item(Key={'project_id': project_id})
        if 'Item' not in response:
            raise Exception(f"Project {project_id} not found")
        return response['Item']

    def load_scene_beats(self, project_id: str):
        """Load scene beats for project"""
        response = self.scene_beats_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('project_id').eq(project_id),
            ScanIndexForward=True  # Sort by sequence_number
        )
        return response['Items']

    def load_generated_assets(self, project_id: str):
        """Load generated assets for all scene beats"""
        # Get all scene beats first
        scene_beats = self.load_scene_beats(project_id)

        assets = {}
        for beat in scene_beats:
            if 'generated_asset_id' in beat:
                response = self.generated_assets_table.get_item(
                    Key={'asset_id': beat['generated_asset_id']}
                )
                if 'Item' in response:
                    assets[beat['beat_id']] = response['Item']

        return assets

    def upload_final_video(self, project_id: str, video_path: str):
        """Upload final compiled video to S3"""
        s3_key = f"final-videos/{project_id}/final_video.mp4"

        with open(video_path, 'rb') as video_file:
            self.s3.upload_fileobj(
                video_file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'CacheControl': 'max-age=31536000',  # 1 year
                    'Metadata': {
                        'project_id': project_id,
                        'generated_at': datetime.now().isoformat()
                    }
                }
            )

        return f"s3://{self.bucket_name}/{s3_key}"

    def update_project_status(self, project_id: str, status: str, final_video_url: str = None, error: str = None):
        """Update project status in DynamoDB"""
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_values = {
            ':status': status,
            ':updated_at': datetime.now().isoformat()
        }
        expression_names = {'#status': 'status'}

        if final_video_url:
            update_expression += ", final_video_url = :final_video_url"
            expression_values[':final_video_url'] = final_video_url

        if error:
            update_expression += ", error_message = :error"
            expression_values[':error'] = error

        self.projects_table.update_item(
            Key={'project_id': project_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )

    def cleanup_temp_files(self):
        """Clean up temporary processing files"""
        import shutil
        temp_dirs = ['/tmp/video-processing', '/tmp/assets']

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)

if __name__ == "__main__":
    # Get project ID from environment or command line
    project_id = os.environ.get('PROJECT_ID')

    if not project_id:
        logger.error("PROJECT_ID environment variable is required")
        exit(1)

    # Process the video
    processor = AIVideoProcessor()
    result = processor.process_project(project_id)

    logger.info(f"Processing result: {result}")
```

### **Video Compiler Implementation**

```python
# terraform/video-processor/src/video_compiler.py
import ffmpeg
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VideoCompiler:
    def __init__(self):
        self.target_resolution = (1080, 1920)  # 9:16 vertical
        self.target_fps = 30
        self.output_format = 'mp4'
        self.temp_dir = '/tmp/video-processing'

    def compile_video(self, scene_beats: List[Dict], local_assets: Dict,
                     audio_segments: List[str], captions: Dict, project_data: Dict) -> str:
        """
        Compile final video from all components

        Returns: Path to final video file
        """

        try:
            logger.info("Starting video compilation")

            # Create temporary directory
            os.makedirs(self.temp_dir, exist_ok=True)

            # 1. Prepare video clips for each scene
            video_clips = self.prepare_video_clips(scene_beats, local_assets)

            # 2. Sync video clips with audio segments
            synced_clips = self.sync_clips_with_audio(video_clips, audio_segments, scene_beats)

            # 3. Add transitions between clips
            transitioned_clips = self.add_transitions(synced_clips, scene_beats)

            # 4. Concatenate all clips
            concat_video = self.concatenate_clips(transitioned_clips)

            # 5. Add captions overlay
            final_video = self.add_captions_overlay(concat_video, captions, project_data)

            # 6. Final encoding and optimization
            output_path = self.final_encode(final_video, project_data)

            logger.info(f"Video compilation completed: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video compilation failed: {str(e)}")
            raise e

    def prepare_video_clips(self, scene_beats: List[Dict], local_assets: Dict) -> List[str]:
        """Prepare individual video clips for each scene beat"""

        video_clips = []

        for i, beat in enumerate(scene_beats):
            asset_path = local_assets.get(beat['beat_id'])

            if not asset_path or not os.path.exists(asset_path):
                logger.warning(f"Asset not found for beat {beat['beat_id']}, creating placeholder")
                asset_path = self.create_placeholder_clip(beat)

            # Process based on asset type
            if beat['asset_type'] == 'video':
                processed_clip = self.process_video_clip(asset_path, beat, i)
            else:  # image
                processed_clip = self.process_image_clip(asset_path, beat, i)

            video_clips.append(processed_clip)

        return video_clips

    def process_video_clip(self, video_path: str, beat: Dict, index: int) -> str:
        """Process video clip to match specifications"""

        output_path = f"{self.temp_dir}/clip_{index:03d}_video.mp4"

        try:
            # Get video info
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

            input_stream = ffmpeg.input(video_path)

            # Apply transformations
            video_stream = (
                input_stream
                .filter('scale', self.target_resolution[0], self.target_resolution[1], force_original_aspect_ratio='decrease')
                .filter('pad', self.target_resolution[0], self.target_resolution[1], '(ow-iw)/2', '(oh-ih)/2', color='black')
                .filter('fps', fps=self.target_fps)
                .filter('setpts', f'PTS*{beat["duration"]}/{float(video_info.get("duration", beat["duration"]))}')  # Time scaling
            )

            # Output with specific duration
            output = ffmpeg.output(
                video_stream,
                output_path,
                vcodec='libx264',
                acodec='aac',
                t=beat['duration'],
                r=self.target_fps,
                preset='fast',
                crf=23
            )

            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error processing video clip {video_path}: {str(e)}")
            return self.create_placeholder_clip(beat)

    def process_image_clip(self, image_path: str, beat: Dict, index: int) -> str:
        """Convert image to video clip with specified duration"""

        output_path = f"{self.temp_dir}/clip_{index:03d}_image.mp4"

        try:
            input_stream = ffmpeg.input(image_path, loop=1, t=beat['duration'], framerate=self.target_fps)

            # Apply transformations
            video_stream = (
                input_stream
                .filter('scale', self.target_resolution[0], self.target_resolution[1], force_original_aspect_ratio='decrease')
                .filter('pad', self.target_resolution[0], self.target_resolution[1], '(ow-iw)/2', '(oh-ih)/2', color='black')
                .filter('zoompan', z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))', d=25*beat['duration'], s=f'{self.target_resolution[0]}x{self.target_resolution[1]}')  # Ken Burns effect
            )

            output = ffmpeg.output(
                video_stream,
                output_path,
                vcodec='libx264',
                preset='fast',
                crf=23,
                pix_fmt='yuv420p'
            )

            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error processing image clip {image_path}: {str(e)}")
            return self.create_placeholder_clip(beat)

    def create_placeholder_clip(self, beat: Dict) -> str:
        """Create placeholder clip when asset is missing"""

        output_path = f"{self.temp_dir}/placeholder_{beat['sequence_number']}.mp4"

        # Create colored background with text
        input_stream = ffmpeg.input('color=c=gray:s=1080x1920:d=' + str(beat['duration']), f='lavfi')

        # Add text overlay
        text_filter = (
            input_stream
            .filter('drawtext',
                   text=f"Scene {beat['sequence_number']}\\n{beat['scene_description'][:50]}...",
                   fontfile='/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
                   fontsize=48,
                   fontcolor='white',
                   x='(w-text_w)/2',
                   y='(h-text_h)/2',
                   borderw=2,
                   bordercolor='black')
        )

        output = ffmpeg.output(text_filter, output_path, vcodec='libx264', preset='fast', crf=23)
        ffmpeg.run(output, overwrite_output=True, quiet=True)

        return output_path

    def sync_clips_with_audio(self, video_clips: List[str], audio_segments: List[str], scene_beats: List[Dict]) -> List[str]:
        """Sync video clips with corresponding audio segments"""

        synced_clips = []

        for i, (video_clip, audio_segment, beat) in enumerate(zip(video_clips, audio_segments, scene_beats)):
            output_path = f"{self.temp_dir}/synced_{i:03d}.mp4"

            try:
                video_input = ffmpeg.input(video_clip)
                audio_input = ffmpeg.input(audio_segment)

                output = ffmpeg.output(
                    video_input['v'],
                    audio_input['a'],
                    output_path,
                    vcodec='copy',
                    acodec='aac',
                    shortest=None  # Use shorter of video or audio
                )

                ffmpeg.run(output, overwrite_output=True, quiet=True)
                synced_clips.append(output_path)

            except Exception as e:
                logger.error(f"Error syncing clip {i}: {str(e)}")
                synced_clips.append(video_clip)  # Fallback to original video

        return synced_clips

    def add_transitions(self, video_clips: List[str], scene_beats: List[Dict]) -> List[str]:
        """Add transitions between video clips"""

        if len(video_clips) <= 1:
            return video_clips

        transitioned_clips = []
        transition_duration = 0.5  # 500ms transitions

        for i in range(len(video_clips) - 1):
            current_clip = video_clips[i]
            next_clip = video_clips[i + 1]
            transition_style = scene_beats[i].get('transition_style', 'fade')

            # Create transition
            transition_path = self.create_transition(
                current_clip, next_clip, transition_style, transition_duration, i
            )

            transitioned_clips.append(transition_path)

        # Add the last clip
        transitioned_clips.append(video_clips[-1])

        return transitioned_clips

    def create_transition(self, clip1: str, clip2: str, style: str, duration: float, index: int) -> str:
        """Create transition between two clips"""

        output_path = f"{self.temp_dir}/transition_{index:03d}.mp4"

        try:
            input1 = ffmpeg.input(clip1)
            input2 = ffmpeg.input(clip2)

            if style == 'fade':
                # Crossfade transition
                transition = ffmpeg.filter([input1, input2], 'xfade', transition='fade', duration=duration, offset=duration)
            elif style == 'slide':
                # Slide transition
                transition = ffmpeg.filter([input1, input2], 'xfade', transition='slideleft', duration=duration, offset=duration)
            else:
                # Default fade
                transition = ffmpeg.filter([input1, input2], 'xfade', transition='fade', duration=duration, offset=duration)

            output = ffmpeg.output(transition, output_path, vcodec='libx264', preset='fast', crf=23)
            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error creating transition {index}: {str(e)}")
            return clip1  # Fallback to first clip

    def concatenate_clips(self, video_clips: List[str]) -> str:
        """Concatenate all video clips into single video"""

        output_path = f"{self.temp_dir}/concatenated.mp4"

        # Create concat file for ffmpeg
        concat_file = f"{self.temp_dir}/concat_list.txt"
        with open(concat_file, 'w') as f:
            for clip in video_clips:
                f.write(f"file '{clip}'\n")

        try:
            input_stream = ffmpeg.input(concat_file, format='concat', safe=0)
            output = ffmpeg.output(input_stream, output_path, vcodec='copy', acodec='copy')
            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error concatenating clips: {str(e)}")
            raise e

    def add_captions_overlay(self, video_path: str, captions: Dict, project_data: Dict) -> str:
        """Add captions overlay to video"""

        output_path = f"{self.temp_dir}/with_captions.mp4"

        try:
            # Generate subtitle file
            subtitle_file = self.create_subtitle_file(captions)

            input_stream = ffmpeg.input(video_path)

            # Add subtitle overlay with safe zone positioning
            video_with_subs = input_stream.filter(
                'subtitles',
                subtitle_file,
                force_style='FontName=DejaVu Sans Bold,FontSize=36,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=200'
            )

            output = ffmpeg.output(video_with_subs, output_path, vcodec='libx264', preset='fast', crf=23)
            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error adding captions: {str(e)}")
            return video_path  # Return original video without captions

    def create_subtitle_file(self, captions: Dict) -> str:
        """Create SRT subtitle file"""

        subtitle_path = f"{self.temp_dir}/captions.srt"

        with open(subtitle_path, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(captions.get('segments', []), 1):
                start_time = self.format_timestamp(caption['start_time'])
                end_time = self.format_timestamp(caption['end_time'])
                text = caption['text'].strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        return subtitle_path

    def format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def final_encode(self, video_path: str, project_data: Dict) -> str:
        """Final encoding and optimization for social media"""

        output_path = f"{self.temp_dir}/final_video.mp4"

        try:
            input_stream = ffmpeg.input(video_path)

            # Optimize for social media platforms
            output = ffmpeg.output(
                input_stream,
                output_path,
                vcodec='libx264',
                acodec='aac',
                preset='slow',  # Better compression
                crf=20,  # High quality
                movflags='faststart',  # Web optimization
                pix_fmt='yuv420p',  # Compatibility
                r=self.target_fps,
                s=f'{self.target_resolution[0]}x{self.target_resolution[1]}',
                audio_bitrate='128k',
                video_bitrate='2000k'
            )

            ffmpeg.run(output, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            logger.error(f"Error in final encoding: {str(e)}")
            raise e
```

---

## 📈 **Pinia Store Implementation**

### **AI Video Store**

```typescript
// src/stores/aiVideo.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { AIVideoService } from '@/core/services/AIVideoService'
import type { AudioProject, TranscriptData, SceneBeat, GeneratedAsset } from '@/types/aiVideo'

export const useAIVideoStore = defineStore('aiVideo', () => {
  // State
  const projects = ref<AudioProject[]>([])
  const currentProject = ref<AudioProject | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Processing states
  const transcriptionStatus = ref<Map<string, string>>(new Map())
  const sceneGenerationStatus = ref<Map<string, string>>(new Map())
  const assetGenerationStatus = ref<Map<string, GeneratedAsset[]>>(new Map())
  const compilationStatus = ref<Map<string, string>>(new Map())

  // Computed
  const userProjects = computed(() => projects.value.filter((p) => p.status !== 'failed'))

  const completedProjects = computed(() => projects.value.filter((p) => p.status === 'completed'))

  const processingProjects = computed(() =>
    projects.value.filter((p) =>
      ['transcribing', 'planning', 'generating', 'compiling'].includes(p.status),
    ),
  )

  // Actions
  const createProject = async (projectData: {
    title: string
    target_duration: number
    audio_duration: number
  }): Promise<AudioProject> => {
    try {
      isLoading.value = true
      error.value = null

      const project = await AIVideoService.createProject(projectData)
      projects.value.unshift(project)
      currentProject.value = project

      return project
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateProject = async (projectId: string, updates: Partial<AudioProject>) => {
    try {
      const updatedProject = await AIVideoService.updateProject(projectId, updates)

      // Update in local state
      const index = projects.value.findIndex((p) => p.project_id === projectId)
      if (index !== -1) {
        projects.value[index] = { ...projects.value[index], ...updatedProject }
      }

      if (currentProject.value?.project_id === projectId) {
        currentProject.value = { ...currentProject.value, ...updatedProject }
      }

      return updatedProject
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update project'
      throw err
    }
  }

  const loadProjects = async () => {
    try {
      isLoading.value = true
      error.value = null

      const userProjects = await AIVideoService.getUserProjects()
      projects.value = userProjects
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load projects'
      console.error('Failed to load AI video projects:', err)
    } finally {
      isLoading.value = false
    }
  }

  const getProject = async (projectId: string): Promise<AudioProject | null> => {
    try {
      // Check if project is already loaded
      let project = projects.value.find((p) => p.project_id === projectId)

      if (!project) {
        project = await AIVideoService.getProject(projectId)
        if (project) {
          projects.value.unshift(project)
        }
      }

      currentProject.value = project || null
      return project || null
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load project'
      return null
    }
  }

  const startTranscription = async (projectId: string) => {
    try {
      transcriptionStatus.value.set(projectId, 'starting')

      await AIVideoService.startTranscription(projectId)

      transcriptionStatus.value.set(projectId, 'transcribing')

      // Start polling for completion
      pollTranscriptionStatus(projectId)
    } catch (err) {
      transcriptionStatus.value.set(projectId, 'failed')
      error.value = err instanceof Error ? err.message : 'Failed to start transcription'
      throw err
    }
  }

  const pollTranscriptionStatus = async (projectId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const project = await AIVideoService.getProject(projectId)

        if (project) {
          await updateProject(projectId, project)

          if (project.status === 'transcribed') {
            transcriptionStatus.value.set(projectId, 'completed')
            clearInterval(pollInterval)
          } else if (project.status === 'failed') {
            transcriptionStatus.value.set(projectId, 'failed')
            clearInterval(pollInterval)
          }
        }
      } catch (err) {
        console.error('Error polling transcription status:', err)
        clearInterval(pollInterval)
      }
    }, 5000) // Poll every 5 seconds

    // Stop polling after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval)
    }, 600000)
  }

  const generateSceneBeats = async (projectId: string) => {
    try {
      sceneGenerationStatus.value.set(projectId, 'generating')

      const sceneBeats = await AIVideoService.generateSceneBeats(projectId)

      sceneGenerationStatus.value.set(projectId, 'completed')

      return sceneBeats
    } catch (err) {
      sceneGenerationStatus.value.set(projectId, 'failed')
      error.value = err instanceof Error ? err.message : 'Failed to generate scene beats'
      throw err
    }
  }

  const updateSceneBeats = async (projectId: string, sceneBeats: SceneBeat[]) => {
    try {
      await AIVideoService.updateSceneBeats(projectId, sceneBeats)

      // Update local state if needed
      if (currentProject.value?.project_id === projectId) {
        currentProject.value.scene_beats_count = sceneBeats.length
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update scene beats'
      throw err
    }
  }

  const generateAssets = async (projectId: string) => {
    try {
      assetGenerationStatus.value.set(projectId, [])

      const assets = await AIVideoService.generateAssets(projectId)
      assetGenerationStatus.value.set(projectId, assets)

      // Start polling for asset completion
      pollAssetGeneration(projectId)

      return assets
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to start asset generation'
      throw err
    }
  }

  const pollAssetGeneration = async (projectId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const assets = await AIVideoService.getProjectAssets(projectId)
        assetGenerationStatus.value.set(projectId, assets)

        // Check if all assets are completed
        const allCompleted = assets.every((asset) => ['completed', 'failed'].includes(asset.status))

        if (allCompleted) {
          clearInterval(pollInterval)

          // Check if any assets failed
          const hasFailures = assets.some((asset) => asset.status === 'failed')
          if (!hasFailures) {
            // All assets completed successfully, ready for compilation
            await updateProject(projectId, { status: 'ready_for_compilation' })
          }
        }
      } catch (err) {
        console.error('Error polling asset generation:', err)
        clearInterval(pollInterval)
      }
    }, 10000) // Poll every 10 seconds

    // Stop polling after 30 minutes
    setTimeout(() => {
      clearInterval(pollInterval)
    }, 1800000)
  }

  const compileVideo = async (projectId: string) => {
    try {
      compilationStatus.value.set(projectId, 'compiling')

      const result = await AIVideoService.compileVideo(projectId)

      compilationStatus.value.set(projectId, 'completed')

      // Update project with final video URL
      await updateProject(projectId, {
        status: 'completed',
        final_video_url: result.final_video_url,
      })

      return result
    } catch (err) {
      compilationStatus.value.set(projectId, 'failed')
      error.value = err instanceof Error ? err.message : 'Failed to compile video'
      throw err
    }
  }

  const deleteProject = async (projectId: string) => {
    try {
      await AIVideoService.deleteProject(projectId)

      // Remove from local state
      projects.value = projects.value.filter((p) => p.project_id !== projectId)

      if (currentProject.value?.project_id === projectId) {
        currentProject.value = null
      }

      // Clean up status maps
      transcriptionStatus.value.delete(projectId)
      sceneGenerationStatus.value.delete(projectId)
      assetGenerationStatus.value.delete(projectId)
      compilationStatus.value.delete(projectId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete project'
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    projects,
    currentProject,
    isLoading,
    error,
    transcriptionStatus,
    sceneGenerationStatus,
    assetGenerationStatus,
    compilationStatus,

    // Computed
    userProjects,
    completedProjects,
    processingProjects,

    // Actions
    createProject,
    updateProject,
    loadProjects,
    getProject,
    startTranscription,
    pollTranscriptionStatus,
    generateSceneBeats,
    updateSceneBeats,
    generateAssets,
    pollAssetGeneration,
    compileVideo,
    deleteProject,
    clearError,
  }
})
```

---

## 🚀 **Implementation Timeline & Deployment Plan**

### **Phase 1: Infrastructure Setup (Week 1-2)**

**Terraform Extensions:**

```bash
# Add new variables to terraform/variables.tf
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

# Deploy new DynamoDB tables, Lambda functions, ECS cluster
# Set up Secrets Manager with API keys
# Configure EventBridge for async processing
```

**Docker Image Build:**

```bash
# Build and push video processor image
cd terraform/video-processor
docker build -t easy-video-share-video-processor .
docker tag easy-video-share-video-processor:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

### **Phase 2: Backend Services (Week 2-3)**

**Lambda Deployment:**

```bash
# Package and deploy Lambda functions
cd terraform/lambdas/audio-transcription
zip -r ../../../audio_transcription_lambda.zip .

cd ../scene-generation
zip -r ../../../scene_generation_lambda.zip .

cd ../kling-integration
zip -r ../../../kling_integration_lambda.zip .

# Update Terraform with new Lambda packages
terraform apply -var-file="terraform.tfvars"
```

**API Gateway Extensions:**

```bash
# Add new API endpoints for AI video pipeline
# Update existing API Gateway configuration
# Test all endpoints with Postman/curl
```

### **Phase 3: Frontend Implementation (Week 3-4)**

**Vue.js Components:**

```bash
# Add AI video routes to router
# Implement step-by-step UI components
# Integrate with Pinia stores
# Test full user workflow
```

**Metronic Integration:**

```bash
# Ensure all components follow Metronic patterns
# Implement responsive design
# Add loading states and error handling
# Test on mobile devices
```

### **Phase 4: Testing & Optimization (Week 4-5)**

**End-to-End Testing:**

```bash
# Test complete audio-to-video pipeline
# Verify asset generation and video compilation
# Test error handling and recovery
# Performance optimization
```

**Production Deployment:**

```bash
# Configure production environment
# Set up monitoring and alerts
# Deploy to production AWS account
# Configure domain and SSL certificates
```

---

## 💰 **Cost Analysis & Optimization**

### **Monthly Cost Estimates (for 100 videos/month)**

**AWS Services:**

- **DynamoDB**: ~$5-10 (PAY_PER_REQUEST)
- **Lambda Functions**: ~$10-20 (transcription, scene generation, asset polling)
- **ECS Fargate**: ~$50-80 (video processing - 4vCPU, 16GB RAM, ~2 hours/month)
- **S3 Storage**: ~$10-15 (audio files, generated assets, final videos)
- **AWS Transcribe**: ~$15-25 (audio transcription)
- **API Gateway**: ~$3-5 (API calls)
- **Secrets Manager**: ~$2 (API key storage)

**External APIs:**

- **Kling AI**: ~$50-100 (video/image generation - pricing TBD)
- **OpenAI GPT-4**: ~$10-20 (scene generation prompts)

**Total Estimated Monthly Cost: $155-275**

### **Cost Optimization Strategies**

1. **Batch Processing**: Group multiple asset generations to reduce API calls
2. **Asset Caching**: Reuse similar generated assets across projects
3. **Efficient Storage**: Use S3 lifecycle policies for older projects
4. **Spot Instances**: Use ECS Spot instances for video processing when possible
5. **Regional Optimization**: Deploy in cost-effective AWS regions

---

## 📊 **Monitoring & Analytics**

### **CloudWatch Dashboards**

```hcl
# terraform/monitoring.tf
resource "aws_cloudwatch_dashboard" "ai_video_pipeline" {
  dashboard_name = "${var.project_name}-ai-video-pipeline"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "${var.project_name}-scene-generation"],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project_name}-scene-generation"],
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-video-processing"],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-video-processing"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "AI Video Pipeline Metrics"
        }
      }
    ]
  })
}
```

### **Custom Metrics**

- **Project Completion Rate**: Track successful vs failed projects
- **Processing Time**: Monitor average time per pipeline stage
- **Asset Quality**: Track Kling AI generation success rates
- **User Engagement**: Monitor feature usage and user satisfaction

---

## 🔐 **Security Considerations**

### **Data Protection**

- **Encryption**: All data encrypted in transit and at rest
- **Access Control**: IAM roles with minimal required permissions
- **API Security**: Rate limiting and authentication on all endpoints
- **Content Filtering**: Validate audio content and generated assets

### **Privacy Compliance**

- **Data Retention**: Automatic cleanup of temporary processing files
- **User Consent**: Clear terms for AI processing of audio content
- **Geographic Compliance**: Region-specific deployment options
- **Audit Logging**: CloudTrail logging for all API operations

---

## 📋 **Success Metrics & KPIs**

### **Technical Metrics**

- **Pipeline Success Rate**: >95% of projects complete successfully
- **Average Processing Time**: <15 minutes end-to-end
- **Asset Generation Quality**: >90% satisfaction rate
- **System Uptime**: >99.9% availability

### **Business Metrics**

- **User Adoption**: Active users creating AI videos
- **Content Creation**: Number of videos generated monthly
- **Platform Distribution**: Success on Instagram/YouTube
- **Cost Efficiency**: Cost per generated video

---

## 🎯 **Conclusion**

This comprehensive plan provides a complete roadmap for implementing an AI-powered short-form video generation pipeline that:

✅ **Extends your existing Vue.js infrastructure** with minimal disruption  
✅ **Leverages proven AWS services** for scalability and reliability  
✅ **Integrates cutting-edge AI technologies** (Kling AI, LLMs) for content generation  
✅ **Follows Metronic UI patterns** for professional user experience  
✅ **Provides comprehensive monitoring** and cost optimization  
✅ **Scales efficiently** with your user base growth

The implementation maintains your current architecture while adding sophisticated AI capabilities that will differentiate your platform in the competitive short-form video market.

**Next Steps**: Begin with Phase 1 infrastructure setup, then progress through each phase systematically. The modular design allows for iterative development and testing at each stage.

---

**Total Estimated Implementation Time**: 4-5 weeks  
**Estimated Monthly Operating Cost**: $155-275 for moderate usage  
**Expected ROI**: High - enabling users to create professional content at scale
