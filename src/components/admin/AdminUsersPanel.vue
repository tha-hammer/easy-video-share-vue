<template>
  <div class="admin-users-panel">
    <!--begin::Header-->
    <div class="d-flex justify-content-between align-items-center mb-5">
      <div>
        <h3 class="text-gray-900 fw-bold">User Management</h3>
        <p class="text-muted fs-6 mb-0">Manage registered users and their access</p>
      </div>
      <div class="d-flex gap-3">
        <button
          @click="refreshUsers"
          class="btn btn-light-primary"
          :disabled="adminStore.loading.users"
        >
          <KTIcon
            v-if="adminStore.loading.users"
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
                placeholder="Search users..."
              />
            </div>
          </div>
          <div class="col-md-3">
            <select v-model="statusFilter" class="form-select form-select-solid">
              <option value="">All Users</option>
              <option value="active">Active Users</option>
              <option value="disabled">Disabled Users</option>
              <option value="admin">Administrators</option>
            </select>
          </div>
          <div class="col-md-2">
            <div class="text-muted fs-7">
              {{ filteredUsers.length }} of {{ adminStore.users.length }} users
            </div>
          </div>
        </div>
      </div>
    </div>
    <!--end::Search and Filters-->

    <!--begin::Users Table-->
    <div class="card">
      <div class="card-body p-0">
        <!-- Loading State -->
        <div v-if="adminStore.loading.users" class="d-flex justify-content-center py-10">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading users...</span>
          </div>
        </div>

        <!-- Users Table -->
        <div v-else-if="filteredUsers.length > 0" class="table-responsive">
          <table class="table table-hover table-rounded table-striped border gy-7 gs-7">
            <thead>
              <tr class="fw-semibold fs-6 text-gray-800 border-bottom border-gray-200">
                <th class="min-w-250px">User</th>
                <th class="min-w-150px">Status</th>
                <th class="min-w-100px">Role</th>
                <th class="min-w-150px">Created</th>
                <th class="min-w-100px">Videos</th>
                <th class="text-end min-w-100px">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in paginatedUsers"
                :key="user.userId"
                class="cursor-pointer"
                @click="viewUserDetails(user)"
              >
                <td>
                  <div class="d-flex align-items-center">
                    <div class="symbol symbol-45px me-5">
                      <div class="symbol-label fs-3 bg-light-primary text-primary">
                        {{ getUserInitials(user) }}
                      </div>
                    </div>
                    <div class="d-flex flex-column">
                      <div class="fw-bold text-gray-800 fs-6">{{ user.email }}</div>
                      <div class="text-muted fs-7">{{ user.username || 'No username' }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span v-if="user.enabled === false" class="badge badge-light-danger fs-7 fw-bold">
                    Disabled
                  </span>
                  <span v-else class="badge badge-light-success fs-7 fw-bold"> Active </span>
                </td>
                <td>
                  <span v-if="user.isAdmin" class="badge badge-light-warning fs-7 fw-bold">
                    Administrator
                  </span>
                  <span v-else class="badge badge-light-info fs-7 fw-bold"> User </span>
                </td>
                <td class="text-muted fs-7">{{ formatDate(user.created_at) }}</td>
                <td>
                  <span class="badge badge-light fs-7">
                    {{ getUserVideoCount(user.userId) }} videos
                  </span>
                </td>
                <td class="text-end">
                  <div class="dropdown" @click.stop>
                    <button
                      class="btn btn-icon btn-sm btn-light-primary dropdown-toggle"
                      type="button"
                      :id="'dropdown-' + user.userId"
                      data-bs-toggle="dropdown"
                      aria-expanded="false"
                    >
                      <KTIcon icon-name="dots-horizontal" icon-class="fs-3" />
                    </button>
                    <ul class="dropdown-menu" :aria-labelledby="'dropdown-' + user.userId">
                      <li>
                        <a class="dropdown-item" @click="viewUserVideos(user)">
                          <KTIcon icon-name="video" icon-class="fs-4 me-2" />
                          View Videos
                        </a>
                      </li>
                      <li><hr class="dropdown-divider" /></li>
                      <li v-if="user.enabled !== false">
                        <a class="dropdown-item text-danger" @click="disableUser(user)">
                          <KTIcon icon-name="user-cross" icon-class="fs-4 me-2" />
                          Disable User
                        </a>
                      </li>
                      <li v-else>
                        <a class="dropdown-item text-success" @click="enableUser(user)">
                          <KTIcon icon-name="user-tick" icon-class="fs-4 me-2" />
                          Enable User
                        </a>
                      </li>
                    </ul>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-10">
          <KTIcon icon-name="user" icon-class="fs-3x text-muted mb-5" />
          <h3 class="text-gray-800 fw-bold mb-3">No Users Found</h3>
          <p class="text-muted fs-6 mb-0">
            {{
              searchTerm ? 'No users match your search criteria.' : 'No users are registered yet.'
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
            {{ Math.min(currentPage * itemsPerPage, filteredUsers.length) }} of
            {{ filteredUsers.length }} users
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
    <!--end::Users Table-->
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { User } from '@/core/services/AdminService'

export default defineComponent({
  name: 'admin-users-panel',
  emits: ['user-selected'],
  setup(props, { emit }) {
    const adminStore = useAdminStore()

    // Reactive data
    const searchTerm = ref('')
    const statusFilter = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Computed properties
    const filteredUsers = computed(() => {
      let users = adminStore.users

      // Apply search filter
      if (searchTerm.value) {
        const search = searchTerm.value.toLowerCase()
        users = users.filter(
          (user) =>
            user.email.toLowerCase().includes(search) ||
            (user.username && user.username.toLowerCase().includes(search)),
        )
      }

      // Apply status filter
      if (statusFilter.value) {
        switch (statusFilter.value) {
          case 'active':
            users = users.filter((user) => user.enabled !== false)
            break
          case 'disabled':
            users = users.filter((user) => user.enabled === false)
            break
          case 'admin':
            users = users.filter((user) => user.isAdmin)
            break
        }
      }

      return users.sort(
        (a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime(),
      )
    })

    const totalPages = computed(() => Math.ceil(filteredUsers.value.length / itemsPerPage))

    const paginatedUsers = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredUsers.value.slice(start, end)
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

    // Reset pagination when filters change
    watch([searchTerm, statusFilter], () => {
      currentPage.value = 1
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

    const getUserVideoCount = (userId: string): number => {
      return adminStore.allVideos.filter((video) => video.user_id === userId).length
    }

    const refreshUsers = async () => {
      await adminStore.loadUsers()
    }

    const viewUserDetails = (user: User) => {
      // Could expand to show user details modal
      console.log('View user details:', user)
    }

    const viewUserVideos = (user: User) => {
      emit('user-selected', user)
    }

    const disableUser = async (user: User) => {
      if (confirm(`Are you sure you want to disable user "${user.email}"?`)) {
        const success = await adminStore.toggleUserStatus(user.userId, false)
        if (success) {
          console.log('User disabled successfully')
        }
      }
    }

    const enableUser = async (user: User) => {
      const success = await adminStore.toggleUserStatus(user.userId, true)
      if (success) {
        console.log('User enabled successfully')
      }
    }

    return {
      adminStore,
      searchTerm,
      statusFilter,
      currentPage,
      itemsPerPage,
      filteredUsers,
      totalPages,
      paginatedUsers,
      visiblePages,

      // Methods
      getUserInitials,
      formatDate,
      getUserVideoCount,
      refreshUsers,
      viewUserDetails,
      viewUserVideos,
      disableUser,
      enableUser,
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
