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
        <div class="editor-layout">
          <!-- Canvas Area -->
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

          <!-- Text Editing Panel -->
          <div v-if="hasActiveText" class="text-editing-panel">
            <div class="panel-header">
              <h5 class="mb-0">
                <KTIcon icon-name="edit" icon-class="fs-4 me-2" />
                Text Properties
              </h5>
            </div>

            <div class="panel-content">
              <!-- Text Content -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Text Content</label>
                <textarea
                  v-model="currentTextContent"
                  @input="updateTextContent"
                  class="form-control"
                  rows="3"
                  placeholder="Enter your text..."
                ></textarea>
              </div>

              <!-- Font Family -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Font Family</label>
                <select v-model="currentFontFamily" @change="updateFontFamily" class="form-select">
                  <option value="Arial">Arial</option>
                  <option value="Helvetica">Helvetica</option>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Verdana">Verdana</option>
                  <option value="Courier New">Courier New</option>
                  <option value="Impact">Impact</option>
                  <option value="Comic Sans MS">Comic Sans MS</option>
                </select>
              </div>

              <!-- Font Size -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Font Size</label>
                <div class="input-group">
                  <input
                    v-model.number="currentFontSize"
                    @input="updateFontSize"
                    type="number"
                    class="form-control"
                    min="8"
                    max="200"
                  />
                  <span class="input-group-text">px</span>
                </div>
                <input
                  v-model.number="currentFontSize"
                  @input="updateFontSize"
                  type="range"
                  class="form-range mt-2"
                  min="8"
                  max="200"
                />
              </div>

              <!-- Font Color -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Font Color</label>
                <div class="color-picker-group">
                  <input
                    v-model="currentFontColor"
                    @input="updateFontColor"
                    type="color"
                    class="form-control form-control-color"
                  />
                  <input
                    v-model="currentFontColor"
                    @input="updateFontColor"
                    type="text"
                    class="form-control ms-2"
                    placeholder="#000000"
                  />
                </div>
              </div>

              <!-- Font Style -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Font Style</label>
                <div class="btn-group w-100" role="group">
                  <button
                    @click="toggleBold"
                    :class="{ active: currentFontWeight === 'bold' }"
                    class="btn btn-outline-secondary"
                  >
                    <strong>B</strong>
                  </button>
                  <button
                    @click="toggleItalic"
                    :class="{ active: currentFontStyle === 'italic' }"
                    class="btn btn-outline-secondary"
                  >
                    <em>I</em>
                  </button>
                </div>
              </div>

              <!-- Background -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Text Background</label>
                <div class="form-check mb-2">
                  <input
                    v-model="hasTextBackground"
                    @change="toggleTextBackground"
                    class="form-check-input"
                    type="checkbox"
                    id="backgroundToggle"
                  />
                  <label class="form-check-label" for="backgroundToggle"> Enable Background </label>
                </div>
                <div v-if="hasTextBackground" class="color-picker-group">
                  <input
                    v-model="currentBackgroundColor"
                    @input="updateBackgroundColor"
                    type="color"
                    class="form-control form-control-color"
                  />
                  <input
                    v-model="currentBackgroundColor"
                    @input="updateBackgroundColor"
                    type="text"
                    class="form-control ms-2"
                    placeholder="#ffffff"
                  />
                </div>
              </div>

              <!-- Opacity -->
              <div class="form-group mb-4">
                <label class="form-label fw-bold">Opacity</label>
                <div class="input-group">
                  <input
                    v-model.number="currentOpacity"
                    @input="updateOpacity"
                    type="number"
                    class="form-control"
                    min="0"
                    max="1"
                    step="0.1"
                  />
                  <span class="input-group-text">%</span>
                </div>
                <input
                  v-model.number="currentOpacity"
                  @input="updateOpacity"
                  type="range"
                  class="form-range mt-2"
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          <!-- Help Text when no text selected -->
          <div v-else-if="isCanvasReady" class="text-editing-panel">
            <div class="panel-content text-center py-5">
              <KTIcon icon-name="information" icon-class="fs-2x text-muted mb-3" />
              <h5 class="text-muted">No Text Selected</h5>
              <p class="text-muted mb-4">
                Click on a text object or add a new one to edit its properties.
              </p>
              <button @click="addNewText" class="btn btn-primary">
                <KTIcon icon-name="plus" icon-class="fs-5" />
                Add Text
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
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

    // Text overlay composable with FFmpeg functions
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
      // FFmpeg translation functions
      extractTextCoordinates,
      convertToFFmpegFilter,
      convertAllTextToFFmpegFilters,
      generateFFmpegCommand,
      canvasToVideoCoordinates,
    } = useTextOverlay()

    // Text editing reactive properties
    const currentTextContent = ref('')
    const currentFontFamily = ref('Arial')
    const currentFontSize = ref(24)
    const currentFontColor = ref('#000000')
    const currentFontWeight = ref('normal')
    const currentFontStyle = ref('normal')
    const hasTextBackground = ref(false)
    const currentBackgroundColor = ref('#ffffff')
    const currentOpacity = ref(1)

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
        1080, // Default video width - could be enhanced to get from segment metadata
        1920, // Default video height - could be enhanced to get from segment metadata
        1080, // max canvas width
        1920, // max canvas height
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

    // Text editing methods
    const updateTextContent = () => {
      if (activeTextObject.value) {
        activeTextObject.value.set('text', currentTextContent.value)
        canvas.value?.renderAll()
      }
    }

    const updateFontFamily = () => {
      if (activeTextObject.value) {
        activeTextObject.value.set('fontFamily', currentFontFamily.value)
        canvas.value?.renderAll()
      }
    }

    const updateFontSize = () => {
      if (activeTextObject.value) {
        activeTextObject.value.set('fontSize', currentFontSize.value)
        canvas.value?.renderAll()
      }
    }

    const updateFontColor = () => {
      if (activeTextObject.value) {
        activeTextObject.value.set('fill', currentFontColor.value)
        canvas.value?.renderAll()
      }
    }

    const toggleBold = () => {
      const newWeight = currentFontWeight.value === 'bold' ? 'normal' : 'bold'
      currentFontWeight.value = newWeight
      if (activeTextObject.value) {
        activeTextObject.value.set('fontWeight', newWeight)
        canvas.value?.renderAll()
      }
    }

    const toggleItalic = () => {
      const newStyle = currentFontStyle.value === 'italic' ? 'normal' : 'italic'
      currentFontStyle.value = newStyle
      if (activeTextObject.value) {
        activeTextObject.value.set('fontStyle', newStyle)
        canvas.value?.renderAll()
      }
    }

    const toggleTextBackground = () => {
      if (activeTextObject.value) {
        if (hasTextBackground.value) {
          activeTextObject.value.set('backgroundColor', currentBackgroundColor.value)
        } else {
          activeTextObject.value.set('backgroundColor', null)
        }
        canvas.value?.renderAll()
      }
    }

    const updateBackgroundColor = () => {
      if (activeTextObject.value && hasTextBackground.value) {
        activeTextObject.value.set('backgroundColor', currentBackgroundColor.value)
        canvas.value?.renderAll()
      }
    }

    const updateOpacity = () => {
      if (activeTextObject.value) {
        activeTextObject.value.set('opacity', currentOpacity.value)
        canvas.value?.renderAll()
      }
    }

    // Watch for active text object changes to sync form values
    watch(activeTextObject, (newTextObj) => {
      if (newTextObj) {
        currentTextContent.value = newTextObj.text || ''
        currentFontFamily.value = newTextObj.fontFamily || 'Arial'
        currentFontSize.value = newTextObj.fontSize || 24
        currentFontColor.value = newTextObj.fill || '#000000'
        currentFontWeight.value = newTextObj.fontWeight || 'normal'
        currentFontStyle.value = newTextObj.fontStyle || 'normal'
        hasTextBackground.value = !!newTextObj.backgroundColor
        currentBackgroundColor.value = newTextObj.backgroundColor || '#ffffff'
        currentOpacity.value = newTextObj.opacity || 1
      }
    })

    // Save text overlays to backend with FFmpeg filter generation
    const saveTextOverlays = async () => {
      if (!canvas.value || !selectedSegment.value) return

      try {
        console.log('🎬 Starting text overlay save process...')
        console.log('📊 Canvas size:', canvasSize.value)
        console.log('📹 Video size:', videoSize.value)
        console.log('⚖️ Scale factors:', scaleFactors.value)

        // 🎯 STEP 1: Generate FFmpeg filters using the coordinate translation system
        const ffmpegFilters = convertAllTextToFFmpegFilters(selectedSegment.value.duration)

        console.log('🎬 Generated FFmpeg Filters:')
        ffmpegFilters.forEach((filter, index) => {
          console.log(`  Filter ${index + 1}: ${filter}`)
        })

        // 🎯 STEP 2: Generate complete FFmpeg command for demonstration
        const ffmpegCommand = generateFFmpegCommand(
          `input_segment_${selectedSegment.value.segment_id}.mp4`,
          `output_segment_${selectedSegment.value.segment_id}.mp4`,
          selectedSegment.value.duration,
        )

        console.log('🎬 Complete FFmpeg Command:')
        console.log(ffmpegCommand)

        // 🎯 STEP 3: Extract detailed overlay data for storage
        const textObjects = canvas.value
          .getObjects()
          .filter((obj: object) => (obj as any).type === 'text')
        const overlays = textObjects.map((obj: object, index: number) => {
          const textObj = obj

          // Use precise coordinate extraction from aCoords
          const coordinates = extractTextCoordinates(textObj)
          const videoCoords = canvasToVideoCoordinates(coordinates.x, coordinates.y)

          const overlay = {
            id: `text_${Date.now()}_${index}`,
            segment_id: selectedSegment.value!.segment_id,

            // Original canvas properties
            canvas_x: coordinates.x,
            canvas_y: coordinates.y,
            canvas_fontSize: textObj.fontSize || 24,

            // Translated video properties (for FFmpeg)
            video_x: Math.round(videoCoords.x),
            video_y: Math.round(videoCoords.y),
            video_fontSize: Math.round(
              (textObj.fontSize || 24) * Math.min(scaleFactors.value.x, scaleFactors.value.y),
            ),

            // Text content and styling
            text: textObj.text || '',
            fontFamily: textObj.fontFamily || 'Arial',
            fontWeight: textObj.fontWeight || 'normal',
            fontStyle: textObj.fontStyle || 'normal',
            color: textObj.fill || '#ffffff',
            backgroundColor: textObj.backgroundColor || null,
            opacity: textObj.opacity || 1,
            rotation: textObj.angle || 0,

            // Text effects
            shadow: textObj.shadow
              ? {
                  enabled: true,
                  color: textObj.shadow.color || '#000000',
                  offsetX: textObj.shadow.offsetX || 0,
                  offsetY: textObj.shadow.offsetY || 0,
                  blur: textObj.shadow.blur || 0,
                }
              : { enabled: false },
            stroke: textObj.stroke
              ? {
                  enabled: true,
                  color: textObj.stroke,
                  width: textObj.strokeWidth || 0,
                }
              : { enabled: false },

            // Timing
            startTime: 0,
            endTime: selectedSegment.value!.duration,

            // Generated FFmpeg filter for this text object
            ffmpeg_filter: ffmpegFilters[index] || '',

            // Metadata
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }

          console.log(`📝 Text ${index + 1} coordinate translation:`)
          console.log(
            `   Canvas: (${coordinates.x}, ${coordinates.y}) → Video: (${overlay.video_x}, ${overlay.video_y})`,
          )
          console.log(`   Font size: ${overlay.canvas_fontSize}px → ${overlay.video_fontSize}px`)

          return overlay
        })

        console.log('💾 Complete overlay data with FFmpeg filters:', overlays)

        // 🎯 STEP 4: Save to backend (overlays with embedded FFmpeg data)
        console.log('💾 Saving enhanced overlay data with FFmpeg filters...')

        await VideoService.saveTextOverlays(selectedSegment.value.segment_id, overlays)

        // Log the complete data for backend integration
        console.log('🎯 FFmpeg Integration Data:')
        console.log({
          segment_id: selectedSegment.value.segment_id,
          ffmpeg_filters: ffmpegFilters,
          ffmpeg_command: ffmpegCommand,
          segment_duration: selectedSegment.value.duration,
          canvas_dimensions: canvasSize.value,
          video_dimensions: videoSize.value,
          scale_factors: scaleFactors.value,
        })

        console.log('✅ Text overlays and FFmpeg filters saved successfully!')
        console.log('🎯 Ready for video processing with precise coordinate translation')

        // Show success notification with detail
        alert(
          `✅ Text Overlays Saved Successfully!\n\n` +
            `Generated ${ffmpegFilters.length} FFmpeg filter(s)\n` +
            `Canvas: ${canvasSize.value.width}×${canvasSize.value.height}\n` +
            `Video: ${videoSize.value.width}×${videoSize.value.height}\n` +
            `Scale: ${scaleFactors.value.x.toFixed(2)}×${scaleFactors.value.y.toFixed(2)}\n\n` +
            `Check console for complete FFmpeg commands!`,
        )
      } catch (error) {
        console.error('❌ Failed to save text overlays:', error)
        alert('❌ Failed to save text overlays. Check console for details.')
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

      // Text editing properties
      currentTextContent,
      currentFontFamily,
      currentFontSize,
      currentFontColor,
      currentFontWeight,
      currentFontStyle,
      hasTextBackground,
      currentBackgroundColor,
      currentOpacity,

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

      // Text editing methods
      updateTextContent,
      updateFontFamily,
      updateFontSize,
      updateFontColor,
      toggleBold,
      toggleItalic,
      toggleTextBackground,
      updateBackgroundColor,
      updateOpacity,
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

.editor-layout {
  display: flex;
  min-height: 500px;
}

.canvas-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px 0 0 8px;
  position: relative;
}

.text-editing-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #dee2e6;
  border-radius: 0 8px 8px 0;
}

.panel-header {
  padding: 15px 20px;
  border-bottom: 1px solid #dee2e6;
  background: #f8f9fa;
}

.panel-content {
  padding: 20px;
  height: 460px;
  overflow-y: auto;
}

.color-picker-group {
  display: flex;
  align-items: center;
}

.form-control-color {
  width: 50px;
  height: 38px;
  padding: 4px;
  border-radius: 6px;
}
</style>
