<template>
  <!--begin::Recent Videos Widget-->
  <div :class="widgetClasses" class="card">
    <!--begin::Header-->
    <div class="card-header border-0 pt-5">
      <h3 class="card-title align-items-start flex-column">
        <span class="card-label fw-bold text-gray-900">Recent Videos</span>
        <span class="text-muted mt-1 fw-semibold fs-7">{{ videos.length }} videos</span>
      </h3>
      <div class="card-toolbar">
        <router-link to="/videos" class="btn btn-sm btn-light-primary">
          <KTIcon icon-name="plus" icon-class="fs-2" />
          View All
        </router-link>
      </div>
    </div>
    <!--end::Header-->

    <!--begin::Body-->
    <div class="card-body py-3">
      <!--begin::Table container-->
      <div class="table-responsive">
        <!--begin::Table-->
        <table class="table align-middle gs-0 gy-5">
          <!--begin::Table head-->
          <thead>
            <tr>
              <th class="p-0 w-50px"></th>
              <th class="p-0 min-w-150px"></th>
              <th class="p-0 min-w-100px"></th>
              <th class="p-0 min-w-100px"></th>
              <th class="p-0 min-w-50px"></th>
            </tr>
          </thead>
          <!--end::Table head-->

          <!--begin::Table body-->
          <tbody>
            <tr v-for="video in recentVideos" :key="video.video_id">
              <td>
                <div class="symbol symbol-50px me-2">
                  <span class="symbol-label bg-light-primary">
                    <KTIcon icon-name="video" icon-class="fs-2x text-primary" />
                  </span>
                </div>
              </td>
              <td>
                <a
                  href="#"
                  class="text-gray-900 fw-bold text-hover-primary fs-6"
                  @click.prevent="$emit('play', video)"
                >
                  {{ video.title }}
                </a>
                <span class="text-muted fw-semibold d-block fs-7">
                  {{ video.filename }}
                </span>
              </td>
              <td class="text-end">
                <span class="text-muted fw-semibold d-block fs-8">
                  {{ formatFileSize(video.file_size) }}
                </span>
              </td>
              <td class="text-end">
                <span class="text-muted fw-semibold d-block fs-8">
                  {{ formatDate(video.upload_date) }}
                </span>
              </td>
              <td class="text-end">
                <div class="d-flex flex-column w-100 me-2">
                  <div class="d-flex flex-stack mb-2">
                    <span class="text-muted me-2 fs-7 fw-semibold">
                      {{ formatDuration(video.duration) }}
                    </span>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
          <!--end::Table body-->
        </table>
        <!--end::Table-->
      </div>
      <!--end::Table container-->
    </div>
    <!--end::Body-->
  </div>
  <!--end::Recent Videos Widget-->
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'
import { useVideosStore } from '@/stores/videos'

export default defineComponent({
  name: 'recent-videos-widget',
  props: {
    widgetClasses: String,
  },
  emits: ['play'],
  setup() {
    const videosStore = useVideosStore()

    const videos = computed(() => videosStore.userVideos)
    const recentVideos = computed(
      () => videos.value.slice(0, 5), // Show only latest 5 videos
    )

    const formatFileSize = (bytes?: number): string => {
      if (!bytes) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (dateString: string): string => {
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }

    const formatDuration = (seconds?: number): string => {
      if (!seconds) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    return {
      videos,
      recentVideos,
      formatFileSize,
      formatDate,
      formatDuration,
    }
  },
})
</script>
