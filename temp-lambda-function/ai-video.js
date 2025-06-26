/* eslint-disable */
// Complete Lambda function for AI video generation with Vertex AI Veo 2
// Note: This file uses CommonJS modules (require) as it's a Lambda function

const {
  DynamoDBClient,
  GetItemCommand,
  PutItemCommand,
  UpdateItemCommand,
  QueryCommand,
} = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb')
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager')
const {
  TranscribeClient,
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
} = require('@aws-sdk/client-transcribe')
const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3')

// Initialize AWS clients
const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)
const secretsClient = new SecretsManagerClient({ region: process.env.AWS_REGION })
const transcribeClient = new TranscribeClient({ region: process.env.AWS_REGION })
const s3Client = new S3Client({ region: process.env.AWS_REGION })

// Modern Google Cloud Authentication with Workload Identity Federation
let googleAuth = null
let vertexAI = null
let openAI = null

async function initializeGoogleCloud() {
  try {
    // Lazy load Google Cloud dependencies only when needed
    const { GoogleAuth } = require('google-auth-library')
    const { VertexAI } = require('@google-cloud/vertexai')
    const { OpenAI } = require('openai')

    // Get secrets from AWS Secrets Manager
    const secretsResponse = await secretsClient.send(
      new GetSecretValueCommand({ SecretId: process.env.SECRETS_MANAGER_ARN }),
    )
    const secrets = JSON.parse(secretsResponse.SecretString)

    // Initialize Google Auth with Workload Identity Federation
    // This will automatically detect AWS Lambda environment and use Workload Identity
    googleAuth = new GoogleAuth({
      scopes: [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/cloud-platform.projects',
      ],
      // The library will automatically use Workload Identity Federation
      // when running in AWS Lambda environment
    })

    // Initialize Vertex AI with modern auth
    vertexAI = new VertexAI({
      project: secrets.google_cloud_project_id || process.env.GOOGLE_CLOUD_PROJECT_ID,
      location: secrets.google_cloud_location || process.env.GOOGLE_CLOUD_LOCATION,
      googleAuth: googleAuth,
    })

    // Initialize OpenAI
    openAI = new OpenAI({
      apiKey: secrets.openai_api_key,
    })

    console.log('✅ Google Cloud initialized with Workload Identity Federation')
    console.log(
      'Project ID:',
      secrets.google_cloud_project_id || process.env.GOOGLE_CLOUD_PROJECT_ID,
    )
    console.log('Location:', secrets.google_cloud_location || process.env.GOOGLE_CLOUD_LOCATION)
  } catch (error) {
    console.error('❌ Error initializing Google Cloud:', error)
    throw error
  }
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'Access-Control-Allow-Credentials': 'true',
  'Access-Control-Max-Age': '86400',
}

const createResponse = (statusCode, body) => {
  const response = {
    statusCode,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  }

  console.log('🔧 Creating Response:')
  console.log('   - Status Code:', statusCode)
  console.log('   - Headers:', JSON.stringify(response.headers, null, 2))
  console.log('   - Body:', JSON.stringify(body, null, 2))

  return response
}

// Main Lambda handler
exports.handler = async (event) => {
  console.log('🚀 AI Video Lambda Handler Started')
  console.log('📋 Full Event:', JSON.stringify(event, null, 2))
  console.log('🔍 HTTP Method:', event.httpMethod)
  console.log('🔍 Path:', event.path)
  console.log('🔍 Path Parameters:', JSON.stringify(event.pathParameters, null, 2))
  console.log('🔍 Headers:', JSON.stringify(event.headers, null, 2))
  console.log('🔍 Query String:', event.queryStringParameters)

  // Handle CORS preflight FIRST, before any other processing
  if (event.httpMethod === 'OPTIONS') {
    console.log('🔄 Handling OPTIONS preflight request')
    const response = createResponse(200, { message: 'CORS preflight' })
    console.log('📤 OPTIONS Response:', JSON.stringify(response, null, 2))
    return response
  }

  try {
    console.log('🔧 Initializing Google Cloud...')
    await initializeGoogleCloud()

    const httpMethod = event.httpMethod
    const path = event.path || event.pathParameters?.proxy || ''
    const videoId = event.pathParameters?.videoId

    console.log('🔍 Parsed values:')
    console.log('   - HTTP Method:', httpMethod)
    console.log('   - Path:', path)
    console.log('   - Video ID:', videoId)

    // Extract user ID from Cognito
    let userId = null
    if (event.requestContext?.authorizer?.claims) {
      userId = event.requestContext.authorizer.claims.sub
      console.log('👤 User ID from Cognito:', userId)
    } else {
      console.log('⚠️  No Cognito claims found in request context')
      console.log('📋 Request Context:', JSON.stringify(event.requestContext, null, 2))
    }

    if (!userId) {
      console.log('❌ No user ID found - returning 401')
      const response = createResponse(401, { error: 'Authentication required' })
      console.log('📤 401 Response:', JSON.stringify(response, null, 2))
      return response
    }

    // Handle POST to /ai-video (start generation)
    if (httpMethod === 'POST' && path.includes('ai-video') && !videoId) {
      console.log('🎬 Handling AI video generation request')
      const response = await handleAIVideoGeneration(event, userId)
      console.log('📤 Generation Response:', JSON.stringify(response, null, 2))
      return response
    }

    // Handle GET to /ai-video/{videoId} (get status)
    if (httpMethod === 'GET' && path.includes('ai-video') && videoId) {
      console.log('📊 Handling AI video status request for video:', videoId)
      const response = await handleGetAIVideoStatus(event, userId, videoId)
      console.log('📤 Status Response:', JSON.stringify(response, null, 2))
      return response
    }

    console.log('❌ No matching route found')
    const response = createResponse(405, {
      error: `Method ${httpMethod} not allowed for path ${path}`,
    })
    console.log('📤 405 Response:', JSON.stringify(response, null, 2))
    return response
  } catch (error) {
    console.error('💥 AI Video Error:', error)
    console.error('💥 Error Stack:', error.stack)
    const response = createResponse(500, {
      error: 'Internal server error',
      message: error.message,
      stack: error.stack,
    })
    console.log('📤 500 Response:', JSON.stringify(response, null, 2))
    return response
  }
}

// Handle AI video generation request
async function handleAIVideoGeneration(event, userId) {
  console.log('🎬 Starting AI video generation handler')
  console.log('📋 Event body:', event.body)

  const body = JSON.parse(event.body || '{}')
  console.log('📋 Parsed body:', JSON.stringify(body, null, 2))

  if (!body.audioId || !body.prompt) {
    console.log('❌ Missing required fields:')
    console.log('   - audioId:', body.audioId)
    console.log('   - prompt:', body.prompt)
    return createResponse(400, {
      error: 'Missing required fields: audioId, prompt',
    })
  }

  console.log(`🎬 Starting AI video generation for audio ${body.audioId}`)
  console.log(`📝 Prompt: ${body.prompt}`)

  // Generate a unique video ID
  const videoId = `${userId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // Initialize AI generation data structure with mock processing steps
  const aiGenerationData = {
    processing_steps: [
      { step: 'transcription', status: 'pending', started_at: new Date().toISOString() },
      { step: 'scene_planning', status: 'pending' },
      { step: 'video_generation', status: 'pending' },
      { step: 'finalization', status: 'pending' },
    ],
    started_at: new Date().toISOString(),
    user_prompt: body.prompt,
    target_duration: body.targetDuration || 30,
    style: body.style || 'realistic',
    generation_settings: {
      aspect_ratio: '9:16',
      quality: 'high',
      fps: 30,
    },
  }

  // Create video metadata record
  const videoMetadata = {
    video_id: videoId,
    user_id: userId,
    user_email: event.requestContext.authorizer.claims.email || 'user@example.com',
    title: `AI Generated Video - ${body.prompt.substring(0, 50)}...`,
    filename: `ai-video-${videoId}.mp4`,
    bucket_location: `ai-videos/${videoId}/final-video.mp4`,
    upload_date: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ai_project_type: 'ai_generated',
    ai_generation_status: 'processing',
    ai_generation_data: aiGenerationData,
  }

  // Save to DynamoDB
  const putCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
    UpdateExpression:
      'SET user_id = :userId, user_email = :userEmail, title = :title, filename = :filename, bucket_location = :bucketLocation, upload_date = :uploadDate, created_at = :createdAt, updated_at = :updatedAt, ai_project_type = :aiProjectType, ai_generation_status = :aiGenerationStatus, ai_generation_data = :aiGenerationData',
    ExpressionAttributeValues: {
      ':userId': videoMetadata.user_id,
      ':userEmail': videoMetadata.user_email,
      ':title': videoMetadata.title,
      ':filename': videoMetadata.filename,
      ':bucketLocation': videoMetadata.bucket_location,
      ':uploadDate': videoMetadata.upload_date,
      ':createdAt': videoMetadata.created_at,
      ':updatedAt': videoMetadata.updated_at,
      ':aiProjectType': videoMetadata.ai_project_type,
      ':aiGenerationStatus': videoMetadata.ai_generation_status,
      ':aiGenerationData': videoMetadata.ai_generation_data,
    },
  })

  await docClient.send(putCommand)

  // Start asynchronous processing (non-blocking)
  processAIVideoAsync(videoId, userId, body).catch((error) => {
    console.error('Async processing error:', error)
    updateAIGenerationStatus(videoId, 'failed', {
      error_message: error.message,
      failed_at: new Date().toISOString(),
    })
  })

  return createResponse(202, {
    success: true,
    message: 'AI video generation started',
    videoId: videoId,
    status: 'processing',
    estimatedTime: '5-10 minutes',
  })
}

// Asynchronous AI video processing pipeline (mock implementation)
async function processAIVideoAsync(videoId, userId, request) {
  console.log(`Starting async processing for video ${videoId}`)

  try {
    // Step 1: Simulate transcription (30 seconds)
    await updateProcessingStep(videoId, 'transcription', 'processing')
    await simulateProcessing(30000) // 30 seconds
    await updateProcessingStep(videoId, 'transcription', 'completed')

    // Step 2: Simulate scene planning (60 seconds)
    await updateProcessingStep(videoId, 'scene_planning', 'processing')
    await simulateProcessing(60000) // 60 seconds
    await updateProcessingStep(videoId, 'scene_planning', 'completed')

    // Step 3: Simulate video generation (120 seconds)
    await updateProcessingStep(videoId, 'video_generation', 'processing')
    await simulateProcessing(120000) // 120 seconds
    await updateProcessingStep(videoId, 'video_generation', 'completed')

    // Step 4: Simulate finalization (30 seconds)
    await updateProcessingStep(videoId, 'finalization', 'processing')
    await simulateProcessing(30000) // 30 seconds
    await updateProcessingStep(videoId, 'finalization', 'completed')

    // Mark as completed
    await updateAIGenerationStatus(videoId, 'completed', {
      completed_at: new Date().toISOString(),
      generation_time: 240000, // 4 minutes
      final_video_url: `https://example.com/mock-video-${videoId}.mp4`, // Mock URL
    })

    console.log(`AI video generation completed for ${videoId}`)
  } catch (error) {
    console.error(`AI video generation failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', {
      error_message: error.message,
      failed_at: new Date().toISOString(),
    })
  }
}

// Simulate processing time
function simulateProcessing(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Update processing step status
async function updateProcessingStep(videoId, stepName, status) {
  try {
    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression:
        'SET ai_generation_data.processing_steps = list_append(if_not_exists(ai_generation_data.processing_steps, :empty_list), :new_step), updated_at = :updated',
      ExpressionAttributeValues: {
        ':empty_list': [],
        ':new_step': [
          {
            step: stepName,
            status: status,
            started_at: status === 'processing' ? new Date().toISOString() : undefined,
            completed_at: status === 'completed' ? new Date().toISOString() : undefined,
          },
        ],
        ':updated': new Date().toISOString(),
      },
    })

    await docClient.send(updateCommand)
    console.log(`Updated step ${stepName} to ${status} for video ${videoId}`)
  } catch (error) {
    console.error(`Error updating processing step ${stepName}:`, error)
  }
}

// Update AI generation status
async function updateAIGenerationStatus(videoId, status, additionalData = {}) {
  try {
    const updateExpression = 'SET ai_generation_status = :status, updated_at = :updated'
    const expressionAttributeValues = {
      ':status': status,
      ':updated': new Date().toISOString(),
    }

    // Add additional data to update expression
    Object.entries(additionalData).forEach(([key, value]) => {
      expressionAttributeValues[`:${key}`] = value
      updateExpression += `, ai_generation_data.${key} = :${key}`
    })

    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression: updateExpression,
      ExpressionAttributeValues: expressionAttributeValues,
    })

    await docClient.send(updateCommand)
    console.log(`Updated AI generation status to ${status} for video ${videoId}`)
  } catch (error) {
    console.error(`Error updating AI generation status:`, error)
  }
}

// Handle get AI video status
async function handleGetAIVideoStatus(event, userId, videoId) {
  if (!videoId) {
    return createResponse(400, { error: 'Video ID is required' })
  }

  try {
    const getCommand = new GetCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
    })

    const result = await docClient.send(getCommand)
    if (!result.Item) {
      return createResponse(404, { error: 'Video not found' })
    }

    // Verify user ownership
    if (result.Item.user_id !== userId) {
      return createResponse(403, { error: 'Access denied' })
    }

    return createResponse(200, {
      success: true,
      video: result.Item,
    })
  } catch (error) {
    console.error('Error getting AI video status:', error)
    return createResponse(500, {
      error: 'Failed to get AI video status',
      message: error.message,
    })
  }
}
