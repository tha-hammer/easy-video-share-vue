import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard',
    component: () => import('@/layouts/default-layout/DefaultLayout.vue'),
    meta: {
      middleware: 'auth',
    },
    children: [
      {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          pageTitle: 'Dashboard',
          breadcrumbs: ['Dashboards'],
        },
      },
      {
        path: '/videos',
        name: 'videos',
        component: () => import('@/views/Videos.vue'),
        meta: {
          pageTitle: 'My Videos',
          breadcrumbs: ['Videos'],
        },
      },
      {
        path: '/videos/:videoId/segments',
        name: 'video-segments',
        component: () => import('@/views/VideoSegmentView.vue'),
        props: true,
        meta: {
          pageTitle: 'Video Segments',
          breadcrumbs: ['Videos', 'Segments'],
        },
      },
      {
        path: '/segments',
        name: 'segments',
        component: () => import('@/views/SegmentsLibrary.vue'),
        meta: {
          pageTitle: 'My Segments',
          breadcrumbs: ['Segments'],
        },
      },
      {
        path: '/upload',
        name: 'upload',
        component: () => import('@/views/Upload.vue'),
        meta: {
          pageTitle: 'Upload Video',
          breadcrumbs: ['Videos', 'Upload'],
        },
      },
      {
        path: '/admin',
        name: 'admin',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: {
          pageTitle: 'Admin Dashboard',
          breadcrumbs: ['Admin'],
          requiresAdmin: true,
        },
      },
      {
        path: '/admin/users',
        name: 'admin-users',
        component: () => import('@/views/admin/Users.vue'),
        meta: {
          pageTitle: 'User Management',
          breadcrumbs: ['Admin', 'Users'],
          requiresAdmin: true,
        },
      },
      {
        path: '/admin/videos',
        name: 'admin-videos',
        component: () => import('@/views/admin/Videos.vue'),
        meta: {
          pageTitle: 'Video Management',
          breadcrumbs: ['Admin', 'Videos'],
          requiresAdmin: true,
        },
      },
      {
        path: '/text-customization/:jobId',
        name: 'TextCustomization',
        component: () => import('@/views/TextCustomization.vue'),
        props: true,
        meta: {
          pageTitle: 'Text Customization',
          breadcrumbs: ['Videos', 'Text Customization'],
        },
      },
      {
        path: '/processing/:jobId',
        name: 'Processing',
        component: () => import('@/views/Processing.vue'),
        props: true,
        meta: {
          pageTitle: 'Processing',
          breadcrumbs: ['Videos', 'Processing'],
        },
      },
    ],
  },
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/Login.vue'),
        meta: {
          pageTitle: 'Sign In',
        },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/Register.vue'),
        meta: {
          pageTitle: 'Sign Up',
        },
      },
    ],
  },
  // Redirect old Metronic demo routes to appropriate pages
  {
    path: '/pages/profile/overview',
    redirect: '/dashboard',
  },
  {
    path: '/apps/subscriptions/add-subscription',
    redirect: '/upload',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    } else {
      return {
        top: 0,
        behavior: 'smooth',
      }
    }
  },
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth on first route
  if (authStore.isLoading) {
    await authStore.initialize()
  }

  // Check if route requires authentication
  if (to.meta.middleware === 'auth') {
    if (!authStore.isAuthenticated) {
      next({ name: 'login' })
      return
    }

    // Check if route requires admin access
    if (to.meta.requiresAdmin && !authStore.user?.isAdmin) {
      next({ name: 'dashboard' })
      return
    }
  }

  // Redirect authenticated users away from auth pages
  if (authStore.isAuthenticated && to.path.startsWith('/auth')) {
    next({ name: 'dashboard' })
    return
  }

  next()
})

export default router
