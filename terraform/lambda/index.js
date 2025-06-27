const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, PutCommand, QueryCommand } = require('@aws-sdk/lib-dynamodb')
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3')
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner')

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)
const s3Client = new S3Client({ region: process.env.AWS_REGION })

const tableName = process.env.DYNAMODB_TABLE
const audioBucket = process.env.AUDIO_BUCKET
const corsOrigin = process.env.CORS_ORIGIN || '*'

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': corsOrigin,
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers':
    'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token',
}

// Response helper
const createResponse = (statusCode, body) => ({
  statusCode,
  headers: corsHeaders,
  body: JSON.stringify(body),
})

// Audio table structure (extends video_metadata table)
const createAudioMetadata = (audioId, userId, userEmail, data) => ({
  video_id: audioId, // Reusing video_id field for audio
  user_id: userId,
  user_email: userEmail,
  title: data.title.trim(),
  filename: data.filename,
  bucket_location: `audio/${userId}/${audioId}/${data.filename}`,
  upload_date: new Date().toISOString(),
  file_size: data.file_size || null,
  content_type: data.content_type || null,
  duration: data.duration || null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  // Audio-specific fields
  media_type: 'audio', // Distinguish from video entries
  transcription_status: 'pending',
})

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2))

  try {
    const httpMethod = event.httpMethod
    const path = event.resource || event.path

    // Handle CORS preflight
    if (httpMethod === 'OPTIONS') {
      return createResponse(200, { message: 'CORS preflight' })
    }

    // Extract user ID from Cognito JWT token
    let userId = null
    let userEmail = null
    console.log('Request context:', JSON.stringify(event.requestContext, null, 2))

    if (event.requestContext && event.requestContext.authorizer) {
      console.log('Authorizer context:', JSON.stringify(event.requestContext.authorizer, null, 2))
      // Cognito puts user info in the authorizer context
      const claims = event.requestContext.authorizer.claims
      if (claims) {
        userId = claims.sub // 'sub' is the unique user ID in Cognito
        userEmail = claims.email
        console.log('Authenticated user:', userId, userEmail)
      } else {
        console.log('No claims found in authorizer context')
      }
    } else {
      console.log('No authorizer context found')
    }

    // Route audio requests
    if (path.includes('/audio')) {
      return await handleAudioRequest(httpMethod, path, event, userId, userEmail)
    }

    // Route video upload URL requests
    if (path.includes('/videos/upload-url') && httpMethod === 'POST') {
      return await handleVideoUploadUrl(event, userId, userEmail)
    }

    // Handle video requests (existing functionality)
    return await handleVideoRequest(httpMethod, event, userId, userEmail)
  } catch (error) {
    console.error('Error:', error)

    return createResponse(500, {
      error: 'Internal server error',
      message: error.message,
      ...(process.env.NODE_ENV === 'development' && { stack: error.stack }),
    })
  }
}

// Handle audio-related requests
async function handleAudioRequest(httpMethod, path, event, userId, userEmail) {
  // Check authentication for all audio operations
  if (!userId) {
    return createResponse(401, {
      error: 'Authentication required',
    })
  }

  // Handle audio upload URL generation
  if (path.includes('/audio/upload-url') && httpMethod === 'POST') {
    return await handleAudioUploadUrl(event, userId, userEmail)
  }

  // Handle audio metadata operations
  if (path === '/audio') {
    if (httpMethod === 'POST') {
      return await handleAudioMetadataCreate(event, userId, userEmail)
    }

    if (httpMethod === 'GET') {
      return await handleAudioList(userId)
    }
  }

  return createResponse(404, {
    error: 'Audio endpoint not found',
  })
}

// Generate presigned URL for audio upload
async function handleAudioUploadUrl(event, userId, userEmail) {
  try {
    const body = JSON.parse(event.body || '{}')

    // Validate required fields
    if (!body.title || !body.filename) {
      return createResponse(400, {
        error: 'Missing required fields: title, filename',
      })
    }

    // Generate unique audio ID
    const audioId = `${userId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Create S3 key
    const s3Key = `audio/${userId}/${audioId}/${body.filename}`

    // Generate presigned URL for upload
    const uploadCommand = new PutObjectCommand({
      Bucket: audioBucket,
      Key: s3Key,
      ContentType: body.content_type || 'audio/mpeg',
    })

    const uploadUrl = await getSignedUrl(s3Client, uploadCommand, {
      expiresIn: 3600, // 1 hour
    })

    // Prepare audio metadata
    const audioMetadata = createAudioMetadata(audioId, userId, userEmail, {
      title: body.title,
      filename: body.filename,
      file_size: body.file_size,
      content_type: body.content_type,
      duration: body.duration,
    })

    return createResponse(200, {
      success: true,
      upload_url: uploadUrl,
      audio: audioMetadata,
    })
  } catch (error) {
    console.error('Error generating audio upload URL:', error)
    return createResponse(500, {
      error: 'Failed to generate upload URL',
      message: error.message,
    })
  }
}

// Save audio metadata after successful upload
async function handleAudioMetadataCreate(event, userId, userEmail) {
  try {
    const body = JSON.parse(event.body || '{}')

    // Validate required fields
    if (!body.audio_id || !body.title || !body.filename || !body.bucket_location) {
      return createResponse(400, {
        error: 'Missing required fields: audio_id, title, filename, bucket_location',
      })
    }

    // Create complete audio metadata
    const audioMetadata = {
      video_id: body.audio_id, // Reusing video_id field
      user_id: userId,
      user_email: userEmail,
      title: body.title.trim(),
      filename: body.filename,
      bucket_location: body.bucket_location,
      upload_date: new Date().toISOString(),
      file_size: body.file_size || null,
      content_type: body.content_type || null,
      duration: body.duration || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      media_type: 'audio',
      transcription_status: 'pending',
    }

    // Save to DynamoDB
    const putCommand = new PutCommand({
      TableName: tableName,
      Item: audioMetadata,
    })

    await docClient.send(putCommand)

    return createResponse(201, {
      success: true,
      message: 'Audio metadata saved successfully',
      audio: {
        audio_id: audioMetadata.video_id, // Map video_id back to audio_id for frontend
        user_id: audioMetadata.user_id,
        user_email: audioMetadata.user_email,
        title: audioMetadata.title,
        filename: audioMetadata.filename,
        bucket_location: audioMetadata.bucket_location,
        upload_date: audioMetadata.upload_date,
        file_size: audioMetadata.file_size,
        content_type: audioMetadata.content_type,
        duration: audioMetadata.duration,
        created_at: audioMetadata.created_at,
        updated_at: audioMetadata.updated_at,
        transcription_status: audioMetadata.transcription_status,
        transcription_data: audioMetadata.transcription_data,
      },
    })
  } catch (error) {
    console.error('Error saving audio metadata:', error)
    return createResponse(500, {
      error: 'Failed to save audio metadata',
      message: error.message,
    })
  }
}

// List user's audio files
async function handleAudioList(userId) {
  try {
    // Query audio files by user_id and media_type
    const queryCommand = new QueryCommand({
      TableName: tableName,
      IndexName: 'user_id-upload_date-index',
      KeyConditionExpression: 'user_id = :userId',
      FilterExpression: 'media_type = :mediaType',
      ExpressionAttributeValues: {
        ':userId': userId,
        ':mediaType': 'audio',
      },
      ScanIndexForward: false, // Sort by upload_date descending (newest first)
    })

    const result = await docClient.send(queryCommand)
    const audioFiles = result.Items || []

    // Format response to match AudioService expectations
    const formattedAudioFiles = audioFiles.map((item) => ({
      audio_id: item.video_id, // Map back to audio_id
      user_id: item.user_id,
      user_email: item.user_email,
      title: item.title,
      filename: item.filename,
      bucket_location: item.bucket_location,
      upload_date: item.upload_date,
      file_size: item.file_size,
      content_type: item.content_type,
      duration: item.duration,
      created_at: item.created_at,
      updated_at: item.updated_at,
      transcription_status: item.transcription_status,
      transcription_data: item.transcription_data,
    }))

    return createResponse(200, {
      success: true,
      count: formattedAudioFiles.length,
      audio_files: formattedAudioFiles,
    })
  } catch (error) {
    console.error('Error listing audio files:', error)
    return createResponse(500, {
      error: 'Failed to load audio files',
      message: error.message,
    })
  }
}

// Generate presigned URL for video upload
async function handleVideoUploadUrl(event, userId, userEmail) {
  try {
    const body = JSON.parse(event.body || '{}')

    // Validate required fields
    if (!body.title || !body.filename) {
      return createResponse(400, {
        error: 'Missing required fields: title, filename',
      })
    }

    // Generate unique video ID
    const videoId = `${userId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Create S3 key for video
    const s3Key = `videos/${userId}/${videoId}/${body.filename}`

    // Generate presigned URL for upload to main video bucket
    const uploadCommand = new PutObjectCommand({
      Bucket: process.env.S3_BUCKET_NAME,
      Key: s3Key,
      ContentType: body.content_type || 'video/mp4',
    })

    const uploadUrl = await getSignedUrl(s3Client, uploadCommand, {
      expiresIn: 3600, // 1 hour
    })

    // Prepare video metadata for frontend
    const videoMetadata = {
      video_id: videoId,
      user_id: userId,
      user_email: userEmail,
      title: body.title,
      filename: body.filename,
      bucket_location: s3Key,
      upload_date: new Date().toISOString(),
      file_size: body.file_size,
      content_type: body.content_type,
      duration: body.duration,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      media_type: 'video',
    }

    return createResponse(200, {
      success: true,
      upload_url: uploadUrl,
      video: videoMetadata,
    })
  } catch (error) {
    console.error('Error generating video upload URL:', error)
    return createResponse(500, {
      error: 'Failed to generate upload URL',
      message: error.message,
    })
  }
}

// Handle video requests (existing functionality)
async function handleVideoRequest(httpMethod, event, userId, userEmail) {
  // Handle POST - Create video metadata
  if (httpMethod === 'POST') {
    // Check if user is authenticated
    if (!userId) {
      return createResponse(401, {
        error: 'Authentication required',
      })
    }

    const body = JSON.parse(event.body || '{}')

    // Validate required fields (username no longer required - comes from JWT)
    if (!body.title || !body.filename || !body.bucketLocation) {
      return createResponse(400, {
        error: 'Missing required fields: title, filename, bucketLocation',
      })
    }

    // Check if this is an admin upload for another user
    const targetUserId = body.adminUploadUserId || userId
    const isAdminUpload = body.adminUploadUserId && body.adminUploadUserId !== userId

    // If admin upload, verify user is admin
    if (isAdminUpload) {
      const userGroups = event.requestContext.authorizer.claims['cognito:groups'] || []
      const isAdmin = userGroups.includes('admin')

      if (!isAdmin) {
        return createResponse(403, {
          error: 'Admin privileges required to upload videos for other users',
        })
      }
    }

    // Generate unique video ID using target user ID
    const videoId = `${targetUserId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Create metadata record
    const videoMetadata = {
      video_id: videoId,
      user_id: targetUserId, // Use target user ID (could be different from authenticated user)
      user_email: isAdminUpload ? `Admin upload by ${userEmail}` : userEmail, // Indicate admin upload
      title: body.title.trim(),
      filename: body.filename,
      bucket_location: body.bucketLocation,
      upload_date: new Date().toISOString(),
      file_size: body.fileSize || null,
      content_type: body.contentType || null,
      duration: body.duration || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      media_type: 'video', // Distinguish from audio entries
    }

    // Save to DynamoDB
    const putCommand = new PutCommand({
      TableName: tableName,
      Item: videoMetadata,
    })

    await docClient.send(putCommand)

    return createResponse(201, {
      success: true,
      videoId: videoId,
      message: 'Video metadata saved successfully',
      data: videoMetadata,
    })
  }

  // Handle GET - List videos (for authenticated user only)
  if (httpMethod === 'GET') {
    // Check if user is authenticated
    if (!userId) {
      return createResponse(401, {
        error: 'Authentication required',
      })
    }

    // Query videos by user_id using GSI (filter out audio files)
    const queryCommand = new QueryCommand({
      TableName: tableName,
      IndexName: 'user_id-upload_date-index',
      KeyConditionExpression: 'user_id = :userId',
      FilterExpression: 'attribute_not_exists(media_type) OR media_type = :mediaType',
      ExpressionAttributeValues: {
        ':userId': userId,
        ':mediaType': 'video',
      },
      ScanIndexForward: false, // Sort by upload_date descending (newest first)
    })

    const result = await docClient.send(queryCommand)
    const videos = result.Items || []

    return createResponse(200, {
      success: true,
      count: videos.length,
      videos: videos,
    })
  }

  // Method not allowed
  return createResponse(405, {
    error: `Method ${httpMethod} not allowed`,
  })
}
