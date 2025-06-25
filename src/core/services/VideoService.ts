import { API_CONFIG } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'

// Video metadata interface based on our Terraform schema
interface VideoMetadata {
  video_id: string // Primary key: userId_timestamp_random
  user_id: string // Cognito user sub (UUID)
  user_email: string // Display email
  title: string // Video title
  filename: string // Original filename
  bucket_location: string // S3 object key
  upload_date: string // ISO timestamp
  file_size?: number // File size in bytes
  content_type?: string // MIME type
  duration?: number // Video duration in seconds
  created_at: string // ISO timestamp
  updated_at: string // ISO timestamp
}

export class VideoService {
  // Helper method to get auth headers
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    console.log('🔑 Getting auth headers...')

    try {
      const token = await authManager.getAccessToken()
      console.log('🔑 Token retrieved:', !!token, 'Length:', token?.length || 0)

      if (!token) {
        console.error('❌ No token returned from authManager.getAccessToken()')
        throw new Error('No authentication token available. User not authenticated.')
      }

      // Log token details for debugging
      console.log('✅ Using auth token for API call (length:', token.length, ')')
      console.log('✅ Token type:', typeof token)
      console.log('✅ Token start:', token.substring(0, 50))
      console.log(
        '✅ Token header (base64 decoded):',
        (() => {
          try {
            const header = token.split('.')[0]
            return JSON.parse(atob(header))
          } catch {
            return 'Could not decode header'
          }
        })(),
      )
      console.log(
        '✅ Token payload (base64 decoded):',
        (() => {
          try {
            const payload = token.split('.')[1]
            return JSON.parse(atob(payload))
          } catch {
            return 'Could not decode payload'
          }
        })(),
      )

      return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      }
    } catch (error) {
      console.error('❌ Error in getAuthHeaders:', error)
      throw error
    }
  }

  // Get user's videos
  static async getUserVideos(): Promise<VideoMetadata[]> {
    try {
      const headers = await this.getAuthHeaders()

      console.log('🌐 Making GET request to:', API_CONFIG.videosEndpoint)
      console.log('🌐 Request headers:', JSON.stringify(headers, null, 2))

      const response = await fetch(API_CONFIG.videosEndpoint, {
        method: 'GET',
        headers,
      })

      console.log('🌐 Response status:', response.status, response.statusText)
      console.log('🌐 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const responseText = await response.text()
        console.log('🌐 Error response body:', responseText)
        throw new Error(`Failed to fetch videos: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle different response formats
      if (Array.isArray(data)) {
        return data
      } else if (data.videos && Array.isArray(data.videos)) {
        return data.videos
      } else if (data.body) {
        // Handle API Gateway Lambda proxy response format
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        return Array.isArray(body) ? body : body.videos || []
      }

      console.log('Unexpected API response format:', data)
      return []
    } catch (error) {
      console.error('Error fetching user videos:', error)
      throw error
    }
  }

  // Save video metadata
  static async saveVideoMetadata(metadata: VideoMetadata): Promise<VideoMetadata> {
    try {
      const headers = await this.getAuthHeaders()

      console.log('🌐 Making POST request to:', API_CONFIG.videosEndpoint)
      console.log('🌐 Request headers:', JSON.stringify(headers, null, 2))
      console.log('🌐 Request body:', JSON.stringify(metadata, null, 2))

      const response = await fetch(API_CONFIG.videosEndpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(metadata),
      })

      console.log('🌐 Response status:', response.status, response.statusText)
      console.log('🌐 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const responseText = await response.text()
        console.log('🌐 Error response body:', responseText)
        throw new Error(`Failed to save video metadata: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle API Gateway Lambda proxy response format
      if (data.body) {
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        return body
      }

      return data
    } catch (error) {
      console.error('Error saving video metadata:', error)
      throw error
    }
  }

  // Delete video (user can only delete their own videos)
  static async deleteVideo(videoId: string): Promise<boolean> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${API_CONFIG.videosEndpoint}/${videoId}`, {
        method: 'DELETE',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to delete video: ${response.statusText}`)
      }

      return true
    } catch (error) {
      console.error('Error deleting video:', error)
      throw error
    }
  }

  // Generate presigned URL for video access (if needed)
  static async getVideoUrl(bucketLocation: string): Promise<string> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${API_CONFIG.videosEndpoint}/url`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ bucket_location: bucketLocation }),
      })

      if (!response.ok) {
        throw new Error(`Failed to get video URL: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle API Gateway Lambda proxy response format
      if (data.body) {
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        return body.url || body.signedUrl
      }

      return data.url || data.signedUrl
    } catch (error) {
      console.error('Error getting video URL:', error)
      throw error
    }
  }
}

export type { VideoMetadata }
