import { defineStore } from 'pinia'
import { AdminService, type User } from '@/core/services/AdminService'
import type { VideoMetadata } from '@/core/services/VideoService'

interface AdminStats {
  totalUsers: number
  totalVideos: number
  totalStorage: number
  activeUsers: number
  formattedStorage: string
}

interface AdminState {
  // Users
  users: User[]
  selectedUser: User | null
  selectedUserVideos: VideoMetadata[]

  // Videos
  allVideos: VideoMetadata[]

  // Stats
  stats: AdminStats | null

  // UI State
  loading: {
    users: boolean
    videos: boolean
    stats: boolean
    userVideos: boolean
    deleteVideo: boolean
  }

  // Current view
  currentView: 'dashboard' | 'users' | 'videos' | 'userVideos'

  // Error handling
  error: string | null
}

export const useAdminStore = defineStore('admin', {
  state: (): AdminState => ({
    users: [],
    selectedUser: null,
    selectedUserVideos: [],
    allVideos: [],
    stats: null,
    loading: {
      users: false,
      videos: false,
      stats: false,
      userVideos: false,
      deleteVideo: false,
    },
    currentView: 'dashboard',
    error: null,
  }),

  getters: {
    // Get user by ID
    getUserById: (state) => (userId: string) => {
      return state.users.find((user) => user.userId === userId)
    },

    // Get video by ID
    getVideoById: (state) => (videoId: string) => {
      return state.allVideos.find((video) => video.video_id === videoId)
    },

    // Filter videos by user
    getVideosByUser: (state) => (userId: string) => {
      return state.allVideos.filter((video) => video.user_id === userId)
    },

    // Get formatted storage size
    getFormattedStorage: (state) => {
      if (!state.stats) return '0 MB'
      const bytes = state.stats.totalStorage
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
      if (bytes === 0) return '0 Bytes'
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
    },

    // Check if any loading state is active
    isLoading: (state) => {
      return Object.values(state.loading).some((loading) => loading)
    },
  },

  actions: {
    // Set current view
    setCurrentView(view: AdminState['currentView']) {
      this.currentView = view
      this.error = null
    },

    // Clear error
    clearError() {
      this.error = null
    },

    // Load all users
    async loadUsers() {
      this.loading.users = true
      this.error = null

      try {
        console.log('Loading all users...')
        this.users = await AdminService.getAllUsers()
        console.log(`Loaded ${this.users.length} users`)
      } catch (error) {
        console.error('Failed to load users:', error)
        this.error = 'Failed to load users. Please try again.'
        // Fallback to mock data for development
        this.users = this.getMockUsers()
      } finally {
        this.loading.users = false
      }
    },

    // Load all videos
    async loadAllVideos() {
      this.loading.videos = true
      this.error = null

      try {
        console.log('Loading all videos...')
        this.allVideos = await AdminService.getAllVideos()
        console.log(`Loaded ${this.allVideos.length} videos`)
      } catch (error) {
        console.error('Failed to load videos:', error)
        this.error = 'Failed to load videos. Please try again.'
        // Fallback to mock data for development
        this.allVideos = this.getMockVideos()
      } finally {
        this.loading.videos = false
      }
    },

    // Load videos for specific user
    async loadUserVideos(userId: string) {
      this.loading.userVideos = true
      this.error = null

      try {
        // Filter from all videos or make specific API call
        this.selectedUserVideos = this.getVideosByUser(userId)
        console.log(`Loaded ${this.selectedUserVideos.length} videos for user ${userId}`)
      } catch (error) {
        console.error('Failed to load user videos:', error)
        this.error = 'Failed to load user videos. Please try again.'
      } finally {
        this.loading.userVideos = false
      }
    },

    // Select user and load their videos
    async selectUser(user: User) {
      this.selectedUser = user
      await this.loadUserVideos(user.userId)
      this.setCurrentView('userVideos')
    },

    // Clear selected user
    clearSelectedUser() {
      this.selectedUser = null
      this.selectedUserVideos = []
      this.setCurrentView('users')
    },

    // Load admin statistics
    async loadStats() {
      this.loading.stats = true
      this.error = null

      try {
        console.log('Loading admin statistics...')
        const stats = await AdminService.getAdminStats()
        this.stats = {
          ...stats,
          formattedStorage: this.formatBytes(stats.totalStorage),
        }
        console.log('Admin stats loaded:', this.stats)
      } catch (error) {
        console.error('Failed to load admin stats:', error)
        this.error = 'Failed to load statistics. Please try again.'
        // Fallback to calculated stats from current data
        this.calculateStatsFromData()
      } finally {
        this.loading.stats = false
      }
    },

    // Delete video (admin action)
    async deleteVideo(videoId: string) {
      this.loading.deleteVideo = true
      this.error = null

      try {
        console.log('Deleting video:', videoId)
        const success = await AdminService.deleteVideo(videoId)

        if (success) {
          // Remove from all videos array
          this.allVideos = this.allVideos.filter((video) => video.video_id !== videoId)

          // Remove from selected user videos if applicable
          this.selectedUserVideos = this.selectedUserVideos.filter(
            (video) => video.video_id !== videoId,
          )

          // Refresh stats
          await this.loadStats()

          console.log('Video deleted successfully')
          return true
        }
        return false
      } catch (error) {
        console.error('Failed to delete video:', error)
        this.error = 'Failed to delete video. Please try again.'
        return false
      } finally {
        this.loading.deleteVideo = false
      }
    },

    // Toggle user status (enable/disable)
    async toggleUserStatus(userId: string, enabled: boolean) {
      try {
        console.log(`${enabled ? 'Enabling' : 'Disabling'} user:`, userId)
        const success = await AdminService.toggleUserStatus(userId, enabled)

        if (success) {
          // Update user in the array
          const userIndex = this.users.findIndex((user) => user.userId === userId)
          if (userIndex !== -1) {
            this.users[userIndex].enabled = enabled
          }

          // Refresh stats
          await this.loadStats()

          console.log('User status updated successfully')
          return true
        }
        return false
      } catch (error) {
        console.error('Failed to update user status:', error)
        this.error = 'Failed to update user status. Please try again.'
        return false
      }
    },

    // Initialize admin data
    async initializeAdmin() {
      console.log('Initializing admin data...')

      // Load all data in parallel
      await Promise.all([this.loadUsers(), this.loadAllVideos(), this.loadStats()])

      console.log('Admin initialization complete')
    },

    // Refresh all data
    async refreshData() {
      await this.initializeAdmin()
    },

    // Helper method to format bytes
    formatBytes(bytes: number): string {
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
      if (bytes === 0) return '0 Bytes'
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
    },

    // Calculate stats from current data (fallback)
    calculateStatsFromData() {
      const totalStorage = this.allVideos.reduce((sum, video) => sum + (video.file_size || 0), 0)
      const activeUsers = this.users.filter((user) => user.enabled !== false).length

      this.stats = {
        totalUsers: this.users.length,
        totalVideos: this.allVideos.length,
        totalStorage,
        activeUsers,
        formattedStorage: this.formatBytes(totalStorage),
      }
    },

    // Mock data for development/fallback
    getMockUsers(): User[] {
      return [
        {
          userId: 'user1',
          username: 'john_doe',
          email: 'john.doe@example.com',
          groups: ['user'],
          isAdmin: false,
          created_at: '2024-01-15T10:30:00Z',
          enabled: true,
        },
        {
          userId: 'user2',
          username: 'jane_smith',
          email: 'jane.smith@example.com',
          groups: ['user'],
          isAdmin: false,
          created_at: '2024-01-20T14:45:00Z',
          enabled: true,
        },
        {
          userId: 'admin1',
          username: 'admin_user',
          email: 'admin@example.com',
          groups: ['admin'],
          isAdmin: true,
          created_at: '2024-01-01T09:00:00Z',
          enabled: true,
        },
      ]
    },

    getMockVideos(): VideoMetadata[] {
      return [
        {
          video_id: 'user1_1642248600_abc123',
          user_id: 'user1',
          user_email: 'john.doe@example.com',
          title: 'Sample Video 1',
          filename: 'sample1.mp4',
          bucket_location: 'videos/user1/sample1.mp4',
          upload_date: '2024-01-15T15:30:00Z',
          file_size: 52428800, // 50MB
          content_type: 'video/mp4',
          duration: 180,
          created_at: '2024-01-15T15:30:00Z',
          updated_at: '2024-01-15T15:30:00Z',
        },
        {
          video_id: 'user2_1642335000_def456',
          user_id: 'user2',
          user_email: 'jane.smith@example.com',
          title: 'Demo Video',
          filename: 'demo.mp4',
          bucket_location: 'videos/user2/demo.mp4',
          upload_date: '2024-01-20T18:20:00Z',
          file_size: 104857600, // 100MB
          content_type: 'video/mp4',
          duration: 240,
          created_at: '2024-01-20T18:20:00Z',
          updated_at: '2024-01-20T18:20:00Z',
        },
      ]
    },
  },
})
