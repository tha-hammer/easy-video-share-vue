<template>
  <div class="d-flex flex-column flex-root">
    <!--begin::Page-->
    <div class="page d-flex flex-row flex-column-fluid">
      <!--begin::Wrapper-->
      <div class="wrapper d-flex flex-column flex-row-fluid" id="kt_wrapper">
        <!--begin::Content-->
        <div class="content d-flex flex-column flex-column-fluid" id="kt_content">
          <!--begin::Content wrapper-->
          <div class="d-flex flex-column flex-column-fluid">
            <!--begin::Toolbar-->
            <div class="toolbar" id="kt_toolbar">
              <div
                class="container-fluid d-flex flex-stack flex-wrap flex-sm-nowrap"
                id="kt_toolbar_container"
              >
                <!--begin::Info-->
                <div
                  class="d-flex flex-column align-items-start justify-content-center flex-wrap me-1"
                >
                  <!--begin::Title-->
                  <h1 class="d-flex text-dark fw-bold my-1 fs-3">
                    Video Segments
                    <span v-if="videoTitle" class="text-muted fs-6 fw-normal ms-2">
                      - {{ videoTitle }}
                    </span>
                  </h1>
                  <!--end::Title-->

                  <!--begin::Breadcrumb-->
                  <ul
                    class="breadcrumb breadcrumb-line bg-transparent text-muted fw-semibold fs-7 my-1"
                  >
                    <li class="breadcrumb-item">
                      <router-link to="/videos" class="text-muted text-hover-primary"
                        >Videos</router-link
                      >
                    </li>
                    <li class="breadcrumb-item text-dark">Segments</li>
                  </ul>
                  <!--end::Breadcrumb-->
                </div>
                <!--end::Info-->

                <!--begin::Actions-->
                <div class="d-flex align-items-center py-1">
                  <button class="btn btn-light-primary me-3" @click="router.go(-1)">
                    <KTIcon icon-name="arrow-left" icon-class="fs-4" />
                    Back to Videos
                  </button>
                </div>
                <!--end::Actions-->
              </div>
            </div>
            <!--end::Toolbar-->

            <!--begin::Post-->
            <div class="post" id="kt_post">
              <!--begin::Container-->
              <div class="container-fluid" id="kt_content_container">
                <!--begin::Filters-->
                <SegmentFilters
                  :filters="segmentsStore.filters"
                  @update-filters="handleFilterUpdate"
                />
                <!--end::Filters-->

                <!--begin::Error Alert-->
                <div v-if="segmentsStore.error" class="alert alert-danger mb-8">
                  <div class="d-flex align-items-center">
                    <KTIcon icon-name="shield-cross" icon-class="fs-2x text-danger me-4" />
                    <div>
                      <h4 class="mb-1">Error Loading Segments</h4>
                      <p class="mb-0">{{ segmentsStore.error }}</p>
                    </div>
                    <button
                      class="btn btn-sm btn-light-danger ms-auto"
                      @click="segmentsStore.clearError"
                    >
                      <KTIcon icon-name="cross" icon-class="fs-4" />
                    </button>
                  </div>
                </div>
                <!--end::Error Alert-->

                <!--begin::Loading State-->
                <div
                  v-if="segmentsStore.loading && segmentsStore.segments.length === 0"
                  class="text-center py-12"
                >
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                  </div>
                  <p class="text-muted mt-3">Loading segments...</p>
                </div>
                <!--end::Loading State-->

                <!--begin::Empty State-->
                <div
                  v-else-if="segmentsStore.filteredSegments.length === 0"
                  class="text-center py-12"
                >
                  <KTIcon icon-name="video" icon-class="fs-2x text-muted mb-4" />
                  <h3 class="text-muted mb-2">No Segments Found</h3>
                  <p class="text-muted mb-4">
                    {{
                      segmentsStore.segments.length === 0
                        ? 'This video has no segments yet. Segments will appear here once video processing is complete.'
                        : 'No segments match your current filters. Try adjusting your search criteria.'
                    }}
                  </p>
                  <button
                    v-if="segmentsStore.segments.length === 0"
                    class="btn btn-primary"
                    @click="loadSegments"
                  >
                    <KTIcon icon-name="refresh" icon-class="fs-4" />
                    Refresh
                  </button>
                </div>
                <!--end::Empty State-->

                <!--begin::Segments Grid-->
                <div v-else class="row g-6 g-xl-9">
                  <div
                    v-for="segment in segmentsStore.filteredSegments"
                    :key="segment.segment_id"
                    class="col-md-6 col-xl-4"
                  >
                    <VideoSegmentCard
                      :segment="segment"
                      @play="handlePlaySegment"
                      @download="handleDownloadSegment"
                    />
                  </div>
                </div>
                <!--end::Segments Grid-->

                <!--begin::Load More-->
                <div v-if="segmentsStore.pagination.has_more" class="text-center mt-8">
                  <button
                    class="btn btn-light-primary"
                    :disabled="segmentsStore.loading"
                    @click="loadMore"
                  >
                    <KTIcon
                      :icon-name="segmentsStore.loading ? 'spinner' : 'arrow-down'"
                      :icon-class="segmentsStore.loading ? 'fs-4 fa-spin' : 'fs-4'"
                    />
                    {{ segmentsStore.loading ? 'Loading...' : 'Load More' }}
                  </button>
                </div>
                <!--end::Load More-->

                <!--begin::Stats-->
                <div v-if="segmentsStore.segments.length > 0" class="card mt-8">
                  <div class="card-body">
                    <div class="row text-center">
                      <div class="col-md-3">
                        <div class="fs-2 fw-bold text-primary">
                          {{ segmentsStore.segments.length }}
                        </div>
                        <div class="fs-6 text-muted">Total Segments</div>
                      </div>
                      <div class="col-md-3">
                        <div class="fs-2 fw-bold text-success">
                          {{ formatDuration(totalDuration) }}
                        </div>
                        <div class="fs-6 text-muted">Total Duration</div>
                      </div>
                      <div class="col-md-3">
                        <div class="fs-2 fw-bold text-info">
                          {{ formatFileSize(totalSize) }}
                        </div>
                        <div class="fs-6 text-muted">Total Size</div>
                      </div>
                      <div class="col-md-3">
                        <div class="fs-2 fw-bold text-warning">
                          {{ totalDownloads }}
                        </div>
                        <div class="fs-6 text-muted">Total Downloads</div>
                      </div>
                    </div>
                  </div>
                </div>
                <!--end::Stats-->
              </div>
              <!--end::Container-->
            </div>
            <!--end::Post-->
          </div>
          <!--end::Content wrapper-->
        </div>
        <!--end::Content-->
      </div>
      <!--end::Wrapper-->
    </div>
    <!--end::Page-->
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSegmentsStore } from '@/stores/segments'
import { useVideosStore } from '@/stores/videos'
import VideoSegmentCard from '@/components/video/VideoSegmentCard.vue'
import SegmentFilters from '@/components/video/SegmentFilters.vue'
import type { VideoSegment } from '@/stores/segments'

export default defineComponent({
  name: 'VideoSegmentView',
  components: {
    VideoSegmentCard,
    SegmentFilters,
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const segmentsStore = useSegmentsStore()
    const videosStore = useVideosStore()

    const videoId = route.params.videoId as string

    // Get video title for display
    const videoTitle = computed(() => {
      const video = videosStore.userVideos.find((v) => v.video_id === videoId)
      return video?.title || ''
    })

    // Calculate stats
    const totalDuration = computed(() => {
      return segmentsStore.segments.reduce((total, segment) => total + segment.duration, 0)
    })

    const totalSize = computed(() => {
      return segmentsStore.segments.reduce((total, segment) => total + segment.file_size, 0)
    })

    const totalDownloads = computed(() => {
      return segmentsStore.segments.reduce((total, segment) => total + segment.download_count, 0)
    })

    // Load segments for the video
    const loadSegments = async () => {
      if (videoId) {
        await segmentsStore.loadVideoSegments(videoId)
      }
    }

    // Load more segments (for pagination)
    const loadMore = async () => {
      await segmentsStore.loadMore()
    }

    // Handle filter updates
    const handleFilterUpdate = async (filters: Partial<typeof segmentsStore.filters>) => {
      await segmentsStore.applyFilters(filters)
    }

    // Handle segment play
    const handlePlaySegment = (segment: VideoSegment) => {
      // TODO: Implement video player modal or redirect to video player
      console.log('Play segment:', segment)
    }

    // Handle segment download
    const handleDownloadSegment = async (segmentId: string) => {
      try {
        const response = await segmentsStore.downloadSegment(segmentId)

        // Create a temporary link and trigger download
        const link = document.createElement('a')
        link.href = response.download_url
        link.download =
          segmentsStore.segments.find((s) => s.segment_id === segmentId)?.filename || 'segment.mp4'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        // TODO: Show success notification
        console.log('Segment downloaded successfully')
      } catch (error) {
        console.error('Failed to download segment:', error)
        // TODO: Show error notification
      }
    }

    // Utility functions
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

    // Lifecycle
    onMounted(() => {
      loadSegments()
    })

    onUnmounted(() => {
      segmentsStore.reset()
    })

    return {
      router,
      segmentsStore,
      videoTitle,
      totalDuration,
      totalSize,
      totalDownloads,
      loadSegments,
      loadMore,
      handleFilterUpdate,
      handlePlaySegment,
      handleDownloadSegment,
      formatDuration,
      formatFileSize,
    }
  },
})
</script>

<style scoped>
.toolbar {
  background-color: var(--kt-toolbar-base-bg-color);
  border-bottom: 1px solid var(--kt-toolbar-base-border-color);
}

.post {
  background-color: var(--kt-content-bg-color);
}
</style>
