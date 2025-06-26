import ApiService from './ApiService'
import JwtService from './JwtService'

export interface AIVideoGenerationRequest {
  videoId: string
  prompt: string
  targetDuration?: number
  style?: 'realistic' | 'cinematic' | 'animated' | 'artistic'
}

export interface AIVideoStatus {
  success: boolean
  video: {
    video_id: string
    user_id: string
    ai_project_type?: 'standard' | 'ai_generated'
    ai_generation_status?: 'processing' | 'completed' | 'failed'
    ai_generation_data?: {
      processing_steps: ProcessingStep[]
      audio_transcription?: AudioTranscription
      scene_beats?: SceneBeats
      vertex_ai_tasks?: VertexAITask[]
      final_video_url?: string
      started_at?: string
      completed_at?: string
      generation_time?: number
      error_message?: string
    }
  }
}

export interface ProcessingStep {
  step: 'transcription' | 'scene_planning' | 'video_generation' | 'finalization'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface AudioTranscription {
  full_text: string
  segments: TranscriptSegment[]
  confidence: number
  language_code: string
}

export interface TranscriptSegment {
  start_time: number
  end_time: number
  text: string
  confidence: number
}

export interface SceneBeats {
  overall_theme: string
  total_duration: number
  scenes: SceneBeat[]
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

export interface VertexAITask {
  task_id: string
  sequence: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  video_url?: string
  prompt: string
  created_at: string
  duration?: number
  scene_description?: string
  error_message?: string
}

class AIVideoService {
  /**
   * Start AI video generation for a given video
   */
  public static async generateAIVideo(
    request: AIVideoGenerationRequest,
  ): Promise<{ success: boolean; message: string; videoId: string; status: string }> {
    // Set authorization header
    ApiService.setHeader()

    try {
      const response = await ApiService.post('ai-video', request)
      return response.data
    } catch (error: unknown) {
      console.error('AI video generation error:', error)

      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as { response?: { data?: { error?: string } } }
        if (apiError.response?.data?.error) {
          throw new Error(apiError.response.data.error)
        }
      }

      throw new Error('Failed to start AI video generation')
    }
  }

  /**
   * Get AI video generation status
   */
  public static async getAIVideoStatus(videoId: string): Promise<AIVideoStatus> {
    // Set authorization header
    ApiService.setHeader()

    try {
      const response = await ApiService.query('ai-video', {
        params: { videoId },
      })
      return response.data
    } catch (error: unknown) {
      console.error('AI video status error:', error)

      if (error && typeof error === 'object' && 'response' in error) {
        const apiError = error as { response?: { data?: { error?: string } } }
        if (apiError.response?.data?.error) {
          throw new Error(apiError.response.data.error)
        }
      }

      throw new Error('Failed to get AI video status')
    }
  }

  /**
   * Calculate processing progress percentage
   */
  public static calculateProgress(steps: ProcessingStep[]): number {
    if (!steps || steps.length === 0) return 0

    const completedSteps = steps.filter((step) => step.status === 'completed').length
    return Math.round((completedSteps / steps.length) * 100)
  }

  /**
   * Get current processing step
   */
  public static getCurrentProcessingStep(steps: ProcessingStep[]): ProcessingStep | null {
    if (!steps || steps.length === 0) return null

    return steps.find((step) => step.status === 'processing') || null
  }

  /**
   * Get user-friendly step name
   */
  public static getStepDisplayName(step: string): string {
    const stepNames: Record<string, string> = {
      transcription: 'Transcribing Audio',
      scene_planning: 'Planning Scenes',
      video_generation: 'Generating Video',
      finalization: 'Finalizing Video',
    }

    return stepNames[step] || step
  }

  /**
   * Get user-friendly processing message
   */
  public static getProcessingMessage(steps: ProcessingStep[]): string {
    const currentStep = this.getCurrentProcessingStep(steps)

    if (!currentStep) {
      const completedSteps = steps?.filter((s) => s.status === 'completed').length || 0
      const totalSteps = steps?.length || 0

      if (completedSteps === totalSteps && totalSteps > 0) {
        return 'AI video generation completed!'
      }

      return 'Processing...'
    }

    const messages: Record<string, string> = {
      transcription: 'Transcribing audio content...',
      scene_planning: 'Planning video scenes with AI...',
      video_generation: 'Generating video with Vertex AI...',
      finalization: 'Finalizing your video...',
    }

    return messages[currentStep.step] || 'Processing...'
  }

  /**
   * Check if AI video generation is available (based on configuration)
   */
  public static isAIVideoAvailable(): boolean {
    // Check if the AI video endpoint is configured
    // This could be based on environment variables or feature flags
    return import.meta.env.VITE_AI_VIDEO_ENABLED === 'true'
  }

  /**
   * Get estimated processing time
   */
  public static getEstimatedProcessingTime(targetDuration: number): string {
    // Rough estimate based on video duration
    const baseTime = 2 // Base 2 minutes
    const additionalTime = Math.ceil(targetDuration / 30) // Additional time per 30s of video
    const totalMinutes = baseTime + additionalTime

    return `${totalMinutes}-${totalMinutes + 2} minutes`
  }
}

export default AIVideoService
