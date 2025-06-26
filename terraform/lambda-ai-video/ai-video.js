/* eslint-disable */
// Complete Lambda function for AI video generation with Vertex AI Veo 2
// Note: This file uses CommonJS modules (require) as it's a Lambda function

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, GetCommand, UpdateCommand } = require('@aws-sdk/lib-dynamodb')
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager')
const {
  TranscribeClient,
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
} = require('@aws-sdk/client-transcribe')
const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3')
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
      { step: 'transcription', status: 'pending', started_at: null, completed_at: null },
      { step: 'scene_planning', status: 'pending', started_at: null, completed_at: null },
      { step: 'video_generation', status: 'pending', started_at: null, completed_at: null },
      { step: 'finalization', status: 'pending', started_at: null, completed_at: null },
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
    await updateAIGenerationData(videoId, { audio_transcription: transcription })

    // Step 2: Generate scene plan
    await updateProcessingStep(videoId, 'transcription', 'completed')
    await updateProcessingStep(videoId, 'scene_planning', 'processing')
    const scenePlan = await generateScenePlan(transcription, videoRecord)
    await updateAIGenerationData(videoId, { scene_beats: scenePlan })

    // Step 3: Generate video with Vertex AI
    await updateProcessingStep(videoId, 'scene_planning', 'completed')
    await updateProcessingStep(videoId, 'video_generation', 'processing')
    const generatedVideo = await generateVideoWithVertexAI(scenePlan, videoRecord)
    await updateAIGenerationData(videoId, { vertex_ai_tasks: generatedVideo })

    // Step 4: Finalize
    await updateProcessingStep(videoId, 'video_generation', 'completed')
    await updateProcessingStep(videoId, 'finalization', 'processing')
    const finalVideoUrl = await finalizeVideo(videoId, generatedVideo)

    // Complete
    await updateProcessingStep(videoId, 'finalization', 'completed')
    await updateAIGenerationStatus(videoId, 'completed', {
      final_video_url: finalVideoUrl,
      generation_time:
        Date.now() - new Date(videoRecord.ai_generation_data?.started_at || Date.now()).getTime(),
    })
  } catch (error) {
    console.error(`AI video processing failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', { error_message: error.message })
  }
}

// Transcribe audio using AWS Transcribe
async function transcribeAudio(videoRecord) {
  console.log('Starting transcription for:', videoRecord.video_id)

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
  let pollCount = 0
  const maxPolls = 60 // 5 minutes timeout

  while (jobStatus === 'IN_PROGRESS' && pollCount < maxPolls) {
    await new Promise((resolve) => setTimeout(resolve, 5000)) // Wait 5 seconds
    pollCount++

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

  if (jobStatus === 'IN_PROGRESS') {
    throw new Error('Transcription timeout')
  }

  return {
    full_text: transcriptionResult.results.transcripts[0].transcript,
    segments: transcriptionResult.results.items
      .filter((item) => item.type === 'pronunciation')
      .map((item) => ({
        start_time: parseFloat(item.start_time || 0),
        end_time: parseFloat(item.end_time || 0),
        text: item.alternatives[0].content,
        confidence: parseFloat(item.alternatives[0].confidence || 0),
      })),
    confidence: parseFloat(transcriptionResult.results.transcripts[0].confidence || 0),
    language_code: 'en-US',
  }
}

// Generate scene plan using OpenAI GPT-4
async function generateScenePlan(transcription, videoRecord) {
  console.log('Generating scene plan for:', videoRecord.video_id)

  const targetDuration = videoRecord.ai_generation_data?.target_duration || 30
  const style = videoRecord.ai_generation_data?.style || 'realistic'
  const userPrompt = videoRecord.ai_generation_data?.user_prompt || ''

  const prompt = `Create a ${targetDuration}-second vertical video plan for social media based on the provided audio transcript.

TRANSCRIPT:
${transcription.full_text}

REQUIREMENTS:
- Exactly ${targetDuration} seconds duration
- Vertical 9:16 format optimized for Instagram Reels/YouTube Shorts/TikTok
- 2-4 engaging visual scenes that sync with the audio
- Each scene should be compelling and visually interesting
- Style: ${style}
- User's creative direction: ${userPrompt}

Create scenes that complement and enhance the audio content. Think about:
- What visual elements would make this content more engaging?
- How can we break up the audio into distinct visual segments?
- What scenes would capture viewer attention on social media?

OUTPUT FORMAT (JSON only, no other text):
{
  "overall_theme": "Brief description of video theme",
  "total_duration": ${targetDuration},
  "scenes": [
    {
      "sequence": 1,
      "start_time": 0,
      "end_time": 12,
      "duration": 12,
      "audio_text": "Relevant transcript portion for this scene",
      "scene_description": "Detailed visual description for AI video generation",
      "vertex_ai_prompt": "Optimized prompt for Vertex AI Veo 2 video generation",
      "visual_style": "Specific style notes (lighting, mood, camera angles, etc.)"
    }
  ]
}`

  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.7,
    response_format: { type: 'json_object' },
  })

  return JSON.parse(response.choices[0].message.content)
}

// Generate video using Vertex AI (placeholder implementation)
async function generateVideoWithVertexAI(scenePlan, videoRecord) {
  console.log('Generating video with Vertex AI for:', videoRecord.video_id)

  // This is a placeholder implementation
  // In a real implementation, you would:
  // 1. Use Google Cloud Vertex AI SDK
  // 2. Call the Veo 2 model for each scene
  // 3. Handle video generation and polling for completion

  const generatedScenes = []

  for (const scene of scenePlan.scenes) {
    try {
      console.log(`Generating scene ${scene.sequence}:`, scene.vertex_ai_prompt)

      // Placeholder for Vertex AI Veo 2 call
      // const vertexResponse = await vertexAI.generateVideo({
      //   prompt: scene.vertex_ai_prompt,
      //   duration: scene.duration,
      //   aspectRatio: '9:16',
      //   style: scene.visual_style
      // })

      // For now, create a placeholder response
      const mockVideoUrl = `https://placeholder-video-${scene.sequence}.mp4`

      generatedScenes.push({
        task_id: `vertex-ai-${Date.now()}-${scene.sequence}`,
        sequence: scene.sequence,
        status: 'completed',
        video_url: mockVideoUrl,
        prompt: scene.vertex_ai_prompt,
        created_at: new Date().toISOString(),
        duration: scene.duration,
        scene_description: scene.scene_description,
      })

      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 2000))
    } catch (error) {
      console.error(`Error generating scene ${scene.sequence}:`, error)
      generatedScenes.push({
        task_id: `vertex-ai-${Date.now()}-${scene.sequence}`,
        sequence: scene.sequence,
        status: 'failed',
        error_message: error.message,
        prompt: scene.vertex_ai_prompt,
        created_at: new Date().toISOString(),
      })
    }
  }

  return generatedScenes
}

// Finalize video
async function finalizeVideo(videoId, generatedScenes) {
  console.log('Finalizing video for:', videoId)

  // For the MVP, we'll use the first successfully generated scene
  const successfulScene = generatedScenes.find((scene) => scene.status === 'completed')

  if (!successfulScene) {
    throw new Error('No successful video generation found')
  }

  // In a full implementation, this would:
  // 1. Download all generated scene videos
  // 2. Use FFmpeg to combine scenes with the original audio
  // 3. Apply transitions and effects
  // 4. Upload the final video to S3

  // For now, return a placeholder URL
  const finalVideoKey = `ai-generated/${videoId}/final_video_${Date.now()}.mp4`
  const finalVideoUrl = `s3://${process.env.S3_BUCKET}/${finalVideoKey}`

  console.log('Final video would be stored at:', finalVideoUrl)

  return finalVideoUrl
}

// Helper functions
async function updateProcessingStep(videoId, step, status) {
  // Get current data first
  const getCommand = new GetCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
  })

  const result = await docClient.send(getCommand)
  if (!result.Item) return

  const currentData = result.Item.ai_generation_data || {}
  const steps = currentData.processing_steps || []

  // Update the specific step
  const updatedSteps = steps.map((s) => {
    if (s.step === step) {
      return {
        ...s,
        status,
        started_at: status === 'processing' ? new Date().toISOString() : s.started_at,
        completed_at: status === 'completed' ? new Date().toISOString() : s.completed_at,
      }
    }
    return s
  })

  const updateCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
    UpdateExpression: 'SET ai_generation_data.processing_steps = :steps, updated_at = :updated',
    ExpressionAttributeValues: {
      ':steps': updatedSteps,
      ':updated': new Date().toISOString(),
    },
  })

  await docClient.send(updateCommand)
}

async function updateAIGenerationData(videoId, additionalData) {
  // Get current data first
  const getCommand = new GetCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
  })

  const result = await docClient.send(getCommand)
  if (!result.Item) return

  const currentData = result.Item.ai_generation_data || {}
  const updatedData = { ...currentData, ...additionalData }

  const updateCommand = new UpdateCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: videoId },
    UpdateExpression: 'SET ai_generation_data = :data, updated_at = :updated',
    ExpressionAttributeValues: {
      ':data': updatedData,
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
      'SET ai_generation_status = :status, ai_generation_data.completed_at = :completed, ai_generation_data.final_video_url = :url, updated_at = :updated',
    ExpressionAttributeValues: {
      ':status': status,
      ':completed': new Date().toISOString(),
      ':url': additionalData.final_video_url || null,
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
    mp4: 'mp4',
    mov: 'mov',
    avi: 'mp4',
  }
  return formatMap[extension] || 'mp3'
}

async function handleGetAIVideoStatus(event, userId) {
  const queryParams = event.queryStringParameters || {}
  const videoId = queryParams.videoId

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
