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

## 🚀 **Lambda Function Implementation**

### **Main AI Video Processor**

```javascript
// terraform/ai-video-lambda/ai-video.js
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb')
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager')
const {
  TranscribeClient,
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
} = require('@aws-sdk/client-transcribe')
const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3')
const { VertexAI } = require('@google-cloud/vertexai')
const OpenAI = require('openai')

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)
const secretsClient = new SecretsManagerClient({ region: process.env.AWS_REGION })
const transcribeClient = new TranscribeClient({ region: process.env.AWS_REGION })
const s3Client = new S3Client({ region: process.env.AWS_REGION })

let secrets = null
let openai = null
let vertexAI = null

// Initialize API clients
async function initializeClients() {
  if (!secrets) {
    const secretResponse = await secretsClient.send(
      new GetSecretValueCommand({ SecretId: process.env.SECRETS_MANAGER_ARN }),
    )
    secrets = JSON.parse(secretResponse.SecretString)

    // Initialize OpenAI
    openai = new OpenAI({
      apiKey: secrets.openai_api_key,
    })

    // Initialize Vertex AI
    const credentials = JSON.parse(secrets.google_cloud_credentials)
    vertexAI = new VertexAI({
      project: secrets.vertex_ai_project_id,
      location: secrets.vertex_ai_location,
      credentials: credentials,
    })
  }
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers':
    'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token',
}

const createResponse = (statusCode, body) => ({
  statusCode,
  headers: corsHeaders,
  body: JSON.stringify(body),
})

exports.handler = async (event) => {
  console.log('AI Video Event:', JSON.stringify(event, null, 2))

  try {
    await initializeClients()

    const httpMethod = event.httpMethod

    if (httpMethod === 'OPTIONS') {
      return createResponse(200, { message: 'CORS preflight' })
    }

    // Extract user ID from Cognito
    let userId = null
    if (event.requestContext?.authorizer?.claims) {
      userId = event.requestContext.authorizer.claims.sub
    }

    if (!userId) {
      return createResponse(401, { error: 'Authentication required' })
    }

    if (httpMethod === 'POST') {
      return await handleAIVideoGeneration(event, userId)
    }

    if (httpMethod === 'GET') {
      return await handleGetAIVideoStatus(event, userId)
    }

    return createResponse(405, { error: `Method ${httpMethod} not allowed` })
  } catch (error) {
    console.error('AI Video Error:', error)
    return createResponse(500, {
      error: 'Internal server error',
      message: error.message,
    })
  }
}

async function handleAIVideoGeneration(event, userId) {
  const body = JSON.parse(event.body || '{}')

  // Validate required fields
  if (!body.videoId || !body.prompt) {
    return createResponse(400, {
      error: 'Missing required fields: videoId, prompt',
    })
  }

  // Get existing video record
  const getCommand = new GetCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: body.videoId },
  })

  const result = await docClient.send(getCommand)
  if (!result.Item) {
    return createResponse(404, { error: 'Video not found' })
  }

  // Verify ownership
  if (result.Item.user_id !== userId) {
    return createResponse(403, { error: 'Access denied' })
  }

  // Initialize AI generation data
  const aiGenerationData = {
    processing_steps: [
      { step: 'transcription', status: 'pending' },
      { step: 'scene_planning', status: 'pending' },
      { step: 'video_generation', status: 'pending' },
      { step: 'finalization', status: 'pending' },
    ],
    started_at: new Date().toISOString(),
    user_prompt: body.prompt,
    target_duration: body.targetDuration || 30,
    style: body.style || 'realistic',
  }

  // Update video record
  const updateCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: body.videoId },
    UpdateExpression:
      'SET ai_project_type = :type, ai_generation_status = :status, ai_generation_data = :data, updated_at = :updated',
    ExpressionAttributeValues: {
      ':type': 'ai_generated',
      ':status': 'processing',
      ':data': aiGenerationData,
      ':updated': new Date().toISOString(),
    },
  })

  await docClient.send(updateCommand)

  // Start async processing
  processAIVideoAsync(body.videoId, userId, result.Item).catch((error) => {
    console.error('Async processing error:', error)
  })

  return createResponse(202, {
    success: true,
    message: 'AI video generation started',
    videoId: body.videoId,
    status: 'processing',
  })
}

async function processAIVideoAsync(videoId, userId, videoRecord) {
  try {
    // Step 1: Transcribe audio
    await updateProcessingStep(videoId, 'transcription', 'processing')
    const transcription = await transcribeAudio(videoRecord)

    // Step 2: Generate scene plan
    await updateProcessingStep(videoId, 'transcription', 'completed')
    await updateProcessingStep(videoId, 'scene_planning', 'processing')
    const scenePlan = await generateScenePlan(transcription, videoRecord)

    // Step 3: Generate video with Vertex AI
    await updateProcessingStep(videoId, 'scene_planning', 'completed')
    await updateProcessingStep(videoId, 'video_generation', 'processing')
    const generatedVideo = await generateVideoWithVertexAI(scenePlan)

    // Step 4: Finalize and save
    await updateProcessingStep(videoId, 'video_generation', 'completed')
    await updateProcessingStep(videoId, 'finalization', 'processing')
    const finalVideoUrl = await finalizeVideo(videoId, generatedVideo)

    // Mark as completed
    await updateProcessingStep(videoId, 'finalization', 'completed')
    await updateAIGenerationStatus(videoId, 'completed', { final_video_url: finalVideoUrl })
  } catch (error) {
    console.error(`AI video processing failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', { error_message: error.message })
  }
}

async function transcribeAudio(videoRecord) {
  const jobName = `transcribe-${videoRecord.video_id}-${Date.now()}`

  const startCommand = new StartTranscriptionJobCommand({
    TranscriptionJobName: jobName,
    Media: {
      MediaFileUri: `s3://${process.env.S3_BUCKET}/${videoRecord.bucket_location}`,
    },
    MediaFormat: getMediaFormat(videoRecord.filename),
    LanguageCode: 'en-US',
  })

  await transcribeClient.send(startCommand)

  // Poll for completion
  let jobStatus = 'IN_PROGRESS'
  let transcriptionResult = null

  while (jobStatus === 'IN_PROGRESS') {
    await new Promise((resolve) => setTimeout(resolve, 5000)) // Wait 5 seconds

    const getCommand = new GetTranscriptionJobCommand({
      TranscriptionJobName: jobName,
    })

    const result = await transcribeClient.send(getCommand)
    jobStatus = result.TranscriptionJob.TranscriptionJobStatus

    if (jobStatus === 'COMPLETED') {
      // Download transcription results
      const transcriptUri = result.TranscriptionJob.Transcript.TranscriptFileUri
      const response = await fetch(transcriptUri)
      transcriptionResult = await response.json()
    } else if (jobStatus === 'FAILED') {
      throw new Error('Transcription failed')
    }
  }

  return {
    full_text: transcriptionResult.results.transcripts[0].transcript,
    segments: transcriptionResult.results.items.map((item) => ({
      start_time: parseFloat(item.start_time || 0),
      end_time: parseFloat(item.end_time || 0),
      text: item.alternatives[0].content,
      confidence: item.alternatives[0].confidence,
    })),
    confidence: transcriptionResult.results.transcripts[0].confidence,
    language_code: 'en-US',
  }
}

async function generateScenePlan(transcription, videoRecord) {
  const prompt = `
Create a ${videoRecord.ai_generation_data.target_duration}-second vertical video plan for social media.

TRANSCRIPT:
${transcription.full_text}

REQUIREMENTS:
- Exactly ${videoRecord.ai_generation_data.target_duration} seconds duration
- Vertical 9:16 format optimized for Instagram Reels/YouTube Shorts
- 2-4 engaging visual scenes
- Each scene should be compelling and visually interesting
- Style: ${videoRecord.ai_generation_data.style}

USER PROMPT: ${videoRecord.ai_generation_data.user_prompt}

OUTPUT FORMAT (JSON):
{
  "overall_theme": "Brief description of video theme",
  "total_duration": ${videoRecord.ai_generation_data.target_duration},
  "scenes": [
    {
      "sequence": 1,
      "start_time": 0,
      "end_time": 10,
      "duration": 10,
      "audio_text": "Relevant transcript portion",
      "scene_description": "Detailed visual description",
      "vertex_ai_prompt": "Optimized prompt for Vertex AI Veo 2",
      "visual_style": "Specific style notes"
    }
  ]
}
`

  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.7,
    response_format: { type: 'json_object' },
  })

  return JSON.parse(response.choices[0].message.content)
}

async function generateVideoWithVertexAI(scenePlan) {
  const generatedScenes = []

  for (const scene of scenePlan.scenes) {
    try {
      // Use Vertex AI Veo 2 for video generation
      const model = vertexAI.getGenerativeModel({ model: 'veo-2' })

      const request = {
        contents: [
          {
            role: 'user',
            parts: [
              {
                text: `Generate a ${scene.duration}-second vertical video (9:16 aspect ratio) with the following description: ${scene.vertex_ai_prompt}. Style: ${scene.visual_style}. High quality, professional, engaging for social media.`,
              },
            ],
          },
        ],
        generationConfig: {
          temperature: 0.8,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 1024,
        },
        safetySettings: [
          { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
        ],
      }

      const response = await model.generateContent(request)

      // Extract video URL from response (exact structure depends on Veo 2 API)
      const videoUrl = response.response.candidates[0].content.parts[0].videoUrl

      generatedScenes.push({
        sequence: scene.sequence,
        video_url: videoUrl,
        duration: scene.duration,
        scene_description: scene.scene_description,
      })
    } catch (error) {
      console.error(`Error generating scene ${scene.sequence}:`, error)
      throw error
    }
  }

  return generatedScenes
}

async function finalizeVideo(videoId, generatedScenes) {
  // For now, use the first generated scene as the final video
  // In a full implementation, this would combine multiple scenes
  const finalScene = generatedScenes[0]

  // Download the video from Vertex AI and upload to S3
  const response = await fetch(finalScene.video_url)
  const videoBuffer = await response.buffer()

  const s3Key = `ai-generated/${videoId}/final_video.mp4`

  await s3Client.send(
    new PutObjectCommand({
      Bucket: process.env.S3_BUCKET,
      Key: s3Key,
      Body: videoBuffer,
      ContentType: 'video/mp4',
    }),
  )

  return `s3://${process.env.S3_BUCKET}/${s3Key}`
}

async function updateProcessingStep(videoId, step, status) {
  const updateCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
    UpdateExpression: 'SET ai_generation_data.processing_steps = :steps, updated_at = :updated',
    ExpressionAttributeValues: {
      ':steps': [
        { step: 'transcription', status: step === 'transcription' ? status : 'completed' },
        { step: 'scene_planning', status: step === 'scene_planning' ? status : 'pending' },
        { step: 'video_generation', status: step === 'video_generation' ? status : 'pending' },
        { step: 'finalization', status: step === 'finalization' ? status : 'pending' },
      ],
      ':updated': new Date().toISOString(),
    },
  })

  await docClient.send(updateCommand)
}

async function updateAIGenerationStatus(videoId, status, additionalData = {}) {
  const updateCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
    UpdateExpression:
      'SET ai_generation_status = :status, ai_generation_data = ai_generation_data + :data, updated_at = :updated',
    ExpressionAttributeValues: {
      ':status': status,
      ':data': {
        ...additionalData,
        completed_at: new Date().toISOString(),
      },
      ':updated': new Date().toISOString(),
    },
  })

  await docClient.send(updateCommand)
}

function getMediaFormat(filename) {
  const extension = filename.split('.').pop().toLowerCase()
  const formatMap = {
    mp3: 'mp3',
    wav: 'wav',
    m4a: 'm4a',
    aac: 'mp3',
    ogg: 'ogg',
    webm: 'webm',
  }
  return formatMap[extension] || 'mp3'
}

async function handleGetAIVideoStatus(event, userId) {
  const videoId = event.pathParameters?.videoId

  if (!videoId) {
    return createResponse(400, { error: 'Video ID required' })
  }

  const getCommand = new GetCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
  })

  const result = await docClient.send(getCommand)

  if (!result.Item) {
    return createResponse(404, { error: 'Video not found' })
  }

  if (result.Item.user_id !== userId) {
    return createResponse(403, { error: 'Access denied' })
  }

  return createResponse(200, {
    success: true,
    video: result.Item,
  })
}
```

---

## 🎨 **Vue.js Frontend Implementation**

### **AI Video Generation Component**

```vue
<!-- src/components/ai-video/AIVideoGenerator.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">
        <h3>AI Video Generation</h3>
      </div>
    </div>

    <div class="card-body">
      <!-- Step 1: Select Audio File -->
      <div v-if="currentStep === 1" class="step-content">
        <h4>Step 1: Select Audio File</h4>
        <p class="text-muted">Choose an audio file to transform into a video</p>

        <div class="row">
          <div class="col-md-6" v-for="video in userVideos" :key="video.video_id">
            <div
              class="card cursor-pointer border-2"
              :class="{ 'border-primary': selectedVideo?.video_id === video.video_id }"
              @click="selectVideo(video)"
            >
              <div class="card-body">
                <h5>{{ video.title }}</h5>
                <p class="text-muted">{{ video.filename }}</p>
                <small class="text-muted">{{ formatDate(video.upload_date) }}</small>
              </div>
            </div>
          </div>
        </div>

        <div class="text-end mt-4">
          <button class="btn btn-primary" :disabled="!selectedVideo" @click="nextStep">
            Next Step
          </button>
        </div>
      </div>

      <!-- Step 2: Configure AI Generation -->
      <div v-if="currentStep === 2" class="step-content">
        <h4>Step 2: Configure AI Video Generation</h4>

        <div class="mb-5">
          <label class="form-label">Video Description/Prompt</label>
          <textarea
            class="form-control"
            rows="3"
            v-model="aiConfig.prompt"
            placeholder="Describe what kind of video you want to create..."
          ></textarea>
        </div>

        <div class="row">
          <div class="col-md-6">
            <label class="form-label">Target Duration</label>
            <select class="form-select" v-model="aiConfig.targetDuration">
              <option value="15">15 seconds</option>
              <option value="30">30 seconds</option>
              <option value="45">45 seconds</option>
              <option value="60">60 seconds</option>
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label">Visual Style</label>
            <select class="form-select" v-model="aiConfig.style">
              <option value="realistic">Realistic</option>
              <option value="cinematic">Cinematic</option>
              <option value="animated">Animated</option>
              <option value="artistic">Artistic</option>
            </select>
          </div>
        </div>

        <div class="d-flex justify-content-between mt-4">
          <button class="btn btn-secondary" @click="previousStep">Previous</button>
          <button
            class="btn btn-primary"
            :disabled="!aiConfig.prompt.trim()"
            @click="startAIGeneration"
          >
            Generate AI Video
          </button>
        </div>
      </div>

      <!-- Step 3: Processing -->
      <div v-if="currentStep === 3" class="step-content">
        <h4>Step 3: AI Video Generation in Progress</h4>

        <div class="mb-5">
          <div class="progress mb-3">
            <div
              class="progress-bar progress-bar-striped progress-bar-animated"
              :style="{ width: `${processingProgress}%` }"
            ></div>
          </div>

          <div class="text-center">
            <p class="mb-2">{{ currentProcessingMessage }}</p>
            <small class="text-muted">{{ processingProgress }}% complete</small>
          </div>
        </div>

        <!-- Processing Steps -->
        <div class="row">
          <div class="col-md-3" v-for="step in processingSteps" :key="step.step">
            <div class="d-flex align-items-center mb-3">
              <div class="symbol symbol-40px me-3">
                <div
                  class="symbol-label"
                  :class="{
                    'bg-success': step.status === 'completed',
                    'bg-primary': step.status === 'processing',
                    'bg-light': step.status === 'pending',
                  }"
                >
                  <i
                    class="fas"
                    :class="{
                      'fa-check text-white': step.status === 'completed',
                      'fa-spinner fa-spin text-white': step.status === 'processing',
                      'fa-clock text-muted': step.status === 'pending',
                    }"
                  ></i>
                </div>
              </div>
              <div>
                <div class="fw-bold">{{ formatStepName(step.step) }}</div>
                <div class="text-muted">{{ step.status }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Completed -->
      <div v-if="currentStep === 4" class="step-content">
        <h4>Step 4: AI Video Generation Complete!</h4>

        <div class="text-center mb-5">
          <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
          <h5 class="mt-3">Your AI video is ready!</h5>
        </div>

        <div v-if="generatedVideo" class="text-center">
          <video
            controls
            class="w-100 mb-4"
            style="max-width: 400px;"
            :src="generatedVideo.final_video_url"
          ></video>

          <div class="d-flex justify-content-center gap-3">
            <button class="btn btn-primary" @click="downloadVideo">
              <i class="fas fa-download me-2"></i>
              Download Video
            </button>
            <button class="btn btn-secondary" @click="shareVideo">
              <i class="fas fa-share me-2"></i>
              Share Video
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVideoStore } from '@/stores/video'
import { AIVideoService } from '@/core/services/AIVideoService'

const videoStore = useVideoStore()

// Component state
const currentStep = ref(1)
const selectedVideo = ref(null)
const aiConfig = ref({
  prompt: '',
  targetDuration: 30,
  style: 'realistic',
})

const processingStatus = ref(null)
const generatedVideo = ref(null)

// Computed properties
const userVideos = computed(() => videoStore.videos.filter((v) => !v.ai_project_type))

const processingSteps = computed(() => {
  return processingStatus.value?.ai_generation_data?.processing_steps || []
})

const processingProgress = computed(() => {
  const steps = processingSteps.value
  if (!steps.length) return 0

  const completedSteps = steps.filter((s) => s.status === 'completed').length
  return Math.round((completedSteps / steps.length) * 100)
})

const currentProcessingMessage = computed(() => {
  const currentStep = processingSteps.value.find((s) => s.status === 'processing')

  const messages = {
    transcription: 'Transcribing audio content...',
    scene_planning: 'Planning video scenes with AI...',
    video_generation: 'Generating video with Vertex AI Veo 2...',
    finalization: 'Finalizing your video...',
  }

  return currentStep ? messages[currentStep.step] : 'Processing...'
})

// Methods
const selectVideo = (video) => {
  selectedVideo.value = video
}

const nextStep = () => {
  currentStep.value++
}

const previousStep = () => {
  currentStep.value--
}

const startAIGeneration = async () => {
  try {
    currentStep.value = 3

    await AIVideoService.generateAIVideo({
      videoId: selectedVideo.value.video_id,
      prompt: aiConfig.value.prompt,
      targetDuration: aiConfig.value.targetDuration,
      style: aiConfig.value.style,
    })

    // Start polling for status
    pollProcessingStatus()
  } catch (error) {
    console.error('Error starting AI generation:', error)
    alert('Failed to start AI video generation')
  }
}

const pollProcessingStatus = async () => {
  const pollInterval = setInterval(async () => {
    try {
      const status = await AIVideoService.getAIVideoStatus(selectedVideo.value.video_id)
      processingStatus.value = status.video

      if (status.video.ai_generation_status === 'completed') {
        clearInterval(pollInterval)
        generatedVideo.value = status.video
        currentStep.value = 4
      } else if (status.video.ai_generation_status === 'failed') {
        clearInterval(pollInterval)
        alert('AI video generation failed')
      }
    } catch (error) {
      console.error('Error polling status:', error)
      clearInterval(pollInterval)
    }
  }, 3000)

  // Stop polling after 15 minutes
  setTimeout(() => clearInterval(pollInterval), 900000)
}

const formatStepName = (step) => {
  const names = {
    transcription: 'Transcription',
    scene_planning: 'Scene Planning',
    video_generation: 'Video Generation',
    finalization: 'Finalization',
  }
  return names[step] || step
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const downloadVideo = () => {
  // Implement video download
  window.open(generatedVideo.value.ai_generation_data.final_video_url)
}

const shareVideo = () => {
  // Implement video sharing
  if (navigator.share) {
    navigator.share({
      title: 'Check out my AI-generated video!',
      url: generatedVideo.value.ai_generation_data.final_video_url,
    })
  }
}

// Lifecycle
onMounted(async () => {
  await videoStore.loadVideos()
})
</script>
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
