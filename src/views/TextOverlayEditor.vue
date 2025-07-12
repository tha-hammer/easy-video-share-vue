<template>
  <div class="text-overlay-editor">
    <!-- Header -->
    <div class="editor-header mb-6">
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
          <button
            @click="generateThumbnail"
            class="btn btn-primary"
            :disabled="generatingThumbnail"
          >
            <KTIcon
              :icon-name="generatingThumbnail ? 'hourglass' : 'image'"
              :icon-class="generatingThumbnail ? 'fs-4 fa-spin' : 'fs-4'"
            />
            {{ generatingThumbnail ? 'Generating...' : 'Generate Thumbnail' }}
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

    <!-- Video Processing Status -->
    <div v-if="processingVideo" class="processing-status card mb-6">
      <div class="card-header">
        <h3 class="card-title">
          <KTIcon icon-name="hourglass" icon-class="fs-2x text-primary me-2" />
          Processing Video with Text Overlays
        </h3>
      </div>
      <div class="card-body">
        <div class="d-flex align-items-center mb-4">
          <div class="spinner-border text-primary me-3" role="status">
            <span class="visually-hidden">Processing...</span>
          </div>
          <div class="flex-grow-1">
            <h6 class="mb-1">{{ processingStatus }}</h6>
            <div class="progress">
              <div
                class="progress-bar progress-bar-striped progress-bar-animated"
                role="progressbar"
                :style="{ width: `${processingProgress}%` }"
                :aria-valuenow="processingProgress"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ processingProgress }}%
              </div>
            </div>
          </div>
        </div>
        <div class="alert alert-info">
          <KTIcon icon-name="information" icon-class="fs-4 me-2" />
          <strong>Processing your video...</strong>
          <p class="mb-0 mt-2">
            This process applies your text overlays to the video using FFmpeg. Processing time
            depends on video length and complexity of text overlays.
          </p>
        </div>
      </div>
    </div>

    <!-- Final Video Player -->
    <div v-if="processedVideoUrl && !processingVideo" class="final-video card mb-6">
      <div class="card-header">
        <h3 class="card-title">
          <KTIcon icon-name="video" icon-class="fs-2x text-success me-2" />
          Final Video with Text Overlays
        </h3>
        <div class="card-toolbar">
          <button @click="downloadProcessedVideo" class="btn btn-sm btn-success">
            <KTIcon icon-name="download" icon-class="fs-5" />
            Download Video
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="final-video-container">
          <video :src="processedVideoUrl" controls preload="metadata" class="final-video-player">
            Your browser does not support the video tag.
          </video>
        </div>
        <div class="mt-4 alert alert-success">
          <KTIcon icon-name="check-circle" icon-class="fs-4 me-2" />
          <strong>Success!</strong> Your video has been processed with text overlays.
          <ul class="mt-2 mb-0">
            <li>Text overlays have been permanently applied to the video</li>
            <li>The video is ready for download or sharing</li>
            <li>All text positioning and styling has been preserved</li>
          </ul>
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
              :disabled="!isCanvasReady || textObjectCount === 0 || processingVideo"
            >
              <KTIcon
                :icon-name="processingVideo ? 'hourglass' : 'document-save'"
                icon-class="fs-5"
              />
              {{ processingVideo ? 'Processing...' : 'Save & Process' }}
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
              <!-- Text Content - Always Visible -->
              <div class="form-group mb-3">
                <label class="form-label fw-bold">Text Content</label>
                <textarea
                  v-model="currentTextContent"
                  @input="updateTextContent"
                  class="form-control"
                  rows="2"
                  placeholder="Enter your text..."
                ></textarea>
              </div>

              <!-- Font Family - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('font-family')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['font-family'] }"
                >
                  <KTIcon icon-name="font" icon-class="fs-5 me-2" />
                  Font Family: {{ currentFontFamily }}
                  <KTIcon
                    :icon-name="collapsedSections['font-family'] ? 'arrow-down' : 'arrow-up'"
                    icon-class="fs-5 ms-auto"
                  />
                </button>
                <div v-show="collapsedSections['font-family']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
                    <select
                      v-model="currentFontFamily"
                      @change="updateFontFamily"
                      class="form-select"
                    >
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
                </div>
              </div>

              <!-- Font Size - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('font-size')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['font-size'] }"
                >
                  <KTIcon icon-name="text" icon-class="fs-5 me-2" />
                  Font Size: {{ currentFontSize }}px
                  <KTIcon
                    :icon-name="collapsedSections['font-size'] ? 'arrow-down' : 'arrow-up'"
                    icon-class="fs-5 ms-auto"
                  />
                </button>
                <div v-show="collapsedSections['font-size']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
                    <div class="input-group mb-2">
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
                      class="form-range"
                      min="8"
                      max="200"
                    />
                  </div>
                </div>
              </div>

              <!-- Font Color - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('font-color')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['font-color'] }"
                >
                  <KTIcon icon-name="palette" icon-class="fs-5 me-2" />
                  Font Color
                  <div
                    class="ms-auto rounded"
                    :style="{
                      backgroundColor: currentFontColor,
                      width: '20px',
                      height: '20px',
                      border: '1px solid #dee2e6',
                    }"
                  ></div>
                </button>
                <div v-show="collapsedSections['font-color']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
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
                </div>
              </div>

              <!-- Font Style - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('font-style')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['font-style'] }"
                >
                  <KTIcon icon-name="text" icon-class="fs-5 me-2" />
                  Font Style
                  <span class="ms-auto">
                    <span v-if="currentFontWeight === 'bold'" class="badge bg-primary me-1">B</span>
                    <span v-if="currentFontStyle === 'italic'" class="badge bg-primary">I</span>
                  </span>
                </button>
                <div v-show="collapsedSections['font-style']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
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
                </div>
              </div>

              <!-- Background - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('background')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['background'] }"
                >
                  <KTIcon icon-name="background" icon-class="fs-5 me-2" />
                  Text Background
                  <span class="ms-auto">
                    <span v-if="hasTextBackground" class="badge bg-success">ON</span>
                    <span v-if="!hasTextBackground" class="badge bg-secondary">OFF</span>
                  </span>
                </button>
                <div v-show="collapsedSections['background']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
                    <div class="form-check mb-2">
                      <input
                        v-model="hasTextBackground"
                        @change="toggleTextBackground"
                        class="form-check-input"
                        type="checkbox"
                        id="backgroundToggle"
                      />
                      <label class="form-check-label" for="backgroundToggle">
                        Enable Background
                      </label>
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
                </div>
              </div>

              <!-- Opacity - Collapsible -->
              <div class="form-group mb-2">
                <button
                  @click="toggleCollapse('opacity')"
                  class="btn btn-outline-secondary btn-sm w-100 text-start"
                  :class="{ collapsed: !collapsedSections['opacity'] }"
                >
                  <KTIcon icon-name="transparency" icon-class="fs-5 me-2" />
                  Opacity: {{ Math.round(currentOpacity * 100) }}%
                  <KTIcon
                    :icon-name="collapsedSections['opacity'] ? 'arrow-down' : 'arrow-up'"
                    icon-class="fs-5 ms-auto"
                  />
                </button>
                <div v-show="collapsedSections['opacity']" class="collapse-content mt-2">
                  <div class="p-2 border rounded bg-light">
                    <div class="input-group mb-2">
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
                      class="form-range"
                      min="0"
                      max="1"
                      step="0.1"
                    />
                  </div>
                </div>
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
  name: 'TextOverlayEditor',
  setup() {
    // Canvas element reference
    const fabricCanvasEl = ref<HTMLCanvasElement | null>(null)

    // Segment data
    const segments = ref<VideoSegment[]>([])
    const selectedSegmentId = ref<string>('')
    const loadingSegments = ref(true)
    const generatingThumbnail = ref(false)
    const thumbnailUrl = ref<string>('')

    // Video processing state
    const processingVideo = ref(false)
    const processingStatus = ref<string>('')
    const processingJobId = ref<string>('')
    const processingProgress = ref(0)
    const processedVideoUrl = ref<string>('')
    const processingError = ref<string>('')

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
      extractTextOverlaysData,
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

    // Collapsible sections state
    const collapsedSections = ref<Record<string, boolean>>({
      'font-family': true,
      'font-size': true,
      'font-color': true,
      'font-style': true,
      background: true,
      opacity: true,
    })

    // Toggle collapse function
    const toggleCollapse = (section: string) => {
      if (section in collapsedSections.value) {
        collapsedSections.value[section] = !collapsedSections.value[section]
      }
    }

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
      if (!selectedSegment.value || generatingThumbnail.value) {
        console.log('⚠️ Skipping thumbnail generation - already in progress or no segment selected')
        return
      }

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

        // Show user-friendly error message
        alert(
          `❌ Thumbnail Generation Failed\n\n` +
            `Error: ${error instanceof Error ? error.message : 'Unknown error'}\n\n` +
            `Please try again or contact support if the issue persists.`,
        )
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

    // Dynamic canvas sizing with viewport constraints
    const calculateCanvasSize = () => {
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
      }

      // Check if we're on mobile (layout changes to vertical)
      const isMobile = viewport.width <= 768
      const isTablet = viewport.width > 768 && viewport.width <= 1024

      // Video aspect ratio (vertical format: 9:16)
      const videoAspectRatio = 1080 / 1920 // 0.5625

      let availableWidth, availableHeight, textPanelWidth

      if (isMobile) {
        // Mobile: vertical layout, text panel below canvas (more compact with collapsible design)
        textPanelWidth = 0 // No side panel on mobile
        const margins = 40 // Reduced margins for mobile
        availableWidth = viewport.width - margins
        availableHeight = viewport.height - 500 // Reduced space needed for compact collapsible panel
      } else if (isTablet) {
        // Tablet: horizontal layout with smaller text panel
        textPanelWidth = 280
        const margins = 60
        availableWidth = viewport.width - textPanelWidth - margins
        availableHeight = viewport.height - 400
      } else {
        // Desktop: horizontal layout with full text panel
        textPanelWidth = 320
        const margins = 80
        availableWidth = viewport.width - textPanelWidth - margins
        availableHeight = viewport.height - 400
      }

      // Calculate maximum canvas size that fits in viewport
      let maxCanvasWidth = Math.min(availableWidth, isMobile ? 600 : 800) // Smaller max on mobile
      let maxCanvasHeight = Math.min(availableHeight, isMobile ? 800 : 1200) // Smaller max on mobile

      // Ensure minimum usable size
      maxCanvasWidth = Math.max(maxCanvasWidth, isMobile ? 300 : 400)
      maxCanvasHeight = Math.max(maxCanvasHeight, isMobile ? 400 : 600)

      // Calculate canvas size maintaining aspect ratio
      let canvasWidth = maxCanvasWidth
      let canvasHeight = maxCanvasWidth / videoAspectRatio

      // If height exceeds available space, scale down
      if (canvasHeight > maxCanvasHeight) {
        canvasHeight = maxCanvasHeight
        canvasWidth = maxCanvasHeight * videoAspectRatio
      }

      // Ensure width doesn't exceed available space
      if (canvasWidth > maxCanvasWidth) {
        canvasWidth = maxCanvasWidth
        canvasHeight = maxCanvasWidth / videoAspectRatio
      }

      return {
        width: Math.floor(canvasWidth),
        height: Math.floor(canvasHeight),
      }
    }

    // Canvas initialization with dynamic sizing
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

      // Calculate dynamic canvas size based on viewport
      const dynamicCanvasSize = calculateCanvasSize()
      console.log('📐 Dynamic canvas size:', dynamicCanvasSize)

      await initializeCanvas(
        fabricCanvasEl.value,
        thumbnailUrl.value,
        1080, // Video width (original)
        1920, // Video height (original)
        dynamicCanvasSize.width, // Dynamic max canvas width
        dynamicCanvasSize.height, // Dynamic max canvas height
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
        currentFontColor.value =
          (typeof newTextObj.fill === 'string' ? newTextObj.fill : '#000000') || '#000000'
        currentFontWeight.value =
          (typeof newTextObj.fontWeight === 'string'
            ? newTextObj.fontWeight
            : String(newTextObj.fontWeight)) || 'normal'
        currentFontStyle.value = newTextObj.fontStyle || 'normal'
        hasTextBackground.value = !!newTextObj.backgroundColor
        currentBackgroundColor.value =
          (typeof newTextObj.backgroundColor === 'string'
            ? newTextObj.backgroundColor
            : '#ffffff') || '#ffffff'
        currentOpacity.value = newTextObj.opacity || 1
      }
    })

    // Poll processing status until complete
    const pollProcessingStatus = async (jobId: string) => {
      const maxAttempts = 60 // 5 minutes with 5-second intervals
      let attempts = 0

      const poll = async () => {
        try {
          attempts++
          const status = await VideoService.getVideoProcessingStatus(jobId)

          console.log(`📊 Processing status check ${attempts}/${maxAttempts}:`, status)

          processingStatus.value = status.status
          processingProgress.value = status.progress || 0

          if (status.status === 'COMPLETED') {
            console.log('✅ Video processing completed successfully!')
            processingVideo.value = false

            // Get the processed video URL from the job status response
            try {
              if (status.output_urls && status.output_urls.length > 0) {
                // Use the first processed video URL from the job status response
                processedVideoUrl.value = status.output_urls[0]
                console.log('🎥 Processed video URL from job status:', processedVideoUrl.value)

                // Show success notification
                alert(
                  `🎉 Video Processing Complete!\n\n` +
                    `✅ Text overlays applied successfully\n` +
                    `🎥 Final video is ready for preview\n` +
                    `⏱️ Processing time: ${Math.round((attempts * 5) / 60)} minutes\n\n` +
                    `You can now preview or download the final video!`,
                )
              } else {
                throw new Error('No processed video URLs found in job status response')
              }
            } catch (urlError) {
              console.error('❌ Failed to get processed video URL:', urlError)
              processingError.value = 'Failed to get processed video URL'
            }
          } else if (status.status === 'FAILED') {
            console.error('❌ Video processing failed:', status.error_message)
            processingVideo.value = false
            processingError.value = status.error_message || 'Video processing failed'

            alert(
              `❌ Video Processing Failed\n\n` +
                `Error: ${status.error_message || 'Unknown error'}\n` +
                `Please try again or contact support.`,
            )
          } else if (attempts >= maxAttempts) {
            console.error('❌ Processing timeout - exceeded maximum attempts')
            processingVideo.value = false
            processingError.value = 'Processing timeout'

            alert(
              `⏰ Processing Timeout\n\n` +
                `Video processing is taking longer than expected.\n` +
                `Please check back later or contact support.`,
            )
          } else {
            // Continue polling
            setTimeout(poll, 5000) // Poll every 5 seconds
          }
        } catch (error) {
          console.error('❌ Error checking processing status:', error)
          attempts++

          if (attempts < maxAttempts) {
            setTimeout(poll, 5000) // Retry after 5 seconds
          } else {
            processingVideo.value = false
            processingError.value = 'Failed to check processing status'
          }
        }
      }

      // Start polling
      poll()
    }

    // Save text overlays to backend with FFmpeg filter generation
    const saveTextOverlays = async () => {
      if (!canvas.value || !selectedSegment.value) return

      try {
        console.log('🎬 Starting text overlay save process...')
        console.log('📊 Canvas size:', canvasSize.value)
        console.log('📹 Video size:', videoSize.value)
        console.log('⚖️ Scale factors:', scaleFactors.value)

        // 🎯 STEP 1: Extract overlay data for backend processing
        const overlayData = extractTextOverlaysData(selectedSegment.value.segment_id)

        console.log('🎯 Extracted overlay data:')
        overlayData.forEach((overlay, index) => {
          console.log(`  Overlay ${index + 1}:`, overlay)
        })

        // 🎯 STEP 2: Save overlay data to backend
        console.log('💾 Saving overlay data to backend...')
        await VideoService.saveTextOverlays(selectedSegment.value.segment_id, overlayData)

        console.log('✅ Text overlays saved successfully!')

        // 🎯 STEP 3: Process the video with text overlays using overlay objects
        console.log('🎬 Starting video processing with text overlays...')
        processingVideo.value = true
        processingStatus.value = 'Processing video with text overlays...'

        try {
          const processResult = await VideoService.processSegmentWithTextOverlayObjects(
            selectedSegment.value.segment_id,
            overlayData,
          )

          console.log('🎬 Video processing job started:', processResult)
          processingJobId.value = processResult.job_id

          // Start polling for processing status
          await pollProcessingStatus(processResult.job_id)
        } catch (error) {
          console.error('❌ Video processing failed:', error)
          processingStatus.value = 'Video processing failed'
          processingVideo.value = false

          const errorMessage = error instanceof Error ? error.message : 'Unknown error'

          // Show error but also success for overlay saving
          alert(
            `✅ Text Overlays Saved Successfully!\n` +
              `❌ Video Processing Failed: ${errorMessage}\n\n` +
              `Generated ${overlayData.length} text overlay(s)\n` +
              `Canvas: ${canvasSize.value.width}×${canvasSize.value.height}\n` +
              `Video: ${videoSize.value.width}×${videoSize.value.height}\n` +
              `Scale: ${scaleFactors.value.x.toFixed(2)}×${scaleFactors.value.y.toFixed(2)}\n\n` +
              `Check console for complete FFmpeg commands!`,
          )
        }
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

    // Debounced window resize handler for dynamic canvas sizing
    let resizeTimeout: NodeJS.Timeout | null = null

    const handleWindowResize = () => {
      // Clear existing timeout
      if (resizeTimeout) {
        clearTimeout(resizeTimeout)
      }

      // Debounce resize events to prevent excessive recalculations
      resizeTimeout = setTimeout(() => {
        if (isCanvasReady.value && canvas.value) {
          console.log('🔄 Window resized, recalculating canvas size...')
          const newCanvasSize = calculateCanvasSize()

          // Update canvas dimensions
          canvas.value.setDimensions({
            width: newCanvasSize.width,
            height: newCanvasSize.height,
          })

          // Update reactive canvas size
          canvasSize.value = newCanvasSize

          console.log('✅ Canvas resized to:', newCanvasSize)
        }
      }, 250) // 250ms debounce delay
    }

    // Lifecycle
    onMounted(() => {
      loadSegments()

      // Add window resize listener
      window.addEventListener('resize', handleWindowResize)
    })

    onUnmounted(() => {
      dispose()

      // Clear resize timeout
      if (resizeTimeout) {
        clearTimeout(resizeTimeout)
      }

      // Remove window resize listener
      window.removeEventListener('resize', handleWindowResize)
    })

    // Download processed video
    const downloadProcessedVideo = async () => {
      if (!processedVideoUrl.value) {
        alert('No processed video available for download. Please process the video first.')
        return
      }

      try {
        console.log('📥 Downloading processed video...')

        // Use the processed video URL directly from the job status response
        const link = document.createElement('a')
        link.href = processedVideoUrl.value
        link.download = `processed_video_${selectedSegment.value?.segment_id || 'segment'}.mp4`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        console.log('📥 Download initiated for processed video')
      } catch (error) {
        console.error('❌ Download failed:', error)
        alert('Failed to download video. Please try again.')
      }
    }

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

      // Video processing state
      processingVideo,
      processingStatus,
      processingJobId,
      processingProgress,
      processedVideoUrl,
      processingError,

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
      downloadProcessedVideo,
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

      // Collapsible methods
      toggleCollapse,
      collapsedSections,
    }
  },
})
</script>

<style scoped>
.text-overlay-editor {
  padding: 20px;
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
  gap: 0;
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
  min-width: 0; /* Allow flex item to shrink below content size */
  overflow: hidden; /* Prevent canvas from overflowing */
}

.text-editing-panel {
  width: 320px;
  min-width: 320px; /* Prevent panel from shrinking */
  background: white;
  border-left: 1px solid #dee2e6;
  border-radius: 0 8px 8px 0;
  overflow-y: auto; /* Allow scrolling if content is too tall */
}

/* Mobile responsive design */
@media (max-width: 768px) {
  .editor-layout {
    flex-direction: column;
    min-height: auto;
    gap: 0;
  }

  .canvas-container {
    border-radius: 8px 8px 0 0;
    padding: 10px;
    min-height: 350px;
    max-height: 65vh; /* Give more space to canvas */
  }

  .text-editing-panel {
    width: 100%;
    min-width: 100%;
    border-left: none;
    border-top: 1px solid #dee2e6;
    border-radius: 0 0 8px 8px;
    max-height: 35vh; /* Reduced height for collapsible design */
  }

  .panel-content {
    height: auto;
    max-height: calc(35vh - 60px); /* Account for panel header */
    padding: 10px;
    overflow-y: auto;
  }

  .fabric-canvas {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  /* Improve touch interactions on mobile */
  .btn {
    min-height: 44px; /* iOS recommended touch target size */
    padding: 8px 16px;
  }

  .form-control {
    min-height: 44px;
  }

  /* Collapsible button styling for mobile */
  .btn[data-bs-toggle='collapse'] {
    font-size: 14px;
    padding: 8px 12px;
  }

  /* Collapse content styling */
  .collapse .p-2 {
    padding: 8px !important;
  }

  /* Compact form groups */
  .form-group {
    margin-bottom: 8px;
  }

  /* Smaller textarea for mobile */
  textarea.form-control {
    rows: 1;
    min-height: 44px;
  }
}

/* Tablet responsive design */
@media (min-width: 769px) and (max-width: 1024px) {
  .text-editing-panel {
    width: 280px;
    min-width: 280px;
  }

  .canvas-container {
    padding: 15px;
  }
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

/* Video processing styles */
.processing-status {
  border-left: 4px solid #007bff;
}

.processing-status .progress {
  height: 20px;
  background-color: #f8f9fa;
}

.processing-status .progress-bar {
  font-size: 12px;
  line-height: 20px;
}

/* Final video player styles */
.final-video {
  border-left: 4px solid #28a745;
}

.final-video-container {
  display: flex;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  padding: 20px;
}

.final-video-player {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Processing status animations */
.processing-status .spinner-border {
  width: 24px;
  height: 24px;
}

.processing-status .alert {
  border-left: 4px solid #17a2b8;
}

/* Success alert styling */
.final-video .alert-success {
  border-left: 4px solid #28a745;
}

.final-video .alert-success ul {
  padding-left: 20px;
}

.final-video .alert-success li {
  margin-bottom: 4px;
}

/* Button state styles */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.processing {
  position: relative;
  overflow: hidden;
}

.btn.processing::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 2s infinite;
}

/* Collapsible button styles */
.btn.collapsed {
  transition: all 0.2s ease;
  border: 1px solid #dee2e6;
  background-color: #f8f9fa;
}

.btn.collapsed:hover {
  background-color: #e9ecef;
  border-color: #adb5bd;
}

.btn:not(.collapsed) {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.btn:not(.collapsed) .kt-icon {
  transform: rotate(180deg);
}

/* Collapse content styling */
.collapse-content {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-top: none;
  transition: all 0.3s ease;
}

/* Badge styling for status indicators */
.badge {
  font-size: 0.75em;
  padding: 0.25em 0.5em;
}

/* Color preview styling */
.color-preview {
  border: 2px solid #dee2e6;
  border-radius: 4px;
  transition: border-color 0.2s ease;
}

.color-preview:hover {
  border-color: #adb5bd;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}
</style>
