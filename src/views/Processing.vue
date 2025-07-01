<template>
  <div class="container py-10 text-center">
    <h2 class="mb-8 fw-bold text-gray-900">Video Processing Progress</h2>
    <div v-if="!progressUpdate" class="my-10">
      <span class="spinner-border text-primary mb-4" style="width: 3rem; height: 3rem"></span>
      <h4 class="fw-bold mt-4">Waiting for progress updates...</h4>
      <div class="text-muted">This may take a few moments. Please wait.</div>
    </div>
    <div v-else class="my-10">
      <div class="progress mb-4" style="height: 24px">
        <div
          class="progress-bar bg-primary"
          role="progressbar"
          :style="{ width: (progressUpdate.progress_percentage || 0) + '%' }"
        >
          {{ (progressUpdate.progress_percentage || 0).toFixed(1) }}%
        </div>
      </div>
      <h4 class="fw-bold mt-4">{{ stageLabel(progressUpdate.stage) }}</h4>
      <div class="text-muted mb-2">{{ progressUpdate.message }}</div>
      <div v-if="progressUpdate.current_segment && progressUpdate.total_segments" class="mb-2">
        Segment {{ progressUpdate.current_segment }} of {{ progressUpdate.total_segments }}
      </div>
      <div v-if="progressUpdate.timestamp" class="mb-2 text-muted fs-7">
        Last update: {{ formatTimestamp(progressUpdate.timestamp) }}
      </div>
      <div
        v-if="
          progressUpdate.stage === 'completed' &&
          progressUpdate.output_urls &&
          progressUpdate.output_urls.length
        "
      >
        <h5 class="fw-bold mt-4">Output Videos</h5>
        <div class="row g-6 g-xl-9 justify-content-center" style="max-width: 900px; margin: 0 auto">
          <div
            v-for="(url, idx) in progressUpdate.output_urls"
            :key="url"
            class="col-md-6 col-xl-4 d-flex align-items-stretch"
          >
            <div class="card shadow-sm w-100 h-100">
              <div class="card-body d-flex flex-column justify-content-between align-items-center">
                <div class="mb-3">
                  <div
                    class="symbol symbol-60px symbol-circle bg-light mb-2 d-flex align-items-center justify-content-center"
                  >
                    <span class="fs-2 fw-bold text-primary">{{ idx + 1 }}</span>
                  </div>
                </div>
                <div class="mb-2 text-truncate w-100" style="max-width: 100%">
                  <span class="fw-semibold">Segment {{ idx + 1 }}</span>
                </div>
                <button @click="openVideoModal(url)" class="btn btn-sm btn-primary mt-2 w-100">
                  View Video
                </button>
              </div>
            </div>
          </div>
        </div>
        <!-- Video Modal -->
        <div
          v-if="showVideoModal"
          class="modal fade show d-block"
          tabindex="-1"
          style="background: rgba(0, 0, 0, 0.5)"
        >
          <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Video Preview</h5>
                <button
                  type="button"
                  class="btn-close"
                  @click="closeVideoModal"
                  aria-label="Close"
                ></button>
              </div>
              <div class="modal-body d-flex justify-content-center">
                <video
                  v-if="selectedVideoUrl"
                  :src="selectedVideoUrl"
                  controls
                  style="max-width: 100%; max-height: 60vh"
                ></video>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="progressUpdate.stage === 'failed' && progressUpdate.error_message"
        class="alert alert-danger mt-4"
      >
        <strong>Error:</strong> {{ progressUpdate.error_message }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

// TypeScript interface matching ProgressUpdate Pydantic model
interface ProgressUpdate {
  job_id: string
  stage: string
  message: string
  current_segment?: number | null
  total_segments?: number | null
  progress_percentage: number
  timestamp: string
  output_urls?: string[] | null
  error_message?: string | null
}

export default defineComponent({
  name: 'VideoProcessing',
  setup() {
    const route = useRoute()
    const jobId = route.params.jobId as string
    const progressUpdate = ref<ProgressUpdate | null>(null)
    let eventSource: EventSource | null = null

    const formatTimestamp = (ts: string) => {
      const d = new Date(ts)
      return d.toLocaleString()
    }

    // Optional: Map backend stage codes to user-friendly labels
    const stageLabel = (stage: string) => {
      switch (stage) {
        case 'extracting':
          return 'Extracting Video Info'
        case 'segmenting':
          return 'Segmenting Video'
        case 'processing_segment':
          return 'Processing Segment'
        case 'uploading':
          return 'Uploading Segments'
        case 'completed':
          return 'Completed'
        case 'failed':
          return 'Failed'
        default:
          return stage.charAt(0).toUpperCase() + stage.slice(1)
      }
    }

    const showVideoModal = ref(false)
    const selectedVideoUrl = ref<string | null>(null)

    function openVideoModal(url: string) {
      selectedVideoUrl.value = url
      showVideoModal.value = true
    }
    function closeVideoModal() {
      showVideoModal.value = false
      selectedVideoUrl.value = null
    }

    onMounted(() => {
      console.log('Attempting to connect to SSE for jobId:', jobId)
      // Use the backend URL from environment variable
      const baseUrl = import.meta.env.VITE_AI_VIDEO_BACKEND_URL || 'http://localhost:8000'
      const sseUrl = `${baseUrl}/api/job-progress/${jobId}/stream`
      console.log('Connecting to SSE URL:', sseUrl)
      eventSource = new EventSource(sseUrl)
      eventSource.onopen = () => {
        console.log('EventSource connected!')
      }
      // Listen for the specific 'progress' event
      eventSource.addEventListener('progress', (event) => {
        console.log('Received "progress" event SSE data:', event.data)
        try {
          const data = JSON.parse(event.data)
          console.log('Parsed SSE message (progress event):', data)
          progressUpdate.value = data
          console.log('Updated progressUpdate ref:', progressUpdate.value)
        } catch (e) {
          console.error('Error parsing "progress" SSE data:', e, 'Raw data:', event.data)
        }
      })
      eventSource.onerror = (error) => {
        console.error('EventSource error:', error)
        if (eventSource) eventSource.close()
      }
    })

    onUnmounted(() => {
      if (eventSource) eventSource.close()
    })

    return {
      progressUpdate,
      formatTimestamp,
      stageLabel,
      showVideoModal,
      selectedVideoUrl,
      openVideoModal,
      closeVideoModal,
    }
  },
})
</script>

<style scoped>
/* Add any component-specific styles here */
</style>
