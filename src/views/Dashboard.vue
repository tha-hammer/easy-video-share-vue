<template>
  <!--begin::Dashboard-->
  <!-- Error Alert -->
  <div v-if="errorMessage" class="mb-5">
    <div class="alert alert-danger d-flex align-items-center p-5 mb-5">
      <i class="ki-duotone ki-shield-cross fs-2hx text-danger me-4">
        <span class="path1"></span>
        <span class="path2"></span>
        <span class="path3"></span>
      </i>
      <div class="d-flex flex-column">
        <h5 class="mb-1">Connection Error</h5>
        <span>{{ errorMessage }}</span>
        <button @click="retryLoadData" class="btn btn-sm btn-light-primary mt-3 align-self-start">
          <i class="ki-duotone ki-arrows-circle fs-2">
            <span class="path1"></span>
            <span class="path2"></span>
          </i>
          Retry
        </button>
      </div>
    </div>

    <!-- Configuration Guide -->
    <ConfigurationNotice />
  </div>

  <div class="row g-5 g-xl-8">
    <div class="col-xl-4">
      <VideoStatsWidget
        widget-classes="card-xl-stretch mb-xl-8"
        icon-name="video"
        color="body-white"
        icon-color="primary"
        title="Total Videos"
        :description="`${videoStats.totalVideos} videos uploaded`"
      />
    </div>

    <div class="col-xl-4">
      <VideoStatsWidget
        widget-classes="card-xl-stretch mb-xl-8"
        icon-name="cloud-upload"
        color="primary"
        icon-color="white"
        title="Storage Used"
        :description="videoStats.storageUsed"
      />
    </div>

    <div class="col-xl-4">
      <VideoStatsWidget
        widget-classes="card-xl-stretch mb-xl-8"
        icon-name="chart-line-up"
        color="dark"
        icon-color="gray-100"
        title="Today's Uploads"
        :description="`${videoStats.todayUploads} videos today`"
      />
    </div>
  </div>

  <div class="row g-5 g-xl-8">
    <div class="col-xl-8">
      <RecentVideosWidget widget-classes="card-xl-stretch mb-xl-8" @play="handlePlayVideo" />
    </div>

    <div class="col-xl-4">
      <VideoUploadWidget widget-classes="card-xl-stretch mb-5 mb-xl-8" />
    </div>
  </div>

  <div class="row g-5 g-xl-8" v-if="isAdmin">
    <div class="col-xl-12">
      <AdminStatsWidget widget-classes="card-xl-stretch mb-5 mb-xl-8" />
    </div>
  </div>

  <!--begin::Video Modal-->
  <VideoModal
    v-if="selectedVideo"
    :video="selectedVideo"
    :show="showVideoModal"
    @close="closeVideoModal"
  />
  <!--end::Video Modal-->
  <!--end::Dashboard-->
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useVideosStore } from '@/stores/videos'
import VideoStatsWidget from '@/components/widgets/VideoStatsWidget.vue'
import RecentVideosWidget from '@/components/widgets/RecentVideosWidget.vue'
import VideoUploadWidget from '@/components/widgets/VideoUploadWidget.vue'
import AdminStatsWidget from '@/components/widgets/AdminStatsWidget.vue'
import ConfigurationNotice from '@/components/ConfigurationNotice.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import type { VideoMetadata } from '@/stores/videos'

export default defineComponent({
  name: 'dashboard-main',
  components: {
    VideoStatsWidget,
    RecentVideosWidget,
    VideoUploadWidget,
    AdminStatsWidget,
    ConfigurationNotice,
    VideoModal,
  },
  setup() {
    const authStore = useAuthStore()
    const videosStore = useVideosStore()

    const videoStats = ref({
      totalVideos: 0,
      storageUsed: '0 MB',
      todayUploads: 0,
    })

    const errorMessage = ref('')
    const isAdmin = computed(() => authStore.user?.isAdmin || false)

    // Modal state
    const selectedVideo = ref<VideoMetadata | null>(null)
    const showVideoModal = ref(false)

    const loadData = async () => {
      try {
        errorMessage.value = ''
        await videosStore.loadUserVideos()
        calculateVideoStats()
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
          errorMessage.value = `Failed to load video data: ${msg}`
        }
      }
    }

    const retryLoadData = () => {
      loadData()
    }

    onMounted(async () => {
      loadData()
    })

    const calculateVideoStats = () => {
      const videos = videosStore.userVideos
      videoStats.value.totalVideos = videos.length

      // Calculate storage used
      const totalBytes = videos.reduce((sum, video) => sum + (video.file_size || 0), 0)
      videoStats.value.storageUsed = formatBytes(totalBytes)

      // Calculate today's uploads
      const today = new Date().toISOString().split('T')[0]
      videoStats.value.todayUploads = videos.filter((video) =>
        video.upload_date.startsWith(today),
      ).length
    }

    const formatBytes = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Modal handlers
    const handlePlayVideo = (video: VideoMetadata) => {
      selectedVideo.value = video
      showVideoModal.value = true
    }

    const closeVideoModal = () => {
      showVideoModal.value = false
      selectedVideo.value = null
    }

    return {
      videoStats,
      isAdmin,
      errorMessage,
      retryLoadData,
      selectedVideo,
      showVideoModal,
      handlePlayVideo,
      closeVideoModal,
    }
  },
})
</script>
