<template>
  <!--begin::Menu wrapper-->
  <div
    id="kt_aside_menu_wrapper"
    ref="scrollElRef"
    class="hover-scroll-overlay-y px-2 my-5 my-lg-5"
    data-kt-scroll="true"
    data-kt-scroll-height="auto"
    data-kt-scroll-dependencies="{default: '#kt_aside_toolbar, #kt_aside_footer', lg: '#kt_header, #kt_aside_toolbar, #kt_aside_footer'}"
    data-kt-scroll-wrappers="#kt_aside_menu"
    data-kt-scroll-offset="5px"
  >
    <!--begin::Menu-->
    <div
      id="#kt_aside_menu"
      class="menu menu-column menu-title-gray-800 menu-state-title-primary menu-state-icon-primary menu-state-bullet-primary menu-arrow-gray-500"
      data-kt-menu="true"
    >
      <!-- Dashboard -->
      <div class="menu-item">
        <router-link to="/dashboard" class="menu-link" active-class="active">
          <span class="menu-icon">
            <KTIcon icon-name="element-11" icon-class="fs-2" />
          </span>
          <span class="menu-title">Dashboard</span>
        </router-link>
      </div>

      <!-- Videos Section -->
      <div class="menu-item">
        <div class="menu-content pt-8 pb-2">
          <span class="menu-section text-muted text-uppercase fs-8 ls-1"> Videos </span>
        </div>
      </div>

      <div class="menu-item">
        <router-link to="/videos" class="menu-link" active-class="active">
          <span class="menu-icon">
            <KTIcon icon-name="video" icon-class="fs-2" />
          </span>
          <span class="menu-title">My Videos</span>
        </router-link>
      </div>

      <div class="menu-item">
        <router-link to="/upload" class="menu-link" active-class="active">
          <span class="menu-icon">
            <KTIcon icon-name="cloud-upload" icon-class="fs-2" />
          </span>
          <span class="menu-title">Upload Video</span>
        </router-link>
      </div>

      <div class="menu-item">
        <router-link to="/segments" class="menu-link" active-class="active">
          <span class="menu-icon">
            <KTIcon icon-name="element-4" icon-class="fs-2" />
          </span>
          <span class="menu-title">My Segments</span>
        </router-link>
      </div>

      <!-- Admin Section (only show for admin users) -->
      <template v-if="isAdmin">
        <div class="menu-item">
          <div class="menu-content pt-8 pb-2">
            <span class="menu-section text-muted text-uppercase fs-8 ls-1"> Administration </span>
          </div>
        </div>

        <div class="menu-item">
          <router-link
            to="/admin"
            class="menu-link"
            active-class="active"
            exact-active-class="active"
          >
            <span class="menu-icon">
              <KTIcon icon-name="security-user" icon-class="fs-2" />
            </span>
            <span class="menu-title">Admin Dashboard</span>
          </router-link>
        </div>

        <div class="menu-item">
          <router-link
            to="/admin/users"
            class="menu-link"
            active-class="active"
            exact-active-class="active"
          >
            <span class="menu-icon">
              <KTIcon icon-name="people" icon-class="fs-2" />
            </span>
            <span class="menu-title">User Management</span>
          </router-link>
        </div>

        <div class="menu-item">
          <router-link
            to="/admin/videos"
            class="menu-link"
            active-class="active"
            exact-active-class="active"
          >
            <span class="menu-icon">
              <KTIcon icon-name="folder" icon-class="fs-2" />
            </span>
            <span class="menu-title">All Videos</span>
          </router-link>
        </div>
      </template>
    </div>
    <!--end::Menu-->
  </div>
  <!--end::Menu wrapper-->
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'kt-menu',
  setup() {
    const authStore = useAuthStore()

    const isAdmin = computed(() => authStore.user?.isAdmin || false)

    return {
      isAdmin,
    }
  },
})
</script>
