<template>
  <div class="container py-10">
    <h2 class="mb-8 fw-bold text-gray-900">Text Customization for Video Segments</h2>
    <div v-if="segments.length === 0" class="alert alert-info">
      No segments available. (Backend processing not yet implemented.)
    </div>
    <div class="row g-6">
      <div v-for="(segment, idx) in segments" :key="idx" class="col-md-6 col-lg-4">
        <div class="card card-flush h-100">
          <div class="card-header">
            <div class="card-title">
              <h4 class="fw-bold mb-0">Segment {{ idx + 1 }}</h4>
            </div>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Text</label>
              <input
                v-model="segment.text"
                type="text"
                class="form-control"
                :placeholder="`Enter text for segment ${idx + 1}`"
              />
            </div>
            <div class="text-muted fs-7">
              <span>Start: {{ segment.start }}s</span> &ndash; <span>End: {{ segment.end }}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-end mt-8 gap-3">
      <button class="btn btn-primary" :disabled="segments.length === 0">Save All Texts</button>
      <button class="btn btn-success" @click="goToProcessing">Continue</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default defineComponent({
  name: 'TextCustomization',
  setup() {
    const router = useRouter()
    const route = useRoute()
    // Simulate segments (since backend is not ready)
    const segments = ref([
      { start: 0, end: 30, text: 'Intro segment' },
      { start: 30, end: 60, text: 'Main content' },
      { start: 60, end: 90, text: 'Conclusion' },
    ])

    const goToProcessing = () => {
      router.push({ name: 'Processing', params: { jobId: route.params.jobId } })
    }

    // In a real app, fetch segments for jobId: route.params.jobId
    onMounted(() => {
      // TODO: Fetch segments from backend when available
    })

    return { segments, goToProcessing }
  },
})
</script>

<style scoped>
.card {
  min-height: 220px;
}
</style>
