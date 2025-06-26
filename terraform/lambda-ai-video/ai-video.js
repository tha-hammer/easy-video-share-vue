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

// Asynchronous AI video processing pipeline (REAL implementation - Step 1: Transcription)
async function processAIVideoAsync(videoId, userId, request) {
  console.log(`🎬 Starting REAL AI video processing for video ${videoId}`)
  console.log(`📋 Request details:`, JSON.stringify(request, null, 2))

  try {
    // Step 1: REAL Audio Transcription with AWS Transcribe
    console.log(`🎤 Step 1: Starting REAL audio transcription for audio ID: ${request.audioId}`)
    await updateProcessingStep(videoId, 'transcription', 'processing')

    const transcriptionResult = await performRealTranscription(request.audioId, userId)
    console.log(
      `✅ Transcription completed successfully:`,
      JSON.stringify(transcriptionResult, null, 2),
    )

    // Store transcription results in AI generation data
    await updateAIGenerationStatus(videoId, 'processing', {
      audio_transcription: transcriptionResult,
    })

    await updateProcessingStep(videoId, 'transcription', 'completed')

    // Step 2: Simulate scene planning (60 seconds) - TODO: Implement in Step 2
    console.log(`🎭 Step 2: Starting scene planning (currently simulated)`)
    await updateProcessingStep(videoId, 'scene_planning', 'processing')
    await simulateProcessing(60000) // 60 seconds
    await updateProcessingStep(videoId, 'scene_planning', 'completed')

    // Step 3: Simulate video generation (120 seconds) - TODO: Implement in Step 3
    console.log(`🎥 Step 3: Starting video generation (currently simulated)`)
    await updateProcessingStep(videoId, 'video_generation', 'processing')
    await simulateProcessing(120000) // 120 seconds
    await updateProcessingStep(videoId, 'video_generation', 'completed')

    // Step 4: Simulate finalization (30 seconds) - TODO: Implement in Step 4
    console.log(`🎬 Step 4: Starting finalization (currently simulated)`)
    await updateProcessingStep(videoId, 'finalization', 'processing')
    await simulateProcessing(30000) // 30 seconds
    await updateProcessingStep(videoId, 'finalization', 'completed')

    // Mark as completed
    await updateAIGenerationStatus(videoId, 'completed', {
      completed_at: new Date().toISOString(),
      generation_time: 240000, // 4 minutes
      final_video_url: `https://example.com/mock-video-${videoId}.mp4`, // Mock URL
    })

    console.log(`✅ AI video generation completed for ${videoId}`)
  } catch (error) {
    console.error(`❌ AI video generation failed for ${videoId}:`, error)
    await updateAIGenerationStatus(videoId, 'failed', {
      error_message: error.message,
      failed_at: new Date().toISOString(),
    })
  }
}

// REAL Audio Transcription with AWS Transcribe
async function performRealTranscription(audioId, userId) {
  console.log(`🎤 Starting REAL transcription for audio ID: ${audioId}`)

  try {
    // Step 1: Get audio metadata from DynamoDB
    console.log(`📋 Step 1.1: Retrieving audio metadata for audio ID: ${audioId}`)
    const audioMetadata = await getAudioMetadata(audioId, userId)
    console.log(`✅ Audio metadata retrieved:`, JSON.stringify(audioMetadata, null, 2))

    // Step 2: Start AWS Transcribe job
    console.log(`🎤 Step 1.2: Starting AWS Transcribe job`)
    const transcriptionJobName = `transcription-${audioId}-${Date.now()}`
    const transcriptionJob = await startTranscriptionJob(transcriptionJobName, audioMetadata)
    console.log(`✅ Transcription job started:`, JSON.stringify(transcriptionJob, null, 2))

    // Step 3: Poll for job completion
    console.log(`⏳ Step 1.3: Polling for transcription job completion`)
    const transcriptionResult = await pollTranscriptionJob(transcriptionJobName)
    console.log(`✅ Transcription job completed:`, JSON.stringify(transcriptionResult, null, 2))

    // Step 4: Parse and store transcription results
    console.log(`💾 Step 1.4: Storing transcription results`)
    const processedTranscription = await processTranscriptionResults(transcriptionResult, audioId)
    console.log(
      `✅ Transcription results processed and stored:`,
      JSON.stringify(processedTranscription, null, 2),
    )

    return processedTranscription
  } catch (error) {
    console.error(`❌ Transcription failed for audio ${audioId}:`, error)
    throw error
  }
}

// Get audio metadata from DynamoDB
async function getAudioMetadata(audioId, userId) {
  console.log(`🔍 Retrieving audio metadata for audio ID: ${audioId}, user ID: ${userId}`)

  try {
    // Query for audio file in the audio table (assuming separate audio table)
    // If using same table, we'll need to filter by audio_id pattern
    const queryCommand = new QueryCommand({
      TableName: process.env.DYNAMODB_TABLE, // Using same table for now
      KeyConditionExpression: 'video_id = :audioId',
      FilterExpression: 'user_id = :userId',
      ExpressionAttributeValues: {
        ':audioId': audioId,
        ':userId': userId,
      },
    })

    const result = await docClient.send(queryCommand)
    console.log(`📋 Query result:`, JSON.stringify(result, null, 2))

    if (!result.Items || result.Items.length === 0) {
      throw new Error(`Audio file not found: ${audioId}`)
    }

    const audioItem = result.Items[0]
    console.log(`✅ Audio metadata found:`, JSON.stringify(audioItem, null, 2))

    return {
      audio_id: audioItem.video_id, // Using video_id field for audio_id
      user_id: audioItem.user_id,
      title: audioItem.title,
      filename: audioItem.filename,
      bucket_location: audioItem.bucket_location,
      file_size: audioItem.file_size,
      content_type: audioItem.content_type,
      duration: audioItem.duration,
    }
  } catch (error) {
    console.error(`❌ Error retrieving audio metadata:`, error)
    throw error
  }
}

// Start AWS Transcribe job
async function startTranscriptionJob(jobName, audioMetadata) {
  console.log(`🎤 Starting AWS Transcribe job: ${jobName}`)
  console.log(`📋 Audio metadata:`, JSON.stringify(audioMetadata, null, 2))

  try {
    // Use AUDIO_BUCKET for audio files, fallback to S3_BUCKET if not set
    const audioBucket = process.env.AUDIO_BUCKET || process.env.S3_BUCKET
    const s3Uri = `s3://${audioBucket}/${audioMetadata.bucket_location}`
    console.log(`📁 S3 URI for transcription: ${s3Uri}`)
    console.log(`📦 Using bucket: ${audioBucket}`)

    const startCommand = new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      LanguageCode: 'en-US', // Default to English, could be made configurable
      MediaFormat: getMediaFormatFromContentType(audioMetadata.content_type),
      Media: {
        MediaFileUri: s3Uri,
      },
      OutputBucketName: audioBucket, // Use same bucket for output
      OutputKey: `transcriptions/${jobName}.json`,
      Settings: {
        ShowSpeakerLabels: true,
        MaxSpeakerLabels: 2, // Assuming single speaker for now
        ShowConfidence: true,
      },
    })

    console.log(
      `🚀 Sending StartTranscriptionJobCommand:`,
      JSON.stringify(startCommand.input, null, 2),
    )
    const result = await transcribeClient.send(startCommand)
    console.log(`✅ Transcription job started successfully:`, JSON.stringify(result, null, 2))

    return result
  } catch (error) {
    console.error(`❌ Error starting transcription job:`, error)
    throw error
  }
}

// Poll for transcription job completion
async function pollTranscriptionJob(jobName) {
  console.log(`⏳ Polling for transcription job completion: ${jobName}`)

  const maxWaitTime = 10 * 60 * 1000 // 10 minutes
  const pollInterval = 5000 // 5 seconds
  const startTime = Date.now()

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        console.log(`🔄 Polling transcription job status: ${jobName}`)

        const getCommand = new GetTranscriptionJobCommand({
          TranscriptionJobName: jobName,
        })

        const result = await transcribeClient.send(getCommand)
        const job = result.TranscriptionJob
        console.log(`📊 Job status: ${job.TranscriptionJobStatus}`)

        if (job.TranscriptionJobStatus === 'COMPLETED') {
          console.log(`✅ Transcription job completed successfully`)
          console.log(`📁 Output location: ${job.Transcript.TranscriptFileUri}`)
          resolve(job)
          return
        }

        if (job.TranscriptionJobStatus === 'FAILED') {
          console.error(`❌ Transcription job failed:`, job.FailureReason)
          reject(new Error(`Transcription failed: ${job.FailureReason}`))
          return
        }

        // Check timeout
        if (Date.now() - startTime > maxWaitTime) {
          console.error(`⏰ Transcription job timed out after ${maxWaitTime / 1000} seconds`)
          reject(new Error('Transcription job timed out'))
          return
        }

        // Continue polling
        console.log(`⏳ Job still in progress, polling again in ${pollInterval / 1000} seconds...`)
        setTimeout(poll, pollInterval)
      } catch (error) {
        console.error(`❌ Error polling transcription job:`, error)
        reject(error)
      }
    }

    // Start polling
    poll()
  })
}

// Process transcription results
async function processTranscriptionResults(transcriptionJob, audioId) {
  console.log(`🔍 Processing transcription results for audio: ${audioId}`)

  try {
    // Get the transcription file from S3
    const transcriptUri = transcriptionJob.Transcript.TranscriptFileUri
    console.log(`📁 Transcript URI: ${transcriptUri}`)

    // Use AUDIO_BUCKET for audio files, fallback to S3_BUCKET if not set
    const audioBucket = process.env.AUDIO_BUCKET || process.env.S3_BUCKET

    // Extract the S3 key from the URI
    const s3Key = transcriptUri.replace(
      `https://${audioBucket}.s3.${process.env.AWS_REGION}.amazonaws.com/`,
      '',
    )
    console.log(`🔑 S3 Key: ${s3Key}`)
    console.log(`📦 Using bucket: ${audioBucket}`)

    // Download the transcript file
    const getObjectCommand = new GetObjectCommand({
      Bucket: audioBucket,
      Key: s3Key,
    })

    const transcriptResponse = await s3Client.send(getObjectCommand)
    const transcriptText = await transcriptResponse.Body.transformToString()
    const transcriptData = JSON.parse(transcriptText)
    console.log(`📄 Raw transcript data:`, JSON.stringify(transcriptData, null, 2))

    // Process the transcript data
    const processedTranscription = {
      full_text: transcriptData.results.transcripts[0].transcript,
      confidence: transcriptData.results.transcripts[0].confidence || 0.95,
      language_code: transcriptData.results.language_code || 'en-US',
      segments: transcriptData.results.items.map((item) => ({
        start_time: parseFloat(item.start_time),
        end_time: parseFloat(item.end_time),
        text: item.alternatives[0].content,
        confidence: parseFloat(item.alternatives[0].confidence),
      })),
      speaker_labels: transcriptData.results.speaker_labels?.segments || [],
      created_at: new Date().toISOString(),
    }

    console.log(`✅ Processed transcription:`, JSON.stringify(processedTranscription, null, 2))

    // Store transcription results in DynamoDB
    await storeTranscriptionResults(audioId, processedTranscription)

    return processedTranscription
  } catch (error) {
    console.error(`❌ Error processing transcription results:`, error)
    throw error
  }
}

// Store transcription results in DynamoDB
async function storeTranscriptionResults(audioId, transcriptionData) {
  console.log(`💾 Storing transcription results for audio: ${audioId}`)

  try {
    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: audioId },
      UpdateExpression: `
        SET transcription_status = :status,
            transcription_data = :data,
            updated_at = :updated
      `,
      ExpressionAttributeValues: {
        ':status': 'completed',
        ':data': transcriptionData,
        ':updated': new Date().toISOString(),
      },
    })

    await docClient.send(updateCommand)
    console.log(`✅ Transcription results stored successfully`)
  } catch (error) {
    console.error(`❌ Error storing transcription results:`, error)
    throw error
  }
}

// Helper function to get media format from content type
function getMediaFormatFromContentType(contentType) {
  console.log(`🔍 Determining media format from content type: ${contentType}`)

  const formatMap = {
    'audio/mpeg': 'mp3',
    'audio/mp3': 'mp3',
    'audio/wav': 'wav',
    'audio/wave': 'wav',
    'audio/x-wav': 'wav',
    'audio/mp4': 'mp4',
    'audio/m4a': 'm4a',
    'audio/aac': 'aac',
    'audio/x-aac': 'aac',
    'audio/ogg': 'ogg',
    'audio/oga': 'oga',
    'audio/webm': 'webm',
    'audio/flac': 'flac',
    'audio/x-flac': 'flac',
  }

  const format = formatMap[contentType] || 'mp3'
  console.log(`✅ Determined media format: ${format}`)
  return format
}

// Update processing step status
async function updateProcessingStep(videoId, stepName, status) {
  try {
    // First, get the current video record to see existing steps
    const getCommand = new GetCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
    })

    const result = await docClient.send(getCommand)
    if (!result.Item) {
      console.error(`Video ${videoId} not found for step update`)
      return
    }

    // Get existing processing steps or create new ones
    let processingSteps = result.Item.ai_generation_data?.processing_steps || []

    // Find the step to update
    let stepIndex = processingSteps.findIndex((step) => step.step === stepName)

    if (stepIndex === -1) {
      // Step doesn't exist, add it
      processingSteps.push({
        step: stepName,
        status: status,
        started_at: status === 'processing' ? new Date().toISOString() : undefined,
        completed_at: status === 'completed' ? new Date().toISOString() : undefined,
      })
    } else {
      // Update existing step
      processingSteps[stepIndex] = {
        ...processingSteps[stepIndex],
        status: status,
        started_at:
          status === 'processing'
            ? new Date().toISOString()
            : processingSteps[stepIndex].started_at,
        completed_at:
          status === 'completed'
            ? new Date().toISOString()
            : processingSteps[stepIndex].completed_at,
      }
    }

    // Update the entire processing_steps array
    const updateCommand = new UpdateCommand({
      TableName: process.env.DYNAMODB_TABLE,
      Key: { video_id: videoId },
      UpdateExpression: 'SET ai_generation_data.processing_steps = :steps, updated_at = :updated',
      ExpressionAttributeValues: {
        ':steps': processingSteps,
        ':updated': new Date().toISOString(),
      },
    })

    await docClient.send(updateCommand)
    console.log(`Updated step ${stepName} to ${status} for video ${videoId}`)
    console.log(`Current processing steps:`, JSON.stringify(processingSteps, null, 2))
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
