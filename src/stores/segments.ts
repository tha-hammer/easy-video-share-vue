import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { VideoService } from '@/core/services/VideoService'
import { useAuthStore } from '@/stores/auth'

// Video segment interface
export interface VideoSegment {
  segment_id: string
  video_id: string
  user_id: string
  segment_type: string
  segment_number: number
  s3_key: string
  s3_url?: string
  duration: number
  file_size: number
  content_type: string
  thumbnail_url?: string
  created_at: string
  updated_at: string
  title?: string
  description?: string
  tags?: string[]
  social_media_usage?: {
    platform: string
    post_id?: string
    post_url?: string
    posted_at?: string
    views: number
    likes: number
    shares: number
    comments: number
    engagement_rate?: number
    last_synced?: string
  }[]
  filename?: string
  download_count: number
  last_downloaded_at?: string
}

// Filter interface
export interface SegmentFilters {
  sort_by: 'date' | 'name' | 'size' | 'duration' | 'downloads'
  order: 'asc' | 'desc'
  min_duration?: number
  max_duration?: number
  min_downloads?: number
  search?: string
}

// Pagination interface
export interface Pagination {
  limit: number
  offset: number
  total_count: number
  has_more: boolean
}

export const useSegmentsStore = defineStore('segments', () => {
  // State
  const segments = ref<VideoSegment[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<SegmentFilters>({
    sort_by: 'date',
    order: 'desc',
  })
  const pagination = ref<Pagination>({
    limit: 20,
    offset: 0,
    total_count: 0,
    has_more: false,
  })

  // Context state to track if we're viewing video-specific segments
  const currentVideoId = ref<string | null>(null)
  const isVideoSpecificView = ref(false)

  // Getters
  const filteredSegments = computed(() => {
    let filtered = [...segments.value]

    // Apply search filter
    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      filtered = filtered.filter(
        (segment) =>
          segment.filename?.toLowerCase().includes(search) ||
          false ||
          segment.title?.toLowerCase().includes(search) ||
          false ||
          segment.description?.toLowerCase().includes(search) ||
          false,
      )
    }

    // Apply duration filters
    if (filters.value.min_duration !== undefined) {
      filtered = filtered.filter((segment) => segment.duration >= filters.value.min_duration!)
    }
    if (filters.value.max_duration !== undefined) {
      filtered = filtered.filter((segment) => segment.duration <= filters.value.max_duration!)
    }

    // Apply downloads filter
    if (filters.value.min_downloads !== undefined) {
      filtered = filtered.filter(
        (segment) => segment.download_count >= filters.value.min_downloads!,
      )
    }

    // Apply sorting
    const reverse = filters.value.order === 'desc'
    switch (filters.value.sort_by) {
      case 'date':
        filtered.sort((a, b) => {
          const dateA = new Date(a.created_at).getTime()
          const dateB = new Date(b.created_at).getTime()
          return reverse ? dateB - dateA : dateA - dateB
        })
        break
      case 'name':
        filtered.sort((a, b) => {
          const nameA = (a.filename || a.title || '').toLowerCase()
          const nameB = (b.filename || b.title || '').toLowerCase()
          return reverse ? nameB.localeCompare(nameA) : nameA.localeCompare(nameB)
        })
        break
      case 'size':
        filtered.sort((a, b) => {
          return reverse ? b.file_size - a.file_size : a.file_size - b.file_size
        })
        break
      case 'duration':
        filtered.sort((a, b) => {
          return reverse ? b.duration - a.duration : a.duration - b.duration
        })
        break
      case 'downloads':
        filtered.sort((a, b) => {
          return reverse ? b.download_count - a.download_count : a.download_count - b.download_count
        })
        break
    }

    return filtered
  })

  // Actions
  const loadVideoSegments = async (videoId: string) => {
    loading.value = true
    error.value = null
    currentVideoId.value = videoId
    isVideoSpecificView.value = true

    try {
      const authStore = useAuthStore()
      const userId = authStore.user?.userId

      if (!userId) {
        throw new Error('User not authenticated')
      }

      const response = await VideoService.getVideoSegments(videoId)
      segments.value = response
      pagination.value.total_count = response.length
      pagination.value.has_more = false
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load segments'
      console.error('Error loading video segments:', err)
    } finally {
      loading.value = false
    }
  }

  const loadAllSegments = async (videoId?: string) => {
    loading.value = true
    error.value = null
    currentVideoId.value = videoId || null
    isVideoSpecificView.value = false

    try {
      const authStore = useAuthStore()
      const userId = authStore.user?.userId

      if (!userId) {
        throw new Error('User not authenticated')
      }

      const params = {
        user_id: userId,
        video_id: videoId,
        sort_by: filters.value.sort_by,
        order: filters.value.order,
        limit: pagination.value.limit,
        offset: pagination.value.offset,
        min_duration: filters.value.min_duration,
        max_duration: filters.value.max_duration,
        min_downloads: filters.value.min_downloads,
      }

      const response = await VideoService.getAllSegments(params)
      segments.value = response.segments
      pagination.value.total_count = response.total_count
      pagination.value.has_more =
        response.page_size > 0 && segments.value.length < response.total_count
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load segments'
      console.error('Error loading all segments:', err)
    } finally {
      loading.value = false
    }
  }

  const downloadSegment = async (segmentId: string) => {
    try {
      const response = await VideoService.downloadSegment(segmentId)

      // Update the segment's download count in the store
      const segment = segments.value.find((s) => s.segment_id === segmentId)
      if (segment) {
        segment.download_count = response.download_count
        segment.last_downloaded_at = new Date().toISOString()
      }

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to download segment'
      console.error('Error downloading segment:', err)
      throw err
    }
  }

  /**
   * Track social media usage for a segment
   * This method will be called when a user indicates they've used a segment in social media
   * Future enhancement: Connect with Instagram/TikTok APIs to automatically track posts
   */
  const trackSocialMediaUsage = async (
    segmentId: string,
    platform: 'instagram' | 'tiktok' | 'youtube' | 'facebook' | 'twitter',
    postData?: {
      post_id?: string
      views?: number
      likes?: number
      shares?: number
      comments?: number
      posted_at?: string
    },
  ) => {
    try {
      // TODO: Implement API call to backend to track social media usage
      // This will store the usage data in the database for analytics

      const segment = segments.value.find((s) => s.segment_id === segmentId)
      if (segment) {
        // Initialize social media usage if it doesn't exist
        if (!segment.social_media_usage) {
          segment.social_media_usage = []
        }

        // Add new social media usage entry
        const newUsage = {
          platform: platform,
          post_id: postData?.post_id,
          post_url: undefined,
          posted_at: postData?.posted_at || new Date().toISOString(),
          views: postData?.views || 0,
          likes: postData?.likes || 0,
          shares: postData?.shares || 0,
          comments: postData?.comments || 0,
          engagement_rate: undefined,
          last_synced: new Date().toISOString(),
        }

        segment.social_media_usage.push(newUsage)

        // TODO: Call backend API to persist this data
        // await VideoService.trackSocialMediaUsage(segmentId, platform, postData)

        console.log(`Tracked ${platform} usage for segment ${segmentId}`)
      }
    } catch (err) {
      console.error('Error tracking social media usage:', err)
      // Don't throw error as this is not critical for core functionality
    }
  }

  /**
   * Get segments that have been used in social media
   * Useful for analytics and understanding which content performs best
   */
  const getSocialMediaSegments = computed(() => {
    return segments.value.filter(
      (segment) => segment.social_media_usage && segment.social_media_usage.length > 0,
    )
  })

  /**
   * Get segments that haven't been used in social media yet
   * Useful for content planning and identifying unused assets
   */
  const getUnusedSegments = computed(() => {
    return segments.value.filter(
      (segment) => !segment.social_media_usage || segment.social_media_usage.length === 0,
    )
  })

  const applyFilters = async (newFilters: Partial<SegmentFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.offset = 0 // Reset pagination when filters change

    if (segments.value.length > 0) {
      // If we have segments loaded, reload with new filters
      if (isVideoSpecificView.value && currentVideoId.value) {
        // For video-specific view, reload video segments and apply filters locally
        await loadVideoSegments(currentVideoId.value)
      } else {
        // For all segments view, reload with new filters
        await loadAllSegments()
      }
    }
  }

  const loadMore = async () => {
    if (!pagination.value.has_more || loading.value) return

    pagination.value.offset += pagination.value.limit
    await loadAllSegments()
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    segments.value = []
    loading.value = false
    error.value = null
    filters.value = {
      sort_by: 'date',
      order: 'desc',
    }
    pagination.value = {
      limit: 20,
      offset: 0,
      total_count: 0,
      has_more: false,
    }
    currentVideoId.value = null
    isVideoSpecificView.value = false
  }

  return {
    // State
    segments,
    loading,
    error,
    filters,
    pagination,
    currentVideoId,
    isVideoSpecificView,

    // Getters
    filteredSegments,
    getSocialMediaSegments,
    getUnusedSegments,

    // Actions
    loadVideoSegments,
    loadAllSegments,
    downloadSegment,
    trackSocialMediaUsage,
    applyFilters,
    loadMore,
    clearError,
    reset,
  }
})
