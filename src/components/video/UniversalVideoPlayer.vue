<template>
  <!--begin::Universal Video Player Modal-->
  <div
    v-if="isVisible"
    class="modal fade show d-block"
    tabindex="-1"
    aria-modal="true"
    role="dialog"
    style="background-color: rgba(0, 0, 0, 0.8)"
    @click.self="closeModal"
  >
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <!--begin::Modal header-->
        <div class="modal-header">
          <h5 class="modal-title">{{ title || 'Video Player' }}</h5>
          <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
        </div>
        <!--end::Modal header-->

        <!--begin::Modal body-->
        <div class="modal-body">
          <div class="video-container">
            <!-- Loading State -->
            <div v-if="loading && !videoUrl" class="text-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-3">Loading video...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="text-center py-5">
              <KTIcon icon-name="triangle-warning" icon-class="fs-2x text-warning mb-3" />
              <h5 class="text-danger mb-3">Failed to load video</h5>
              <p class="text-muted mb-3">{{ error }}</p>
              <button class="btn btn-primary" @click="retryLoad">
                <KTIcon icon-name="refresh" icon-class="fs-4" />
                Retry
              </button>
            </div>

            <!-- Video Player -->
            <div v-else-if="videoUrl" class="video-wrapper">
              <!-- Debug info -->
              <div class="mb-3 p-2 bg-light rounded">
                <small class="text-muted"
                  >Debug: Video URL loaded - {{ videoUrl.substring(0, 100) }}...</small
                >
              </div>

              <video
                ref="videoPlayer"
                :src="videoUrl"
                controls
                preload="metadata"
                crossorigin="anonymous"
                class="w-100"
                style="max-height: 70vh; background: #000"
                @loadedmetadata="onVideoLoaded"
                @error="onVideoError"
                @loadstart="onLoadStart"
                @canplay="onCanPlay"
                @playing="onPlaying"
                @waiting="onWaiting"
              >
                Your browser does not support the video tag.
              </video>

              <!-- Video loading overlay -->
              <div v-if="videoLoading" class="video-loading-overlay">
                <div class="spinner-border text-white" role="status">
                  <span class="visually-hidden">Loading video...</span>
                </div>
              </div>
            </div>

            <!-- No Video State -->
            <div v-else class="text-center py-5">
              <KTIcon icon-name="video" icon-class="fs-2x text-muted mb-3" />
              <p class="text-muted">No video available</p>
            </div>
          </div>
        </div>
        <!--end::Modal body-->

        <!--begin::Modal footer-->
        <div class="modal-footer">
          <div class="d-flex justify-content-between align-items-center w-100">
            <div class="text-muted">
              <small v-if="metadata">
                Duration: {{ formatDuration(metadata.duration || 0) }} | Size:
                {{ formatFileSize(metadata.file_size || 0) }}
              </small>
            </div>

            <div class="btn-group">
              <button
                v-if="showDownload"
                class="btn btn-primary"
                @click="downloadVideo"
                :disabled="downloading"
              >
                <KTIcon
                  :icon-name="downloading ? 'spinner' : 'download'"
                  :icon-class="downloading ? 'fs-4 fa-spin' : 'fs-4'"
                />
                {{ downloading ? 'Downloading...' : 'Download' }}
              </button>
              <button class="btn btn-light" @click="closeModal">Close</button>
            </div>
          </div>
        </div>
        <!--end::Modal footer-->
      </div>
    </div>
  </div>
  <!--end::Universal Video Player Modal-->
</template>

<script lang="ts">
import { defineComponent, ref, watch, nextTick } from 'vue'

interface VideoMetadata {
  duration?: number
  file_size?: number
  filename?: string
}

export default defineComponent({
  name: 'universal-video-player',
  props: {
    isVisible: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: '',
    },
    videoUrl: {
      type: String,
      default: '',
    },
    metadata: {
      type: Object as () => VideoMetadata | null,
      default: null,
    },
    showDownload: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const videoPlayer = ref<HTMLVideoElement | null>(null)
    const loading = ref(false)
    const videoLoading = ref(false)
    const error = ref<string | null>(null)
    const downloading = ref(false)

    const closeModal = () => {
      // Pause video if playing
      if (videoPlayer.value) {
        videoPlayer.value.pause()
      }
      error.value = null
      videoLoading.value = false
      emit('close')
    }

    const downloadVideo = async () => {
      if (!props.videoUrl) return

      downloading.value = true
      try {
        const link = document.createElement('a')
        link.href = props.videoUrl
        link.download = props.metadata?.filename || 'video.mp4'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (err) {
        console.error('Failed to download video:', err)
      } finally {
        downloading.value = false
      }
    }

    const retryLoad = () => {
      error.value = null
      videoLoading.value = true
      if (videoPlayer.value) {
        videoPlayer.value.load()
      }
    }

    const testVideoUrl = async (url: string): Promise<boolean> => {
      try {
        console.log('🎬 Testing video URL accessibility:', url)
        const response = await fetch(url, { method: 'HEAD' })
        console.log('🎬 Video URL test response:', response.status, response.statusText)
        return response.ok
      } catch (error) {
        console.error('🎬 Video URL test failed:', error)
        return false
      }
    }

    const initializeVideo = async () => {
      if (!props.videoUrl || !videoPlayer.value) return

      console.log('🎬 Initializing video with URL:', props.videoUrl)

      // Test URL accessibility first
      const isAccessible = await testVideoUrl(props.videoUrl)
      if (!isAccessible) {
        error.value = 'Video URL is not accessible. Please check the URL or try again later.'
        loading.value = false
        videoLoading.value = false
        return
      }

      // Set video source and load
      videoPlayer.value.src = props.videoUrl
      videoPlayer.value.load()
    }

    const onVideoLoaded = () => {
      console.log('🎬 Video loaded successfully')
      loading.value = false
      videoLoading.value = false
      error.value = null
    }

    const onVideoError = (err: Event) => {
      console.error('🎬 Video error:', err)

      // Get more detailed error information
      const videoElement = videoPlayer.value
      if (videoElement) {
        console.error('🎬 Video error code:', videoElement.error?.code)
        console.error('🎬 Video error message:', videoElement.error?.message)
        console.error('🎬 Video network state:', videoElement.networkState)
        console.error('🎬 Video ready state:', videoElement.readyState)
        console.error('🎬 Video current src:', videoElement.currentSrc)
      }

      console.error('🎬 Video error details:', {
        error: err,
        videoUrl: props.videoUrl,
        videoElement: videoPlayer.value,
      })

      loading.value = false
      videoLoading.value = false

      // Provide more specific error messages
      let errorMessage = 'Failed to load video. Please try again.'
      if (videoElement?.error) {
        switch (videoElement.error.code) {
          case 1:
            errorMessage = 'Video loading was aborted.'
            break
          case 2:
            errorMessage = 'Network error occurred while loading video.'
            break
          case 3:
            errorMessage = 'Video decoding failed. The file may be corrupted.'
            break
          case 4:
            errorMessage = 'Video format is not supported by your browser.'
            break
          default:
            errorMessage = `Video error: ${videoElement.error.message}`
        }
      }

      error.value = errorMessage
    }

    const onLoadStart = () => {
      console.log('🎬 Video load started')
      videoLoading.value = true
      error.value = null
    }

    const onCanPlay = () => {
      console.log('🎬 Video can play')
      videoLoading.value = false
    }

    const onPlaying = () => {
      console.log('🎬 Video is playing')
      videoLoading.value = false
    }

    const onWaiting = () => {
      console.log('🎬 Video is waiting for data')
      videoLoading.value = true
    }

    const formatDuration = (seconds: number): string => {
      if (seconds === 0) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatFileSize = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Watch for visibility changes
    watch(
      () => props.isVisible,
      async (newValue) => {
        console.log('🎬 Modal visibility changed:', newValue)
        if (newValue) {
          loading.value = true
          error.value = null
          videoLoading.value = false

          // Wait for DOM update and then initialize video
          await nextTick()
          if (props.videoUrl) {
            await initializeVideo()
          }
        }
      },
    )

    // Watch for video URL changes
    watch(
      () => props.videoUrl,
      async (newValue) => {
        console.log('🎬 Video URL changed:', newValue)
        if (newValue) {
          loading.value = true
          error.value = null
          videoLoading.value = true

          // Wait for DOM update and then initialize video
          await nextTick()
          await initializeVideo()
        }
      },
    )

    return {
      videoPlayer,
      loading,
      videoLoading,
      error,
      downloading,
      closeModal,
      downloadVideo,
      retryLoad,
      initializeVideo,
      onVideoLoaded,
      onVideoError,
      onLoadStart,
      onCanPlay,
      onPlaying,
      onWaiting,
      formatDuration,
      formatFileSize,
    }
  },
})
</script>

<style scoped>
.video-container {
  position: relative;
  width: 100%;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
}

.video-wrapper {
  position: relative;
  width: 100%;
}

.video-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.modal.show {
  backdrop-filter: blur(5px);
}

video {
  display: block;
  width: 100%;
  height: auto;
  max-height: 70vh;
}
</style>
