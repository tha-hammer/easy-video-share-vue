<template>
  <div class="container-fluid">
    <!--begin::Row-->
    <div class="row gy-5 gx-xl-8">
      <!--begin::Page Header-->
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <div class="d-flex align-items-center">
              <h1 class="h3 text-gray-900 mb-0">
                <KTIcon icon-name="shield-tick" icon-class="fs-1 text-primary me-3" />
                Admin Dashboard
              </h1>
            </div>
            <div class="card-toolbar">
              <button
                @click="refreshAllData"
                class="btn btn-primary"
                :disabled="adminStore.isLoading"
              >
                <KTIcon
                  v-if="adminStore.isLoading"
                  icon-name="arrows-loop-1"
                  icon-class="fs-3 spinner me-2"
                />
                <KTIcon v-else icon-name="arrows-loop-1" icon-class="fs-3 me-2" />
                Refresh Data
              </button>
            </div>
          </div>
        </div>
      </div>
      <!--end::Page Header-->

      <!--begin::Stats Overview-->
      <div class="col-xl-3 col-md-6">
        <AdminStatsWidget widget-classes="card-xl-stretch mb-xl-8" />
      </div>

      <div class="col-xl-9 col-md-6">
        <!--begin::Tab Navigation-->
        <div class="card card-xl-stretch">
          <div class="card-header border-0 pt-5">
            <h3 class="card-title align-items-start flex-column">
              <span class="card-label fw-bold text-gray-900">Admin Management</span>
              <span class="text-muted mt-1 fw-semibold fs-7">User and video administration</span>
            </h3>
          </div>
          <div class="card-body pt-0">
            <!--begin::Nav Tabs-->
            <ul
              class="nav nav-tabs nav-line-tabs nav-line-tabs-2x border-transparent fs-4 fw-semibold mb-5"
            >
              <li class="nav-item">
                <a
                  class="nav-link text-active-primary d-flex align-items-center pb-5"
                  :class="{ active: currentTab === 'overview' }"
                  @click="setCurrentTab('overview')"
                  role="button"
                >
                  <KTIcon icon-name="element-11" icon-class="fs-2 me-2" />
                  Overview
                </a>
              </li>
              <li class="nav-item">
                <a
                  class="nav-link text-active-primary d-flex align-items-center pb-5"
                  :class="{ active: currentTab === 'users' }"
                  @click="setCurrentTab('users')"
                  role="button"
                >
                  <KTIcon icon-name="people" icon-class="fs-2 me-2" />
                  Users ({{ adminStore.users.length }})
                </a>
              </li>
              <li class="nav-item">
                <a
                  class="nav-link text-active-primary d-flex align-items-center pb-5"
                  :class="{ active: currentTab === 'videos' }"
                  @click="setCurrentTab('videos')"
                  role="button"
                >
                  <KTIcon icon-name="video" icon-class="fs-2 me-2" />
                  Videos ({{ adminStore.allVideos.length }})
                </a>
              </li>
              <li class="nav-item" v-if="adminStore.selectedUser">
                <a
                  class="nav-link text-active-primary d-flex align-items-center pb-5"
                  :class="{ active: currentTab === 'userVideos' }"
                  @click="setCurrentTab('userVideos')"
                  role="button"
                >
                  <KTIcon icon-name="user" icon-class="fs-2 me-2" />
                  {{ adminStore.selectedUser.email }} Videos
                  <button
                    @click.stop="clearSelectedUser"
                    class="btn btn-icon btn-sm btn-light-danger ms-2"
                    title="Close user view"
                  >
                    <KTIcon icon-name="cross" icon-class="fs-3" />
                  </button>
                </a>
              </li>
            </ul>
            <!--end::Nav Tabs-->

            <!--begin::Tab Content-->
            <div class="tab-content">
              <!--begin::Overview Tab-->
              <div v-if="currentTab === 'overview'" class="tab-pane active">
                <AdminOverviewPanel />
              </div>
              <!--end::Overview Tab-->

              <!--begin::Users Tab-->
              <div v-if="currentTab === 'users'" class="tab-pane active">
                <AdminUsersPanel @user-selected="handleUserSelected" />
              </div>
              <!--end::Users Tab-->

              <!--begin::Videos Tab-->
              <div v-if="currentTab === 'videos'" class="tab-pane active">
                <AdminVideosPanel />
              </div>
              <!--end::Videos Tab-->

              <!--begin::User Videos Tab-->
              <div
                v-if="currentTab === 'userVideos' && adminStore.selectedUser"
                class="tab-pane active"
              >
                <AdminUserVideosPanel :user="adminStore.selectedUser" />
              </div>
              <!--end::User Videos Tab-->
            </div>
            <!--end::Tab Content-->
          </div>
        </div>
      </div>
      <!--end::Main Content-->
    </div>
    <!--end::Row-->

    <!-- Global Error Alert -->
    <div v-if="adminStore.error" class="alert alert-danger alert-dismissible mt-5">
      <div class="d-flex align-items-center">
        <KTIcon icon-name="warning-2" icon-class="fs-2 text-danger me-3" />
        <div class="d-flex flex-column">
          <span class="fw-bold">Error</span>
          <span class="fs-7">{{ adminStore.error }}</span>
        </div>
      </div>
      <button
        @click="adminStore.clearError"
        type="button"
        class="btn-close"
        aria-label="Close"
      ></button>
    </div>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmationModal
      :show="showDeleteModal"
      :item-type="deleteModalType"
      :item-name="getItemName(deleteModalItem)"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />

    <!-- Video Player Modal -->
    <VideoModal :show="showVideoModal" :video="selectedVideo" @close="closeVideoModal" />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, provide } from 'vue'
import { useAdminStore } from '@/stores/admin'
import AdminStatsWidget from '@/components/widgets/AdminStatsWidget.vue'
import AdminOverviewPanel from '@/components/admin/AdminOverviewPanel.vue'
import AdminUsersPanel from '@/components/admin/AdminUsersPanel.vue'
import AdminVideosPanel from '@/components/admin/AdminVideosPanel.vue'
import AdminUserVideosPanel from '@/components/admin/AdminUserVideosPanel.vue'
import DeleteConfirmationModal from '@/components/admin/DeleteConfirmationModal.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import type { User } from '@/core/services/AdminService'
import type { VideoMetadata } from '@/core/services/VideoService'

export default defineComponent({
  name: 'admin-dashboard',
  components: {
    AdminStatsWidget,
    AdminOverviewPanel,
    AdminUsersPanel,
    AdminVideosPanel,
    AdminUserVideosPanel,
    DeleteConfirmationModal,
    VideoModal,
  },
  setup() {
    const adminStore = useAdminStore()

    // Reactive data
    const currentTab = ref<string>('overview')
    const showDeleteModal = ref(false)
    const deleteModalType = ref<'user' | 'video'>('video')
    const deleteModalItem = ref<User | VideoMetadata | null>(null)
    const showVideoModal = ref(false)
    const selectedVideo = ref<VideoMetadata | null>(null)

    // Computed
    const isLoading = computed(() => adminStore.isLoading)

    // Methods
    const setCurrentTab = (tab: string) => {
      currentTab.value = tab
      if (tab === 'dashboard' || tab === 'users' || tab === 'videos' || tab === 'userVideos') {
        adminStore.setCurrentView(tab)
      }
    }

    const refreshAllData = async () => {
      await adminStore.refreshData()
    }

    const handleUserSelected = async (user: User) => {
      await adminStore.selectUser(user)
      currentTab.value = 'userVideos'
    }

    const clearSelectedUser = () => {
      adminStore.clearSelectedUser()
      currentTab.value = 'users'
    }

    const handleDeleteConfirm = async () => {
      if (deleteModalType.value === 'video' && deleteModalItem.value) {
        const video = deleteModalItem.value as VideoMetadata
        const success = await adminStore.deleteVideo(video.video_id)
        if (success) {
          console.log('Video deleted successfully')
        }
      }

      showDeleteModal.value = false
      deleteModalItem.value = null
    }

    const handleDeleteCancel = () => {
      showDeleteModal.value = false
      deleteModalItem.value = null
    }

    const openVideoModal = (video: VideoMetadata) => {
      selectedVideo.value = video
      showVideoModal.value = true
    }

    const closeVideoModal = () => {
      showVideoModal.value = false
      selectedVideo.value = null
    }

    const getItemName = (item: User | VideoMetadata | null): string => {
      if (item) {
        if (deleteModalType.value === 'user') {
          const user = item as User
          return user.email
        } else if (deleteModalType.value === 'video') {
          const video = item as VideoMetadata
          return video.title || video.video_id.toString()
        }
      }
      return 'item'
    }

    // Initialize admin data
    onMounted(async () => {
      console.log('Admin Dashboard mounted - initializing data...')
      await adminStore.initializeAdmin()
    })

    // Provide methods to child components using Vue's provide/inject
    provide('openDeleteModal', (type: 'user' | 'video', item: User | VideoMetadata) => {
      deleteModalType.value = type
      deleteModalItem.value = item
      showDeleteModal.value = true
    })

    provide('openVideoModal', openVideoModal)

    return {
      adminStore,
      currentTab,
      isLoading,
      showDeleteModal,
      deleteModalType,
      deleteModalItem,
      showVideoModal,
      selectedVideo,

      // Methods
      setCurrentTab,
      refreshAllData,
      handleUserSelected,
      clearSelectedUser,
      handleDeleteConfirm,
      handleDeleteCancel,
      openVideoModal,
      closeVideoModal,
      getItemName,
    }
  },
})
</script>

<style scoped>
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

.nav-link {
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-link:hover {
  color: var(--bs-primary) !important;
}

.tab-pane {
  min-height: 400px;
}
</style>
