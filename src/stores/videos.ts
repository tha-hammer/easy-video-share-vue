import { defineStore } from 'pinia'
import { ref } from 'vue'
import { VideoService } from '@/core/services/VideoService'
import type { VideoMetadata } from '@/core/services/VideoService'

// Upload progress tracking
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
}

export const useVideosStore = defineStore('videos', () => {
  const userVideos = ref<VideoMetadata[]>([])
  const allVideos = ref<VideoMetadata[]>([])
  const loading = ref(false)
  const uploadProgress = ref<Map<string, UploadProgress>>(new Map())

  const loadUserVideos = async () => {
    try {
      loading.value = true
      const videos = await VideoService.getUserVideos()
      userVideos.value = videos
      console.log('Loaded videos from API:', videos.length)
    } catch (error) {
      console.error('Failed to load user videos:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const loadAllVideos = async () => {
    try {
      loading.value = true
      // This will be used by admin panel
      const videos = await VideoService.getUserVideos() // For now, same as user videos
      allVideos.value = videos
    } catch (error) {
      console.error('Failed to load all videos:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const saveVideoMetadata = async (metadata: VideoMetadata) => {
    try {
      const savedVideo = await VideoService.saveVideoMetadata(metadata)
      addVideo(savedVideo)
      return savedVideo
    } catch (error) {
      console.error('Failed to save video metadata:', error)
      throw error
    }
  }

  const deleteVideo = async (videoId: string) => {
    try {
      await VideoService.deleteVideo(videoId)
      removeVideo(videoId)
      return true
    } catch (error) {
      console.error('Failed to delete video:', error)
      throw error
    }
  }

  const updateUploadProgress = (videoId: string, progress: UploadProgress) => {
    uploadProgress.value.set(videoId, progress)
  }

  const removeUploadProgress = (videoId: string) => {
    uploadProgress.value.delete(videoId)
  }

  const addVideo = (video: VideoMetadata) => {
    userVideos.value.unshift(video) // Add to beginning
  }

  const removeVideo = (videoId: string) => {
    userVideos.value = userVideos.value.filter((video) => video.video_id !== videoId)
    allVideos.value = allVideos.value.filter((video) => video.video_id !== videoId)
  }

  return {
    userVideos,
    allVideos,
    loading,
    uploadProgress,
    loadUserVideos,
    loadAllVideos,
    saveVideoMetadata,
    deleteVideo,
    updateUploadProgress,
    removeUploadProgress,
    addVideo,
    removeVideo,
  }
})

export type { VideoMetadata, UploadProgress }
