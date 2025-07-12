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
  // Additional fields for AI video processing
  status?: string // Job status (QUEUED, PROCESSING, COMPLETED, FAILED)
  output_s3_urls?: string[] // S3 keys of processed video segments
  error_message?: string // Error message if job failed
}

// AI Video Processing interfaces
interface InitiateUploadRequest {
  filename: string
  content_type: string
  file_size: number
}

interface InitiateUploadResponse {
  presigned_url: string
  s3_key: string
  job_id: string
}

interface CompleteUploadRequest {
  s3_key: string
  job_id: string
}

interface JobCreatedResponse {
  job_id: string
  status: string
  message: string
}

interface JobStatusResponse {
  job_id: string
  status: string
  progress?: number
  output_urls?: string[]
  error_message?: string
  created_at?: string
  updated_at?: string
}

// Video Segment interfaces
interface VideoSegment {
  segment_id: string
  video_id: string
  user_id: string
  segment_type: string
  segment_number: number
  s3_key: string
  s3_url?: string
  duration: number
  file_size: number
  content_type: string
  thumbnail_url?: string
  created_at: string
  updated_at: string
  title?: string
  description?: string
  tags?: string[]
  social_media_usage?: {
    platform: string
    post_id?: string
    post_url?: string
    posted_at?: string
    views: number
    likes: number
    shares: number
    comments: number
    engagement_rate?: number
    last_synced?: string
  }[]
  filename?: string
  download_count: number
  last_downloaded_at?: string
}

interface SegmentListParams {
  user_id?: string
  video_id?: string
  sort_by?: string
  order?: string
  limit?: number
  offset?: number
  min_duration?: number
  max_duration?: number
  min_downloads?: number
}

interface SegmentListResponse {
  segments: VideoSegment[]
  total_count: number
  page: number
  page_size: number
}

interface SegmentDownloadResponse {
  segment_id: string
  download_url: string
  download_count: number
  expires_at: string
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
      // Use the local FastAPI backend instead of AWS API Gateway
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const url = `${baseUrl}/api/videos/url`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ bucket_location: bucketLocation }),
      })

      if (!response.ok) {
        throw new Error(`Failed to get video URL: ${response.statusText}`)
      }

      const data = await response.json()
      return data.url || data.signedUrl
    } catch (error) {
      console.error('Error getting video URL:', error)
      throw error
    }
  }

  // === AI Video Processing Methods (Sprint 1) ===

  /**
   * Initiate AI video upload - generates presigned URL for S3 direct upload
   */
  static async initiateAIVideoUpload(
    request: InitiateUploadRequest,
  ): Promise<InitiateUploadResponse> {
    try {
      console.log('🤖 Initiating AI video upload:', request)

      // Construct the full URL for Railway deployment
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const uploadUrl = `${baseUrl}/api/upload/initiate`

      console.log('🤖 Making request to:', uploadUrl)

      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      console.log('🤖 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('🤖 Error response:', errorText)
        throw new Error(`Failed to initiate AI video upload: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🤖 Upload initiated successfully:', data)
      return data
    } catch (error) {
      console.error('Error initiating AI video upload:', error)
      throw error
    }
  }

  /**
   * Complete AI video upload - starts background processing
   */
  static async completeAIVideoUpload(request: CompleteUploadRequest): Promise<JobCreatedResponse> {
    try {
      console.log('🤖 Completing AI video upload:', request)

      // Construct the full URL for Railway deployment
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const completeUrl = `${baseUrl}/api/upload/complete`

      console.log('🤖 Making request to:', completeUrl)

      const response = await fetch(completeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      console.log('🤖 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('🤖 Error response:', errorText)
        throw new Error(`Failed to complete AI video upload: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🤖 Upload completed successfully:', data)
      return data
    } catch (error) {
      console.error('Error completing AI video upload:', error)
      throw error
    }
  }

  /**
   * Get AI video processing job status
   */
  static async getAIVideoJobStatus(jobId: string): Promise<JobStatusResponse> {
    try {
      console.log('🤖 Getting AI video job status for:', jobId)

      // Construct the full URL for Railway deployment
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const statusUrl = `${baseUrl}/api/jobs/${jobId}/status`

      console.log('🤖 Making request to:', statusUrl)

      const response = await fetch(statusUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      console.log('🤖 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('🤖 Error response:', errorText)
        throw new Error(`Failed to get AI video job status: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🤖 Job status retrieved:', data)
      return data
    } catch (error) {
      console.error('Error getting AI video job status:', error)
      throw error
    }
  }

  /**
   * Upload file directly to S3 using presigned URL
   */
  static async uploadToS3(presignedUrl: string, file: File): Promise<void> {
    try {
      console.log('📤 Uploading file to S3:', file.name, 'Size:', file.size)

      const response = await fetch(presignedUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      })

      console.log('📤 S3 upload response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.log('📤 S3 upload error:', errorText)
        throw new Error(`S3 upload failed: ${response.statusText}`)
      }

      console.log('📤 File uploaded to S3 successfully')
    } catch (error) {
      console.error('Error uploading to S3:', error)
      throw error
    }
  }

  /**
   * Check backend health
   */
  static async checkBackendHealth(): Promise<{ status: string; message: string }> {
    try {
      // Construct the full URL for Railway deployment
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const healthUrl = `${baseUrl}/health`

      console.log('🤖 Checking backend health at:', healthUrl)

      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Backend health check failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Backend health check failed:', error)
      throw error
    }
  }

  /**
   * Get all AI-processed video metadata from backend
   */
  static async getAIVideoMetadataList(): Promise<VideoMetadata[]> {
    try {
      // Construct the full URL for Railway deployment
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const videosUrl = `${baseUrl}/api/videos`

      console.log('🤖 Fetching AI video metadata from:', videosUrl)

      const response = await fetch(videosUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch AI video metadata: ${response.statusText}`)
      }
      const data = await response.json()
      console.log('🤖 Raw response from /api/videos:', data)

      const videos = Array.isArray(data) ? data : data.videos || []
      console.log('🤖 Processed videos array:', videos)

      return videos
    } catch (error) {
      console.error('Error fetching AI video metadata:', error)
      throw error
    }
  }

  /**
   * Get video segments for a specific video
   */
  static async getVideoSegments(videoId: string): Promise<VideoSegment[]> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const segmentsUrl = `${baseUrl}/api/videos/${videoId}/segments`

      console.log('🎬 Fetching video segments from:', segmentsUrl)

      const response = await fetch(segmentsUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch video segments: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎬 Video segments response:', data)

      // Backend returns SegmentListResponse with segments property
      return data.segments || []
    } catch (error) {
      console.error('Error fetching video segments:', error)
      throw error
    }
  }

  /**
   * Get all segments with filtering and pagination
   */
  static async getAllSegments(params: SegmentListParams): Promise<SegmentListResponse> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const segmentsUrl = `${baseUrl}/api/segments`

      // Build query parameters
      const queryParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })

      const url = queryParams.toString() ? `${segmentsUrl}?${queryParams.toString()}` : segmentsUrl
      console.log('🎬 Fetching all segments from:', url)

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch segments: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎬 All segments response:', data)

      return data
    } catch (error) {
      console.error('Error fetching all segments:', error)
      throw error
    }
  }

  /**
   * Download a segment (get presigned URL and increment download count)
   *
   * FUTURE ENHANCEMENT: This method will be enhanced to track social media usage
   * When a user downloads a segment, we can assume it's for social media posting
   * Integration with Instagram/TikTok APIs will allow automatic tracking of:
   * - Post creation and publication
   * - Performance metrics (views, likes, shares, comments)
   * - Cross-platform performance comparison
   * - Content optimization recommendations
   */
  static async downloadSegment(segmentId: string): Promise<SegmentDownloadResponse> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const downloadUrl = `${baseUrl}/api/segments/${segmentId}/download`

      console.log('📥 Downloading segment from:', downloadUrl)

      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to download segment: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('📥 Download response:', data)

      return data
    } catch (error) {
      console.error('Error downloading segment:', error)
      throw error
    }
  }

  /**
   * Track social media usage for a segment
   * FUTURE ENHANCEMENT: This will integrate with social media APIs
   *
   * Instagram API Integration:
   * - Connect user's Instagram Business account
   * - Automatically detect when segments are posted
   * - Track post performance metrics
   * - Provide hashtag optimization suggestions
   *
   * TikTok API Integration:
   * - Connect user's TikTok Creator account
   * - Track video performance across TikTok
   * - Monitor trending hashtags and sounds
   * - Provide content optimization recommendations
   *
   * YouTube Shorts Integration:
   * - Connect user's YouTube channel
   * - Track Shorts performance metrics
   * - Monitor audience retention and engagement
   * - Provide thumbnail and title optimization
   */
  static async trackSocialMediaUsage(
    segmentId: string,
    platform: 'instagram' | 'tiktok' | 'youtube' | 'facebook' | 'twitter',
    postData?: {
      post_id?: string
      views?: number
      likes?: number
      shares?: number
      comments?: number
      posted_at?: string
    },
  ): Promise<void> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const trackUrl = `${baseUrl}/api/segments/${segmentId}/social-media-usage`

      console.log('📊 Tracking social media usage:', { segmentId, platform, postData })

      const response = await fetch(trackUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment_id: segmentId,
          platform,
          post_data: postData,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to track social media usage: ${response.statusText}`)
      }

      console.log('📊 Social media usage tracked successfully')
    } catch (error) {
      console.error('Error tracking social media usage:', error)
      throw error
    }
  }

  /**
   * Get segment play URL (presigned URL for streaming)
   */
  static async getSegmentPlayUrl(
    segmentId: string,
  ): Promise<{ play_url: string; expires_at: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const playUrl = `${baseUrl}/api/segments/${segmentId}/play`

      console.log('🎬 Getting segment play URL from:', playUrl)

      const response = await fetch(playUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to get segment play URL: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎬 Segment play URL response:', data)

      return data
    } catch (error) {
      console.error('Error getting segment play URL:', error)
      throw error
    }
  }

  /**
   * Get segment metadata
   */
  static async getSegmentMetadata(segmentId: string): Promise<VideoSegment> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const metadataUrl = `${baseUrl}/api/segments/${segmentId}`

      console.log('📋 Fetching segment metadata from:', metadataUrl)

      const response = await fetch(metadataUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch segment metadata: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('📋 Segment metadata response:', data)

      return data
    } catch (error) {
      console.error('Error fetching segment metadata:', error)
      throw error
    }
  }

  /**
   * Generate thumbnail for a video segment
   */
  static async generateSegmentThumbnail(segmentId: string): Promise<{ thumbnail_url: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const thumbnailUrl = `${baseUrl}/api/segments/${segmentId}/generate-thumbnail`

      console.log('🖼️ Generating thumbnail for segment:', segmentId)

      const response = await fetch(thumbnailUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to generate thumbnail: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🖼️ Thumbnail generation response:', data)

      return data
    } catch (error) {
      console.error('Error generating segment thumbnail:', error)
      throw error
    }
  }

  /**
   * Save text overlays for a video segment
   */
  static async saveTextOverlays(segmentId: string, overlays: object[]): Promise<void> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const saveUrl = `${baseUrl}/api/segments/${segmentId}/text-overlays`

      console.log('💾 Saving text overlays for segment:', segmentId, overlays)

      const response = await fetch(saveUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ overlays }),
      })

      if (!response.ok) {
        throw new Error(`Failed to save text overlays: ${response.statusText}`)
      }

      console.log('💾 Text overlays saved successfully')
    } catch (error) {
      console.error('Error saving text overlays:', error)
      throw error
    }
  }

  /**
   * Process video segment with text overlay objects (preferred method)
   */
  static async processSegmentWithTextOverlayObjects(
    segmentId: string,
    overlays: object[],
  ): Promise<{ job_id: string; status: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const processUrl = `${baseUrl}/api/segments/${segmentId}/process-with-text-overlays`

      console.log('🎬 Processing segment with text overlay objects:', {
        segmentId,
        overlayCount: overlays.length,
      })

      const response = await fetch(processUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment_id: segmentId,
          overlays: overlays,
          processing_type: 'text_overlays',
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to process segment with text overlays: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎬 Video processing started:', data)

      return data
    } catch (error) {
      console.error('Error processing segment with text overlays:', error)
      throw error
    }
  }

  /**
   * Process video segment with text overlays to create final video (legacy FFmpeg filters method)
   */
  static async processSegmentWithTextOverlays(
    segmentId: string,
    ffmpegFilters: string[],
    ffmpegCommand?: string,
  ): Promise<{ job_id: string; status: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const processUrl = `${baseUrl}/api/segments/${segmentId}/process-with-text-overlays`

      console.log('🎬 Processing segment with text overlays:', {
        segmentId,
        filterCount: ffmpegFilters.length,
        ffmpegCommand,
      })

      const response = await fetch(processUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment_id: segmentId,
          ffmpeg_filters: ffmpegFilters,
          ffmpeg_command: ffmpegCommand,
          processing_type: 'text_overlays',
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to process segment with text overlays: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎬 Video processing started:', data)

      return data
    } catch (error) {
      console.error('Error processing segment with text overlays:', error)
      throw error
    }
  }

  /**
   * Get video processing status
   */
  static async getVideoProcessingStatus(jobId: string): Promise<{
    job_id: string
    status: string
    progress?: number
    output_url?: string
    error_message?: string
    created_at?: string
    updated_at?: string
  }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const statusUrl = `${baseUrl}/api/jobs/${jobId}/status`

      console.log('📊 Checking video processing status:', jobId)

      const response = await fetch(statusUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to get processing status: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('📊 Processing status:', data)

      return data
    } catch (error) {
      console.error('Error getting processing status:', error)
      throw error
    }
  }

  /**
   * Get processed video URL (final video with text overlays)
   */
  static async getProcessedVideoUrl(
    segmentId: string,
  ): Promise<{ video_url: string; expires_at: string; processed_at: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const videoUrl = `${baseUrl}/api/segments/${segmentId}/processed-video`

      console.log('🎥 Getting processed video URL for segment:', segmentId)

      const response = await fetch(videoUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to get processed video URL: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎥 Processed video URL:', data)

      return data
    } catch (error) {
      console.error('Error getting processed video URL:', error)
      throw error
    }
  }

  /**
   * Download processed video segment
   */
  static async downloadProcessedSegment(
    segmentId: string,
  ): Promise<{ download_url: string; expires_at: string; filename: string }> {
    try {
      const baseUrl = API_CONFIG.aiVideoBackend.endsWith('/')
        ? API_CONFIG.aiVideoBackend.slice(0, -1)
        : API_CONFIG.aiVideoBackend
      const downloadUrl = `${baseUrl}/api/segments/${segmentId}/download-processed`

      console.log('📥 Getting download URL for processed segment:', segmentId)

      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to get download URL: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('📥 Download URL:', data)

      return data
    } catch (error) {
      console.error('Error getting download URL:', error)
      throw error
    }
  }
}

export type {
  VideoMetadata,
  InitiateUploadRequest,
  InitiateUploadResponse,
  CompleteUploadRequest,
  JobCreatedResponse,
  JobStatusResponse,
  VideoSegment,
  SegmentListParams,
  SegmentListResponse,
  SegmentDownloadResponse,
}
