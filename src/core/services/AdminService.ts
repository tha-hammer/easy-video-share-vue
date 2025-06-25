import { API_CONFIG } from '@/core/config/config'
import { authManager } from '@/core/auth/authManager'
import type { VideoMetadata } from './VideoService'

// User interface from Cognito
interface User {
  userId: string
  username: string
  email: string
  groups: string[]
  isAdmin: boolean
  created_at?: string
  last_modified?: string
  enabled?: boolean
}

export class AdminService {
  // Helper method to get auth headers
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await authManager.getAccessToken()
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    }
  }

  // Get all users (admin only)
  static async getAllUsers(): Promise<User[]> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(API_CONFIG.adminUsersEndpoint, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle different response formats
      if (Array.isArray(data)) {
        return data
      } else if (data.users && Array.isArray(data.users)) {
        return data.users
      } else if (data.body) {
        // Handle API Gateway Lambda proxy response format
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        return Array.isArray(body) ? body : body.users || []
      }

      console.log('Unexpected API response format:', data)
      return []
    } catch (error) {
      console.error('Error fetching users:', error)
      throw error
    }
  }

  // Get all videos (admin only)
  static async getAllVideos(): Promise<VideoMetadata[]> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(API_CONFIG.adminVideosEndpoint, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch all videos: ${response.statusText}`)
      }

      const data = await response.json()

      // Handle different response formats
      if (Array.isArray(data)) {
        return data
      } else if (data.videos && Array.isArray(data.videos)) {
        return data.videos
      } else if (data.body) {
        // Handle API Gateway Lambda proxy response format
        const body = typeof data.body === 'string' ? JSON.parse(data.body) : data.body
        return Array.isArray(body) ? body : body.videos || []
      }

      console.log('Unexpected API response format:', data)
      return []
    } catch (error) {
      console.error('Error fetching all videos:', error)
      throw error
    }
  }

  // Delete video (admin can delete any video)
  static async deleteVideo(videoId: string): Promise<boolean> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${API_CONFIG.adminVideosEndpoint}/${videoId}`, {
        method: 'DELETE',
        headers,
      })

      if (!response.ok) {
        throw new Error(`Failed to delete video: ${response.statusText}`)
      }

      return true
    } catch (error) {
      console.error('Error deleting video:', error)
      throw error
    }
  }

  // Disable/Enable user (admin only)
  static async toggleUserStatus(userId: string, enabled: boolean): Promise<boolean> {
    try {
      const headers = await this.getAuthHeaders()

      const response = await fetch(`${API_CONFIG.adminUsersEndpoint}/${userId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ enabled }),
      })

      if (!response.ok) {
        throw new Error(`Failed to update user status: ${response.statusText}`)
      }

      return true
    } catch (error) {
      console.error('Error updating user status:', error)
      throw error
    }
  }

  // Get admin statistics
  static async getAdminStats(): Promise<{
    totalUsers: number
    totalVideos: number
    totalStorage: number
    activeUsers: number
  }> {
    try {
      const [users, videos] = await Promise.all([this.getAllUsers(), this.getAllVideos()])

      const totalStorage = videos.reduce((sum, video) => sum + (video.file_size || 0), 0)
      const activeUsers = users.filter((user) => user.enabled !== false).length

      return {
        totalUsers: users.length,
        totalVideos: videos.length,
        totalStorage,
        activeUsers,
      }
    } catch (error) {
      console.error('Error getting admin stats:', error)
      throw error
    }
  }
}

export type { User }
