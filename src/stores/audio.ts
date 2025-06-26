import { defineStore } from 'pinia'
import { ref } from 'vue'
import AudioService from '@/core/services/AudioService'
import type { AudioMetadata, AudioUploadParams } from '@/core/services/AudioService'

// Upload progress tracking for audio
interface AudioUploadProgress {
  audioId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number
  uploadSpeed?: number
}

export const useAudioStore = defineStore('audio', () => {
  const userAudioFiles = ref<AudioMetadata[]>([])
  const loading = ref(false)
  const uploadProgress = ref<Map<string, AudioUploadProgress>>(new Map())

  const loadUserAudioFiles = async () => {
    try {
      loading.value = true
      const audioFiles = await AudioService.getUserAudioFiles()
      userAudioFiles.value = audioFiles
      console.log('Loaded audio files from API:', audioFiles.length)
    } catch (error) {
      console.error('Failed to load user audio files:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const uploadAudio = async (params: AudioUploadParams): Promise<AudioMetadata> => {
    try {
      const audioId = `temp-${Date.now()}`

      // Initialize upload progress
      updateUploadProgress(audioId, {
        audioId,
        filename: params.file.name,
        totalSize: params.file.size,
        uploadedSize: 0,
        percentage: 0,
        status: 'uploading',
      })

      // Upload with progress tracking
      const result = await AudioService.uploadAudio({
        ...params,
        onProgress: (percentage) => {
          updateUploadProgress(audioId, {
            audioId,
            filename: params.file.name,
            totalSize: params.file.size,
            uploadedSize: Math.round((params.file.size * percentage) / 100),
            percentage,
            status: 'uploading',
          })
        },
      })

      // Mark as completed
      updateUploadProgress(audioId, {
        audioId,
        filename: params.file.name,
        totalSize: params.file.size,
        uploadedSize: params.file.size,
        percentage: 100,
        status: 'completed',
      })

      // Add to user audio files
      addAudioFile(result.audio)

      // Clean up progress after a delay
      setTimeout(() => {
        removeUploadProgress(audioId)
      }, 3000)

      return result.audio
    } catch (error) {
      console.error('Failed to upload audio:', error)
      throw error
    }
  }

  const deleteAudioFile = async (audioId: string) => {
    try {
      await AudioService.deleteAudio(audioId)
      removeAudioFile(audioId)
      return true
    } catch (error) {
      console.error('Failed to delete audio file:', error)
      throw error
    }
  }

  const getAudioDetails = async (audioId: string): Promise<AudioMetadata> => {
    try {
      return await AudioService.getAudioDetails(audioId)
    } catch (error) {
      console.error('Failed to get audio details:', error)
      throw error
    }
  }

  const updateUploadProgress = (audioId: string, progress: AudioUploadProgress) => {
    uploadProgress.value.set(audioId, progress)
  }

  const removeUploadProgress = (audioId: string) => {
    uploadProgress.value.delete(audioId)
  }

  const addAudioFile = (audio: AudioMetadata) => {
    userAudioFiles.value.unshift(audio) // Add to beginning
  }

  const removeAudioFile = (audioId: string) => {
    userAudioFiles.value = userAudioFiles.value.filter((audio) => audio.audio_id !== audioId)
  }

  const clearAudioFiles = () => {
    userAudioFiles.value = []
  }

  // Computed getters
  const getAudioById = (audioId: string): AudioMetadata | undefined => {
    return userAudioFiles.value.find((audio) => audio.audio_id === audioId)
  }

  const getTotalAudioFiles = (): number => {
    return userAudioFiles.value.length
  }

  const getTotalAudioSize = (): number => {
    return userAudioFiles.value.reduce((total, audio) => total + (audio.file_size || 0), 0)
  }

  const getRecentAudioFiles = (limit: number = 5): AudioMetadata[] => {
    return userAudioFiles.value
      .slice()
      .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
      .slice(0, limit)
  }

  return {
    // State
    userAudioFiles,
    loading,
    uploadProgress,

    // Actions
    loadUserAudioFiles,
    uploadAudio,
    deleteAudioFile,
    getAudioDetails,
    updateUploadProgress,
    removeUploadProgress,
    addAudioFile,
    removeAudioFile,
    clearAudioFiles,

    // Getters
    getAudioById,
    getTotalAudioFiles,
    getTotalAudioSize,
    getRecentAudioFiles,
  }
})

export type { AudioMetadata, AudioUploadProgress }
