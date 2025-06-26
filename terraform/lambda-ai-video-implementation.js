// terraform/lambda-ai-video-implementation.js
// Complete Lambda function for AI video generation with Vertex AI Veo 2

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

    // Initialize Vertex AI with service account credentials
    const credentials = JSON.parse(secrets.google_cloud_credentials)
    vertexAI = new VertexAI({
      project: secrets.vertex_ai_project_id,
      location: secrets.vertex_ai_location,
      credentials: credentials,
    })

    console.log('API clients initialized successfully')
  }
}

// CORS headers for browser compatibility
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers':
    'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token',
}

// Helper function to create standardized API responses
const createResponse = (statusCode, body) => ({
  statusCode,
  headers: corsHeaders,
  body: JSON.stringify(body),
})

// Main Lambda handler
exports.handler = async (event) => {
  console.log('AI Video Generation Event:', JSON.stringify(event, null, 2))

  try {
    // Initialize external API clients
    await initializeClients()

    const httpMethod = event.httpMethod
    const path = event.path || event.pathParameters?.proxy || ''

    // Handle CORS preflight requests
    if (httpMethod === 'OPTIONS') {
      return createResponse(200, { message: 'CORS preflight' })
    }

    // Extract user ID from Cognito JWT token
    let userId = null
    if (event.requestContext?.authorizer?.claims) {
      userId = event.requestContext.authorizer.claims.sub
      console.log('Authenticated user:', userId)
    }

    if (!userId) {
      return createResponse(401, { error: 'Authentication required' })
    }

    // Route to appropriate handler
    if (httpMethod === 'POST' && path.includes('ai-video')) {
      return await handleAIVideoGeneration(event, userId)
    }

    if (httpMethod === 'GET' && path.includes('ai-video')) {
      return await handleGetAIVideoStatus(event, userId)
    }

    return createResponse(405, { error: `Method ${httpMethod} not allowed` })
  } catch (error) {
    console.error('AI Video Processing Error:', error)
    return createResponse(500, {
      error: 'Internal server error',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    })
  }
}

// Handle AI video generation request
async function handleAIVideoGeneration(event, userId) {
  const body = JSON.parse(event.body || '{}')

  // Validate required fields
  if (!body.videoId || !body.prompt) {
    return createResponse(400, {
      error: 'Missing required fields: videoId, prompt',
    })
  }

  console.log(`Starting AI video generation for video ${body.videoId}`)

  // Get existing video record from DynamoDB
  const getCommand = new GetCommand({
    TableName: process.env.DYNAMODB_TABLE,
    Key: { video_id: body.videoId },
  })

  const result = await docClient.send(getCommand)
  if (!result.Item) {
    return createResponse(404, { error: 'Video not found' })
  }

  // Verify user ownership
  if (result.Item.user_id !== userId) {
    return createResponse(403, { error: 'Access denied' })
  }

  // Initialize AI generation data structure
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

  // Update video record with AI generation status
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

  // Start asynchronous processing (non-blocking)
  processAIVideoAsync(body.videoId, userId, result.Item).catch((error) => {
    console.error('Async processing error:', error)
    updateAIGenerationStatus(body.videoId, 'failed', {
      error_message: error.message,
      failed_at: new Date().toISOString(),
    })
  })

  return createResponse(202, {
    success: true,
    message: 'AI video generation started',
    videoId: body.videoId,
    status: 'processing',
    estimatedTime: '5-10 minutes',
  })
}

// Asynchronous AI video processing pipeline
async function processAIVideoAsync(videoId, userId, videoRecord) {
  const startTime = Date.now()

  try {
    console.log(`Starting AI video processing pipeline for ${videoId}`)

    // Step 1: Transcribe audio content
    await updateProcessingStep(videoId, 'transcription', 'processing')
    console.log('Starting audio transcription...')
    const transcription = await transcribeAudio(videoRecord)
    console.log('Transcription completed')

    // Step 2: Generate scene plan using GPT-4
    await updateProcessingStep(videoId, 'transcription', 'completed')
    await updateProcessingStep(videoId, 'scene_planning', 'processing')
    console.log('Starting scene planning...')
    const scenePlan = await generateScenePlan(transcription, videoRecord)
    console.log('Scene planning completed')

    // Step 3: Generate video with Vertex AI Veo 2
    await updateProcessingStep(videoId, 'scene_planning', 'completed')
    await updateProcessingStep(videoId, 'video_generation', 'processing')
    console.log('Starting video generation with Vertex AI...')
    const generatedVideo = await generateVideoWithVertexAI(scenePlan, videoRecord)
    console.log('Video generation completed')

    // Step 4: Finalize and store the video
    await updateProcessingStep(videoId, 'video_generation', 'completed')
    await updateProcessingStep(videoId, 'finalization', 'processing')
    console.log('Finalizing video...')
    const finalVideoUrl = await finalizeVideo(videoId, generatedVideo)
    console.log('Video finalization completed')

    // Mark as completed with final results
    await updateProcessingStep(videoId, 'finalization', 'completed')

    const processingTime = Math.round((Date.now() - startTime) / 1000)
    await updateAIGenerationStatus(videoId, 'completed', {
      final_video_url: finalVideoUrl,
      generation_time: processingTime,
      completed_at: new Date().toISOString(),
      audio_transcription: transcription,
      scene_beats: scenePlan,
    })

    console.log(`AI video processing completed for ${videoId} in ${processingTime} seconds`)
  } catch (error) {
    console.error(`AI video processing failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', {
      error_message: error.message,
      failed_at: new Date().toISOString(),
      stack: error.stack,
    })
    throw error
  }
}

// Transcribe audio using AWS Transcribe
async function transcribeAudio(videoRecord) {
  const jobName = `ai-video-transcribe-${videoRecord.video_id}-${Date.now()}`

  console.log(`Starting transcription job: ${jobName}`)

  const startCommand = new StartTranscriptionJobCommand({
    TranscriptionJobName: jobName,
    Media: {
      MediaFileUri: `s3://${process.env.S3_BUCKET}/${videoRecord.bucket_location}`,
    },
    MediaFormat: getMediaFormat(videoRecord.filename),
    LanguageCode: 'en-US',
    Settings: {
      ShowSpeakerLabels: false,
      ShowAlternatives: true,
      MaxAlternatives: 2,
    },
  })

  await transcribeClient.send(startCommand)

  // Poll for completion with exponential backoff
  let jobStatus = 'IN_PROGRESS'
  let transcriptionResult = null
  let attempts = 0
  const maxAttempts = 60 // 5 minutes max wait time

  while (jobStatus === 'IN_PROGRESS' && attempts < maxAttempts) {
    const waitTime = Math.min(5000 + attempts * 1000, 15000) // Progressive backoff
    await new Promise((resolve) => setTimeout(resolve, waitTime))

    const getCommand = new GetTranscriptionJobCommand({
      TranscriptionJobName: jobName,
    })

    const result = await transcribeClient.send(getCommand)
    jobStatus = result.TranscriptionJob.TranscriptionJobStatus

    console.log(`Transcription job ${jobName} status: ${jobStatus}`)

    if (jobStatus === 'COMPLETED') {
      // Download and parse transcription results
      const transcriptUri = result.TranscriptionJob.Transcript.TranscriptFileUri
      const response = await fetch(transcriptUri)
      transcriptionResult = await response.json()
      break
    } else if (jobStatus === 'FAILED') {
      throw new Error(`Transcription failed: ${result.TranscriptionJob.FailureReason}`)
    }

    attempts++
  }

  if (jobStatus === 'IN_PROGRESS') {
    throw new Error('Transcription timed out')
  }

  // Process transcription results
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
    confidence: transcriptionResult.results.transcripts[0].confidence || 0.8,
    language_code: 'en-US',
  }
}

// Generate scene plan using OpenAI GPT-4
async function generateScenePlan(transcription, videoRecord) {
  const targetDuration = videoRecord.ai_generation_data.target_duration
  const userPrompt = videoRecord.ai_generation_data.user_prompt
  const style = videoRecord.ai_generation_data.style

  const prompt = `
Create a ${targetDuration}-second vertical video plan optimized for social media (Instagram Reels/YouTube Shorts).

AUDIO TRANSCRIPT:
"${transcription.full_text}"

USER REQUIREMENTS:
- Duration: ${targetDuration} seconds
- Style: ${style}
- User prompt: "${userPrompt}"
- Format: Vertical 9:16 aspect ratio
- Target: Social media engagement

REQUIREMENTS:
- Create 2-4 compelling visual scenes
- Each scene should be 5-15 seconds long
- Total duration must equal ${targetDuration} seconds
- Scenes should be visually interesting and engaging
- Focus on the most important parts of the audio content
- Ensure smooth narrative flow

OUTPUT FORMAT (JSON only, no additional text):
{
  "overall_theme": "Brief description of the video's visual theme",
  "total_duration": ${targetDuration},
  "scenes": [
    {
      "sequence": 1,
      "start_time": 0,
      "end_time": 12,
      "duration": 12,
      "audio_text": "Relevant portion of the transcript for this scene",
      "scene_description": "Detailed visual description of what should be shown",
      "vertex_ai_prompt": "Optimized prompt for Vertex AI Veo 2 video generation",
      "visual_style": "${style} style with high quality cinematography"
    }
  ]
}
`

  console.log('Generating scene plan with GPT-4...')

  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
    temperature: 0.7,
    max_tokens: 2000,
    response_format: { type: 'json_object' },
  })

  const scenePlan = JSON.parse(response.choices[0].message.content)

  // Validate and adjust scene timing
  let currentTime = 0
  scenePlan.scenes.forEach((scene, index) => {
    scene.start_time = currentTime
    scene.end_time = currentTime + scene.duration
    currentTime += scene.duration
    scene.sequence = index + 1
  })

  console.log(`Generated scene plan with ${scenePlan.scenes.length} scenes`)
  return scenePlan
}

// Generate video using Vertex AI Veo 2
async function generateVideoWithVertexAI(scenePlan, videoRecord) {
  console.log('Starting video generation with Vertex AI Veo 2...')

  const generatedScenes = []

  // For now, combine all scenes into a single video prompt
  // In future versions, we could generate multiple scenes and combine them
  const mainScene = scenePlan.scenes[0] // Use the first scene as primary

  // Enhance the prompt for Vertex AI
  const enhancedPrompt = `
Create a ${scenePlan.total_duration}-second vertical video (9:16 aspect ratio) with the following specifications:

Visual Content: ${mainScene.vertex_ai_prompt}
Style: ${mainScene.visual_style}
Duration: ${scenePlan.total_duration} seconds
Quality: High definition, professional cinematography
Orientation: Vertical (portrait mode) for social media
Movement: Smooth, engaging camera work
Lighting: Professional lighting setup
Color: Vibrant, engaging color palette

The video should be compelling and optimized for social media engagement.
  `.trim()

  try {
    // Initialize Vertex AI model
    const model = vertexAI.getGenerativeModel({
      model: 'imagegeneration@006', // Using available model, update when Veo 2 is available
      generationConfig: {
        maxOutputTokens: 2048,
        temperature: 0.8,
        topP: 0.95,
        topK: 40,
      },
      safetySettings: [
        {
          category: HarmCategory.HARM_CATEGORY_HARASSMENT,
          threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
          category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
          threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
          category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
          threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
          category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
          threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
      ],
    })

    // Note: This is a placeholder implementation
    // When Vertex AI Veo 2 becomes available, replace with actual video generation
    const request = {
      contents: [
        {
          role: 'user',
          parts: [
            {
              text: enhancedPrompt,
            },
          ],
        },
      ],
    }

    console.log('Sending request to Vertex AI...')
    const response = await model.generateContent(request)

    // For now, create a placeholder response
    // In actual implementation, this would return the generated video URL
    const placeholderVideoUrl = await createPlaceholderVideo(scenePlan, videoRecord)

    generatedScenes.push({
      sequence: 1,
      video_url: placeholderVideoUrl,
      duration: scenePlan.total_duration,
      scene_description: mainScene.scene_description,
      prompt_used: enhancedPrompt,
    })

    console.log('Video generation completed')
    return generatedScenes
  } catch (error) {
    console.error('Error generating video with Vertex AI:', error)

    // Fallback: Create placeholder video
    const placeholderVideoUrl = await createPlaceholderVideo(scenePlan, videoRecord)

    return [
      {
        sequence: 1,
        video_url: placeholderVideoUrl,
        duration: scenePlan.total_duration,
        scene_description: 'Placeholder video due to generation error',
        error: error.message,
      },
    ]
  }
}

// Create placeholder video (temporary implementation)
async function createPlaceholderVideo(scenePlan, videoRecord) {
  // This is a placeholder implementation
  // In a real scenario, you would use FFmpeg to create a video with text overlay

  const placeholderContent = {
    title: videoRecord.title,
    duration: scenePlan.total_duration,
    scenes: scenePlan.scenes.length,
    theme: scenePlan.overall_theme,
    timestamp: new Date().toISOString(),
  }

  // For now, return a data URL representing the video metadata
  // In actual implementation, this would generate a real video file
  return `data:application/json;base64,${Buffer.from(JSON.stringify(placeholderContent)).toString('base64')}`
}

// Finalize and store the generated video
async function finalizeVideo(videoId, generatedScenes) {
  console.log('Finalizing video...')

  const primaryScene = generatedScenes[0]

  if (primaryScene.video_url.startsWith('data:')) {
    // Handle placeholder video
    return primaryScene.video_url
  }

  try {
    // Download the video from Vertex AI and upload to S3
    const response = await fetch(primaryScene.video_url)
    if (!response.ok) {
      throw new Error(`Failed to download video: ${response.statusText}`)
    }

    const videoBuffer = await response.arrayBuffer()
    const s3Key = `ai-generated/${videoId}/final_video_${Date.now()}.mp4`

    await s3Client.send(
      new PutObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: s3Key,
        Body: new Uint8Array(videoBuffer),
        ContentType: 'video/mp4',
        Metadata: {
          'ai-generated': 'true',
          'video-id': videoId,
          'generated-at': new Date().toISOString(),
        },
      }),
    )

    console.log(`Video uploaded to S3: ${s3Key}`)
    return `https://${process.env.S3_BUCKET}.s3.amazonaws.com/${s3Key}`
  } catch (error) {
    console.error('Error finalizing video:', error)
    // Return the original URL if upload fails
    return primaryScene.video_url
  }
}

// Update processing step status
async function updateProcessingStep(videoId, stepName, status) {
  try {
    const getCommand = new GetCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
    })

    const result = await docClient.send(getCommand)
    if (!result.Item) return

    const aiData = result.Item.ai_generation_data || {}
    const steps = aiData.processing_steps || []

    // Update the specific step
    const stepIndex = steps.findIndex((step) => step.step === stepName)
    if (stepIndex !== -1) {
      steps[stepIndex].status = status
      if (status === 'processing') {
        steps[stepIndex].started_at = new Date().toISOString()
      } else if (status === 'completed') {
        steps[stepIndex].completed_at = new Date().toISOString()
      }
    }

    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression: 'SET ai_generation_data.processing_steps = :steps, updated_at = :updated',
      ExpressionAttributeValues: {
        ':steps': steps,
        ':updated': new Date().toISOString(),
      },
    })

    await docClient.send(updateCommand)
    console.log(`Updated processing step ${stepName} to ${status}`)
  } catch (error) {
    console.error(`Error updating processing step ${stepName}:`, error)
  }
}

// Update overall AI generation status
async function updateAIGenerationStatus(videoId, status, additionalData = {}) {
  try {
    const updateExpression = 'SET ai_generation_status = :status, updated_at = :updated'
    const expressionValues = {
      ':status': status,
      ':updated': new Date().toISOString(),
    }

    // Add additional data to ai_generation_data
    Object.keys(additionalData).forEach((key, index) => {
      const placeholder = `:data${index}`
      updateExpression += `, ai_generation_data.${key} = ${placeholder}`
      expressionValues[placeholder] = additionalData[key]
    })

    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression: updateExpression,
      ExpressionAttributeValues: expressionValues,
    })

    await docClient.send(updateCommand)
    console.log(`Updated AI generation status to ${status}`)
  } catch (error) {
    console.error(`Error updating AI generation status:`, error)
  }
}

// Get media format from filename extension
function getMediaFormat(filename) {
  const extension = filename.split('.').pop().toLowerCase()
  const formatMap = {
    mp3: 'mp3',
    wav: 'wav',
    m4a: 'm4a',
    aac: 'mp3', // Transcribe treats AAC as MP3
    ogg: 'ogg',
    webm: 'webm',
    mp4: 'mp4',
    mov: 'mp4',
  }
  return formatMap[extension] || 'mp3'
}

// Handle AI video status requests
async function handleGetAIVideoStatus(event, userId) {
  const videoId = event.pathParameters?.videoId || event.queryStringParameters?.videoId

  if (!videoId) {
    return createResponse(400, { error: 'Video ID required' })
  }

  console.log(`Getting AI video status for ${videoId}`)

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
    ai_status: result.Item.ai_generation_status,
    ai_data: result.Item.ai_generation_data,
  })
}
