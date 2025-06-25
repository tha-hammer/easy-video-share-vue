import { ref, computed } from 'vue'
import {
  S3Client,
  CreateMultipartUploadCommand,
  UploadPartCommand,
  CompleteMultipartUploadCommand,
  AbortMultipartUploadCommand,
} from '@aws-sdk/client-s3'
import { config } from '@/core/config/config'

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
  bucketLocation: string
  upload_date: string
  file_size?: number
  content_type?: string
  duration?: number
  created_at: string
  updated_at: string
}

export function useVideoUpload() {
  // Reactive state
  const uploadProgress = ref<Map<string, UploadProgress>>(new Map())
  const isUploading = ref(false)
  const currentUpload = ref<string | null>(null)

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

  // Initialize S3 clients
  const uploadConfig = getUploadConfig()

  const s3Client = new S3Client({
    region: config.aws.region,
    credentials: config.aws.credentials,
    useAccelerateEndpoint: uploadConfig.useTransferAcceleration,
  })

  const s3ClientFallback = new S3Client({
    region: config.aws.region,
    credentials: config.aws.credentials,
    useAccelerateEndpoint: false,
  })

  // Upload state management
  let currentMultipartUpload: {
    uploadId: string
    key: string
    abortController: AbortController
  } | null = null
  let uploadedParts: { ETag: string; PartNumber: number }[] = []
  let uploadStartTime: number = 0
  const lastProgressTime: number = 0
  const lastProgressBytes: number = 0

  // Main upload function
  const uploadVideo = async (file: File, metadata: VideoMetadata): Promise<void> => {
    const videoId = metadata.video_id

    // Initialize progress tracking
    const totalChunks = Math.ceil(file.size / uploadConfig.chunkSize)
    const progress: UploadProgress = {
      videoId,
      filename: file.name,
      totalSize: file.size,
      uploadedSize: 0,
      percentage: 0,
      status: 'pending',
      chunkProgress: new Map(),
      completedChunks: 0,
      totalChunks,
    }

    uploadProgress.value.set(videoId, progress)
    isUploading.value = true
    currentUpload.value = videoId

    try {
      const key = metadata.bucketLocation
      await uploadWithMultipart(file, key, videoId)

      // Mark as completed
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
      currentMultipartUpload = null
      uploadedParts = []
    }
  }

  // Multipart upload implementation
  const uploadWithMultipart = async (file: File, key: string, videoId: string): Promise<void> => {
    const bucketName = config.aws.bucketName

    try {
      // Step 1: Create multipart upload
      const createCommand = new CreateMultipartUploadCommand({
        Bucket: bucketName,
        Key: key,
        ContentType: file.type,
        Metadata: {
          'original-filename': file.name,
          'video-id': videoId,
        },
      })

      const createResponse = await s3Client.send(createCommand)
      const uploadId = createResponse.UploadId!

      // Set up abort controller for cancellation
      const abortController = new AbortController()
      currentMultipartUpload = { uploadId, key, abortController }

      // Step 2: Upload parts in parallel
      uploadStartTime = Date.now()
      await uploadPartsInParallel(file, key, uploadId, videoId, abortController)

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
      console.log(`✅ Multipart upload completed for ${key}`)
    } catch (error) {
      // Clean up failed upload
      if (currentMultipartUpload) {
        await abortMultipartUpload()
      }
      throw error
    }
  }

  // Upload parts in parallel with progress tracking
  const uploadPartsInParallel = async (
    file: File,
    key: string,
    uploadId: string,
    videoId: string,
    abortController: AbortController,
  ): Promise<void> => {
    const totalChunks = Math.ceil(file.size / uploadConfig.chunkSize)
    const semaphore = new Array(uploadConfig.maxConcurrentUploads).fill(null)
    let partNumber = 1

    const uploadPromises: Promise<void>[] = []

    const uploadNextChunk = async (): Promise<void> => {
      const currentPartNumber = partNumber++
      if (currentPartNumber > totalChunks) return

      const startByte = (currentPartNumber - 1) * uploadConfig.chunkSize
      const endByte = Math.min(startByte + uploadConfig.chunkSize, file.size)
      const chunk = file.slice(startByte, endByte)

      try {
        await uploadChunkWithProgress(
          chunk,
          key,
          uploadId,
          currentPartNumber,
          startByte,
          file.size,
          totalChunks,
          videoId,
          abortController,
        )

        // Recursively upload next chunk
        await uploadNextChunk()
      } catch (error) {
        if (!abortController.signal.aborted) {
          throw error
        }
      }
    }

    // Start parallel uploads
    for (let i = 0; i < uploadConfig.maxConcurrentUploads && i < totalChunks; i++) {
      uploadPromises.push(uploadNextChunk())
    }

    await Promise.all(uploadPromises)
  }

  // Upload individual chunk with progress tracking
  const uploadChunkWithProgress = async (
    chunk: Blob,
    key: string,
    uploadId: string,
    partNumber: number,
    startByte: number,
    totalFileSize: number,
    totalChunks: number,
    videoId: string,
    abortController: AbortController,
  ): Promise<void> => {
    const bucketName = config.aws.bucketName

    try {
      // Convert Blob to ArrayBuffer for AWS SDK v3 compatibility
      const arrayBuffer = await chunk.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)

      const uploadCommand = new UploadPartCommand({
        Bucket: bucketName,
        Key: key,
        PartNumber: partNumber,
        UploadId: uploadId,
        Body: uint8Array,
      })

      // Send the upload command
      const response = await s3Client.send(uploadCommand)

      if (abortController.signal.aborted) {
        throw new Error('Upload aborted')
      }

      // Store completed part
      uploadedParts.push({
        ETag: response.ETag!,
        PartNumber: partNumber,
      })

      // Update progress
      const progress = uploadProgress.value.get(videoId)
      if (progress) {
        progress.chunkProgress.set(partNumber, 100)
        progress.completedChunks++
        updateAggregatedProgress(totalFileSize, totalChunks, videoId)
      }
    } catch (error) {
      if (!abortController.signal.aborted) {
        console.error(`❌ Chunk ${partNumber} upload failed:`, error)
        throw error
      }
    }
  }

  // Update aggregated progress across all chunks
  const updateAggregatedProgress = (
    totalFileSize: number,
    totalChunks: number,
    videoId: string,
  ): void => {
    const progress = uploadProgress.value.get(videoId)
    if (!progress) return

    const completedBytes = progress.completedChunks * uploadConfig.chunkSize
    const adjustedBytes = Math.min(completedBytes, totalFileSize)

    progress.uploadedSize = adjustedBytes
    progress.percentage = Math.round((adjustedBytes / totalFileSize) * 100)

    // Calculate upload speed and ETA
    const now = Date.now()
    const timeElapsed = (now - uploadStartTime) / 1000 // seconds

    if (timeElapsed > 0) {
      progress.uploadSpeed = adjustedBytes / timeElapsed // bytes per second

      if (progress.uploadSpeed > 0) {
        const remainingBytes = totalFileSize - adjustedBytes
        progress.estimatedTimeRemaining = remainingBytes / progress.uploadSpeed
      }
    }

    // Update reactive state
    uploadProgress.value.set(videoId, { ...progress })
  }

  // Pause upload
  const pauseUpload = async (): Promise<void> => {
    if (currentUpload.value) {
      const progress = uploadProgress.value.get(currentUpload.value)
      if (progress) {
        progress.status = 'paused'
        uploadProgress.value.set(currentUpload.value, { ...progress })
      }
    }
    // Note: AWS S3 doesn't support native pause, but we can implement it by stopping new chunks
  }

  // Resume upload
  const resumeUpload = async (): Promise<void> => {
    if (currentUpload.value) {
      const progress = uploadProgress.value.get(currentUpload.value)
      if (progress) {
        progress.status = 'uploading'
        uploadProgress.value.set(currentUpload.value, { ...progress })
      }
    }
    // Resume logic would need to track completed parts and continue from where we left off
  }

  // Cancel upload
  const cancelUpload = async (): Promise<void> => {
    if (currentMultipartUpload) {
      await abortMultipartUpload()
    }

    if (currentUpload.value) {
      uploadProgress.value.delete(currentUpload.value)
      currentUpload.value = null
    }

    isUploading.value = false
  }

  // Abort multipart upload
  const abortMultipartUpload = async (): Promise<void> => {
    if (!currentMultipartUpload) return

    try {
      const { uploadId, key, abortController } = currentMultipartUpload

      // Signal all ongoing uploads to abort
      abortController.abort()

      // Abort the multipart upload on S3
      const abortCommand = new AbortMultipartUploadCommand({
        Bucket: config.aws.bucketName,
        Key: key,
        UploadId: uploadId,
      })

      await s3Client.send(abortCommand)
      console.log('✅ Multipart upload aborted successfully')
    } catch (error) {
      console.error('❌ Error aborting multipart upload:', error)
    } finally {
      currentMultipartUpload = null
      uploadedParts = []
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
