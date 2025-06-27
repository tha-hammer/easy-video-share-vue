import { ref, computed } from 'vue'
import { config } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'
import AudioService from '@/core/services/AudioService'

interface UploadProgress {
  audioId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number
  uploadSpeed?: number
}

interface AudioMetadata {
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

interface PresignedUploadResponse {
  success: boolean
  upload_url: string
  audio: AudioMetadata & { video_id?: string } // Backend also returns video_id field
}

export function useAudioUpload() {
  // Reactive state
  const uploadProgress = ref<Map<string, UploadProgress>>(new Map())
  const isUploading = ref(false)
  const currentUpload = ref<string | null>(null)

  // Upload state management
  let currentUploadAbortController: AbortController | null = null
  let uploadStartTime: number = 0

  // Get authentication headers using Cognito token
  const getAuthHeaders = async (): Promise<HeadersInit> => {
    try {
      // Get the current user from authManager to get the token
      const currentUser = authManager.getCurrentUser()
      if (!currentUser) {
        throw new Error('No authenticated user found')
      }

      // Get the JWT token from authManager (this returns ID token)
      const token = await authManager.getAccessToken()
      if (!token) {
        throw new Error('No authentication token available')
      }

      return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      }
    } catch (error) {
      console.error('Error getting auth headers:', error)
      throw new Error('Authentication failed. Please log in again.')
    }
  }

  // Generate presigned URL for upload
  const getUploadUrl = async (
    audioMetadata: Partial<AudioMetadata>,
  ): Promise<PresignedUploadResponse> => {
    try {
      const headers = await getAuthHeaders()

      console.log('🚀 Requesting audio upload URL from:', config.api.audioUploadUrlEndpoint)
      console.log('📋 Upload metadata:', {
        title: audioMetadata.title,
        filename: audioMetadata.filename,
        content_type: audioMetadata.content_type,
        file_size: audioMetadata.file_size,
      })

      const response = await fetch(config.api.audioUploadUrlEndpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          title: audioMetadata.title,
          filename: audioMetadata.filename,
          content_type: audioMetadata.content_type,
          file_size: audioMetadata.file_size,
          duration: audioMetadata.duration,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ Audio upload URL request failed:', response.status, errorText)
        throw new Error(`Failed to get upload URL: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('✅ Audio upload URL response:', {
        success: data.success,
        hasUploadUrl: !!data.upload_url,
        audioId: data.audio?.audio_id || data.audio?.video_id, // Backend uses video_id field
        audioMetadata: data.audio,
      })

      if (!data.success) {
        throw new Error(data.error || 'Failed to generate upload URL')
      }

      return data
    } catch (error) {
      console.error('❌ Error getting audio upload URL:', error)
      throw error
    }
  }

  // Upload file using presigned URL
  const uploadToS3 = async (
    file: File,
    presignedUrl: string,
    audioId: string,
    abortController: AbortController,
  ): Promise<void> => {
    console.log('📤 Starting S3 audio upload with presigned URL')
    console.log('🔗 URL:', presignedUrl.substring(0, 100) + '...')

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = uploadProgress.value.get(audioId)
          if (progress) {
            progress.uploadedSize = event.loaded
            progress.percentage = Math.round((event.loaded / event.total) * 100)

            // Calculate upload speed and ETA
            const now = Date.now()
            const timeElapsed = (now - uploadStartTime) / 1000 // seconds

            if (timeElapsed > 0) {
              progress.uploadSpeed = event.loaded / timeElapsed // bytes per second

              if (progress.uploadSpeed > 0) {
                const remainingBytes = event.total - event.loaded
                progress.estimatedTimeRemaining = remainingBytes / progress.uploadSpeed
              }
            }

            uploadProgress.value.set(audioId, { ...progress })

            // Log progress every 10%
            if (progress.percentage % 10 === 0) {
              console.log(
                `📊 Audio upload progress: ${progress.percentage}% (${formatFileSize(progress.uploadedSize)}/${formatFileSize(progress.totalSize)})`,
              )
            }
          }
        }
      })

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          console.log('✅ S3 audio upload completed successfully')
          resolve()
        } else {
          console.error('❌ S3 audio upload failed:', xhr.status, xhr.statusText)
          reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`))
        }
      })

      // Handle errors
      xhr.addEventListener('error', () => {
        console.error('❌ S3 audio upload failed due to network error')
        reject(new Error('Upload failed due to network error'))
      })

      // Handle abort
      xhr.addEventListener('abort', () => {
        console.log('⏹️ S3 audio upload was aborted')
        reject(new Error('Upload was aborted'))
      })

      // Set up abort signal
      abortController.signal.addEventListener('abort', () => {
        xhr.abort()
      })

      // Start the upload
      xhr.open('PUT', presignedUrl)
      xhr.setRequestHeader('Content-Type', file.type)
      console.log('🚀 Starting S3 audio PUT request...')
      xhr.send(file)
    })
  }

  // Main upload function
  const uploadAudio = async (file: File, title: string): Promise<AudioMetadata> => {
    // Validate file type
    if (!isValidAudioFile(file)) {
      throw new Error('Invalid file type. Please select an audio file (MP3, WAV, M4A, AAC, OGG).')
    }

    // Validate file size (max 100MB for audio)
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      throw new Error('File size too large. Maximum size is 100MB.')
    }

    // Generate a temporary audio ID for progress tracking
    const tempAudioId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Initialize progress tracking
    const progress: UploadProgress = {
      audioId: tempAudioId,
      filename: file.name,
      totalSize: file.size,
      uploadedSize: 0,
      percentage: 0,
      status: 'pending',
    }

    uploadProgress.value.set(tempAudioId, progress)
    isUploading.value = true
    currentUpload.value = tempAudioId

    // Set up abort controller
    const abortController = new AbortController()
    currentUploadAbortController = abortController

    try {
      console.log('🚀 Starting audio upload:', {
        filename: file.name,
        size: file.size,
        type: file.type,
        title,
      })

      progress.status = 'uploading'
      uploadProgress.value.set(tempAudioId, { ...progress })

      // Step 1: Get presigned URL
      console.log('📋 Step 1: Getting presigned URL...')
      const uploadData = await getUploadUrl({
        title: title.trim(),
        filename: file.name,
        content_type: file.type,
        file_size: file.size,
        duration: undefined, // Will be filled later if needed
      })

      // Update progress with real audio ID
      // Backend returns video_id field instead of audio_id
      const realAudioId = uploadData.audio.audio_id || uploadData.audio.video_id
      if (!realAudioId) {
        throw new Error('No audio ID returned from upload URL response')
      }

      progress.audioId = realAudioId
      uploadProgress.value.delete(tempAudioId)
      uploadProgress.value.set(realAudioId, { ...progress })
      currentUpload.value = realAudioId

      console.log('✅ Step 1 complete. Audio ID:', realAudioId)

      // Step 2: Upload to S3 using presigned URL
      console.log('📤 Step 2: Uploading to S3...')
      uploadStartTime = Date.now()
      await uploadToS3(file, uploadData.upload_url, realAudioId, abortController)

      // Step 3: Save metadata to database
      console.log('💾 Step 3: Saving metadata to database...')
      // Create the metadata for saving with correct field names
      const metadataToSave: AudioMetadata = {
        audio_id: realAudioId,
        user_id: uploadData.audio.user_id,
        user_email: uploadData.audio.user_email,
        title: uploadData.audio.title,
        filename: uploadData.audio.filename,
        bucket_location: uploadData.audio.bucket_location,
        upload_date: uploadData.audio.upload_date,
        file_size: uploadData.audio.file_size,
        content_type: uploadData.audio.content_type,
        duration: uploadData.audio.duration,
        created_at: uploadData.audio.created_at,
        updated_at: uploadData.audio.updated_at,
        transcription_status: uploadData.audio.transcription_status || 'pending',
        transcription_data: uploadData.audio.transcription_data,
      }

      console.log('🎵 Metadata to save:', metadataToSave)
      console.log('🎵 Audio ID in metadata:', metadataToSave.audio_id)

      const savedAudio = await AudioService.saveAudioMetadata(metadataToSave)

      // Mark as completed
      progress.status = 'completed'
      progress.percentage = 100
      uploadProgress.value.set(realAudioId, { ...progress })

      console.log('✅ Audio upload completed successfully!')
      console.log('📊 Final metadata:', savedAudio)

      return savedAudio
    } catch (error) {
      console.error('❌ Audio upload failed:', error)

      // Update progress for the current audio ID (temp or real)
      const currentProgressKey = currentUpload.value || tempAudioId
      const currentProgress = uploadProgress.value.get(currentProgressKey)
      if (currentProgress) {
        currentProgress.status = 'error'
        uploadProgress.value.set(currentProgressKey, { ...currentProgress })
      }

      throw error
    } finally {
      isUploading.value = false
      currentUpload.value = null
      currentUploadAbortController = null
    }
  }

  // Pause upload (not supported with presigned URLs)
  const pauseUpload = async (): Promise<void> => {
    console.warn('Pause/resume is not supported with presigned URL uploads')
  }

  // Resume upload (not supported with presigned URLs)
  const resumeUpload = async (): Promise<void> => {
    console.warn('Pause/resume is not supported with presigned URL uploads')
  }

  // Cancel upload
  const cancelUpload = async (): Promise<void> => {
    if (currentUploadAbortController) {
      currentUploadAbortController.abort()
    }

    if (currentUpload.value) {
      uploadProgress.value.delete(currentUpload.value)
      currentUpload.value = null
    }

    isUploading.value = false
    currentUploadAbortController = null
  }

  // Validate if file is a supported audio format
  const isValidAudioFile = (file: File): boolean => {
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

  // Computed properties
  const currentProgress = computed(() => {
    if (!currentUpload.value) return null
    return uploadProgress.value.get(currentUpload.value) || null
  })

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}m ${secs}s`
  }

  const formatSpeed = (bytesPerSecond: number): string => {
    return formatFileSize(bytesPerSecond) + '/s'
  }

  return {
    // State
    uploadProgress,
    isUploading,
    currentUpload,
    currentProgress,

    // Actions
    uploadAudio,
    pauseUpload,
    resumeUpload,
    cancelUpload,

    // Utils
    formatFileSize,
    formatTime,
    formatSpeed,
    isValidAudioFile,
  }
}
