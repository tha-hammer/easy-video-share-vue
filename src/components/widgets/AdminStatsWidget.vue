<template>
  <!--begin::Admin Stats Widget-->
  <div :class="widgetClasses" class="card">
    <!--begin::Header-->
    <div class="card-header border-0 pt-5">
      <h3 class="card-title align-items-start flex-column">
        <span class="card-label fw-bold text-gray-900">Admin Overview</span>
        <span class="text-muted mt-1 fw-semibold fs-7">System statistics</span>
      </h3>
      <div class="card-toolbar">
        <button
          @click="refreshData"
          class="btn btn-sm btn-light-info me-2"
          :disabled="adminStore.isLoading"
        >
          <KTIcon v-if="adminStore.isLoading" icon-name="arrows-loop-1" icon-class="fs-3 spinner" />
          <KTIcon v-else icon-name="arrows-loop-1" icon-class="fs-3" />
          Refresh
        </button>
        <router-link to="/admin" class="btn btn-sm btn-info"> Admin Panel </router-link>
      </div>
    </div>
    <!--end::Header-->

    <!--begin::Body-->
    <div class="card-body pt-2">
      <!-- Loading State -->
      <div v-if="adminStore.loading.stats" class="d-flex justify-content-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading statistics...</span>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="adminStore.error" class="alert alert-light-danger d-flex align-items-center">
        <KTIcon icon-name="warning-2" icon-class="fs-2 text-danger me-3" />
        <div class="d-flex flex-column">
          <span class="fw-bold">Error loading statistics</span>
          <span class="fs-7">{{ adminStore.error }}</span>
        </div>
      </div>

      <!-- Statistics Content -->
      <div v-else class="row g-3">
        <!-- Total Users -->
        <div class="col-6">
          <div class="d-flex align-items-center">
            <div class="symbol symbol-45px me-5">
              <span class="symbol-label bg-light-success">
                <KTIcon icon-name="people" icon-class="fs-1 text-success" />
              </span>
            </div>
            <div class="d-flex flex-column">
              <div class="fw-bold fs-6">Total Users</div>
              <div class="fw-semibold text-muted fs-7">{{ stats?.totalUsers || 0 }} registered</div>
            </div>
          </div>
        </div>

        <!-- Total Videos -->
        <div class="col-6">
          <div class="d-flex align-items-center">
            <div class="symbol symbol-45px me-5">
              <span class="symbol-label bg-light-primary">
                <KTIcon icon-name="video" icon-class="fs-1 text-primary" />
              </span>
            </div>
            <div class="d-flex flex-column">
              <div class="fw-bold fs-6">Total Videos</div>
              <div class="fw-semibold text-muted fs-7">{{ stats?.totalVideos || 0 }} uploaded</div>
            </div>
          </div>
        </div>

        <!-- Active Users -->
        <div class="col-6">
          <div class="d-flex align-items-center">
            <div class="symbol symbol-45px me-5">
              <span class="symbol-label bg-light-warning">
                <KTIcon icon-name="user-tick" icon-class="fs-1 text-warning" />
              </span>
            </div>
            <div class="d-flex flex-column">
              <div class="fw-bold fs-6">Active Users</div>
              <div class="fw-semibold text-muted fs-7">{{ stats?.activeUsers || 0 }} enabled</div>
            </div>
          </div>
        </div>

        <!-- Total Storage -->
        <div class="col-6">
          <div class="d-flex align-items-center">
            <div class="symbol symbol-45px me-5">
              <span class="symbol-label bg-light-info">
                <KTIcon icon-name="storage" icon-class="fs-1 text-info" />
              </span>
            </div>
            <div class="d-flex flex-column">
              <div class="fw-bold fs-6">Storage Used</div>
              <div class="fw-semibold text-muted fs-7">
                {{ stats?.formattedStorage || '0 MB' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-6 pt-5 border-top">
        <div class="row g-3">
          <div class="col-6">
            <router-link
              to="/admin/users"
              class="btn btn-sm btn-light-success w-100"
              @click="adminStore.setCurrentView('users')"
            >
              <KTIcon icon-name="people" icon-class="fs-3 me-2" />
              Manage Users
            </router-link>
          </div>
          <div class="col-6">
            <router-link
              to="/admin/videos"
              class="btn btn-sm btn-light-primary w-100"
              @click="adminStore.setCurrentView('videos')"
            >
              <KTIcon icon-name="video" icon-class="fs-3 me-2" />
              Manage Videos
            </router-link>
          </div>
        </div>
      </div>
    </div>
    <!--end::Body-->
  </div>
  <!--end::Admin Stats Widget-->
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

export default defineComponent({
  name: 'admin-stats-widget',
  props: {
    widgetClasses: String,
  },
  setup() {
    const adminStore = useAdminStore()

    // Computed properties
    const stats = computed(() => adminStore.stats)

    // Methods
    const refreshData = async () => {
      await adminStore.refreshData()
    }

    // Initialize data on mount
    onMounted(async () => {
      if (!adminStore.stats) {
        await adminStore.loadStats()
      }
    })

    return {
      adminStore,
      stats,
      refreshData,
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
