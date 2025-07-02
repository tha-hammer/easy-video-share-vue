import { ref, computed } from 'vue'

interface UploadProgress {
  videoId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number
  uploadSpeed?: number
  chunkProgress: Map<number, number>
  completedChunks: number
  totalChunks: number
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

// New interfaces for API integration
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
  cutting_options?: Record<string, unknown>
  text_strategy?: string
  text_input?: unknown
  user_id?: string // Optional user ID for tracking
  // Additional video metadata fields
  filename?: string
  file_size?: number
  title?: string
  user_email?: string
  content_type?: string
}

interface AnalyzeDurationRequest {
  s3_key: string
  cutting_options: Record<string, unknown>
}

interface AnalyzeDurationResponse {
  estimated_num_segments: number
  duration_seconds: number
}

// --- Replace CuttingOptions interface with backend-aligned structure ---
interface CuttingOptionsFixed {
  strategy: 'fixed'
  params: { duration_seconds: number }
}
interface CuttingOptionsRandom {
  strategy: 'random'
  params: { min_seconds: number; max_seconds: number }
}
type CuttingOptions = CuttingOptionsFixed | CuttingOptionsRandom

export function useVideoUpload() {
  // Reactive state
  const uploadProgress = ref<Map<string, UploadProgress>>(new Map())
  const isUploading = ref(false)
  const currentUpload = ref<string | null>(null)

  // New state for wizard
  const jobId = ref<string | null>(null)
  const s3Key = ref<string | null>(null)
  const presignedUrl = ref<string | null>(null)
  const estimatedSegments = ref<number | null>(null)
  const videoDuration = ref<number | null>(null)
  const cuttingOptions = ref<CuttingOptions>({
    strategy: 'fixed',
    params: { duration_seconds: 30 },
  })

  // Upload configuration (adaptive based on device/network)
  const getUploadConfig = () => {
    const MB = 1024 * 1024
    const isMobile = /Android|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(navigator.userAgent)
    const netInfo =
      (navigator as unknown as { connection?: { effectiveType?: string } }).connection ||
      (navigator as unknown as { mozConnection?: { effectiveType?: string } }).mozConnection ||
      (navigator as unknown as { webkitConnection?: { effectiveType?: string } }).webkitConnection
    const slowLink =
      netInfo && netInfo.effectiveType && ['slow-2g', '2g', '3g'].includes(netInfo.effectiveType)

    if (isMobile || slowLink) {
      return {
        chunkSize: 8 * MB, // 8 MB parts for mobile
        maxConcurrentUploads: 3, // Fewer parallel uploads
        useTransferAcceleration: false,
      }
    } else {
      return {
        chunkSize: 16 * MB, // 16 MB parts for desktop
        maxConcurrentUploads: 6, // More parallel uploads
        useTransferAcceleration: true,
      }
    }
  }

  // Upload state management
  const currentMultipartUpload: {
    uploadId: string
    key: string
    abortController: AbortController
  } | null = null
  const uploadedParts: { ETag: string; PartNumber: number }[] = []
  const uploadStartTime: number = 0
  const lastProgressTime: number = 0
  const lastProgressBytes: number = 0

  // Main upload function using pre-signed URL
  const uploadVideo = async (file: File, metadata: VideoMetadata): Promise<void> => {
    const videoId = metadata.video_id
    const progress: UploadProgress = {
      videoId,
      filename: file.name,
      totalSize: file.size,
      uploadedSize: 0,
      percentage: 0,
      status: 'pending',
      chunkProgress: new Map(),
      completedChunks: 0,
      totalChunks: 1,
    }
    uploadProgress.value.set(videoId, progress)
    isUploading.value = true
    currentUpload.value = videoId
    try {
      // Use pre-signed URL for upload
      if (!presignedUrl.value) throw new Error('No pre-signed URL available')
      await uploadFileToPresignedUrl(file, presignedUrl.value, progress)
      progress.status = 'completed'
      progress.percentage = 100
      uploadProgress.value.set(videoId, { ...progress })
      console.log(`✅ Upload completed for ${videoId}`)
    } catch (error) {
      console.error(`❌ Upload failed for ${videoId}:`, error)
      progress.status = 'error'
      uploadProgress.value.set(videoId, { ...progress })
      throw error
    } finally {
      isUploading.value = false
      currentUpload.value = null
    }
  }

  // Upload file to S3 using pre-signed URL with progress
  const uploadFileToPresignedUrl = async (
    file: File,
    url: string,
    progress: UploadProgress,
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      console.log('🔍 Debug: Starting S3 upload to:', url)
      console.log('🔍 Debug: File size:', file.size, 'File type:', file.type)

      const xhr = new XMLHttpRequest()
      xhr.open('PUT', url, true)
      xhr.setRequestHeader('Content-Type', file.type)

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          progress.uploadedSize = event.loaded
          progress.percentage = Math.round((event.loaded / event.total) * 100)
          progress.status = 'uploading'
          uploadProgress.value.set(progress.videoId, { ...progress })
          console.log(`🔍 Debug: Upload progress: ${progress.percentage}%`)
        }
      }

      xhr.onload = () => {
        console.log('🔍 Debug: S3 upload response status:', xhr.status)
        console.log('🔍 Debug: S3 upload response headers:', xhr.getAllResponseHeaders())

        if (xhr.status >= 200 && xhr.status < 300) {
          console.log('🔍 Debug: S3 upload successful')
          resolve()
        } else {
          console.error('🔍 Debug: S3 upload failed:', xhr.status, xhr.statusText)
          console.error('🔍 Debug: S3 upload response:', xhr.responseText)
          reject(new Error(`S3 upload failed: ${xhr.status} ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => {
        console.error('🔍 Debug: S3 upload network error')
        reject(new Error('S3 upload failed'))
      }

      xhr.send(file)
    })
  }

  // API: Initiate upload
  const initiateUpload = async (file: File): Promise<InitiateUploadResponse> => {
    const req: InitiateUploadRequest = {
      filename: file.name,
      content_type: file.type,
      file_size: file.size,
    }

    // Use Railway backend URL from environment or fallback to localhost for development
    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/initiate`

    console.log('🔍 Debug: Making request to:', url)
    console.log('🔍 Debug: Request body:', req)
    console.log(
      '🔍 Debug: Environment VITE_AI_VIDEO_BACKEND_URL:',
      import.meta.env.VITE_AI_VIDEO_BACKEND_URL,
    )

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      console.log('🔍 Debug: Response status:', res.status)
      console.log('🔍 Debug: Response headers:', Object.fromEntries(res.headers.entries()))

      if (!res.ok) {
        const errorText = await res.text()
        console.error('🔍 Debug: Error response body:', errorText)
        console.error('🔍 Debug: Full error details:', {
          status: res.status,
          statusText: res.statusText,
          url: res.url,
          headers: Object.fromEntries(res.headers.entries()),
        })
        throw new Error(`Failed to initiate upload: ${res.status} ${res.statusText} - ${errorText}`)
      }

      const data = await res.json()
      console.log('🔍 Debug: Success response:', data)
      presignedUrl.value = data.presigned_url
      s3Key.value = data.s3_key
      jobId.value = data.job_id
      return data
    } catch (error) {
      console.error('🔍 Debug: Fetch error:', error)
      throw error
    }
  }

  // Utility to flatten cutting options for backend
  function flattenCuttingOptions(options: CuttingOptions): Record<string, unknown> {
    if (!options) return {}
    const { strategy, params } = options as { strategy: string; params: Record<string, unknown> }
    if (!params || typeof params !== 'object') return { strategy }
    return { strategy, ...params }
  }

  // API: Complete upload
  const completeUpload = async (
    cutting_options?: CuttingOptions,
    text_strategy?: string,
    text_input?: unknown,
    userId?: string,
    videoMetadata?: VideoMetadata,
  ): Promise<{ job_id: string }> => {
    if (!s3Key.value || !jobId.value) throw new Error('Missing s3Key or jobId')

    // Convert frontend cutting options to backend format
    let backendCuttingOptions: Record<string, unknown> | undefined
    if (cutting_options) {
      if (cutting_options.strategy === 'fixed') {
        backendCuttingOptions = {
          type: 'fixed',
          duration_seconds: cutting_options.params.duration_seconds,
        }
      } else if (cutting_options.strategy === 'random') {
        backendCuttingOptions = {
          type: 'random',
          min_duration: cutting_options.params.min_seconds,
          max_duration: cutting_options.params.max_seconds,
        }
      }
    }

    const req: CompleteUploadRequest = {
      s3_key: s3Key.value,
      job_id: jobId.value,
      cutting_options: backendCuttingOptions,
      text_strategy,
      text_input,
      user_id: userId, // Optional user ID for tracking
      filename: videoMetadata?.filename,
      file_size: videoMetadata?.file_size,
      title: videoMetadata?.title,
      user_email: videoMetadata?.user_email,
      content_type: videoMetadata?.content_type,
    }

    console.log('🔍 Debug: complete-upload request:', req)

    // Use Railway backend URL from environment or fallback to localhost for development
    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/upload/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })

    if (!res.ok) {
      const errorText = await res.text()
      console.error('🔍 Debug: complete-upload error:', res.status, errorText)
      throw new Error(`Failed to complete upload: ${res.status} ${res.statusText}`)
    }

    const data = await res.json()
    console.log('🔍 Debug: complete-upload response:', data)
    return data
  }

  // API: Analyze duration
  const analyzeDuration = async (payload?: CuttingOptions): Promise<AnalyzeDurationResponse> => {
    if (!s3Key.value) throw new Error('Missing s3Key')

    // Convert frontend cutting options to backend format
    const options = payload || cuttingOptions.value
    let backendCuttingOptions: Record<string, unknown>

    if (options.strategy === 'fixed') {
      backendCuttingOptions = {
        type: 'fixed',
        duration_seconds: options.params.duration_seconds,
      }
    } else if (options.strategy === 'random') {
      backendCuttingOptions = {
        type: 'random',
        min_duration: options.params.min_seconds,
        max_duration: options.params.max_seconds,
      }
    } else {
      throw new Error('Invalid cutting strategy')
    }

    const req: AnalyzeDurationRequest = {
      s3_key: s3Key.value,
      cutting_options: backendCuttingOptions,
    }

    console.log('🔍 Debug: analyze-duration request:', req)

    // Use Railway backend URL from environment or fallback to localhost for development
    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/video/analyze-duration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })

    if (!res.ok) {
      const errorText = await res.text()
      console.error('🔍 Debug: analyze-duration error:', res.status, errorText)
      throw new Error(`Failed to analyze duration: ${res.status} ${res.statusText}`)
    }

    const data = await res.json()
    console.log('🔍 Debug: analyze-duration response:', data)
    estimatedSegments.value = data.num_segments
    videoDuration.value = data.total_duration
    return data
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

    // New state and actions
    jobId,
    s3Key,
    presignedUrl,
    estimatedSegments,
    videoDuration,
    cuttingOptions,
    initiateUpload,
    completeUpload,
    analyzeDuration,

    // Actions
    uploadVideo,

    // Utils
    formatFileSize,
    formatTime,
    formatSpeed,
  }
}
