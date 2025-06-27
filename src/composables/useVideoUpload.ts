import { ref, computed } from 'vue'
import { config } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'

interface UploadProgress {
  videoId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number
  uploadSpeed?: number
}

interface VideoMetadata {
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
}

interface PresignedUploadResponse {
  success: boolean
  upload_url: string
  video: VideoMetadata
}

export function useVideoUpload() {
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
    videoMetadata: Partial<VideoMetadata>,
  ): Promise<PresignedUploadResponse> => {
    try {
      const headers = await getAuthHeaders()

      console.log('🚀 Requesting upload URL from:', config.api.videosUploadUrlEndpoint)
      console.log('📋 Upload metadata:', {
        title: videoMetadata.title,
        filename: videoMetadata.filename,
        content_type: videoMetadata.content_type,
        file_size: videoMetadata.file_size,
      })

      const response = await fetch(config.api.videosUploadUrlEndpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          title: videoMetadata.title,
          filename: videoMetadata.filename,
          content_type: videoMetadata.content_type,
          file_size: videoMetadata.file_size,
          duration: videoMetadata.duration,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ Upload URL request failed:', response.status, errorText)
        throw new Error(`Failed to get upload URL: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('✅ Upload URL response:', {
        success: data.success,
        hasUploadUrl: !!data.upload_url,
        videoId: data.video?.video_id,
      })

      if (!data.success) {
        throw new Error(data.error || 'Failed to generate upload URL')
      }

      return data
    } catch (error) {
      console.error('❌ Error getting upload URL:', error)
      throw error
    }
  }

  // Upload file using presigned URL
  const uploadToS3 = async (
    file: File,
    presignedUrl: string,
    videoId: string,
    abortController: AbortController,
  ): Promise<void> => {
    console.log('📤 Starting S3 upload with presigned URL')
    console.log('🔗 URL:', presignedUrl.substring(0, 100) + '...')

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = uploadProgress.value.get(videoId)
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

            uploadProgress.value.set(videoId, { ...progress })

            // Log progress every 10%
            if (progress.percentage % 10 === 0) {
              console.log(
                `📊 Upload progress: ${progress.percentage}% (${formatFileSize(progress.uploadedSize)}/${formatFileSize(progress.totalSize)})`,
              )
            }
          }
        }
      })

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          console.log('✅ S3 upload completed successfully')
          resolve()
        } else {
          console.error('❌ S3 upload failed:', xhr.status, xhr.statusText)
          reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`))
        }
      })

      // Handle errors
      xhr.addEventListener('error', () => {
        console.error('❌ S3 upload failed due to network error')
        reject(new Error('Upload failed due to network error'))
      })

      // Handle abort
      xhr.addEventListener('abort', () => {
        console.log('⏹️ S3 upload was aborted')
        reject(new Error('Upload was aborted'))
      })

      // Set up abort signal
      abortController.signal.addEventListener('abort', () => {
        xhr.abort()
      })

      // Start the upload
      xhr.open('PUT', presignedUrl)
      xhr.setRequestHeader('Content-Type', file.type)
      console.log('🚀 Starting S3 PUT request...')
      xhr.send(file)
    })
  }

  // Main upload function
  const uploadVideo = async (file: File, title: string): Promise<VideoMetadata> => {
    // Generate a temporary video ID for progress tracking
    const tempVideoId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Initialize progress tracking
    const progress: UploadProgress = {
      videoId: tempVideoId,
      filename: file.name,
      totalSize: file.size,
      uploadedSize: 0,
      percentage: 0,
      status: 'pending',
    }

    uploadProgress.value.set(tempVideoId, progress)
    isUploading.value = true
    currentUpload.value = tempVideoId

    // Set up abort controller
    const abortController = new AbortController()
    currentUploadAbortController = abortController

    try {
      console.log('🚀 Starting video upload:', {
        filename: file.name,
        size: file.size,
        type: file.type,
        title,
      })

      progress.status = 'uploading'
      uploadProgress.value.set(tempVideoId, { ...progress })

      // Step 1: Get presigned URL
      console.log('📋 Step 1: Getting presigned URL...')
      const uploadData = await getUploadUrl({
        title: title.trim(),
        filename: file.name,
        content_type: file.type,
        file_size: file.size,
        duration: undefined, // Will be filled later if needed
      })

      // Update progress with real video ID
      const realVideoId = uploadData.video.video_id
      progress.videoId = realVideoId
      uploadProgress.value.delete(tempVideoId)
      uploadProgress.value.set(realVideoId, { ...progress })
      currentUpload.value = realVideoId

      console.log('✅ Step 1 complete. Video ID:', realVideoId)

      // Step 2: Upload to S3 using presigned URL
      console.log('📤 Step 2: Uploading to S3...')
      uploadStartTime = Date.now()
      await uploadToS3(file, uploadData.upload_url, realVideoId, abortController)

      // Mark as completed
      progress.status = 'completed'
      progress.percentage = 100
      uploadProgress.value.set(realVideoId, { ...progress })

      console.log('✅ Upload completed successfully!')
      console.log('📊 Final metadata:', uploadData.video)

      return uploadData.video
    } catch (error) {
      console.error('❌ Upload failed:', error)

      // Update progress for the current video ID (temp or real)
      const currentProgressKey = currentUpload.value || tempVideoId
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
    uploadVideo,
    pauseUpload,
    resumeUpload,
    cancelUpload,

    // Utils
    formatFileSize,
    formatTime,
    formatSpeed,
  }
}
