<template>
  <div class="text-overlay-demo-simple">
    <!-- Header -->
    <div class="demo-header mb-6">
      <h1 class="display-6 fw-bold text-gray-900 mb-2">Text Overlay Editor</h1>
      <p class="text-muted fs-5 mb-0">
        Design text overlays for your video segments using Fabric.js canvas editor
      </p>
    </div>

    <!-- Segment Selection -->
    <div class="segment-selection card mb-6">
      <div class="card-header">
        <h3 class="card-title">Select Video Segment</h3>
      </div>
      <div class="card-body">
        <div v-if="loadingSegments" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading segments...</span>
          </div>
          <p class="text-muted mt-3">Loading your video segments...</p>
        </div>

        <div v-else-if="segments.length === 0" class="text-center py-4">
          <KTIcon icon-name="video" icon-class="fs-2x text-muted mb-3" />
          <h5 class="text-muted">No Segments Found</h5>
          <p class="text-muted">
            Upload and process videos to create segments for text overlay editing.
          </p>
        </div>

        <div v-else class="row g-4">
          <div class="col-md-6">
            <label class="form-label">Choose a segment to edit:</label>
            <select v-model="selectedSegmentId" class="form-select" @change="onSegmentSelected">
              <option value="">Select a segment...</option>
              <option
                v-for="segment in segments"
                :key="segment.segment_id"
                :value="segment.segment_id"
              >
                {{ segment.title || `Segment ${segment.segment_number}` }} ({{
                  formatDuration(segment.duration)
                }})
              </option>
            </select>
          </div>
          <div class="col-md-6" v-if="selectedSegment">
            <label class="form-label">Segment Details:</label>
            <div class="bg-light p-3 rounded">
              <small class="text-muted">
                <strong>Video ID:</strong> {{ selectedSegment.video_id }}<br />
                <strong>Duration:</strong> {{ formatDuration(selectedSegment.duration) }}<br />
                <strong>File Size:</strong> {{ formatFileSize(selectedSegment.file_size) }}
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Thumbnail Generation -->
    <div v-if="selectedSegment && !thumbnailUrl" class="thumbnail-generation card mb-6">
      <div class="card-header">
        <h3 class="card-title">Generate Thumbnail</h3>
      </div>
      <div class="card-body text-center">
        <div v-if="!generatingThumbnail" class="py-4">
          <KTIcon icon-name="image" icon-class="fs-2x text-muted mb-3" />
          <h5>Thumbnail Required</h5>
          <p class="text-muted mb-4">
            Generate a thumbnail image to design text overlays on this segment.
          </p>
          <button @click="generateThumbnail" class="btn btn-primary">
            <KTIcon icon-name="image" icon-class="fs-4" />
            Generate Thumbnail
          </button>
        </div>

        <div v-else class="py-4">
          <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">Generating...</span>
          </div>
          <h5>Generating Thumbnail...</h5>
          <p class="text-muted">This may take a few moments.</p>
        </div>
      </div>
    </div>

    <!-- Status Panel -->
    <div v-if="selectedSegment && thumbnailUrl" class="status-panel card mb-6">
      <div class="card-header">
        <h3 class="card-title">Canvas Status</h3>
      </div>
      <div class="card-body">
        <div class="row g-4">
          <div class="col-md-3">
            <div class="status-item">
              <span class="status-label">Canvas Ready:</span>
              <span :class="isCanvasReady ? 'text-success' : 'text-warning'">
                {{ isCanvasReady ? '✅ Ready' : '⏳ Loading...' }}
              </span>
            </div>
          </div>
          <div class="col-md-3">
            <div class="status-item">
              <span class="status-label">Text Objects:</span>
              <span class="text-info">{{ textObjectCount }}</span>
            </div>
          </div>
          <div class="col-md-3">
            <div class="status-item">
              <span class="status-label">Active Text:</span>
              <span :class="hasActiveText ? 'text-success' : 'text-muted'">
                {{ hasActiveText ? 'Selected' : 'None' }}
              </span>
            </div>
          </div>
          <div class="col-md-3">
            <div class="status-item">
              <span class="status-label">Canvas Size:</span>
              <span class="text-info">{{ canvasSize.width }}×{{ canvasSize.height }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Editor Area -->
    <div v-if="selectedSegment && thumbnailUrl" class="editor-area card">
      <div class="card-header">
        <h3 class="card-title">
          Text Overlay Editor
          <span class="badge badge-light-primary ms-2">
            {{ selectedSegment.title || `Segment ${selectedSegment.segment_number}` }}
          </span>
        </h3>
        <div class="card-toolbar">
          <div class="btn-group" role="group">
            <button @click="addNewText" class="btn btn-sm btn-primary" :disabled="!isCanvasReady">
              <KTIcon icon-name="plus" icon-class="fs-5" />
              Add Text
            </button>
            <button
              @click="deleteSelectedText"
              class="btn btn-sm btn-danger"
              :disabled="!hasActiveText"
            >
              <KTIcon icon-name="trash" icon-class="fs-5" />
              Delete
            </button>
            <button @click="duplicateText" class="btn btn-sm btn-info" :disabled="!hasActiveText">
              <KTIcon icon-name="copy" icon-class="fs-5" />
              Duplicate
            </button>
            <button
              @click="saveTextOverlays"
              class="btn btn-sm btn-success"
              :disabled="!isCanvasReady || textObjectCount === 0"
            >
              <KTIcon icon-name="document-save" icon-class="fs-5" />
              Save Overlays
            </button>
          </div>
        </div>
      </div>

      <div class="card-body p-0">
        <div class="canvas-container">
          <!-- Canvas will be mounted here -->
          <canvas
            ref="fabricCanvasEl"
            :width="canvasSize.width"
            :height="canvasSize.height"
            class="fabric-canvas"
            :style="{ opacity: isCanvasReady ? 1 : 0.3 }"
          />

          <!-- Loading overlay -->
          <div v-if="!isCanvasReady" class="loading-overlay">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading canvas...</span>
            </div>
            <p class="text-muted mt-3">Initializing Fabric.js canvas...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useTextOverlay } from '@/composables/useTextOverlay'
import { VideoService } from '@/core/services/VideoService'
import { useAuthStore } from '@/stores/auth'
import type { VideoSegment } from '@/stores/segments'

export default defineComponent({
  name: 'TextOverlayDemoSimple',
  setup() {
    // Canvas element reference
    const fabricCanvasEl = ref<HTMLCanvasElement | null>(null)

    // Segment data
    const segments = ref<VideoSegment[]>([])
    const selectedSegmentId = ref<string>('')
    const loadingSegments = ref(true)
    const generatingThumbnail = ref(false)
    const thumbnailUrl = ref<string>('')

    // Text overlay composable
    const {
      canvas,
      isCanvasReady,
      activeTextObject,
      hasActiveText,
      canvasSize,
      videoSize,
      scaleFactors,
      initializeCanvas,
      addTextObject,
      removeTextObject,
      dispose,
    } = useTextOverlay()

    // Auth store
    const authStore = useAuthStore()

    // Computed properties
    const selectedSegment = computed(() => {
      return segments.value.find((s) => s.segment_id === selectedSegmentId.value)
    })

    const textObjectCount = computed(() => {
      if (!canvas.value) return 0
      return canvas.value.getObjects().filter((obj: { type: string }) => obj.type === 'text').length
    })

    // Load user segments
    const loadSegments = async () => {
      try {
        loadingSegments.value = true

        const userId = authStore.user?.userId
        if (!userId) {
          console.error('User not authenticated')
          return
        }

        // Get all segments for the user
        const response = await VideoService.getAllSegments({
          user_id: userId,
          sort_by: 'date',
          order: 'desc',
          limit: 50,
          offset: 0,
        })

        segments.value = response.segments || []
        console.log('✅ Loaded segments:', segments.value.length)
      } catch (error) {
        console.error('❌ Failed to load segments:', error)
      } finally {
        loadingSegments.value = false
      }
    }

    // Generate thumbnail for selected segment
    const generateThumbnail = async () => {
      if (!selectedSegment.value) return

      try {
        generatingThumbnail.value = true
        console.log('🖼️ Generating thumbnail for segment:', selectedSegment.value.segment_id)

        // Call backend API to generate thumbnail
        const response = await VideoService.generateSegmentThumbnail(
          selectedSegment.value.segment_id,
        )
        thumbnailUrl.value = response.thumbnail_url

        console.log('✅ Thumbnail generated:', thumbnailUrl.value)

        // Initialize canvas with the thumbnail
        await initializeEditor()
      } catch (error) {
        console.error('❌ Failed to generate thumbnail:', error)
        // TODO: Show user-friendly error message
      } finally {
        generatingThumbnail.value = false
      }
    }

    // Handle segment selection
    const onSegmentSelected = () => {
      if (selectedSegment.value) {
        console.log('📹 Selected segment:', selectedSegment.value)
        // Reset thumbnail and canvas
        thumbnailUrl.value = ''
        if (canvas.value) {
          canvas.value.clear()
        }
        // Check if segment already has a thumbnail
        if (selectedSegment.value.thumbnail_url) {
          thumbnailUrl.value = selectedSegment.value.thumbnail_url
          initializeEditor()
        }
      }
    }

    // Canvas initialization
    const initializeEditor = async () => {
      if (!thumbnailUrl.value || !selectedSegment.value) return

      await nextTick()

      // Add a small delay to ensure DOM is fully rendered
      await new Promise((resolve) => setTimeout(resolve, 100))

      if (!fabricCanvasEl.value) {
        console.error('❌ Canvas element not found')
        return
      }

      console.log('🎨 Initializing Text Overlay Editor')
      console.log('🖼️ Using thumbnail:', thumbnailUrl.value)

      await initializeCanvas(
        fabricCanvasEl.value,
        thumbnailUrl.value,
        1920, // Default video width - could be enhanced to get from segment metadata
        1080, // Default video height - could be enhanced to get from segment metadata
        800, // max canvas width
        450, // max canvas height
      )
    }

    // Text object management
    const addNewText = async () => {
      const textObj = await addTextObject('Sample Text')
      if (textObj) {
        console.log('✅ Text object added successfully')
      }
    }

    const deleteSelectedText = () => {
      if (activeTextObject.value) {
        removeTextObject(activeTextObject.value)
        console.log('🗑️ Text object deleted')
      }
    }

    const duplicateText = async () => {
      if (!activeTextObject.value) return

      const originalText = activeTextObject.value
      const newText = await addTextObject(
        originalText.text || 'Duplicated Text',
        (originalText.left || 0) + 20,
        (originalText.top || 0) + 20,
        {
          fontSize: originalText.fontSize,
          fontFamily: originalText.fontFamily,
          fill: originalText.fill,
        },
      )

      if (newText) {
        console.log('📋 Text object duplicated')
      }
    }

    // Save text overlays to backend
    const saveTextOverlays = async () => {
      if (!canvas.value || !selectedSegment.value) return

      try {
        const textObjects = canvas.value.getObjects().filter((obj: any) => obj.type === 'text')
        const overlays = textObjects.map((obj: any) => {
          const textObj = obj
          // Extract text overlay data from Fabric.js object
          // This would use the coordinate conversion system from the requirements
          return {
            id: `text_${Date.now()}_${Math.random()}`,
            segment_id: selectedSegment.value!.segment_id,
            text: textObj.text || '',
            x: textObj.left || 0,
            y: textObj.top || 0,
            width: textObj.width || 0,
            height: textObj.height || 0,
            fontSize: textObj.fontSize || 24,
            fontFamily: textObj.fontFamily || 'Arial',
            fontWeight: textObj.fontWeight || 'normal',
            fontStyle: textObj.fontStyle || 'normal',
            color: textObj.fill || '#ffffff',
            backgroundColor: textObj.backgroundColor || null,
            opacity: textObj.opacity || 1,
            rotation: textObj.angle || 0,
            scaleX: textObj.scaleX || 1,
            scaleY: textObj.scaleY || 1,
            shadow: obj.shadow
              ? {
                  enabled: true,
                  color: obj.shadow.color || '#000000',
                  offsetX: obj.shadow.offsetX || 0,
                  offsetY: obj.shadow.offsetY || 0,
                  blur: obj.shadow.blur || 0,
                }
              : { enabled: false },
            stroke: obj.stroke
              ? {
                  enabled: true,
                  color: obj.stroke,
                  width: obj.strokeWidth || 0,
                }
              : { enabled: false },
            startTime: 0, // Default to start of segment
            endTime: selectedSegment.value!.duration, // Default to end of segment
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        })

        console.log('💾 Saving text overlays:', overlays)

        // Call backend API to save overlays
        await VideoService.saveTextOverlays(selectedSegment.value.segment_id, overlays)

        console.log('✅ Text overlays saved successfully')
        // TODO: Show success notification
      } catch (error) {
        console.error('❌ Failed to save text overlays:', error)
        // TODO: Show error notification
      }
    }

    // Utility functions
    const formatDuration = (seconds: number): string => {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatFileSize = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Lifecycle
    onMounted(() => {
      loadSegments()
    })

    onUnmounted(() => {
      dispose()
    })

    return {
      // Refs
      fabricCanvasEl,

      // Segment data
      segments,
      selectedSegmentId,
      selectedSegment,
      loadingSegments,
      generatingThumbnail,
      thumbnailUrl,

      // Canvas state
      canvas,
      isCanvasReady,
      activeTextObject,
      hasActiveText,
      canvasSize,
      videoSize,
      scaleFactors,

      // Computed
      textObjectCount,

      // Methods
      onSegmentSelected,
      generateThumbnail,
      addNewText,
      deleteSelectedText,
      duplicateText,
      saveTextOverlays,
      formatDuration,
      formatFileSize,
    }
  },
})
</script>

<style scoped>
.text-overlay-demo-simple {
  padding: 20px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.status-label {
  font-weight: 500;
  color: #6c757d;
}

.canvas-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 20px;
  position: relative;
}

.fabric-canvas {
  border: 2px solid #dee2e6;
  border-radius: 8px;
  background: white;
  transition: opacity 0.3s ease;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  z-index: 10;
}

.instructions ul li {
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.instructions ul li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #28a745;
  font-weight: bold;
}
</style>
