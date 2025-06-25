<template>
  <div class="d-flex flex-column">
    <!--begin::Toolbar-->
    <div class="app-toolbar py-3 py-lg-6">
      <div class="app-container container-xxl d-flex flex-stack">
        <!--begin::Page title-->
        <div class="page-title d-flex flex-column justify-content-center flex-wrap me-3">
          <h1
            class="page-heading d-flex text-gray-900 fw-bold fs-3 flex-column justify-content-center my-0"
          >
            User Management
          </h1>
          <ul class="breadcrumb breadcrumb-separatorless fw-semibold fs-7 my-0 pt-1">
            <li class="breadcrumb-item text-muted">
              <router-link to="/admin" class="text-muted text-hover-primary">Admin</router-link>
            </li>
            <li class="breadcrumb-item">
              <span class="bullet bg-gray-500 w-5px h-2px"></span>
            </li>
            <li class="breadcrumb-item text-muted">Users</li>
          </ul>
        </div>
        <!--end::Page title-->

        <!--begin::Actions-->
        <div class="d-flex align-items-center gap-2 gap-lg-3">
          <router-link to="/admin" class="btn btn-sm fw-bold btn-secondary">
            <KTIcon icon-name="arrow-left" icon-class="fs-3 me-1" />
            Back to Dashboard
          </router-link>
          <button @click="refreshData" class="btn btn-sm fw-bold btn-primary" :disabled="isLoading">
            <KTIcon v-if="isLoading" icon-name="arrows-loop-1" icon-class="fs-3 me-1 spinner" />
            <KTIcon v-else icon-name="arrows-loop-1" icon-class="fs-3 me-1" />
            Refresh
          </button>
        </div>
        <!--end::Actions-->
      </div>
    </div>
    <!--end::Toolbar-->

    <!--begin::Content-->
    <div class="app-content flex-column-fluid">
      <div class="app-container container-xxl">
        <AdminUsersPanel />
      </div>
    </div>
    <!--end::Content-->

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmationModal
      :show="showDeleteModal"
      :item-type="deleteModalType"
      :item-name="deleteModalItem?.email || 'item'"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />

    <!-- Video Player Modal -->
    <VideoModal :show="showVideoModal" :video="selectedVideo" @close="closeVideoModal" />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, provide } from 'vue'
import { useAdminStore } from '@/stores/admin'
import AdminUsersPanel from '@/components/admin/AdminUsersPanel.vue'
import DeleteConfirmationModal from '@/components/admin/DeleteConfirmationModal.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import type { User } from '@/core/services/AdminService'
import type { VideoMetadata } from '@/core/services/VideoService'

export default defineComponent({
  name: 'admin-users-view',
  components: {
    AdminUsersPanel,
    DeleteConfirmationModal,
    VideoModal,
  },
  setup() {
    const adminStore = useAdminStore()

    // Reactive data
    const showDeleteModal = ref(false)
    const deleteModalType = ref<'user' | 'video'>('user')
    const deleteModalItem = ref<User | VideoMetadata | null>(null)
    const showVideoModal = ref(false)
    const selectedVideo = ref<VideoMetadata | null>(null)

    // Computed
    const isLoading = computed(() => adminStore.isLoading)

    // Methods
    const refreshData = async () => {
      await adminStore.refreshData()
    }

    const handleDeleteConfirm = async () => {
      if (deleteModalType.value === 'user' && deleteModalItem.value) {
        const user = deleteModalItem.value as User
        const success = await adminStore.toggleUserStatus(user.userId, false)
        if (success) {
          console.log('User disabled successfully')
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

    // Initialize admin data
    onMounted(async () => {
      console.log('Users view mounted - initializing data...')
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
      isLoading,
      showDeleteModal,
      deleteModalType,
      deleteModalItem,
      showVideoModal,
      selectedVideo,

      // Methods
      refreshData,
      handleDeleteConfirm,
      handleDeleteCancel,
      openVideoModal,
      closeVideoModal,
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
</style>
