<template>
  <div class="admin-user-videos-panel">
    <!--begin::User Header-->
    <div class="card mb-5">
      <div class="card-body">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <div class="symbol symbol-50px me-5">
              <div class="symbol-label fs-2 bg-light-primary text-primary">
                {{ getUserInitials(user) }}
              </div>
            </div>
            <div>
              <h4 class="fw-bold text-gray-800 mb-1">{{ user.email }}</h4>
              <div class="d-flex align-items-center">
                <span class="badge badge-light-success fs-8 me-3">{{
                  user.isAdmin ? 'Administrator' : 'User'
                }}</span>
                <span class="text-muted fs-7">Member since {{ formatDate(user.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="d-flex gap-3">
            <button
              @click="refreshUserVideos"
              class="btn btn-light-primary"
              :disabled="adminStore.loading.userVideos"
            >
              <KTIcon
                v-if="adminStore.loading.userVideos"
                icon-name="arrows-loop-1"
                icon-class="fs-3 spinner me-2"
              />
              <KTIcon v-else icon-name="arrows-loop-1" icon-class="fs-3 me-2" />
              Refresh
            </button>
            <button @click="$emit('back-to-users')" class="btn btn-light-secondary">
              <KTIcon icon-name="arrow-left" icon-class="fs-3 me-2" />
              Back to Users
            </button>
          </div>
        </div>
      </div>
    </div>
    <!--end::User Header-->

    <!--begin::User Stats-->
    <div class="row g-5 mb-5">
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-primary">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <KTIcon icon-name="video" icon-class="fs-1 text-primary me-3" />
              <div>
                <div class="fw-bold text-gray-800 fs-2x">{{ userVideos.length }}</div>
                <div class="fw-semibold text-muted fs-7">Total Videos</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-info">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <KTIcon icon-name="storage" icon-class="fs-1 text-info me-3" />
              <div>
                <div class="fw-bold text-gray-800 fs-2x">{{ totalUserStorageFormatted }}</div>
                <div class="fw-semibold text-muted fs-7">Storage Used</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-success">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <KTIcon icon-name="calendar-8" icon-class="fs-1 text-success me-3" />
              <div>
                <div class="fw-bold text-gray-800 fs-6">{{ latestUploadDate }}</div>
                <div class="fw-semibold text-muted fs-7">Latest Upload</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-warning">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <KTIcon icon-name="chart-simple" icon-class="fs-1 text-warning me-3" />
              <div>
                <div class="fw-bold text-gray-800 fs-6">{{ averageFileSize }}</div>
                <div class="fw-semibold text-muted fs-7">Avg File Size</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!--end::User Stats-->

    <!--begin::Videos Content-->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <h3 class="fw-bold">{{ user.email }}'s Videos</h3>
        </div>
        <div class="card-toolbar">
          <button @click="toggleViewMode" class="btn btn-sm btn-light-secondary">
            <KTIcon
              :icon-name="viewMode === 'grid' ? 'row-horizontal' : 'category'"
              icon-class="fs-3 me-2"
            />
            {{ viewMode === 'grid' ? 'List View' : 'Grid View' }}
          </button>
        </div>
      </div>

      <div class="card-body p-0">
        <!-- Loading State -->
        <div v-if="adminStore.loading.userVideos" class="d-flex justify-content-center py-10">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading user videos...</span>
          </div>
        </div>

        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid' && userVideos.length > 0" class="p-5">
          <div class="row g-5">
            <div
              v-for="video in userVideos"
              :key="video.video_id"
              class="col-xl-4 col-lg-6 col-md-6"
            >
              <div class="card card-hover">
                <div class="card-body p-5">
                  <!-- Video Thumbnail -->
                  <div class="position-relative mb-4">
                    <div
                      class="bg-light-primary rounded h-150px d-flex align-items-center justify-content-center"
                    >
                      <KTIcon icon-name="video" icon-class="fs-1 text-primary" />
                    </div>
                    <div class="position-absolute top-0 end-0 p-2">
                      <div class="dropdown">
                        <button
                          class="btn btn-icon btn-sm btn-light-primary dropdown-toggle"
                          type="button"
                          :id="'dropdown-' + video.video_id"
                          data-bs-toggle="dropdown"
                          aria-expanded="false"
                        >
                          <KTIcon icon-name="dots-vertical" icon-class="fs-3" />
                        </button>
                        <ul class="dropdown-menu" :aria-labelledby="'dropdown-' + video.video_id">
                          <li>
                            <a class="dropdown-item" @click="playVideo(video)">
                              <KTIcon icon-name="play" icon-class="fs-4 me-2" />
                              Play Video
                            </a>
                          </li>
                          <li><hr class="dropdown-divider" /></li>
                          <li>
                            <a class="dropdown-item text-danger" @click="confirmDeleteVideo(video)">
                              <KTIcon icon-name="trash" icon-class="fs-4 me-2" />
                              Delete Video
                            </a>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <!-- Video Info -->
                  <div class="mb-3">
                    <h6 class="fw-bold text-gray-800 mb-2 cursor-pointer" @click="playVideo(video)">
                      {{ video.title }}
                    </h6>
                    <div class="d-flex justify-content-between align-items-center">
                      <span class="badge badge-light fs-8">{{
                        formatFileSize(video.file_size)
                      }}</span>
                      <span class="text-muted fs-8">{{ formatDate(video.upload_date) }}</span>
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="d-flex gap-2">
                    <button
                      @click="playVideo(video)"
                      class="btn btn-sm btn-light-primary flex-grow-1"
                    >
                      <KTIcon icon-name="play" icon-class="fs-4 me-1" />
                      Play
                    </button>
                    <button @click="confirmDeleteVideo(video)" class="btn btn-sm btn-light-danger">
                      <KTIcon icon-name="trash" icon-class="fs-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- List View -->
        <div v-else-if="viewMode === 'list' && userVideos.length > 0" class="table-responsive">
          <table class="table table-hover table-rounded table-striped border gy-7 gs-7">
            <thead>
              <tr class="fw-semibold fs-6 text-gray-800 border-bottom border-gray-200">
                <th class="min-w-250px">Video</th>
                <th class="min-w-100px">Size</th>
                <th class="min-w-150px">Upload Date</th>
                <th class="text-end min-w-100px">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="video in userVideos"
                :key="video.video_id"
                class="cursor-pointer"
                @click="playVideo(video)"
              >
                <td>
                  <div class="d-flex align-items-center">
                    <div class="symbol symbol-45px me-5">
                      <div class="symbol-label bg-light-primary">
                        <KTIcon icon-name="video" icon-class="fs-2 text-primary" />
                      </div>
                    </div>
                    <div class="d-flex flex-column">
                      <div class="fw-bold text-gray-800 fs-6">{{ video.title }}</div>
                      <div class="text-muted fs-7">{{ video.filename }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="badge badge-light fs-7">{{ formatFileSize(video.file_size) }}</span>
                </td>
                <td class="text-muted fs-7">{{ formatDate(video.upload_date) }}</td>
                <td class="text-end">
                  <div class="d-flex gap-2 justify-content-end" @click.stop>
                    <button @click="playVideo(video)" class="btn btn-icon btn-sm btn-light-primary">
                      <KTIcon icon-name="play" icon-class="fs-3" />
                    </button>
                    <button
                      @click="confirmDeleteVideo(video)"
                      class="btn btn-icon btn-sm btn-light-danger"
                    >
                      <KTIcon icon-name="trash" icon-class="fs-3" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-10">
          <KTIcon icon-name="video" icon-class="fs-3x text-muted mb-5" />
          <h3 class="text-gray-800 fw-bold mb-3">No Videos Found</h3>
          <p class="text-muted fs-6 mb-0">This user hasn't uploaded any videos yet.</p>
        </div>
      </div>
    </div>
    <!--end::Videos Content-->
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref, inject } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { User } from '@/core/services/AdminService'
import type { VideoMetadata } from '@/core/services/VideoService'

export default defineComponent({
  name: 'admin-user-videos-panel',
  props: {
    user: {
      type: Object as () => User,
      required: true,
    },
  },
  emits: ['back-to-users'],
  setup(props) {
    const adminStore = useAdminStore()

    // Inject methods from parent component
    const openVideoModal = inject<(video: VideoMetadata) => void>('openVideoModal')
    const openDeleteModal = inject<(type: string, item: VideoMetadata) => void>('openDeleteModal')

    // Reactive data
    const viewMode = ref<'grid' | 'list'>('grid')

    // Computed properties
    const userVideos = computed(() => {
      return [...adminStore.selectedUserVideos].sort(
        (a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime(),
      )
    })

    const totalUserStorageFormatted = computed(() => {
      const totalBytes = userVideos.value.reduce((sum, video) => sum + (video.file_size || 0), 0)
      return formatFileSize(totalBytes)
    })

    const latestUploadDate = computed(() => {
      if (userVideos.value.length === 0) return 'No uploads'
      const latest = userVideos.value[0]
      return formatDate(latest.upload_date)
    })

    const averageFileSize = computed(() => {
      if (userVideos.value.length === 0) return '0 MB'
      const totalBytes = userVideos.value.reduce((sum, video) => sum + (video.file_size || 0), 0)
      const avgBytes = totalBytes / userVideos.value.length
      return formatFileSize(avgBytes)
    })

    // Methods
    const getUserInitials = (user: User): string => {
      const email = user.email || user.username || 'U'
      return email.substring(0, 2).toUpperCase()
    }

    const formatFileSize = (bytes?: number): string => {
      if (!bytes) return '0 MB'
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
    }

    const formatDate = (dateString?: string): string => {
      if (!dateString) return 'Unknown'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    }

    const toggleViewMode = () => {
      viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
    }

    const refreshUserVideos = async () => {
      await adminStore.loadUserVideos(props.user.userId)
    }

    const playVideo = (video: VideoMetadata) => {
      if (openVideoModal) {
        openVideoModal(video)
      }
    }

    const confirmDeleteVideo = (video: VideoMetadata) => {
      if (openDeleteModal) {
        openDeleteModal('video', video)
      }
    }

    return {
      adminStore,
      viewMode,
      userVideos,
      totalUserStorageFormatted,
      latestUploadDate,
      averageFileSize,

      // Methods
      getUserInitials,
      formatFileSize,
      formatDate,
      toggleViewMode,
      refreshUserVideos,
      playVideo,
      confirmDeleteVideo,
    }
  },
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1.5rem 0.5rem rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.h-150px {
  height: 150px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.table > tbody > tr:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
