import { API_CONFIG } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'
import {
  S3Client,
  CreateMultipartUploadCommand,
  UploadPartCommand,
  CompleteMultipartUploadCommand,
  AbortMultipartUploadCommand,
} from '@aws-sdk/client-s3'
import { config } from '@/core/config/config'

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

  // Initialize S3 client for audio uploads
  private static getS3Client(): S3Client {
    return new S3Client({
      region: config.aws.region,
      credentials: config.aws.credentials,
    })
  }

  /**
   * Upload audio file to S3 audio bucket using multipart upload
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
      // Generate unique audio ID (same pattern as video upload)
      const user = await this.getCurrentUser()
      const audioId = `${user.userId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      // Create audio metadata
      const audioMetadata: AudioMetadata = {
        audio_id: audioId,
        user_id: user.userId,
        user_email: user.email,
        title,
        filename: file.name,
        bucket_location: `audio/${audioId}/${file.name}`,
        upload_date: new Date().toISOString(),
        file_size: file.size,
        content_type: file.type,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        transcription_status: 'pending',
      }

      // Upload file to S3 using multipart upload
      await this.uploadToS3(file, audioMetadata.bucket_location, onProgress)

      // Save metadata to database
      const savedAudio = await this.saveAudioMetadata(audioMetadata)

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
   * Upload file to S3 using multipart upload (following video upload pattern)
   */
  private static async uploadToS3(
    file: File,
    key: string,
    onProgress?: (progress: number) => void,
  ): Promise<void> {
    const s3Client = this.getS3Client()
    const bucketName = config.aws.bucketName // Use the same bucket as videos
    const chunkSize = 8 * 1024 * 1024 // 8MB chunks for audio files
    const totalChunks = Math.ceil(file.size / chunkSize)

    let uploadId: string | undefined
    const uploadedParts: { ETag: string; PartNumber: number }[] = []

    try {
      // Step 1: Create multipart upload
      const createCommand = new CreateMultipartUploadCommand({
        Bucket: bucketName,
        Key: key,
        ContentType: file.type,
        Metadata: {
          'original-filename': file.name,
        },
      })

      const createResponse = await s3Client.send(createCommand)
      uploadId = createResponse.UploadId!

      // Step 2: Upload parts
      for (let partNumber = 1; partNumber <= totalChunks; partNumber++) {
        const startByte = (partNumber - 1) * chunkSize
        const endByte = Math.min(startByte + chunkSize, file.size)
        const chunk = file.slice(startByte, endByte)

        // Convert Blob to ArrayBuffer for AWS SDK v3
        const arrayBuffer = await chunk.arrayBuffer()
        const uint8Array = new Uint8Array(arrayBuffer)

        const uploadCommand = new UploadPartCommand({
          Bucket: bucketName,
          Key: key,
          PartNumber: partNumber,
          UploadId: uploadId,
          Body: uint8Array,
        })

        const response = await s3Client.send(uploadCommand)

        uploadedParts.push({
          ETag: response.ETag!,
          PartNumber: partNumber,
        })

        // Update progress
        if (onProgress) {
          const progress = Math.round((partNumber / totalChunks) * 100)
          onProgress(progress)
        }
      }

      // Step 3: Complete multipart upload
      const completeCommand = new CompleteMultipartUploadCommand({
        Bucket: bucketName,
        Key: key,
        UploadId: uploadId,
        MultipartUpload: {
          Parts: uploadedParts.sort((a, b) => a.PartNumber - b.PartNumber),
        },
      })

      await s3Client.send(completeCommand)
      console.log(`✅ Audio upload completed for ${key}`)
    } catch (error) {
      // Clean up failed upload
      if (uploadId) {
        try {
          const abortCommand = new AbortMultipartUploadCommand({
            Bucket: bucketName,
            Key: key,
            UploadId: uploadId,
          })
          await s3Client.send(abortCommand)
        } catch (abortError) {
          console.error('Error aborting multipart upload:', abortError)
        }
      }
      throw error
    }
  }

  /**
   * Get current user info
   */
  private static async getCurrentUser(): Promise<{ userId: string; email: string }> {
    // This should get user info from auth store or token
    // For now, we'll extract from the JWT token
    const token = await authManager.getAccessToken()
    if (!token) {
      throw new Error('No authentication token available')
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return {
        userId: payload.sub,
        email: payload.email,
      }
    } catch (error) {
      throw new Error('Invalid authentication token')
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
