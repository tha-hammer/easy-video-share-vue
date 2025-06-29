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
      <h4 class="fw-bold mt-4">{{ progressUpdate.stage | stageLabel }}</h4>
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
        <ul class="list-group text-start mx-auto" style="max-width: 600px">
          <li v-for="(url, idx) in progressUpdate.output_urls" :key="url" class="list-group-item">
            <a :href="url" target="_blank" rel="noopener">Segment {{ idx + 1 }}</a>
          </li>
        </ul>
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
  name: 'Processing',
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

    onMounted(() => {
      eventSource = new EventSource(`/api/job-progress/${jobId}/stream`)
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          progressUpdate.value = data
        } catch (e) {
          // Ignore malformed events
        }
      }
      eventSource.onerror = () => {
        if (eventSource) eventSource.close()
      }
    })

    onUnmounted(() => {
      if (eventSource) eventSource.close()
    })

    return { progressUpdate, formatTimestamp }
  },
  filters: {
    stageLabel(val: string) {
      switch (val) {
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
          return val.charAt(0).toUpperCase() + val.slice(1)
      }
    },
  },
})
</script>
