import { API_CONFIG } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'

export interface AudioMetadata {
  audio_id: string
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
  transcription_status?: 'pending' | 'processing' | 'completed' | 'failed'
  transcription_data?: {
    full_text?: string
    confidence?: number
    language_code?: string
    created_at?: string
  }
}

export interface AudioUploadParams {
  title: string
  description?: string
  file: File
  onProgress?: (progress: number) => void
}

export interface AudioUploadResponse {
  success: boolean
  audio: AudioMetadata
}

class AudioService {
  // NOTE: Audio uploads now use presigned URLs via the useAudioUpload composable
  // The uploadAudio method below is deprecated and should not be used for new implementations
  // Use the useAudioUpload composable instead for secure, credential-free uploads

  // Helper method to get auth headers
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      const token = await authManager.getAccessToken()

      if (!token) {
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
   * Save audio metadata to database
   */
  public static async saveAudioMetadata(metadata: AudioMetadata): Promise<AudioMetadata> {
    try {
      const headers = await this.getAuthHeaders()
      const audioUrl = `${API_CONFIG.baseUrl}/audio`

      console.log('🌐 Saving audio metadata to:', audioUrl)
      console.log('🌐 Request body:', JSON.stringify(metadata, null, 2))

      const response = await fetch(audioUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(metadata),
      })

      console.log('🌐 Response status:', response.status, response.statusText)

      if (!response.ok) {
        const responseText = await response.text()
        console.error('🌐 Error response body:', responseText)
        throw new Error(`Failed to save audio metadata: ${response.statusText}`)
      }

      const data = await response.json()
      return data.audio
    } catch (error: unknown) {
      console.error('Save metadata error:', error)
      throw new Error('Failed to save audio metadata')
    }
  }

  /**
   * Get user's audio files
   */
  public static async getUserAudioFiles(): Promise<AudioMetadata[]> {
    try {
      console.log('🔍 AudioService.getUserAudioFiles() called')
      const headers = await this.getAuthHeaders()
      const audioUrl = `${API_CONFIG.baseUrl}/audio`

      console.log('🌐 Fetching audio files from:', audioUrl)
      const response = await fetch(audioUrl, {
        method: 'GET',
        headers,
      })

      console.log('🌐 Audio files response status:', response.status, response.statusText)

      if (!response.ok) {
        if (response.status === 404) {
          console.log('📭 No audio files found (404)')
          return [] // No audio files found
        }
        const errorText = await response.text()
        console.error('❌ Failed to load audio files:', response.status, errorText)
        throw new Error(`Failed to load audio files: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('🎵 Raw audio files response:', data)
      const audioFiles = data.audio_files || []
      console.log('🎵 Processed audio files:', audioFiles.length, audioFiles)
      return audioFiles
    } catch (error: unknown) {
      console.error('❌ Get audio files error:', error)
      throw new Error('Failed to load audio files')
    }
  }

  /**
   * Delete audio file
   */
  public static async deleteAudio(audioId: string): Promise<boolean> {
    try {
      const headers = await this.getAuthHeaders()
      const audioUrl = `${API_CONFIG.baseUrl}/audio/${audioId}`

      const response = await fetch(audioUrl, {
        method: 'DELETE',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to delete audio file: ${response.statusText}`)
      }

      return true
    } catch (error: unknown) {
      console.error('Delete audio error:', error)
      throw new Error('Failed to delete audio file')
    }
  }

  /**
   * Get audio file details
   */
  public static async getAudioDetails(audioId: string): Promise<AudioMetadata> {
    try {
      const headers = await this.getAuthHeaders()
      const audioUrl = `${API_CONFIG.baseUrl}/audio/${audioId}`

      const response = await fetch(audioUrl, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to get audio details: ${response.statusText}`)
      }

      const data = await response.json()
      return data.audio
    } catch (error: unknown) {
      console.error('Get audio details error:', error)
      throw new Error('Failed to get audio details')
    }
  }

  /**
   * Validate if file is a supported audio format
   */
  public static isValidAudioFile(file: File): boolean {
    const validTypes = [
      'audio/mpeg',
      'audio/mp3',
      'audio/wav',
      'audio/wave',
      'audio/x-wav',
      'audio/mp4',
      'audio/m4a',
      'audio/aac',
      'audio/x-aac',
      'audio/ogg',
      'audio/oga',
      'audio/webm',
      'audio/flac',
      'audio/x-flac',
    ]

    const validExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.oga', '.webm', '.flac']

    // Check MIME type
    if (validTypes.includes(file.type.toLowerCase())) {
      return true
    }

    // Check file extension as fallback
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    return validExtensions.includes(extension)
  }

  /**
   * Get supported audio formats for display
   */
  public static getSupportedFormats(): string[] {
    return ['MP3', 'WAV', 'M4A', 'AAC', 'OGG', 'FLAC']
  }

  /**
   * Format file size for display
   */
  public static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * Format duration for display
   */
  public static formatDuration(seconds: number): string {
    if (!seconds || seconds === 0) return 'Unknown'

    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)

    if (minutes === 0) {
      return `${remainingSeconds}s`
    }

    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  /**
   * Estimate processing time for AI video generation
   */
  public static estimateProcessingTime(fileSizeBytes: number, durationSeconds?: number): string {
    // Base estimation: 2-3 minutes per minute of audio + file size factor
    const baseDuration = durationSeconds || 30 // default estimate
    const durationMinutes = Math.ceil(baseDuration / 60)
    const sizeFactor = Math.ceil(fileSizeBytes / (10 * 1024 * 1024)) // 10MB chunks

    const estimatedMinutes = Math.max(2, durationMinutes * 2 + sizeFactor)

    if (estimatedMinutes < 60) {
      return `${estimatedMinutes} minutes`
    }

    const hours = Math.floor(estimatedMinutes / 60)
    const minutes = estimatedMinutes % 60

    return `${hours}h ${minutes}m`
  }
}

export default AudioService
