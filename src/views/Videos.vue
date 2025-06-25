<template>
  <!--begin::Videos Page-->
  <div class="d-flex flex-column gap-7 gap-lg-10">
    <!--begin::Page Header-->
    <div class="card card-flush">
      <div class="card-header align-items-center py-5 gap-2 gap-md-5">
        <!--begin::Title-->
        <div class="card-title">
          <h2 class="text-gray-900">My Videos</h2>
        </div>
        <!--end::Title-->

        <!--begin::Actions-->
        <div class="card-toolbar flex-row-fluid justify-content-end gap-5">
          <!--begin::View Toggle-->
          <div class="btn-group" role="group">
            <button
              type="button"
              class="btn btn-sm"
              :class="viewMode === 'grid' ? 'btn-primary' : 'btn-light'"
              @click="viewMode = 'grid'"
            >
              <KTIcon icon-name="element-4" icon-class="fs-3" />
              Grid
            </button>
            <button
              type="button"
              class="btn btn-sm"
              :class="viewMode === 'list' ? 'btn-primary' : 'btn-light'"
              @click="viewMode = 'list'"
            >
              <KTIcon icon-name="row-vertical" icon-class="fs-3" />
              List
            </button>
          </div>
          <!--end::View Toggle-->

          <!--begin::Upload Button-->
          <router-link to="/upload" class="btn btn-primary">
            <KTIcon icon-name="plus" icon-class="fs-2" />
            Upload Video
          </router-link>
          <!--end::Upload Button-->
        </div>
        <!--end::Actions-->
      </div>
    </div>
    <!--end::Page Header-->

    <!--begin::Videos Content-->
    <div class="card card-flush">
      <div class="card-body pt-0">
        <!--begin::Error State-->
        <div v-if="errorMessage" class="alert alert-danger d-flex align-items-center p-5 mb-5">
          <i class="ki-duotone ki-shield-cross fs-2hx text-danger me-4">
            <span class="path1"></span>
            <span class="path2"></span>
            <span class="path3"></span>
          </i>
          <div class="d-flex flex-column">
            <h5 class="mb-1">Failed to Load Videos</h5>
            <span>{{ errorMessage }}</span>
            <button
              @click="retryLoadData"
              class="btn btn-sm btn-light-primary mt-3 align-self-start"
            >
              <i class="ki-duotone ki-arrows-circle fs-2">
                <span class="path1"></span>
                <span class="path2"></span>
              </i>
              Retry
            </button>
          </div>
        </div>
        <!--end::Error State-->

        <!--begin::Loading State-->
        <div v-else-if="videosStore.loading" class="text-center py-10">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="text-muted mt-3">Loading your videos...</p>
        </div>
        <!--end::Loading State-->

        <!--begin::Empty State-->
        <div v-else-if="videosStore.userVideos.length === 0" class="text-center py-10">
          <KTIcon icon-name="file-up" icon-class="fs-4x text-muted mb-5" />
          <h3 class="text-gray-900">No videos yet</h3>
          <p class="text-muted">Upload your first video to get started</p>
          <router-link to="/upload" class="btn btn-primary mt-3">
            <KTIcon icon-name="plus" icon-class="fs-2" />
            Upload Video
          </router-link>
        </div>
        <!--end::Empty State-->

        <!--begin::Videos Grid-->
        <div v-else-if="viewMode === 'grid'" class="row g-6 g-xl-9">
          <div
            v-for="video in videosStore.userVideos"
            :key="video.video_id"
            class="col-md-6 col-lg-4 col-xl-3"
          >
            <VideoCard :video="video" @delete="handleDeleteVideo" @play="handlePlayVideo" />
          </div>
        </div>
        <!--end::Videos Grid-->

        <!--begin::Videos List-->
        <div v-else class="table-responsive">
          <table class="table table-row-dashed table-row-gray-300 gy-7">
            <thead>
              <tr class="fw-bold fs-6 text-gray-800">
                <th>Video</th>
                <th>Size</th>
                <th>Duration</th>
                <th>Upload Date</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="video in videosStore.userVideos" :key="video.video_id">
                <td>
                  <div class="d-flex align-items-center">
                    <div class="symbol symbol-45px me-5">
                      <span class="symbol-label bg-light-primary text-primary fs-6 fw-bold">
                        <KTIcon icon-name="video" icon-class="fs-2" />
                      </span>
                    </div>
                    <div class="d-flex justify-content-start flex-column">
                      <a
                        href="#"
                        class="text-gray-900 fw-bold text-hover-primary mb-1 fs-6"
                        @click.prevent="handlePlayVideo(video)"
                      >
                        {{ video.title }}
                      </a>
                      <span class="text-muted fw-semibold text-muted d-block fs-7">
                        {{ video.filename }}
                      </span>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="text-gray-900 fw-bold d-block fs-6">
                    {{ formatFileSize(video.file_size || 0) }}
                  </span>
                </td>
                <td>
                  <span class="text-gray-900 fw-bold d-block fs-6">
                    {{ formatDuration(video.duration || 0) }}
                  </span>
                </td>
                <td>
                  <span class="text-gray-900 fw-bold d-block fs-6">
                    {{ formatDate(video.upload_date) }}
                  </span>
                </td>
                <td class="text-end">
                  <button
                    class="btn btn-sm btn-light btn-active-light-primary me-2"
                    @click="handlePlayVideo(video)"
                  >
                    <KTIcon icon-name="play" icon-class="fs-3" />
                  </button>
                  <button
                    class="btn btn-sm btn-light btn-active-light-danger"
                    @click="handleDeleteVideo(video.video_id)"
                  >
                    <KTIcon icon-name="trash" icon-class="fs-3" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!--end::Videos List-->
      </div>
    </div>
    <!--end::Videos Content-->
  </div>

  <!--begin::Video Modal-->
  <VideoModal
    v-if="selectedVideo"
    :video="selectedVideo"
    :show="showVideoModal"
    @close="closeVideoModal"
  />
  <!--end::Video Modal-->
  <!--end::Videos Page-->
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useVideosStore } from '@/stores/videos'
import VideoCard from '@/components/video/VideoCard.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import type { VideoMetadata } from '@/stores/videos'

export default defineComponent({
  name: 'videos-page',
  components: {
    VideoCard,
    VideoModal,
  },
  setup() {
    const videosStore = useVideosStore()
    const viewMode = ref<'grid' | 'list'>('grid')
    const selectedVideo = ref<VideoMetadata | null>(null)
    const showVideoModal = ref(false)
    const errorMessage = ref('')

    const loadData = async () => {
      try {
        errorMessage.value = ''
        await videosStore.loadUserVideos()
      } catch (error) {
        const msg = error instanceof Error ? error.message : 'Unknown error'

        if (msg.includes('Failed to fetch') || msg.includes('net::ERR_FAILED')) {
          errorMessage.value =
            'Cannot connect to the server. Please check your internet connection and API configuration.'
        } else if (msg.includes('CORS')) {
          errorMessage.value =
            'Server access denied. The API needs to be configured to allow requests from this domain.'
        } else if (msg.includes('401') || msg.includes('Unauthorized')) {
          errorMessage.value = 'Authentication failed. Please refresh the page to log in again.'
        } else {
          errorMessage.value = `Failed to load videos: ${msg}`
        }
      }
    }

    const retryLoadData = () => {
      loadData()
    }

    onMounted(() => {
      loadData()
    })

    const handlePlayVideo = (video: VideoMetadata) => {
      selectedVideo.value = video
      showVideoModal.value = true
    }

    const closeVideoModal = () => {
      showVideoModal.value = false
      selectedVideo.value = null
    }

    const handleDeleteVideo = async (videoId: string) => {
      if (confirm('Are you sure you want to delete this video?')) {
        try {
          await videosStore.deleteVideo(videoId)
        } catch (error) {
          console.error('Failed to delete video:', error)
          alert('Failed to delete video. Please try again.')
        }
      }
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
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatDate = (dateString: string): string => {
      return new Date(dateString).toLocaleDateString()
    }

    return {
      videosStore,
      viewMode,
      selectedVideo,
      showVideoModal,
      errorMessage,
      retryLoadData,
      handlePlayVideo,
      closeVideoModal,
      handleDeleteVideo,
      formatFileSize,
      formatDuration,
      formatDate,
    }
  },
})
</script>
