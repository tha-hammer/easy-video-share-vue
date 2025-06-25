<template>
  <!--begin::Video Modal-->
  <div
    v-if="show"
    class="modal fade show d-block"
    style="background-color: rgba(0, 0, 0, 0.8)"
    tabindex="-1"
    @click.self="$emit('close')"
  >
    <div class="modal-dialog modal-xl modal-dialog-centered">
      <div class="modal-content">
        <!--begin::Modal header-->
        <div class="modal-header">
          <h2 class="modal-title">{{ video?.title || 'Video Player' }}</h2>

          <!--begin::Close-->
          <div class="btn btn-sm btn-icon btn-active-color-primary" @click="$emit('close')">
            <KTIcon icon-name="cross" icon-class="fs-1" />
          </div>
          <!--end::Close-->
        </div>
        <!--end::Modal header-->

        <!--begin::Modal body-->
        <div class="modal-body p-0">
          <!--begin::Video Player-->
          <div class="position-relative bg-black video-container">
            <video
              v-if="video && videoUrl"
              ref="videoPlayer"
              class="w-100 h-100"
              :src="videoUrl"
              controls
              preload="metadata"
              @loadedmetadata="onVideoLoaded"
              @error="onVideoError"
              style="max-height: 70vh; object-fit: contain"
            >
              <p class="text-white text-center p-5">
                Your browser doesn't support HTML5 video.
                <a :href="videoUrl" class="text-primary">Download the video</a> instead.
              </p>
            </video>

            <!-- No video placeholder -->
            <div v-else class="d-flex align-items-center justify-content-center h-300px">
              <div class="text-center text-white">
                <KTIcon icon-name="video" icon-class="fs-4x text-muted mb-3" />
                <p class="text-muted">No video selected</p>
              </div>
            </div>

            <!-- Loading overlay -->
            <div
              v-if="isLoading"
              class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-black bg-opacity-50"
            >
              <div class="text-center text-white">
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <p>Loading video...</p>
              </div>
            </div>

            <!-- Error overlay -->
            <div
              v-if="hasError"
              class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-black bg-opacity-75"
            >
              <div class="text-center text-white">
                <KTIcon icon-name="triangle-warning" icon-class="fs-4x text-warning mb-3" />
                <h5 class="text-white mb-3">Failed to load video</h5>
                <p class="text-muted mb-3">{{ errorMessage }}</p>
                <button class="btn btn-primary" @click="retryLoad">
                  <KTIcon icon-name="arrows-circle" icon-class="fs-4" />
                  Retry
                </button>
              </div>
            </div>
          </div>
          <!--end::Video Player-->
        </div>
        <!--end::Modal body-->

        <!--begin::Modal footer-->
        <div class="modal-footer">
          <div class="d-flex flex-column flex-sm-row justify-content-between w-100">
            <!--begin::Video Info-->
            <div v-if="video" class="d-flex flex-column">
              <div class="d-flex align-items-center mb-2">
                <span class="text-muted me-3">Filename:</span>
                <span class="fw-bold">{{ video.filename }}</span>
              </div>
              <div class="d-flex align-items-center mb-2">
                <span class="text-muted me-3">Size:</span>
                <span class="fw-bold">{{ formatFileSize(video.file_size || 0) }}</span>
              </div>
              <div class="d-flex align-items-center">
                <span class="text-muted me-3">Duration:</span>
                <span class="fw-bold">{{ formatDuration(video.duration || 0) }}</span>
              </div>
            </div>
            <!--end::Video Info-->

            <!--begin::Actions-->
            <div class="d-flex align-items-center gap-3 mt-3 mt-sm-0">
              <button class="btn btn-light-primary" @click="copyShareLink">
                <KTIcon icon-name="share" icon-class="fs-4" />
                Share
              </button>
              <button class="btn btn-light-danger" @click="handleDelete">
                <KTIcon icon-name="trash" icon-class="fs-4" />
                Delete
              </button>
              <button class="btn btn-primary" @click="$emit('close')">Close</button>
            </div>
            <!--end::Actions-->
          </div>
        </div>
        <!--end::Modal footer-->
      </div>
    </div>
  </div>
  <!--end::Video Modal-->
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, nextTick } from 'vue'
import type { VideoMetadata } from '@/stores/videos'
import { config } from '@/core/config/config'

export default defineComponent({
  name: 'video-modal',
  props: {
    video: {
      type: Object as () => VideoMetadata | null,
      required: false,
      default: null,
    },
    show: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close', 'delete'],
  setup(props, { emit }) {
    const videoPlayer = ref<HTMLVideoElement>()
    const isLoading = ref(true)
    const hasError = ref(false)
    const errorMessage = ref('')

    // Construct video URL from S3 bucket location
    const videoUrl = computed(() => {
      if (!props.video) return ''
      const bucketLocation = props.video.bucketLocation || props.video.bucket_location
      if (!bucketLocation) {
        return ''
      }
      return `https://${config.aws.bucketName}.s3.amazonaws.com/${bucketLocation}`
    })

    // Video player event handlers
    const onVideoLoaded = () => {
      isLoading.value = false
      hasError.value = false
    }

    const onVideoError = (event: Event) => {
      isLoading.value = false
      hasError.value = true

      const target = event.target as HTMLVideoElement
      const error = target.error

      if (error) {
        switch (error.code) {
          case error.MEDIA_ERR_ABORTED:
            errorMessage.value = 'Video playback was aborted'
            break
          case error.MEDIA_ERR_NETWORK:
            errorMessage.value = 'Network error occurred while loading video'
            break
          case error.MEDIA_ERR_DECODE:
            errorMessage.value = 'Video format is not supported'
            break
          case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
            errorMessage.value = 'Video source is not available or supported'
            break
          default:
            errorMessage.value = 'An unknown error occurred'
        }
      } else {
        errorMessage.value = 'Failed to load video'
      }

      console.error('Video error:', error, 'URL:', videoUrl.value)
    }

    const retryLoad = () => {
      hasError.value = false
      isLoading.value = true

      if (videoPlayer.value) {
        videoPlayer.value.load()
      }
    }

    // Reset state when modal opens/closes or video changes
    watch([() => props.show, () => props.video?.video_id], async () => {
      if (props.show && props.video) {
        isLoading.value = true
        hasError.value = false
        errorMessage.value = ''

        await nextTick()

        if (videoPlayer.value) {
          videoPlayer.value.load()
        }
      } else {
        // Pause video when modal closes
        if (videoPlayer.value && !videoPlayer.value.paused) {
          videoPlayer.value.pause()
        }
      }
    })

    // Handle escape key to close modal
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && props.show) {
        emit('close')
      }
    }

    // Add/remove event listeners
    watch(
      () => props.show,
      (show) => {
        if (show) {
          document.addEventListener('keydown', handleKeydown)
        } else {
          document.removeEventListener('keydown', handleKeydown)
        }
      },
    )

    // Cleanup on unmount
    // onUnmounted(() => {
    //   document.removeEventListener('keydown', handleKeydown)
    // })
    const formatFileSize = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDuration = (seconds: number): string => {
      if (seconds === 0) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const copyShareLink = async () => {
      if (!props.video) return
      try {
        const shareUrl = `${window.location.origin}/video/${props.video.video_id}`
        await navigator.clipboard.writeText(shareUrl)
        // TODO: Show success notification using Metronic's Notice component
        console.log('Share link copied to clipboard')
      } catch (error) {
        console.error('Failed to copy share link:', error)
      }
    }

    const handleDelete = () => {
      if (!props.video) return
      if (confirm('Are you sure you want to delete this video?')) {
        emit('delete', props.video.video_id)
        emit('close')
      }
    }

    return {
      videoPlayer,
      videoUrl,
      isLoading,
      hasError,
      errorMessage,
      onVideoLoaded,
      onVideoError,
      retryLoad,
      formatFileSize,
      formatDuration,
      copyShareLink,
      handleDelete,
    }
  },
})
</script>

<style scoped>
.modal {
  backdrop-filter: blur(5px);
}

.video-container {
  min-height: 300px;
  max-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-container video {
  width: 100%;
  height: auto;
  max-width: 100%;
  max-height: 100%;
}

/* Ensure modal fits in viewport */
.modal-xl {
  max-width: 90vw;
  max-height: 90vh;
}

.modal-content {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-body {
  flex: 1;
  overflow: hidden;
}
</style>
