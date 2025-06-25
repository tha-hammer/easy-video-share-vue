<template>
  <div class="admin-videos-panel">
    <!--begin::Header-->
    <div class="d-flex justify-content-between align-items-center mb-5">
      <div>
        <h3 class="text-gray-900 fw-bold">Video Management</h3>
        <p class="text-muted fs-6 mb-0">Manage all videos across the platform</p>
      </div>
      <div class="d-flex gap-3">
        <button @click="toggleViewMode" class="btn btn-light-secondary">
          <KTIcon
            :icon-name="viewMode === 'grid' ? 'row-horizontal' : 'category'"
            icon-class="fs-3 me-2"
          />
          {{ viewMode === 'grid' ? 'List View' : 'Grid View' }}
        </button>
        <button
          @click="refreshVideos"
          class="btn btn-light-primary"
          :disabled="adminStore.loading.videos"
        >
          <KTIcon
            v-if="adminStore.loading.videos"
            icon-name="arrows-loop-1"
            icon-class="fs-3 spinner me-2"
          />
          <KTIcon v-else icon-name="arrows-loop-1" icon-class="fs-3 me-2" />
          Refresh
        </button>
      </div>
    </div>
    <!--end::Header-->

    <!--begin::Search and Filters-->
    <div class="card mb-5">
      <div class="card-body">
        <div class="row g-3 align-items-center">
          <div class="col-md-4">
            <div class="position-relative">
              <KTIcon icon-name="magnifier" icon-class="fs-3 position-absolute ms-3 mt-3" />
              <input
                v-model="searchTerm"
                type="text"
                class="form-control form-control-solid ps-10"
                placeholder="Search videos..."
              />
            </div>
          </div>
          <div class="col-md-3">
            <select v-model="userFilter" class="form-select form-select-solid">
              <option value="">All Users</option>
              <option v-for="user in uniqueUsers" :key="user.userId" :value="user.userId">
                {{ user.email }}
              </option>
            </select>
          </div>
          <div class="col-md-2">
            <select v-model="sortBy" class="form-select form-select-solid">
              <option value="upload_date">Sort by Date</option>
              <option value="title">Sort by Title</option>
              <option value="file_size">Sort by Size</option>
              <option value="user_email">Sort by User</option>
            </select>
          </div>
          <div class="col-md-3">
            <div class="text-muted fs-7">
              {{ filteredVideos.length }} of {{ adminStore.allVideos.length }} videos ({{
                totalStorageFormatted
              }})
            </div>
          </div>
        </div>
      </div>
    </div>
    <!--end::Search and Filters-->

    <!--begin::Videos Content-->
    <div class="card">
      <div class="card-body p-0">
        <!-- Loading State -->
        <div v-if="adminStore.loading.videos" class="d-flex justify-content-center py-10">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading videos...</span>
          </div>
        </div>

        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid' && filteredVideos.length > 0" class="p-5">
          <div class="row g-5">
            <div
              v-for="video in paginatedVideos"
              :key="video.video_id"
              class="col-xl-3 col-lg-4 col-md-6"
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
                    <div class="text-muted fs-7 mb-2">by {{ video.user_email }}</div>
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
        <div v-else-if="viewMode === 'list' && filteredVideos.length > 0" class="table-responsive">
          <table class="table table-hover table-rounded table-striped border gy-7 gs-7">
            <thead>
              <tr class="fw-semibold fs-6 text-gray-800 border-bottom border-gray-200">
                <th class="min-w-250px">Video</th>
                <th class="min-w-150px">User</th>
                <th class="min-w-100px">Size</th>
                <th class="min-w-150px">Upload Date</th>
                <th class="text-end min-w-100px">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="video in paginatedVideos"
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
                <td class="text-muted fs-6">{{ video.user_email }}</td>
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
          <p class="text-muted fs-6 mb-0">
            {{
              searchTerm
                ? 'No videos match your search criteria.'
                : 'No videos have been uploaded yet.'
            }}
          </p>
        </div>

        <!-- Pagination -->
        <div
          v-if="totalPages > 1"
          class="d-flex justify-content-between align-items-center p-5 border-top"
        >
          <div class="text-muted fs-7">
            Showing {{ (currentPage - 1) * itemsPerPage + 1 }} to
            {{ Math.min(currentPage * itemsPerPage, filteredVideos.length) }} of
            {{ filteredVideos.length }} videos
          </div>
          <nav>
            <ul class="pagination pagination-sm">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <button class="page-link" @click="currentPage = Math.max(1, currentPage - 1)">
                  Previous
                </button>
              </li>
              <li
                v-for="page in visiblePages"
                :key="page"
                class="page-item"
                :class="{ active: page === currentPage }"
              >
                <button class="page-link" @click="currentPage = page">{{ page }}</button>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <button
                  class="page-link"
                  @click="currentPage = Math.min(totalPages, currentPage + 1)"
                >
                  Next
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>
    <!--end::Videos Content-->
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, inject } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { VideoMetadata } from '@/core/services/VideoService'
import type { User } from '@/core/services/AdminService'

export default defineComponent({
  name: 'admin-videos-panel',
  setup() {
    const adminStore = useAdminStore()

    // Inject methods from parent component
    const openVideoModal = inject<(video: VideoMetadata) => void>('openVideoModal')
    const openDeleteModal =
      inject<(type: string, item: VideoMetadata | User) => void>('openDeleteModal')

    // Reactive data
    const searchTerm = ref('')
    const userFilter = ref('')
    const sortBy = ref('upload_date')
    const viewMode = ref<'grid' | 'list'>('grid')
    const currentPage = ref(1)
    const itemsPerPage = 12

    // Computed properties
    const uniqueUsers = computed(() => {
      const users = new Map()
      adminStore.allVideos.forEach((video) => {
        if (!users.has(video.user_id)) {
          users.set(video.user_id, {
            userId: video.user_id,
            email: video.user_email,
          })
        }
      })
      return Array.from(users.values()).sort((a, b) => (a.email || '').localeCompare(b.email || ''))
    })

    const filteredVideos = computed(() => {
      let videos = adminStore.allVideos

      // Apply search filter
      if (searchTerm.value) {
        const search = searchTerm.value.toLowerCase()
        videos = videos.filter(
          (video) =>
            (video.title || '').toLowerCase().includes(search) ||
            (video.user_email || '').toLowerCase().includes(search) ||
            (video.filename || '').toLowerCase().includes(search),
        )
      }

      // Apply user filter
      if (userFilter.value) {
        videos = videos.filter((video) => video.user_id === userFilter.value)
      }

      // Apply sorting
      return videos.sort((a, b) => {
        switch (sortBy.value) {
          case 'title':
            return (a.title || '').localeCompare(b.title || '')
          case 'file_size':
            return (b.file_size || 0) - (a.file_size || 0)
          case 'user_email':
            return (a.user_email || '').localeCompare(b.user_email || '')
          case 'upload_date':
          default:
            return new Date(b.upload_date || 0).getTime() - new Date(a.upload_date || 0).getTime()
        }
      })
    })

    const totalPages = computed(() => Math.ceil(filteredVideos.value.length / itemsPerPage))

    const paginatedVideos = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredVideos.value.slice(start, end)
    })

    const visiblePages = computed(() => {
      const pages = []
      const start = Math.max(1, currentPage.value - 2)
      const end = Math.min(totalPages.value, start + 4)

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

    const totalStorageFormatted = computed(() => {
      const totalBytes = filteredVideos.value.reduce(
        (sum, video) => sum + (video.file_size || 0),
        0,
      )
      return formatFileSize(totalBytes)
    })

    // Reset pagination when filters change
    watch([searchTerm, userFilter, sortBy], () => {
      currentPage.value = 1
    })

    // Methods
    const formatFileSize = (bytes?: number): string => {
      if (!bytes) return '0 MB'
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
    }

    const formatDate = (dateString: string): string => {
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

    const refreshVideos = async () => {
      await adminStore.loadAllVideos()
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
      searchTerm,
      userFilter,
      sortBy,
      viewMode,
      currentPage,
      itemsPerPage,
      uniqueUsers,
      filteredVideos,
      totalPages,
      paginatedVideos,
      visiblePages,
      totalStorageFormatted,

      // Methods
      formatFileSize,
      formatDate,
      toggleViewMode,
      refreshVideos,
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
