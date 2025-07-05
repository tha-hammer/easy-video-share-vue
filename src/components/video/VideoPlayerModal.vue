<template>
  <!--begin::Modal-->
  <div
    v-if="isVisible"
    class="modal fade show d-block"
    tabindex="-1"
    aria-modal="true"
    role="dialog"
    style="background-color: rgba(0, 0, 0, 0.5)"
  >
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <!--begin::Modal header-->
        <div class="modal-header">
          <h5 class="modal-title">{{ segment?.title || 'Video Player' }}</h5>
          <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
        </div>
        <!--end::Modal header-->

        <!--begin::Modal body-->
        <div class="modal-body">
          <div class="video-container">
            <video
              v-if="videoUrl"
              ref="videoPlayer"
              :src="videoUrl"
              controls
              class="w-100"
              style="max-height: 70vh"
              @loadedmetadata="onVideoLoaded"
              @error="onVideoError"
            >
              Your browser does not support the video tag.
            </video>

            <div v-else class="text-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-3">Loading video...</p>
            </div>
          </div>
        </div>
        <!--end::Modal body-->

        <!--begin::Modal footer-->
        <div class="modal-footer">
          <div class="d-flex justify-content-between align-items-center w-100">
            <div class="text-muted">
              <small>
                Duration: {{ formatDuration(segment?.duration || 0) }} | Size:
                {{ formatFileSize(segment?.file_size || 0) }}
              </small>
            </div>

            <div class="btn-group">
              <button class="btn btn-primary" @click="downloadVideo" :disabled="downloading">
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
  <!--end::Modal-->
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'
import type { VideoSegment } from '@/stores/segments'

export default defineComponent({
  name: 'video-player-modal',
  props: {
    isVisible: {
      type: Boolean,
      default: false,
    },
    segment: {
      type: Object as () => VideoSegment | null,
      default: null,
    },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const videoPlayer = ref<HTMLVideoElement | null>(null)
    const videoUrl = ref<string | null>(null)
    const downloading = ref(false)

    const generateVideoUrl = async () => {
      if (props.segment?.s3_key && !videoUrl.value) {
        try {
          const baseUrl = 'http://localhost:8000'
          const response = await fetch(`${baseUrl}/api/segments/${props.segment.segment_id}/play`)
          if (response.ok) {
            const data = await response.json()
            videoUrl.value = data.play_url
          }
        } catch (error) {
          console.error('Failed to generate video URL:', error)
        }
      }
    }

    const closeModal = () => {
      // Pause video if playing
      if (videoPlayer.value) {
        videoPlayer.value.pause()
      }
      videoUrl.value = null
      emit('close')
    }

    const downloadVideo = async () => {
      if (!videoUrl.value) return

      downloading.value = true
      try {
        const link = document.createElement('a')
        link.href = videoUrl.value
        link.download = props.segment?.filename || 'segment.mp4'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (error) {
        console.error('Failed to download video:', error)
      } finally {
        downloading.value = false
      }
    }

    const onVideoLoaded = () => {
      console.log('Video loaded successfully')
    }

    const onVideoError = (error: Event) => {
      console.error('Video error:', error)
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
      (newValue) => {
        if (newValue && props.segment) {
          generateVideoUrl()
        }
      },
    )

    // Watch for segment changes
    watch(
      () => props.segment,
      (newSegment) => {
        if (newSegment && props.isVisible) {
          videoUrl.value = null
          generateVideoUrl()
        }
      },
    )

    return {
      videoPlayer,
      videoUrl,
      downloading,
      closeModal,
      downloadVideo,
      onVideoLoaded,
      onVideoError,
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
}

.modal.show {
  backdrop-filter: blur(5px);
}
</style>
