const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb')
const { TranscribeClient, GetTranscriptionJobCommand } = require('@aws-sdk/client-transcribe')
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3')

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)
const transcribeClient = new TranscribeClient({ region: process.env.AWS_REGION })
const s3Client = new S3Client({ region: process.env.AWS_REGION })

const tableName = process.env.DYNAMODB_TABLE

/**
 * EventBridge handler for AWS Transcribe job state changes
 * This replaces the inefficient polling mechanism
 */
exports.handler = async (event) => {
  console.log('🎯 EventBridge Transcription Event:', JSON.stringify(event, null, 2))

  try {
    const detail = event.detail
    const jobName = detail.TranscriptionJobName
    const jobStatus = detail.TranscriptionJobStatus

    console.log(`📋 Processing transcription job: ${jobName}, Status: ${jobStatus}`)

    // Get the full transcription job details
    const transcriptionJob = await getTranscriptionJobDetails(jobName)

    if (!transcriptionJob) {
      console.error(`❌ Could not retrieve transcription job details for: ${jobName}`)
      return
    }

    // Extract video ID from job name (format: transcription-{audioId}-{timestamp})
    const videoId = extractVideoIdFromJobName(jobName)

    if (!videoId) {
      console.error(`❌ Could not extract video ID from job name: ${jobName}`)
      return
    }

    console.log(`🎬 Found video ID: ${videoId}`)

    // Process based on job status
    if (jobStatus === 'COMPLETED') {
      await handleTranscriptionCompleted(videoId, transcriptionJob)
    } else if (jobStatus === 'FAILED') {
      await handleTranscriptionFailed(videoId, transcriptionJob)
    }

    console.log('✅ Transcription event processed successfully')
  } catch (error) {
    console.error('❌ Error processing transcription event:', error)
    throw error
  }
}

/**
 * Get full transcription job details from AWS Transcribe
 */
async function getTranscriptionJobDetails(jobName) {
  try {
    const command = new GetTranscriptionJobCommand({
      TranscriptionJobName: jobName,
    })

    const response = await transcribeClient.send(command)
    return response.TranscriptionJob
  } catch (error) {
    console.error('❌ Error getting transcription job details:', error)
    return null
  }
}

/**
 * Extract video ID from transcription job name
 * Job name format: transcription-{audioId}-{timestamp}
 */
function extractVideoIdFromJobName(jobName) {
  try {
    // Remove 'transcription-' prefix and '-{timestamp}' suffix
    const match = jobName.match(/^transcription-(.+)-\d+$/)
    if (match && match[1]) {
      // The audioId is what we need to find the video
      return match[1]
    }
    return null
  } catch (error) {
    console.error('❌ Error extracting video ID from job name:', error)
    return null
  }
}

/**
 * Handle successful transcription completion
 */
async function handleTranscriptionCompleted(audioId, transcriptionJob) {
  console.log(`✅ Handling completed transcription for audio: ${audioId}`)

  try {
    // Find the AI video that uses this audio
    const videoRecord = await findVideoByAudioId(audioId)

    if (!videoRecord) {
      console.error(`❌ Could not find video record for audio ID: ${audioId}`)
      return
    }

    const videoId = videoRecord.video_id
    console.log(`🎬 Found video: ${videoId}`)

    // Download and parse transcription results
    const transcriptionResults = await downloadTranscriptionResults(transcriptionJob)

    if (!transcriptionResults) {
      console.error(
        `❌ Could not download transcription results for job: ${transcriptionJob.TranscriptionJobName}`,
      )
      return
    }

    // Update video record with transcription completion
    await updateVideoTranscriptionStatus(videoId, 'completed', transcriptionResults)

    // Trigger next step in AI video pipeline (scene planning)
    await triggerScenePlanning(videoId, transcriptionResults)

    // Send real-time update to connected clients (if WebSocket is implemented)
    await notifyClientTranscriptionCompleted(videoRecord.user_id, videoId, transcriptionResults)

    console.log(`✅ Transcription processing completed for video: ${videoId}`)
  } catch (error) {
    console.error(`❌ Error handling transcription completion for audio ${audioId}:`, error)
    throw error
  }
}

/**
 * Handle failed transcription
 */
async function handleTranscriptionFailed(audioId, transcriptionJob) {
  console.log(`❌ Handling failed transcription for audio: ${audioId}`)

  try {
    // Find the AI video that uses this audio
    const videoRecord = await findVideoByAudioId(audioId)

    if (!videoRecord) {
      console.error(`❌ Could not find video record for audio ID: ${audioId}`)
      return
    }

    const videoId = videoRecord.video_id
    const failureReason = transcriptionJob.FailureReason || 'Unknown transcription failure'

    console.log(`🎬 Marking video ${videoId} as failed: ${failureReason}`)

    // Update video record with failure
    await updateVideoTranscriptionStatus(videoId, 'failed', null, failureReason)

    // Send real-time update to connected clients
    await notifyClientTranscriptionFailed(videoRecord.user_id, videoId, failureReason)

    console.log(`❌ Transcription failure processed for video: ${videoId}`)
  } catch (error) {
    console.error(`❌ Error handling transcription failure for audio ${audioId}:`, error)
    throw error
  }
}

/**
 * Find video record by source audio ID
 */
async function findVideoByAudioId(audioId) {
  try {
    // Query videos where source_audio_id matches
    const command = new DynamoDBDocumentClient.QueryCommand({
      TableName: tableName,
      IndexName: 'user_id-upload_date-index',
      FilterExpression:
        'ai_generation_data.source_audio_id = :audioId AND ai_project_type = :projectType',
      ExpressionAttributeValues: {
        ':audioId': audioId,
        ':projectType': 'ai_generated',
      },
    })

    const result = await docClient.send(command)

    if (result.Items && result.Items.length > 0) {
      return result.Items[0] // Return the first matching video
    }

    return null
  } catch (error) {
    console.error('❌ Error finding video by audio ID:', error)
    return null
  }
}

/**
 * Download transcription results from S3
 */
async function downloadTranscriptionResults(transcriptionJob) {
  try {
    const transcriptFileUri = transcriptionJob.Transcript?.TranscriptFileUri

    if (!transcriptFileUri) {
      console.error('❌ No transcript file URI found in transcription job')
      return null
    }

    console.log(`📁 Downloading transcription results from: ${transcriptFileUri}`)

    // Parse S3 URI to get bucket and key
    const s3Uri = new URL(transcriptFileUri)
    const bucket = s3Uri.hostname.split('.')[0] // Extract bucket from hostname
    const key = s3Uri.pathname.substring(1) // Remove leading slash

    // Download the transcript file
    const command = new GetObjectCommand({
      Bucket: bucket,
      Key: key,
    })

    const response = await s3Client.send(command)
    const transcriptJson = await response.Body.transformToString()
    const transcriptData = JSON.parse(transcriptJson)

    console.log('✅ Transcription results downloaded and parsed')

    // Extract useful information
    return {
      full_text: transcriptData.results?.transcripts?.[0]?.transcript || '',
      confidence: calculateAverageConfidence(transcriptData.results?.items || []),
      segments: extractSegments(transcriptData.results?.items || []),
      speaker_labels: transcriptData.results?.speaker_labels || null,
      raw_data: transcriptData, // Keep full data for advanced processing
    }
  } catch (error) {
    console.error('❌ Error downloading transcription results:', error)
    return null
  }
}

/**
 * Calculate average confidence from transcription items
 */
function calculateAverageConfidence(items) {
  if (!items || items.length === 0) return 0

  const confidenceValues = items
    .filter((item) => item.alternatives && item.alternatives[0] && item.alternatives[0].confidence)
    .map((item) => parseFloat(item.alternatives[0].confidence))

  if (confidenceValues.length === 0) return 0

  const sum = confidenceValues.reduce((acc, val) => acc + val, 0)
  return sum / confidenceValues.length
}

/**
 * Extract segments with timestamps
 */
function extractSegments(items) {
  if (!items || items.length === 0) return []

  return items
    .filter((item) => item.type === 'pronunciation')
    .map((item) => ({
      text: item.alternatives?.[0]?.content || '',
      start_time: parseFloat(item.start_time || 0),
      end_time: parseFloat(item.end_time || 0),
      confidence: parseFloat(item.alternatives?.[0]?.confidence || 0),
    }))
}

/**
 * Update video record with transcription status
 */
async function updateVideoTranscriptionStatus(
  videoId,
  status,
  transcriptionResults = null,
  failureReason = null,
) {
  try {
    const updateExpression = []
    const expressionAttributeValues = {}
    const expressionAttributeNames = {}

    // Update transcription step status
    updateExpression.push('#steps[0].#status = :status')
    expressionAttributeNames['#steps'] = 'ai_generation_data.processing_steps'
    expressionAttributeNames['#status'] = 'status'
    expressionAttributeValues[':status'] = status

    if (status === 'completed') {
      updateExpression.push('#steps[0].completed_at = :completedAt')
      expressionAttributeValues[':completedAt'] = new Date().toISOString()

      if (transcriptionResults) {
        updateExpression.push('ai_generation_data.transcription_results = :results')
        expressionAttributeValues[':results'] = transcriptionResults
      }
    } else if (status === 'failed' && failureReason) {
      updateExpression.push('#steps[0].failure_reason = :failureReason')
      expressionAttributeValues[':failureReason'] = failureReason
    }

    // Always update the updated_at timestamp
    updateExpression.push('updated_at = :updatedAt')
    expressionAttributeValues[':updatedAt'] = new Date().toISOString()

    const command = new UpdateCommand({
      TableName: tableName,
      Key: { video_id: videoId },
      UpdateExpression: `SET ${updateExpression.join(', ')}`,
      ExpressionAttributeNames: expressionAttributeNames,
      ExpressionAttributeValues: expressionAttributeValues,
      ReturnValues: 'UPDATED_NEW',
    })

    await docClient.send(command)
    console.log(`✅ Updated video ${videoId} transcription status to: ${status}`)
  } catch (error) {
    console.error(`❌ Error updating video transcription status:`, error)
    throw error
  }
}

/**
 * Trigger the next step in AI video pipeline (scene planning)
 */
async function triggerScenePlanning(videoId, _transcriptionResults) {
  try {
    console.log(`🎬 Triggering scene planning for video: ${videoId}`)

    // Update scene planning step to processing
    const command = new UpdateCommand({
      TableName: tableName,
      Key: { video_id: videoId },
      UpdateExpression:
        'SET ai_generation_data.processing_steps[1].#status = :status, ai_generation_data.processing_steps[1].started_at = :startedAt',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':status': 'processing',
        ':startedAt': new Date().toISOString(),
      },
    })

    await docClient.send(command)

    // Here you would typically invoke another Lambda or start the scene planning process
    // For now, we'll just log that it's ready
    console.log(`✅ Scene planning triggered for video: ${videoId}`)
  } catch (error) {
    console.error(`❌ Error triggering scene planning:`, error)
    throw error
  }
}

/**
 * Send real-time notification to connected clients (WebSocket)
 */
async function notifyClientTranscriptionCompleted(userId, videoId, _transcriptionResults) {
  try {
    // This would send WebSocket notifications to connected clients
    // Implementation depends on your WebSocket setup
    console.log(
      `📡 Would notify user ${userId} about transcription completion for video ${videoId}`,
    )

    // TODO: Implement WebSocket notification
    // const connections = await getActiveConnectionsForUser(userId)
    // for (const connection of connections) {
    //   await sendWebSocketMessage(connection.connectionId, {
    //     type: 'transcription_completed',
    //     videoId,
    //     transcriptionResults
    //   })
    // }
  } catch (error) {
    console.error('❌ Error sending transcription completion notification:', error)
    // Don't throw - notifications are not critical
  }
}

/**
 * Send real-time notification about transcription failure
 */
async function notifyClientTranscriptionFailed(userId, videoId, failureReason) {
  try {
    console.log(
      `📡 Would notify user ${userId} about transcription failure for video ${videoId}: ${failureReason}`,
    )

    // TODO: Implement WebSocket notification
  } catch (error) {
    console.error('❌ Error sending transcription failure notification:', error)
    // Don't throw - notifications are not critical
  }
}
