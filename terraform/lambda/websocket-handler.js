const { DynamoDBClient } = require('@aws-sdk/client-dynamodb')
const {
  DynamoDBDocumentClient,
  PutCommand,
  DeleteCommand,
  QueryCommand,
} = require('@aws-sdk/lib-dynamodb')
const {
  ApiGatewayManagementApiClient,
  PostToConnectionCommand,
} = require('@aws-sdk/client-apigatewaymanagementapi')

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION })
const docClient = DynamoDBDocumentClient.from(dynamoClient)

const connectionsTable = `${process.env.DYNAMODB_TABLE}-websocket-connections`

/**
 * WebSocket handler for real-time AI video status updates
 */
exports.handler = async (event) => {
  console.log('🔌 WebSocket Event:', JSON.stringify(event, null, 2))

  const { requestContext } = event
  const { connectionId, routeKey, domainName, stage } = requestContext

  const apiGwManagementApi = new ApiGatewayManagementApiClient({
    endpoint: `https://${domainName}/${stage}`,
    region: process.env.AWS_REGION,
  })

  try {
    switch (routeKey) {
      case '$connect':
        return await handleConnect(connectionId, event)
      case '$disconnect':
        return await handleDisconnect(connectionId)
      case '$default':
        return await handleMessage(connectionId, event, apiGwManagementApi)
      default:
        console.log(`⚠️ Unknown route: ${routeKey}`)
        return { statusCode: 400 }
    }
  } catch (error) {
    console.error('❌ WebSocket handler error:', error)
    return { statusCode: 500 }
  }
}

/**
 * Handle WebSocket connection
 */
async function handleConnect(connectionId, event) {
  try {
    console.log(`🔗 New WebSocket connection: ${connectionId}`)

    // Extract user ID from authorization context
    const userId = extractUserIdFromEvent(event)

    if (!userId) {
      console.error('❌ No user ID found in connection event')
      return { statusCode: 401 }
    }

    // Store connection in DynamoDB
    const connection = {
      connectionId,
      userId,
      connectedAt: new Date().toISOString(),
      ttl: Math.floor(Date.now() / 1000) + 24 * 60 * 60, // 24 hours TTL
    }

    await docClient.send(
      new PutCommand({
        TableName: connectionsTable,
        Item: connection,
      }),
    )

    console.log(`✅ WebSocket connection stored for user: ${userId}`)
    return { statusCode: 200 }
  } catch (error) {
    console.error('❌ Error handling WebSocket connect:', error)
    return { statusCode: 500 }
  }
}

/**
 * Handle WebSocket disconnection
 */
async function handleDisconnect(connectionId) {
  try {
    console.log(`❌ WebSocket disconnection: ${connectionId}`)

    // Remove connection from DynamoDB
    await docClient.send(
      new DeleteCommand({
        TableName: connectionsTable,
        Key: { connectionId },
      }),
    )

    console.log(`✅ WebSocket connection removed: ${connectionId}`)
    return { statusCode: 200 }
  } catch (error) {
    console.error('❌ Error handling WebSocket disconnect:', error)
    return { statusCode: 500 }
  }
}

/**
 * Handle WebSocket messages
 */
async function handleMessage(connectionId, event, apiGwManagementApi) {
  try {
    const body = event.body ? JSON.parse(event.body) : {}
    const { action, data } = body

    console.log(`📨 WebSocket message from ${connectionId}: ${action}`)

    switch (action) {
      case 'ping':
        return await sendMessage(apiGwManagementApi, connectionId, {
          type: 'pong',
          timestamp: new Date().toISOString(),
        })

      case 'subscribe_video':
        return await handleVideoSubscription(connectionId, data, apiGwManagementApi)

      default:
        console.log(`⚠️ Unknown WebSocket action: ${action}`)
        return { statusCode: 400 }
    }
  } catch (error) {
    console.error('❌ Error handling WebSocket message:', error)
    return { statusCode: 500 }
  }
}

/**
 * Handle video status subscription
 */
async function handleVideoSubscription(connectionId, data, apiGwManagementApi) {
  try {
    const { videoId } = data

    if (!videoId) {
      return await sendMessage(apiGwManagementApi, connectionId, {
        type: 'error',
        message: 'Video ID is required for subscription',
      })
    }

    // TODO: Store video subscription for this connection
    // This would allow targeted notifications when video status changes

    return await sendMessage(apiGwManagementApi, connectionId, {
      type: 'subscription_confirmed',
      videoId,
      message: `Subscribed to video ${videoId} status updates`,
    })
  } catch (error) {
    console.error('❌ Error handling video subscription:', error)
    return { statusCode: 500 }
  }
}

/**
 * Send message to WebSocket connection
 */
async function sendMessage(apiGwManagementApi, connectionId, message) {
  try {
    await apiGwManagementApi.send(
      new PostToConnectionCommand({
        ConnectionId: connectionId,
        Data: JSON.stringify(message),
      }),
    )

    return { statusCode: 200 }
  } catch (error) {
    if (error.name === 'GoneException') {
      console.log(`🗑️ Connection ${connectionId} is gone, removing from database`)
      await handleDisconnect(connectionId)
    } else {
      console.error('❌ Error sending WebSocket message:', error)
    }
    return { statusCode: 500 }
  }
}

/**
 * Extract user ID from WebSocket event
 */
function extractUserIdFromEvent(event) {
  try {
    // Check for Cognito authorizer context
    if (event.requestContext?.authorizer?.claims?.sub) {
      return event.requestContext.authorizer.claims.sub
    }

    // Check for custom authorizer
    if (event.requestContext?.authorizer?.userId) {
      return event.requestContext.authorizer.userId
    }

    // Check query parameters (less secure, for development only)
    if (event.queryStringParameters?.userId) {
      console.warn('⚠️ Using userId from query parameters (development only)')
      return event.queryStringParameters.userId
    }

    return null
  } catch (error) {
    console.error('❌ Error extracting user ID from event:', error)
    return null
  }
}

/**
 * Utility function to broadcast message to all connections for a user
 * This can be called from the transcription processor
 */
async function broadcastToUser(userId, message) {
  try {
    // Get all active connections for the user
    const connections = await docClient.send(
      new QueryCommand({
        TableName: connectionsTable,
        IndexName: 'userId-index',
        KeyConditionExpression: 'userId = :userId',
        ExpressionAttributeValues: {
          ':userId': userId,
        },
      }),
    )

    if (!connections.Items || connections.Items.length === 0) {
      console.log(`📡 No active WebSocket connections for user: ${userId}`)
      return
    }

    console.log(`📡 Broadcasting to ${connections.Items.length} connections for user: ${userId}`)

    // Create API Gateway Management API client
    // Note: This endpoint would need to be dynamically determined or configured
    const apiGwManagementApi = new ApiGatewayManagementApiClient({
      endpoint: process.env.WEBSOCKET_ENDPOINT,
      region: process.env.AWS_REGION,
    })

    // Send message to all user connections
    const promises = connections.Items.map(async (connection) => {
      try {
        await apiGwManagementApi.send(
          new PostToConnectionCommand({
            ConnectionId: connection.connectionId,
            Data: JSON.stringify(message),
          }),
        )
        console.log(`✅ Message sent to connection: ${connection.connectionId}`)
      } catch (error) {
        if (error.name === 'GoneException') {
          console.log(`🗑️ Connection ${connection.connectionId} is gone, removing`)
          await handleDisconnect(connection.connectionId)
        } else {
          console.error(`❌ Error sending to connection ${connection.connectionId}:`, error)
        }
      }
    })

    await Promise.all(promises)
    console.log(`✅ Broadcast completed for user: ${userId}`)
  } catch (error) {
    console.error('❌ Error broadcasting to user:', error)
  }
}

// Export utility function for use by other Lambda functions
module.exports = { broadcastToUser }
