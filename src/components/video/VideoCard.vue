<template>
  <!--begin::Video Card-->
  <div class="card h-100 hoverable">
    <!--begin::Card body-->
    <div class="card-body d-flex flex-column">
      <!--begin::Video Preview-->
      <div class="position-relative mb-5">
        <div
          class="bg-light-primary rounded d-flex align-items-center justify-content-center"
          style="height: 180px"
        >
          <KTIcon icon-name="video" icon-class="fs-1 text-primary" />
        </div>

        <!--begin::Play Button Overlay-->
        <div
          class="position-absolute top-50 start-50 translate-middle cursor-pointer"
          @click="$emit('play', video)"
        >
          <div class="btn btn-icon btn-light-primary btn-lg shadow">
            <KTIcon icon-name="play" icon-class="fs-2x" />
          </div>
        </div>
        <!--end::Play Button Overlay-->

        <!--begin::Duration Badge-->
        <div v-if="video.duration" class="position-absolute bottom-0 end-0 m-3">
          <span class="badge badge-dark">{{ formatDuration(video.duration) }}</span>
        </div>
        <!--end::Duration Badge-->
      </div>
      <!--end::Video Preview-->

      <!--begin::Video Info-->
      <div class="flex-grow-1">
        <!--begin::Title-->
        <h6
          class="fw-bold text-gray-900 mb-2 cursor-pointer text-hover-primary"
          @click="$emit('play', video)"
        >
          {{ video.title }}
        </h6>
        <!--end::Title-->

        <!--begin::Filename-->
        <p class="text-muted fs-7 mb-3">{{ video.filename }}</p>
        <!--end::Filename-->

        <!--begin::Details-->
        <div class="d-flex justify-content-between align-items-center text-muted fs-7 mb-3">
          <span>{{ formatFileSize(video.file_size || 0) }}</span>
          <span>{{ formatDate(video.upload_date) }}</span>
        </div>
        <!--end::Details-->
      </div>
      <!--end::Video Info-->

      <!--begin::Actions-->
      <div class="d-flex justify-content-between align-items-center">
        <button class="btn btn-sm btn-light-primary" @click="$emit('play', video)">
          <KTIcon icon-name="play" icon-class="fs-4" />
          Play
        </button>

        <div class="btn-group">
          <button class="btn btn-sm btn-light" @click="copyShareLink" title="Copy share link">
            <KTIcon icon-name="share" icon-class="fs-4" />
          </button>
          <button
            class="btn btn-sm btn-light text-danger"
            @click="$emit('delete', video.video_id)"
            title="Delete video"
          >
            <KTIcon icon-name="trash" icon-class="fs-4" />
          </button>
        </div>
      </div>
      <!--end::Actions-->
    </div>
    <!--end::Card body-->
  </div>
  <!--end::Video Card-->
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import type { VideoMetadata } from '@/stores/videos'

export default defineComponent({
  name: 'video-card',
  props: {
    video: {
      type: Object as () => VideoMetadata,
      required: true,
    },
  },
  emits: ['play', 'delete'],
  setup(props) {
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

    const formatDate = (dateString: string): string => {
      return new Date(dateString).toLocaleDateString()
    }

    const copyShareLink = async () => {
      try {
        const shareUrl = `${window.location.origin}/video/${props.video.video_id}`
        await navigator.clipboard.writeText(shareUrl)
        // TODO: Show success notification using Metronic's Notice component
        console.log('Share link copied to clipboard')
      } catch (error) {
        console.error('Failed to copy share link:', error)
      }
    }

    return {
      formatFileSize,
      formatDuration,
      formatDate,
      copyShareLink,
    }
  },
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>
