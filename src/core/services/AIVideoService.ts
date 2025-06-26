import { API_CONFIG } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'
import type { AudioMetadata } from './AudioService'

export interface AIVideoGenerationRequest {
  videoId?: string
  audioId: string
  prompt: string
  targetDuration: number
  style: string
}

export interface ProcessingStep {
  step: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface TranscriptSegment {
  start_time: number
  end_time: number
  text: string
  confidence: number
}

export interface SceneBeat {
  sequence: number
  start_time: number
  end_time: number
  duration: number
  audio_text: string
  scene_description: string
  vertex_ai_prompt: string
  visual_style: string
}

export interface AIGenerationData {
  audio_transcription?: {
    full_text: string
    segments: TranscriptSegment[]
    confidence: number
    language_code: string
  }
  scene_beats?: {
    overall_theme: string
    scenes: SceneBeat[]
    target_duration: number
  }
  vertex_ai_tasks?: {
    task_id: string
    status: 'pending' | 'processing' | 'completed' | 'failed'
    video_url?: string
    prompt: string
    created_at: string
  }[]
  processing_steps?: ProcessingStep[]
  final_video_url?: string
  generation_time?: number
  cost_breakdown?: {
    transcription: number
    scene_generation: number
    video_generation: number
    total: number
  }
  started_at?: string
  completed_at?: string
  user_prompt?: string
  target_duration?: number
  style?: string
  error_message?: string
}

export interface VideoMetadata {
  video_id: string
  user_id: string
  user_email: string
  title: string
  filename: string
  bucket_location: string
  upload_date: string
  file_size?: number
  content_type?: string
  duration?: number
  created_at: string
  updated_at: string
  ai_project_type?: 'standard' | 'ai_generated'
  ai_generation_status?: 'processing' | 'completed' | 'failed'
  ai_generation_data?: AIGenerationData
}

export interface AIVideoGenerationResponse {
  success: boolean
  message: string
  videoId: string
  status: string
}

export interface AIVideoStatusResponse {
  success: boolean
  video: VideoMetadata
}

class AIVideoService {
  // Helper method to get auth headers (same as VideoService)
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    console.log('🔑 Getting auth headers for AI video service...')

    try {
      const token = await authManager.getAccessToken()
      console.log('🔑 Token retrieved:', !!token, 'Length:', token?.length || 0)

      if (!token) {
        console.error('❌ No token returned from authManager.getAccessToken()')
        throw new Error('No authentication token available. User not authenticated.')
      }

      return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      }
    } catch (error) {
      console.error('❌ Error in getAuthHeaders:', error)
      throw error
    }
  }

  /**
   * Start AI video generation process
   */
  public static async generateAIVideo(
    request: AIVideoGenerationRequest,
  ): Promise<AIVideoGenerationResponse> {
    try {
      const headers = await this.getAuthHeaders()
      const url = `${API_CONFIG.baseUrl}/ai-video`

      console.log('🌐 Making POST request to:', url)
      console.log('🌐 Request headers:', JSON.stringify(headers, null, 2))
      console.log('🌐 Request body:', JSON.stringify(request, null, 2))
      console.log('🌐 API_CONFIG.baseUrl:', API_CONFIG.baseUrl)

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
      })

      console.log('🌐 Response status:', response.status, response.statusText)
      console.log('🌐 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const responseText = await response.text()
        console.log('🌐 Error response body:', responseText)
        throw new Error(
          `Failed to start AI video generation: ${response.statusText} - ${responseText}`,
        )
      }

      const data = await response.json()
      console.log('🌐 Response data:', JSON.stringify(data, null, 2))

      // Handle API Gateway Lambda proxy response format
      if (data.body) {
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        console.log('🌐 Parsed body from API Gateway:', JSON.stringify(body, null, 2))
        return body
      }

      return data
    } catch (error: unknown) {
      console.error('AI video generation error:', error)

      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as { response?: { data?: { error?: string } } }
        const errorMessage = apiError.response?.data?.error || 'Failed to start AI video generation'
        throw new Error(errorMessage)
      }

      throw new Error('Failed to start AI video generation')
    }
  }

  /**
   * Get AI video generation status
   */
  public static async getAIVideoStatus(videoId: string): Promise<AIVideoStatusResponse> {
    try {
      const headers = await this.getAuthHeaders()
      const url = `${API_CONFIG.baseUrl}/ai-video/${videoId}`

      console.log('🌐 Making GET request to:', url)
      console.log('🌐 Request headers:', JSON.stringify(headers, null, 2))
      console.log('🌐 Video ID:', videoId)
      console.log('🌐 API_CONFIG.baseUrl:', API_CONFIG.baseUrl)

      const response = await fetch(url, {
        method: 'GET',
        headers,
      })

      console.log('🌐 Response status:', response.status, response.statusText)
      console.log('🌐 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const responseText = await response.text()
        console.log('🌐 Error response body:', responseText)
        throw new Error(`Failed to get AI video status: ${response.statusText} - ${responseText}`)
      }

      const data = await response.json()
      console.log('🌐 Response data:', JSON.stringify(data, null, 2))

      // Handle API Gateway Lambda proxy response format
      if (data.body) {
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        console.log('🌐 Parsed body from API Gateway:', JSON.stringify(body, null, 2))
        return body
      }

      return data
    } catch (error: unknown) {
      console.error('AI video status error:', error)

      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as { response?: { data?: { error?: string } } }
        const errorMessage = apiError.response?.data?.error || 'Failed to get AI video status'
        throw new Error(errorMessage)
      }

      throw new Error('Failed to get AI video status')
    }
  }

  /**
   * Poll for AI video completion with automatic retries
   */
  public static async pollForCompletion(
    videoId: string,
    onProgress?: (video: VideoMetadata) => void,
    maxWaitTime: number = 900000, // 15 minutes
    pollInterval: number = 3000, // 3 seconds
  ): Promise<VideoMetadata> {
    const startTime = Date.now()

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const statusResponse = await this.getAIVideoStatus(videoId)
          const video = statusResponse.video

          // Call progress callback if provided
          if (onProgress) {
            onProgress(video)
          }

          // Check if completed
          if (video.ai_generation_status === 'completed') {
            resolve(video)
            return
          }

          // Check if failed
          if (video.ai_generation_status === 'failed') {
            const errorMessage =
              video.ai_generation_data?.error_message || 'AI video generation failed'
            reject(new Error(errorMessage))
            return
          }

          // Check timeout
          if (Date.now() - startTime > maxWaitTime) {
            reject(new Error('AI video generation timed out'))
            return
          }

          // Continue polling
          setTimeout(poll, pollInterval)
        } catch (error) {
          console.error('Polling error:', error)
          reject(error)
        }
      }

      // Start polling
      poll()
    })
  }

  /**
   * Calculate processing progress percentage
   */
  public static calculateProgress(processingSteps?: ProcessingStep[]): number {
    if (!processingSteps || processingSteps.length === 0) return 0

    const completedSteps = processingSteps.filter((step) => step.status === 'completed').length
    return Math.round((completedSteps / processingSteps.length) * 100)
  }

  /**
   * Get current processing step message
   */
  public static getCurrentStepMessage(processingSteps?: ProcessingStep[]): string {
    if (!processingSteps) return 'Initializing...'

    const currentStep = processingSteps.find((step) => step.status === 'processing')

    const messages: Record<string, string> = {
      transcription: 'Transcribing audio content...',
      scene_planning: 'Planning video scenes with AI...',
      video_generation: 'Generating video with Vertex AI...',
      finalization: 'Finalizing your video...',
    }

    return currentStep ? messages[currentStep.step] || 'Processing...' : 'Waiting to start...'
  }

  /**
   * Format step name for display
   */
  public static formatStepName(step: string): string {
    const names: Record<string, string> = {
      transcription: 'Audio Transcription',
      scene_planning: 'Scene Planning',
      video_generation: 'Video Generation',
      finalization: 'Finalization',
    }
    return names[step] || step
  }

  /**
   * Get estimated completion time
   */
  public static getEstimatedTime(
    processingSteps?: ProcessingStep[],
    targetDuration: number = 30,
  ): string {
    if (!processingSteps) return 'Calculating...'

    const completedSteps = processingSteps.filter((step) => step.status === 'completed').length
    const totalSteps = processingSteps.length

    // Rough estimates based on step complexity
    const stepTimes: Record<string, number> = {
      transcription: 30, // 30 seconds
      scene_planning: 60, // 1 minute
      video_generation: 180 + targetDuration * 3, // 3-6 minutes depending on duration
      finalization: 30, // 30 seconds
    }

    const remainingSteps = processingSteps.filter(
      (step) => step.status === 'pending' || step.status === 'processing',
    )

    const remainingTime = remainingSteps.reduce((total, step) => {
      return total + (stepTimes[step.step] || 60)
    }, 0)

    if (remainingTime < 60) {
      return `~${remainingTime} seconds`
    } else {
      const minutes = Math.ceil(remainingTime / 60)
      return `~${minutes} minute${minutes === 1 ? '' : 's'}`
    }
  }

  /**
   * Validate AI video generation request
   */
  public static validateRequest(request: AIVideoGenerationRequest): string[] {
    const errors: string[] = []

    if (!request.audioId) {
      errors.push('Audio ID is required')
    }

    if (!request.prompt || request.prompt.trim().length === 0) {
      errors.push('Video description/prompt is required')
    }

    if (request.prompt && request.prompt.length > 500) {
      errors.push('Video description must be less than 500 characters')
    }

    if (!request.targetDuration || request.targetDuration < 15 || request.targetDuration > 60) {
      errors.push('Target duration must be between 15 and 60 seconds')
    }

    if (!request.style) {
      errors.push('Visual style is required')
    }

    return errors
  }

  /**
   * Get default video styles
   */
  public static getVideoStyles(): Array<{ value: string; label: string; description: string }> {
    return [
      {
        value: 'realistic',
        label: 'Realistic',
        description: 'Photorealistic scenes and environments',
      },
      {
        value: 'cinematic',
        label: 'Cinematic',
        description: 'Movie-like dramatic scenes with professional lighting',
      },
      {
        value: 'animated',
        label: 'Animated',
        description: 'Cartoon or 3D animated style',
      },
      {
        value: 'artistic',
        label: 'Artistic',
        description: 'Stylized and creative artistic interpretations',
      },
    ]
  }

  /**
   * Get supported durations
   */
  public static getSupportedDurations(): Array<{ value: number; label: string }> {
    return [
      { value: 15, label: '15 seconds' },
      { value: 30, label: '30 seconds' },
      { value: 45, label: '45 seconds' },
      { value: 60, label: '60 seconds' },
    ]
  }
}

export default AIVideoService
