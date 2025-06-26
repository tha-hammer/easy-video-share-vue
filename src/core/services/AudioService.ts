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
  upload_url?: string
}

// Interface for the Lambda response from presigned URL generation
interface PresignedUrlResponse {
  success: boolean
  upload_url: string
  audio: {
    video_id: string // Lambda returns video_id, not audio_id
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
    media_type: string
    transcription_status?: string
  }
}

class AudioService {
  // Helper method to get auth headers (same as VideoService)
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
   * Upload audio file to S3 audio bucket
   */
  public static async uploadAudio(params: AudioUploadParams): Promise<AudioUploadResponse> {
    const { title, description, file, onProgress } = params
    // Note: description is available in params but not currently used in this implementation

    // Validate file type
    if (!this.isValidAudioFile(file)) {
      throw new Error('Invalid file type. Please select an audio file (MP3, WAV, M4A, AAC, OGG).')
    }

    // Validate file size (max 100MB for audio)
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      throw new Error('File size too large. Maximum size is 100MB.')
    }

    try {
      // Create audio metadata first
      const audioMetadata: Partial<AudioMetadata> = {
        title,
        filename: file.name,
        file_size: file.size,
        content_type: file.type,
        upload_date: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Get presigned URL for upload
      const presignedResponse = await this.getPresignedUploadUrl(audioMetadata)

      // Upload file to S3 using presigned URL
      await this.uploadToS3(presignedResponse.upload_url!, file, onProgress)

      // Save metadata to database
      // Note: Lambda returns video_id but frontend expects audio_id
      const audioId = presignedResponse.audio.video_id
      const bucketLocation = presignedResponse.audio.bucket_location

      if (!audioId) {
        throw new Error('No audio ID returned from presigned URL generation')
      }

      const savedAudio = await this.saveAudioMetadata({
        ...audioMetadata,
        audio_id: audioId,
        bucket_location: bucketLocation,
      } as AudioMetadata)

      return {
        success: true,
        audio: savedAudio,
      }
    } catch (error: unknown) {
      console.error('Audio upload error:', error)

      if (error instanceof Error) {
        throw error
      }

      throw new Error('Failed to upload audio file')
    }
  }

  /**
   * Get presigned URL for audio upload
   */
  private static async getPresignedUploadUrl(
    metadata: Partial<AudioMetadata>,
  ): Promise<PresignedUrlResponse> {
    try {
      const headers = await this.getAuthHeaders()
      const audioUploadUrl = `${API_CONFIG.baseUrl}/audio/upload-url`

      const response = await fetch(audioUploadUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(metadata),
      })

      if (!response.ok) {
        const responseText = await response.text()
        console.error('Presigned URL error response:', responseText)
        throw new Error(`Failed to get upload URL: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error: unknown) {
      console.error('Presigned URL error:', error)
      throw new Error('Failed to get upload URL')
    }
  }

  /**
   * Upload file directly to S3
   */
  private static async uploadToS3(
    uploadUrl: string,
    file: File,
    onProgress?: (progress: number) => void,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100)
            onProgress(progress)
          }
        })
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
        } else {
          reject(new Error(`Upload failed with status: ${xhr.status}`))
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed due to network error'))
      })

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload was aborted'))
      })

      xhr.open('PUT', uploadUrl)
      xhr.setRequestHeader('Content-Type', file.type)
      xhr.send(file)
    })
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
      const headers = await this.getAuthHeaders()
      const audioUrl = `${API_CONFIG.baseUrl}/audio`

      const response = await fetch(audioUrl, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        if (response.status === 404) {
          return [] // No audio files found
        }
        throw new Error(`Failed to load audio files: ${response.statusText}`)
      }

      const data = await response.json()
      return data.audio_files || []
    } catch (error: unknown) {
      console.error('Get audio files error:', error)
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
