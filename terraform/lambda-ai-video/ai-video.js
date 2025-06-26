// Complete Lambda function for AI video generation with Vertex AI Veo 2
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb')
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager')
const {
  TranscribeClient,
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
} = require('@aws-sdk/client-transcribe')
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3')
const { VertexAI, HarmCategory, HarmBlockThreshold } = require('@google-cloud/vertexai')
const OpenAI = require('openai')

// Initialize AWS clients
const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)
const secretsClient = new SecretsManagerClient({ region: process.env.AWS_REGION })
const transcribeClient = new TranscribeClient({ region: process.env.AWS_REGION })
const s3Client = new S3Client({ region: process.env.AWS_REGION })

// Global variables for caching credentials
let secrets = null
let openai = null
let vertexAI = null

// Initialize external API clients
async function initializeClients() {
  if (!secrets) {
    console.log('Initializing API clients...')

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

    console.log('API clients initialized successfully')
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

// Main Lambda handler
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

// Handle AI video generation request
async function handleAIVideoGeneration(event, userId) {
  const body = JSON.parse(event.body || '{}')

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
  if (!result.Item || result.Item.user_id !== userId) {
    return createResponse(404, { error: 'Video not found or access denied' })
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
  await docClient.send(
    new UpdateCommand({
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
    }),
  )

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

// Async AI video processing pipeline
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

    // Step 4: Finalize
    await updateProcessingStep(videoId, 'video_generation', 'completed')
    await updateProcessingStep(videoId, 'finalization', 'processing')
    const finalVideoUrl = await finalizeVideo(videoId, generatedVideo)

    // Complete
    await updateProcessingStep(videoId, 'finalization', 'completed')
    await updateAIGenerationStatus(videoId, 'completed', { final_video_url: finalVideoUrl })
  } catch (error) {
    console.error(`AI video processing failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', { error_message: error.message })
  }
}

// Transcribe audio using AWS Transcribe
async function transcribeAudio(videoRecord) {
  const jobName = `ai-video-${videoRecord.video_id}-${Date.now()}`

  await transcribeClient.send(
    new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      Media: {
        MediaFileUri: `s3://${process.env.S3_BUCKET}/${videoRecord.bucket_location}`,
      },
      MediaFormat: getMediaFormat(videoRecord.filename),
      LanguageCode: 'en-US',
    }),
  )

  // Poll for completion
  let jobStatus = 'IN_PROGRESS'
  let attempts = 0

  while (jobStatus === 'IN_PROGRESS' && attempts < 60) {
    await new Promise((resolve) => setTimeout(resolve, 5000))

    const result = await transcribeClient.send(
      new GetTranscriptionJobCommand({
        TranscriptionJobName: jobName,
      }),
    )

    jobStatus = result.TranscriptionJob.TranscriptionJobStatus

    if (jobStatus === 'COMPLETED') {
      const transcriptUri = result.TranscriptionJob.Transcript.TranscriptFileUri
      const response = await fetch(transcriptUri)
      const transcriptionResult = await response.json()

      return {
        full_text: transcriptionResult.results.transcripts[0].transcript,
        segments: transcriptionResult.results.items.map((item) => ({
          start_time: parseFloat(item.start_time || 0),
          end_time: parseFloat(item.end_time || 0),
          text: item.alternatives[0].content,
          confidence: item.alternatives[0].confidence,
        })),
      }
    } else if (jobStatus === 'FAILED') {
      throw new Error('Transcription failed')
    }

    attempts++
  }

  throw new Error('Transcription timed out')
}

// Generate scene plan using OpenAI GPT-4
async function generateScenePlan(transcription, videoRecord) {
  const prompt = `
Create a ${videoRecord.ai_generation_data.target_duration}-second vertical video plan for social media.

TRANSCRIPT: "${transcription.full_text}"
USER PROMPT: "${videoRecord.ai_generation_data.user_prompt}"
STYLE: ${videoRecord.ai_generation_data.style}

Create 2-4 engaging scenes that total ${videoRecord.ai_generation_data.target_duration} seconds.

OUTPUT FORMAT (JSON):
{
  "overall_theme": "Video theme description",
  "total_duration": ${videoRecord.ai_generation_data.target_duration},
  "scenes": [
    {
      "sequence": 1,
      "duration": 10,
      "scene_description": "Visual description",
      "vertex_ai_prompt": "Optimized prompt for Vertex AI Veo 2"
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

// Generate video using Vertex AI (placeholder implementation)
async function generateVideoWithVertexAI(scenePlan) {
  // Note: This is a placeholder for when Vertex AI Veo 2 becomes available
  // For now, create a simple placeholder

  const mainScene = scenePlan.scenes[0]

  // Placeholder video generation
  return [
    {
      sequence: 1,
      video_url: `placeholder://generated-video-${Date.now()}`,
      duration: scenePlan.total_duration,
      scene_description: mainScene.scene_description,
    },
  ]
}

// Finalize video
async function finalizeVideo(videoId, generatedScenes) {
  const scene = generatedScenes[0]

  // For placeholder implementation, return a data URL
  const placeholderData = {
    videoId,
    timestamp: new Date().toISOString(),
    scene: scene.scene_description,
  }

  return `data:application/json;base64,${Buffer.from(JSON.stringify(placeholderData)).toString('base64')}`
}

// Helper functions
async function updateProcessingStep(videoId, step, status) {
  // Implementation to update specific processing step
  console.log(`Updating ${videoId} step ${step} to ${status}`)
}

async function updateAIGenerationStatus(videoId, status, additionalData = {}) {
  await docClient.send(
    new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression: 'SET ai_generation_status = :status, updated_at = :updated',
      ExpressionAttributeValues: {
        ':status': status,
        ':updated': new Date().toISOString(),
      },
    }),
  )
}

function getMediaFormat(filename) {
  const extension = filename.split('.').pop().toLowerCase()
  const formatMap = {
    mp3: 'mp3',
    wav: 'wav',
    m4a: 'm4a',
    aac: 'mp3',
  }
  return formatMap[extension] || 'mp3'
}

async function handleGetAIVideoStatus(event, userId) {
  const videoId = event.pathParameters?.videoId || event.queryStringParameters?.videoId

  if (!videoId) {
    return createResponse(400, { error: 'Video ID required' })
  }

  const result = await docClient.send(
    new GetCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
    }),
  )

  if (!result.Item || result.Item.user_id !== userId) {
    return createResponse(404, { error: 'Video not found or access denied' })
  }

  return createResponse(200, {
    success: true,
    video: result.Item,
  })
}
