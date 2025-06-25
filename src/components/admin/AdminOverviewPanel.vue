<template>
  <div class="admin-overview">
    <!--begin::Statistics Cards-->
    <div class="row g-5 g-xl-8 mb-8">
      <!--begin::Total Users Card-->
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-success">
          <div class="card-body">
            <div class="d-flex flex-column">
              <div class="d-flex align-items-center justify-content-between mb-5">
                <span class="fw-semibold text-success fs-6">Total Users</span>
                <KTIcon icon-name="people" icon-class="fs-1 text-success" />
              </div>
              <div class="d-flex align-items-baseline">
                <span class="fw-bold text-gray-800 fs-2x me-2">{{ stats?.totalUsers || 0 }}</span>
                <span class="fw-semibold text-muted fs-7">registered</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!--end::Total Users Card-->

      <!--begin::Total Videos Card-->
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-primary">
          <div class="card-body">
            <div class="d-flex flex-column">
              <div class="d-flex align-items-center justify-content-between mb-5">
                <span class="fw-semibold text-primary fs-6">Total Videos</span>
                <KTIcon icon-name="video" icon-class="fs-1 text-primary" />
              </div>
              <div class="d-flex align-items-baseline">
                <span class="fw-bold text-gray-800 fs-2x me-2">{{ stats?.totalVideos || 0 }}</span>
                <span class="fw-semibold text-muted fs-7">uploaded</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!--end::Total Videos Card-->

      <!--begin::Active Users Card-->
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-warning">
          <div class="card-body">
            <div class="d-flex flex-column">
              <div class="d-flex align-items-center justify-content-between mb-5">
                <span class="fw-semibold text-warning fs-6">Active Users</span>
                <KTIcon icon-name="user-tick" icon-class="fs-1 text-warning" />
              </div>
              <div class="d-flex align-items-baseline">
                <span class="fw-bold text-gray-800 fs-2x me-2">{{ stats?.activeUsers || 0 }}</span>
                <span class="fw-semibold text-muted fs-7">enabled</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!--end::Active Users Card-->

      <!--begin::Storage Used Card-->
      <div class="col-xl-3 col-md-6">
        <div class="card bg-light-info">
          <div class="card-body">
            <div class="d-flex flex-column">
              <div class="d-flex align-items-center justify-content-between mb-5">
                <span class="fw-semibold text-info fs-6">Storage Used</span>
                <KTIcon icon-name="storage" icon-class="fs-1 text-info" />
              </div>
              <div class="d-flex align-items-baseline">
                <span class="fw-bold text-gray-800 fs-2x">{{
                  stats?.formattedStorage || '0 MB'
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!--end::Storage Used Card-->
    </div>
    <!--end::Statistics Cards-->

    <!--begin::Recent Activity Section-->
    <div class="row g-5 g-xl-8">
      <!--begin::Recent Users-->
      <div class="col-xl-6">
        <div class="card card-xl-stretch">
          <div class="card-header border-0 pt-5">
            <h3 class="card-title align-items-start flex-column">
              <span class="card-label fw-bold text-gray-900">Recent Users</span>
              <span class="text-muted mt-1 fw-semibold fs-7">Latest registered users</span>
            </h3>
            <div class="card-toolbar">
              <router-link to="/admin/users" class="btn btn-sm btn-light-success">
                View All
              </router-link>
            </div>
          </div>
          <div class="card-body pt-0">
            <!-- Loading state -->
            <div v-if="adminStore.loading.users" class="d-flex justify-content-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading users...</span>
              </div>
            </div>

            <!-- Users list -->
            <div v-else-if="recentUsers.length > 0" class="d-flex flex-column">
              <div
                v-for="user in recentUsers"
                :key="user.userId"
                class="d-flex align-items-center border-bottom border-gray-300 pb-3 mb-3"
              >
                <div class="symbol symbol-45px me-5">
                  <div class="symbol-label fs-3 bg-light-primary text-primary">
                    {{ getUserInitials(user) }}
                  </div>
                </div>
                <div class="d-flex flex-column flex-grow-1">
                  <div class="fw-semibold text-gray-800 fs-6">{{ user.email }}</div>
                  <div class="text-muted fs-7">
                    <span class="badge badge-light-success fs-8 me-2">{{
                      user.isAdmin ? 'Admin' : 'User'
                    }}</span>
                    {{ formatDate(user.created_at) }}
                  </div>
                </div>
                <div class="text-end">
                  <span v-if="user.enabled === false" class="badge badge-light-danger"
                    >Disabled</span
                  >
                  <span v-else class="badge badge-light-success">Active</span>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else class="text-center py-5">
              <KTIcon icon-name="user" icon-class="fs-3x text-muted mb-3" />
              <p class="text-muted">No users found</p>
            </div>
          </div>
        </div>
      </div>
      <!--end::Recent Users-->

      <!--begin::Recent Videos-->
      <div class="col-xl-6">
        <div class="card card-xl-stretch">
          <div class="card-header border-0 pt-5">
            <h3 class="card-title align-items-start flex-column">
              <span class="card-label fw-bold text-gray-900">Recent Videos</span>
              <span class="text-muted mt-1 fw-semibold fs-7">Latest video uploads</span>
            </h3>
            <div class="card-toolbar">
              <router-link to="/admin/videos" class="btn btn-sm btn-light-primary">
                View All
              </router-link>
            </div>
          </div>
          <div class="card-body pt-0">
            <!-- Loading state -->
            <div v-if="adminStore.loading.videos" class="d-flex justify-content-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading videos...</span>
              </div>
            </div>

            <!-- Videos list -->
            <div v-else-if="recentVideos.length > 0" class="d-flex flex-column">
              <div
                v-for="video in recentVideos"
                :key="video.video_id"
                class="d-flex align-items-center border-bottom border-gray-300 pb-3 mb-3 cursor-pointer"
                @click="playVideo(video)"
              >
                <div class="symbol symbol-45px me-5">
                  <div class="symbol-label bg-light-primary">
                    <KTIcon icon-name="video" icon-class="fs-2 text-primary" />
                  </div>
                </div>
                <div class="d-flex flex-column flex-grow-1">
                  <div class="fw-semibold text-gray-800 fs-6">{{ video.title }}</div>
                  <div class="text-muted fs-7">by {{ video.user_email }}</div>
                  <div class="text-muted fs-8">
                    {{ formatFileSize(video.file_size) }} • {{ formatDate(video.upload_date) }}
                  </div>
                </div>
                <div class="text-end">
                  <button
                    class="btn btn-icon btn-sm btn-light-primary"
                    @click.stop="playVideo(video)"
                  >
                    <KTIcon icon-name="play" icon-class="fs-3" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-else class="text-center py-5">
              <KTIcon icon-name="video" icon-class="fs-3x text-muted mb-3" />
              <p class="text-muted">No videos found</p>
            </div>
          </div>
        </div>
      </div>
      <!--end::Recent Videos-->
    </div>
    <!--end::Recent Activity Section-->
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, inject } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { VideoMetadata } from '@/core/services/VideoService'
import type { User } from '@/core/services/AdminService'

export default defineComponent({
  name: 'admin-overview-panel',
  setup() {
    const adminStore = useAdminStore()

    // Inject methods from parent component
    const openVideoModal = inject<(video: VideoMetadata) => void>('openVideoModal')

    // Computed properties
    const stats = computed(() => adminStore.stats)

    const recentUsers = computed(() => {
      return adminStore.users
        .slice()
        .sort(
          (a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime(),
        )
        .slice(0, 5)
    })

    const recentVideos = computed(() => {
      return adminStore.allVideos
        .slice()
        .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
        .slice(0, 5)
    })

    // Methods
    const getUserInitials = (user: User): string => {
      const email = user.email || user.username || 'U'
      return email.substring(0, 2).toUpperCase()
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

    const formatFileSize = (bytes?: number): string => {
      if (!bytes) return '0 MB'
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
    }

    const playVideo = (video: VideoMetadata) => {
      if (openVideoModal) {
        openVideoModal(video)
      }
    }

    return {
      adminStore,
      stats,
      recentUsers,
      recentVideos,

      // Methods
      getUserInitials,
      formatDate,
      formatFileSize,
      playVideo,
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
  border-radius: 0.5rem;
}
</style>
