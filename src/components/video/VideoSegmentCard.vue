<template>
  <!--begin::Segment Card-->
  <div class="card h-100 hoverable">
    <!--begin::Card body-->
    <div class="card-body d-flex flex-column">
      <!--begin::Segment Preview-->
      <div class="position-relative mb-5">
        <div
          class="bg-light-primary rounded d-flex align-items-center justify-content-center"
          style="height: 180px; overflow: hidden"
        >
          <!-- Video Preview Placeholder -->
          <div class="d-flex align-items-center justify-content-center w-100 h-100">
            <KTIcon icon-name="video" icon-class="fs-1 text-primary" />
          </div>
        </div>

        <!--begin::Play Button Overlay-->
        <div
          class="position-absolute top-50 start-50 translate-middle cursor-pointer"
          @click="handlePlay"
        >
          <div class="btn btn-icon btn-light-primary btn-lg shadow">
            <KTIcon icon-name="play" icon-class="fs-2x" />
          </div>
        </div>
        <!--end::Play Button Overlay-->

        <!--begin::Duration Badge-->
        <div class="position-absolute bottom-0 end-0 m-3">
          <span class="badge badge-dark">{{ formatDuration(segment.duration) }}</span>
        </div>
        <!--end::Duration Badge-->

        <!--begin::Segment Number Badge-->
        <div class="position-absolute top-0 start-0 m-3">
          <span class="badge badge-primary">#{{ segment.segment_number }}</span>
        </div>
        <!--end::Segment Number Badge-->
      </div>
      <!--end::Segment Preview-->

      <!--begin::Segment Info-->
      <div class="flex-grow-1">
        <!--begin::Title-->
        <h6
          class="fw-bold text-gray-900 mb-2 cursor-pointer text-hover-primary"
          @click="$emit('play', segment)"
        >
          {{ segment.title || segment.filename || `Segment ${segment.segment_number}` }}
        </h6>
        <!--end::Title-->

        <!--begin::Description-->
        <div v-if="segment.description" class="mb-3">
          <p class="text-muted fs-7 mb-2">
            <strong>Description:</strong>
          </p>
          <p class="text-gray-700 fs-7 mb-2">
            {{ truncateText(segment.description, 100) }}
          </p>
        </div>
        <!--end::Description-->

        <!--begin::Tags-->
        <div v-if="segment.tags && segment.tags.length > 0" class="mb-3">
          <div class="d-flex flex-wrap gap-1">
            <span
              v-for="tag in segment.tags.slice(0, 3)"
              :key="tag"
              class="badge badge-light-primary fs-8"
            >
              {{ tag }}
            </span>
            <span v-if="segment.tags.length > 3" class="badge badge-light fs-8">
              +{{ segment.tags.length - 3 }}
            </span>
          </div>
        </div>
        <!--end::Tags-->

        <!--begin::Details-->
        <div class="d-flex justify-content-between align-items-center text-muted fs-7 mb-3">
          <span>{{ formatFileSize(segment.file_size) }}</span>
          <span>{{ formatDate(segment.created_at) }}</span>
        </div>
        <!--end::Details-->

        <!--begin::Download Stats-->
        <div class="d-flex justify-content-between align-items-center text-muted fs-7 mb-3">
          <span>
            <KTIcon icon-name="download" icon-class="fs-5" />
            {{ segment.download_count }} downloads
          </span>
          <span v-if="segment.last_downloaded_at">
            Last: {{ formatDate(segment.last_downloaded_at) }}
          </span>
        </div>
        <!--end::Download Stats-->
      </div>
      <!--end::Segment Info-->

      <!--begin::Actions-->
      <div class="d-flex justify-content-between align-items-center">
        <button class="btn btn-sm btn-primary" @click="handleDownload" :disabled="downloading">
          <KTIcon
            :icon-name="downloading ? 'spinner' : 'download'"
            :icon-class="downloading ? 'fs-4 fa-spin' : 'fs-4'"
          />
          {{ downloading ? 'Downloading...' : 'Download' }}
        </button>

        <div class="btn-group">
          <button class="btn btn-sm btn-light" @click="copyShareLink" title="Copy share link">
            <KTIcon icon-name="share" icon-class="fs-4" />
          </button>
          <button class="btn btn-sm btn-light" @click="$emit('play', segment)" title="Play segment">
            <KTIcon icon-name="play" icon-class="fs-4" />
          </button>
          <button
            class="btn btn-sm btn-light-success"
            @click="$emit('track-social-media', segment)"
            title="Track social media usage"
          >
            <KTIcon icon-name="chart-line-up" icon-class="fs-4" />
          </button>
        </div>
      </div>
      <!--end::Actions-->
    </div>
    <!--end::Card body-->
  </div>
  <!--end::Segment Card-->
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import type { VideoSegment } from '@/stores/segments'

export default defineComponent({
  name: 'video-segment-card',
  props: {
    segment: {
      type: Object as () => VideoSegment,
      required: true,
    },
  },
  emits: ['play', 'download', 'track-social-media'],
  setup(props, { emit }) {
    const downloading = ref(false)
    const isPlaying = ref(false)

    const handlePlay = () => {
      isPlaying.value = true
      emit('play', props.segment)
    }

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
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatTime = (seconds: number): string => {
      if (seconds === 0) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatDate = (dateString: string): string => {
      return new Date(dateString).toLocaleDateString()
    }

    const truncateText = (text: string, maxLength: number): string => {
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const handleDownload = async () => {
      downloading.value = true
      try {
        emit('download', props.segment.segment_id)
      } finally {
        downloading.value = false
      }
    }

    const copyShareLink = async () => {
      try {
        const shareUrl = `${window.location.origin}/segments/${props.segment.segment_id}`
        await navigator.clipboard.writeText(shareUrl)
        // TODO: Show success notification using Metronic's Notice component
        console.log('Segment share link copied to clipboard')
      } catch (error) {
        console.error('Failed to copy share link:', error)
      }
    }

    return {
      downloading,
      isPlaying,
      formatFileSize,
      formatDuration,
      formatTime,
      formatDate,
      truncateText,
      handleDownload,
      copyShareLink,
      handlePlay,
    }
  },
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.hoverable:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease-in-out;
}

.text-hover-primary:hover {
  color: var(--kt-primary) !important;
}
</style>
