import { ref, computed } from 'vue'
import type { VideoMetadata } from '@/core/services/VideoService'

// Types for multi-part upload
interface MultipartUploadState {
  uploadId: string
  s3Key: string
  jobId: string
  chunkSize: number
  maxConcurrentUploads: number
  parts: Array<{
    partNumber: number
    etag: string
    uploaded: boolean
  }>
  totalParts: number
}

interface UploadChunk {
  partNumber: number
  start: number
  end: number
  data: Blob
}

interface InitiateMultipartUploadResponse {
  upload_id: string
  s3_key: string
  job_id: string
  chunk_size: number
  max_concurrent_uploads: number
}

interface UploadPartResponse {
  presigned_url: string
  part_number: number
}

interface CompleteMultipartUploadRequest {
  upload_id: string
  s3_key: string
  job_id: string
  parts: Array<{
    PartNumber: number
    ETag: string
  }>
  cutting_options?: any
  text_strategy?: string
  text_input?: any
  user_id?: string
  filename?: string
  file_size?: number
  title?: string
  user_email?: string
  content_type?: string
}

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

interface UploadProgress {
  videoId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  chunkProgress: Map<number, number>
  completedChunks: number
  totalChunks: number
}

interface CuttingOptions {
  strategy: 'fixed' | 'random'
  params: {
    duration_seconds?: number
    min_duration?: number
    max_duration?: number
  }
}

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

  // Multi-part upload state
  const multipartState = ref<MultipartUploadState | null>(null)

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

  // Determine if we should use multi-part upload
  const shouldUseMultipart = (fileSize: number): boolean => {
    const MB = 1024 * 1024
    const isMobile = /Android|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(navigator.userAgent)

    // Use multi-part for files larger than 100MB on mobile or 200MB on desktop
    if (isMobile) {
      return fileSize > 100 * MB
    } else {
      return fileSize > 200 * MB
    }
  }

  // Split file into chunks for multi-part upload
  const splitFileIntoChunks = (file: File, chunkSize: number): UploadChunk[] => {
    const chunks: UploadChunk[] = []
    let partNumber = 1
    let start = 0

    while (start < file.size) {
      const end = Math.min(start + chunkSize, file.size)
      const data = file.slice(start, end)

      chunks.push({
        partNumber,
        start,
        end,
        data,
      })

      start = end
      partNumber++
    }

    return chunks
  }

  // Upload a single chunk
  const uploadChunk = async (
    chunk: UploadChunk,
    presignedUrl: string,
    progress: UploadProgress,
  ): Promise<{ ETag: string; PartNumber: number }> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('PUT', presignedUrl, true)

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const chunkProgress = (event.loaded / event.total) * 100
          progress.chunkProgress.set(chunk.partNumber, chunkProgress)

          // Update overall progress
          let totalChunkProgress = 0
          progress.chunkProgress.forEach((p) => {
            totalChunkProgress += p
          })
          progress.uploadedSize = Math.round(
            (totalChunkProgress / progress.totalChunks) * progress.totalSize,
          )
          progress.percentage = Math.round((progress.uploadedSize / progress.totalSize) * 100)

          uploadProgress.value.set(progress.videoId, { ...progress })
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const etag = xhr.getResponseHeader('ETag')?.replace(/"/g, '') || ''
          progress.completedChunks++
          uploadProgress.value.set(progress.videoId, { ...progress })
          resolve({ ETag: etag, PartNumber: chunk.partNumber })
        } else {
          reject(new Error(`Chunk upload failed: ${xhr.status} ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => {
        reject(new Error('Chunk upload network error'))
      }

      xhr.send(chunk.data)
    })
  }

  // Main upload function with multi-part support
  const uploadVideo = async (file: File, metadata: VideoMetadata): Promise<void> => {
    const videoId = metadata.video_id

    if (shouldUseMultipart(file.size)) {
      await uploadVideoMultipart(file, metadata)
    } else {
      await uploadVideoSingle(file, metadata)
    }
  }

  // Single-part upload (existing logic)
  const uploadVideoSingle = async (file: File, metadata: VideoMetadata): Promise<void> => {
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

  // Multi-part upload
  const uploadVideoMultipart = async (file: File, metadata: VideoMetadata): Promise<void> => {
    const videoId = metadata.video_id

    if (!multipartState.value) {
      throw new Error('Multi-part upload not initiated')
    }

    const progress: UploadProgress = {
      videoId,
      filename: file.name,
      totalSize: file.size,
      uploadedSize: 0,
      percentage: 0,
      status: 'pending',
      chunkProgress: new Map(),
      completedChunks: 0,
      totalChunks: multipartState.value.totalParts,
    }
    uploadProgress.value.set(videoId, progress)
    isUploading.value = true
    currentUpload.value = videoId

    try {
      // Split file into chunks
      const chunks = splitFileIntoChunks(file, multipartState.value.chunkSize)
      console.log(`📦 Split file into ${chunks.length} chunks`)

      // Upload chunks in parallel with concurrency limit
      const uploadedParts: Array<{ ETag: string; PartNumber: number }> = []
      const concurrencyLimit = multipartState.value.maxConcurrentUploads

      for (let i = 0; i < chunks.length; i += concurrencyLimit) {
        const batch = chunks.slice(i, i + concurrencyLimit)
        const batchPromises = batch.map(async (chunk) => {
          // Get presigned URL for this part
          const partResponse = await getUploadPartUrl(chunk.partNumber)

          // Upload the chunk
          const result = await uploadChunk(chunk, partResponse.presigned_url, progress)
          return result
        })

        const batchResults = await Promise.all(batchPromises)
        uploadedParts.push(...batchResults)

        console.log(
          `✅ Uploaded batch ${Math.floor(i / concurrencyLimit) + 1}/${Math.ceil(chunks.length / concurrencyLimit)}`,
        )
      }

      // Complete the multi-part upload
      await completeMultipartUpload(uploadedParts, metadata)

      progress.status = 'completed'
      progress.percentage = 100
      uploadProgress.value.set(videoId, { ...progress })
      console.log(`✅ Multi-part upload completed for ${videoId}`)
    } catch (error) {
      console.error(`❌ Multi-part upload failed for ${videoId}:`, error)
      progress.status = 'error'
      uploadProgress.value.set(videoId, { ...progress })

      // Try to abort the upload
      try {
        await abortMultipartUpload()
      } catch (abortError) {
        console.error('Failed to abort multi-part upload:', abortError)
      }

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

  // API: Initiate upload (single-part)
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

  // API: Initiate multi-part upload
  const initiateMultipartUpload = async (file: File): Promise<InitiateMultipartUploadResponse> => {
    const req: InitiateUploadRequest = {
      filename: file.name,
      content_type: file.type,
      file_size: file.size,
    }

    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/initiate-multipart`

    console.log('🔍 Debug: Initiating multi-part upload to:', url)
    console.log('🔍 Debug: Request body:', req)

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(
          `Failed to initiate multipart upload: ${res.status} ${res.statusText} - ${errorText}`,
        )
      }

      const data: InitiateMultipartUploadResponse = await res.json()
      console.log('🔍 Debug: Multi-part upload initiated:', data)

      // Calculate total parts
      const totalParts = Math.ceil(file.size / data.chunk_size)

      // Initialize multi-part state
      multipartState.value = {
        uploadId: data.upload_id,
        s3Key: data.s3_key,
        jobId: data.job_id,
        chunkSize: data.chunk_size,
        maxConcurrentUploads: data.max_concurrent_uploads,
        parts: [],
        totalParts,
      }

      s3Key.value = data.s3_key
      jobId.value = data.job_id

      return data
    } catch (error) {
      console.error('🔍 Debug: Multi-part upload initiation error:', error)
      throw error
    }
  }

  // API: Get presigned URL for uploading a part
  const getUploadPartUrl = async (partNumber: number): Promise<UploadPartResponse> => {
    if (!multipartState.value) {
      throw new Error('Multi-part upload not initiated')
    }

    const req = {
      upload_id: multipartState.value.uploadId,
      s3_key: multipartState.value.s3Key,
      part_number: partNumber,
      content_type: 'video/mp4', // We'll use a generic content type for parts
    }

    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/part`

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(
          `Failed to get upload part URL: ${res.status} ${res.statusText} - ${errorText}`,
        )
      }

      const data: UploadPartResponse = await res.json()
      return data
    } catch (error) {
      console.error('🔍 Debug: Get upload part URL error:', error)
      throw error
    }
  }

  // API: Complete multi-part upload
  const completeMultipartUpload = async (
    parts: Array<{ ETag: string; PartNumber: number }>,
    metadata: VideoMetadata,
  ): Promise<void> => {
    if (!multipartState.value) {
      throw new Error('Multi-part upload not initiated')
    }

    const req: CompleteMultipartUploadRequest = {
      upload_id: multipartState.value.uploadId,
      s3_key: multipartState.value.s3Key,
      job_id: multipartState.value.jobId,
      parts: parts.map((p) => ({ PartNumber: p.PartNumber, ETag: p.ETag })),
      user_id: metadata.user_id,
      filename: metadata.filename,
      file_size: metadata.file_size,
      title: metadata.title,
      user_email: metadata.user_email,
      content_type: metadata.content_type,
    }

    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/complete-multipart`

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(
          `Failed to complete multipart upload: ${res.status} ${res.statusText} - ${errorText}`,
        )
      }

      const data = await res.json()
      console.log('🔍 Debug: Multi-part upload completed:', data)
    } catch (error) {
      console.error('🔍 Debug: Complete multipart upload error:', error)
      throw error
    }
  }

  // API: Abort multi-part upload
  const abortMultipartUpload = async (): Promise<void> => {
    if (!multipartState.value) {
      return
    }

    const req = {
      upload_id: multipartState.value.uploadId,
      s3_key: multipartState.value.s3Key,
    }

    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/abort-multipart`

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      if (res.ok) {
        console.log('🔍 Debug: Multi-part upload aborted successfully')
      }
    } catch (error) {
      console.error('🔍 Debug: Abort multipart upload error:', error)
    }
  }

  // API: Complete upload (single-part)
  const completeUpload = async (
    cuttingOptions: any,
    textStrategy: string,
    textInput: any,
    userId: string,
    videoMetadata: VideoMetadata,
  ): Promise<void> => {
    const req = {
      s3_key: s3Key.value,
      job_id: jobId.value,
      cutting_options: cuttingOptions,
      text_strategy: textStrategy,
      text_input: textInput,
      user_id: userId,
      filename: videoMetadata.filename,
      file_size: videoMetadata.file_size,
      title: videoMetadata.title,
      user_email: videoMetadata.user_email,
      content_type: videoMetadata.content_type,
    }

    // Use Railway backend URL from environment or fallback to localhost for development
    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/upload/complete`

    console.log('🔍 Debug: Making complete request to:', url)
    console.log('🔍 Debug: Request body:', req)

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      console.log('🔍 Debug: Complete response status:', res.status)

      if (!res.ok) {
        const errorText = await res.text()
        console.error('🔍 Debug: Complete error response:', errorText)
        throw new Error(`Failed to complete upload: ${res.status} ${res.statusText} - ${errorText}`)
      }

      const data = await res.json()
      console.log('🔍 Debug: Complete success response:', data)
    } catch (error) {
      console.error('🔍 Debug: Complete fetch error:', error)
      throw error
    }
  }

  // API: Analyze duration
  const analyzeDuration = async (s3Key: string, cuttingOptions: any): Promise<any> => {
    const req = {
      s3_key: s3Key,
      cutting_options: cuttingOptions,
    }

    // Use Railway backend URL from environment or fallback to localhost for development
    const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/video/analyze-duration`

    console.log('🔍 Debug: Making analyze-duration request to:', url)
    console.log('🔍 Debug: Request body:', req)

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })

      console.log('🔍 Debug: analyze-duration response status:', res.status)

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
    } catch (error) {
      console.error('🔍 Debug: analyze-duration fetch error:', error)
      throw error
    }
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
    multipartState,
    initiateUpload,
    initiateMultipartUpload,
    completeUpload,
    analyzeDuration,

    // Actions
    uploadVideo,
    uploadVideoSingle,
    uploadVideoMultipart,
    shouldUseMultipart,

    // Utils
    formatFileSize,
    formatTime,
    formatSpeed,
  }
}
