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
<<<<<<< HEAD
              <p class="text-muted mt-3">Initializing Fabric.js canvas...</p>
=======
              <p class="text-muted mt-3">
                Initializing Fabric.js canvas... BOOOOOOOOOOOOOOOOOOOOOOOOOOOYAAAAAAAHHHHHHHHHHHHHHHHHHHHHHHHHHHH
              </p>
            </div>
          </div>
        </div>

        <!-- Editor Controls (Bottom 1/3 on mobile) -->
        <div class="controls-section mobile-controls-section">
          <!-- Mobile Only: Normal Mode: Main Editor Menu -->
          <div v-if="!isTextEditingMode" class="main-editor-menu mobile-main-menu">
            <div class="menu-actions">
              <button
                @click="addNewText"
                class="btn btn-primary"
                :disabled="!isCanvasReady"
                title="Add Text"
              >
                <KTIcon icon-name="plus" icon-class="fs-6" />
              </button>
              <button
                @click="deleteSelectedText"
                class="btn btn-danger"
                :disabled="!hasActiveText"
                title="Delete"
              >
                <KTIcon icon-name="trash" icon-class="fs-6" />
              </button>
              <button
                @click="duplicateText"
                class="btn btn-info"
                :disabled="!hasActiveText"
                title="Duplicate"
              >
                <KTIcon icon-name="copy" icon-class="fs-6" />
              </button>
>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
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

<<<<<<< HEAD
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
=======
          <!-- Show help text when no text selected -->
          <div v-else class="text-center py-5">
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

  <!-- Mobile Text Editing Panel -->
  <div v-if="isMobileView && isCanvasReady" class="mobile-text-editing-panel">
    <!-- Text Input Bar -->
    <div class="mobile-text-input-bar">
      <div class="d-flex align-items-center gap-2">
        <input
          v-model="currentTextContent"
          @input="updateTextContent"
          type="text"
          class="form-control mobile-text-input"
          placeholder="Enter your text..."
        />
        <button
          @click="exitTextEditingMode"
          class="btn btn-sm btn-outline-secondary mobile-expand-btn"
          title="Close Text Editor"
        >
          <KTIcon icon-name="cross" icon-class="fs-6" />
        </button>
        <button
          @click="confirmTextEdit"
          class="btn btn-sm btn-success mobile-confirm-btn"
          title="Confirm Text"
        >
          <KTIcon icon-name="check" icon-class="fs-6" />
        </button>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="mobile-tab-nav">
      <ul class="nav nav-tabs mobile-nav-tabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'fonts' }"
            @click="activeTab = 'fonts'"
            type="button"
            role="tab"
          >
            Fonts
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'styles' }"
            @click="activeTab = 'styles'"
            type="button"
            role="tab"
          >
            Styles
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button
            class="nav-link"
            :class="{ active: activeTab === 'effects' }"
            @click="activeTab = 'effects'"
            type="button"
            role="tab"
          >
            Effects
          </button>
        </li>
      </ul>
    </div>

    <!-- Tab Content -->
    <div class="mobile-tab-content">
      <!-- Fonts Tab -->
      <div v-if="activeTab === 'fonts'" class="tab-pane active">
        <div class="row g-2">
          <div class="col-6" v-for="font in fontOptions" :key="font">
            <div
              class="mobile-font-option"
              :class="{ active: currentFontFamily === font }"
              @click="selectFont(font)"
            >
              <span :style="{ fontFamily: font }">{{ font }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Styles Tab -->
      <div v-if="activeTab === 'styles'" class="tab-pane active">
        <div class="row g-2">
          <!-- Font Size -->
          <div class="col-12 mb-3">
            <label class="form-label">Font Size</label>
            <div class="d-flex align-items-center gap-3">
              <input
                v-model.number="currentFontSize"
                @input="updateFontSize"
                type="range"
                class="form-range flex-grow-1"
                min="8"
                max="200"
              />
              <span class="badge badge-light">{{ currentFontSize }}px</span>
            </div>
          </div>

          <!-- Font Color -->
          <div class="col-6">
            <label class="form-label">Color</label>
            <input
              v-model="currentFontColor"
              @input="updateFontColor"
              type="color"
              class="form-control form-control-color"
            />
          </div>

          <!-- Font Style -->
          <div class="col-6">
            <label class="form-label">Style</label>
            <div class="btn-group d-flex" role="group">
              <button
                @click="toggleBold"
                :class="{ active: currentFontWeight === 'bold' }"
                class="btn btn-outline-secondary"
              >
                <strong>B</strong>
>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
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
        540, // max canvas width (scaled down for display)
        960, // max canvas height (scaled down for display)
      )
    }

    // Text object management
    const addNewText = async () => {
<<<<<<< HEAD
      const textObj = await addTextObject('Sample Text')
      if (textObj) {
        console.log('✅ Text object added successfully')
=======
      console.log('🎯 addNewText called (Mobile mode:', isMobileView.value, ')')
      console.log('🎯 Canvas ready:', isCanvasReady.value)
      console.log('🎯 Canvas exists:', !!canvas.value)
      console.log('🎯 addTextObject function exists:', typeof addTextObject)

      if (!isCanvasReady.value) {
        console.error('❌ Canvas not ready for text creation')
        return
      }

      if (!canvas.value) {
        console.error('❌ Canvas is null')
        return
      }

      try {
        console.log('🎯 Calling addTextObject...')
        const textObj = await addTextObject('Sample Text')
        console.log('🎯 addTextObject returned:', !!textObj)

        if (textObj) {
          console.log('✅ Text object added successfully')
          console.log('🎯 Canvas object count:', canvas.value.getObjects().length)
          console.log('🎯 Text object details:', {
            type: textObj.type,
            text: textObj.text,
            left: textObj.left,
            top: textObj.top,
            visible: textObj.visible,
          })

          // Automatically select the newly created text object
          activeTextObject.value = textObj
          canvas.value.setActiveObject(textObj)

          // Sync form values with the new text object
          currentTextContent.value = textObj.text || ''
          currentFontFamily.value = textObj.fontFamily || 'Arial'
          currentFontSize.value = textObj.fontSize || 24
          currentFontColor.value =
            (typeof textObj.fill === 'string' ? textObj.fill : '#000000') || '#000000'
          currentFontWeight.value =
            (typeof textObj.fontWeight === 'string'
              ? textObj.fontWeight
              : String(textObj.fontWeight)) || 'normal'
          currentFontStyle.value = textObj.fontStyle || 'normal'
          hasTextBackground.value = !!textObj.backgroundColor
          currentBackgroundColor.value =
            (typeof textObj.backgroundColor === 'string' ? textObj.backgroundColor : '#ffffff') ||
            '#ffffff'
          currentOpacity.value = textObj.opacity || 1

          // Enter text editing mode
          if (isMobileView.value) {
            isTextEditingMode.value = true
            nextTick(() => {
              const textInput = document.querySelector('.mobile-text-input') as HTMLInputElement
              if (textInput) {
                textInput.focus()
                textInput.select() // Select the default text for easy replacement
              }
            })
          } else {
            // On desktop, focus the text content input
            nextTick(() => {
              textContentInput.value?.focus()
              textContentInput.value?.select() // Select the default text for easy replacement
            })
          }

          canvas.value.renderAll()
        } else {
          console.error('❌ addTextObject returned null')
        }
      } catch (error) {
        console.error('❌ Error in addNewText:', error)
>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
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
<<<<<<< HEAD
=======
      // Calculate offset that keeps the duplicated text visible on canvas
      const offsetX = 20
      const offsetY = 20

      // Ensure the duplicated text stays within canvas bounds
      let newLeft = (originalText.left || 0) + offsetX
      let newTop = (originalText.top || 0) + offsetY

      // Check bounds and wrap around if necessary
      if (newLeft > canvasSize.value.width - 50) {
        newLeft = 50 // Reset to left side with padding
      }
      if (newTop > canvasSize.value.height - 50) {
        newTop = 50 // Reset to top with padding
      }

>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
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

    // Lifecycle
    onMounted(() => {
      loadSegments()
    })

    onUnmounted(() => {
      dispose()
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

<<<<<<< HEAD
=======
    // New methods for mobile/desktop layout
    const windowWidth = ref(window.innerWidth)

    const isMobileView = computed(() => {
      return windowWidth.value <= 768
    })

    // Update window width on resize
    const updateWindowWidth = () => {
      windowWidth.value = window.innerWidth
    }

    const isTextEditingMode = ref(false)
    const textContentInput = ref<HTMLTextAreaElement | null>(null)

    // Mobile tab state
    const activeTab = ref('fonts')
    const fontOptions = ref([
      'Arial',
      'Helvetica',
      'Times New Roman',
      'Georgia',
      'Verdana',
      'Courier New',
      'Impact',
      'Comic Sans MS',
    ])

    const enterTextEditingMode = async () => {
      isTextEditingMode.value = true

      // Add a new text object if none exists
      if (!hasActiveText.value) {
        await addNewText()
      }

      nextTick(() => {
        textContentInput.value?.focus()
      })
    }

    const exitTextEditingMode = () => {
      isTextEditingMode.value = false
      textContentInput.value?.blur()
    }

    const confirmTextEdit = () => {
      console.log('🔄 Mobile confirm button clicked')
      // Apply any pending changes and exit text editing mode
      if (activeTextObject.value && currentTextContent.value.trim()) {
        updateTextContent()
      }
      exitTextEditingMode()
    }

    const handleTextInputFocus = () => {
      // Prevent viewport from scrolling when keyboard opens
      if (isMobileView.value) {
        document.body.style.overflow = 'hidden'
      }
    }

    const handleTextInputBlur = () => {
      // Restore normal scrolling when keyboard closes
      if (isMobileView.value) {
        document.body.style.overflow = 'auto'
      }
    }

    const handleCanvasClick = (event: Event) => {
      if (isCanvasReady.value && canvas.value) {
        const mouseEvent = event as MouseEvent

        // Check if the click is on an existing text object
        const clickedObject = canvas.value.findTarget(mouseEvent)

        if (clickedObject && clickedObject.type === 'text') {
          // If a text object is clicked, select it and enter editing mode
          const textObj = clickedObject as unknown as {
            text: string
            fontFamily: string
            fontSize: number
            fill: string
            fontWeight: string | number
            fontStyle: string
            backgroundColor: string
            opacity: number
          }
          activeTextObject.value = clickedObject
          currentTextContent.value = textObj.text || ''
          currentFontFamily.value = textObj.fontFamily || 'Arial'
          currentFontSize.value = textObj.fontSize || 24
          currentFontColor.value =
            (typeof textObj.fill === 'string' ? textObj.fill : '#000000') || '#000000'
          currentFontWeight.value =
            (typeof textObj.fontWeight === 'string'
              ? textObj.fontWeight
              : String(textObj.fontWeight)) || 'normal'
          currentFontStyle.value = textObj.fontStyle || 'normal'
          hasTextBackground.value = !!textObj.backgroundColor
          currentBackgroundColor.value =
            (typeof textObj.backgroundColor === 'string' ? textObj.backgroundColor : '#ffffff') ||
            '#ffffff'
          currentOpacity.value = textObj.opacity || 1

          // On mobile, enter text editing mode and focus the text input
          if (isMobileView.value) {
            isTextEditingMode.value = true
            nextTick(() => {
              const textInput = document.querySelector('.mobile-text-input') as HTMLInputElement
              if (textInput) {
                textInput.focus()
                textInput.select() // Select existing text for easy editing
              }
            })
          } else {
            // On desktop, focus the text content input
            nextTick(() => {
              textContentInput.value?.focus()
              textContentInput.value?.select() // Select existing text for easy editing
            })
          }
        }
        // If no text object is clicked, do nothing - user must explicitly click "Add Text" button
      }
    }

    const goBackToSegmentSelection = () => {
      isTextEditingMode.value = false
      thumbnailUrl.value = ''
      if (canvas.value) {
        canvas.value.clear()
      }
      // Reset form values to default
      currentTextContent.value = ''
      currentFontFamily.value = 'Arial'
      currentFontSize.value = 24
      currentFontColor.value = '#000000'
      currentFontWeight.value = 'normal'
      currentFontStyle.value = 'normal'
      hasTextBackground.value = false
      currentBackgroundColor.value = '#ffffff'
      currentOpacity.value = 1
      activeTextObject.value = null

      // Remove mobile class when going back to segment selection
      if (isMobileView.value) {
        document.body.classList.remove('mobile-text-editor')
      }
    }

    // Mobile font selection
    const selectFont = (font: string) => {
      currentFontFamily.value = font
      updateFontFamily()
    }

    // Handle clicks outside text input to exit text editing mode
    const handleDocumentClick = (event: Event) => {
      if (isTextEditingMode.value && isMobileView.value) {
        const target = event.target as HTMLElement
        const textInputSection = document.querySelector('.mobile-text-input')

        if (textInputSection && !textInputSection.contains(target)) {
          exitTextEditingMode()
        }
      }
    }

    // Set up global click listener for mobile and window resize
    onMounted(() => {
      loadSegments()

      // Add window resize listener
      window.addEventListener('resize', handleWindowResize)

      if (isMobileView.value) {
        document.addEventListener('click', handleDocumentClick)
        // Add class to body to hide header/sidebar on mobile
        document.body.classList.add('mobile-text-editor')
      }
    })

    onUnmounted(() => {
      if (canvas.value) {
        dispose()
      }

      // Clear resize timeout
      if (resizeTimeout) {
        clearTimeout(resizeTimeout)
      }

      // Remove window resize listener
      window.removeEventListener('resize', handleWindowResize)

      if (isMobileView.value) {
        document.removeEventListener('click', handleDocumentClick)
        // Remove class from body when component unmounts
        document.body.classList.remove('mobile-text-editor')
      }
    })

>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
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
<<<<<<< HEAD
=======

      // Collapsible methods
      toggleCollapse,
      collapsedSections,

      // New methods for mobile/desktop layout
      isMobileView,
      isTextEditingMode,
      textContentInput,
      enterTextEditingMode,
      exitTextEditingMode,
      confirmTextEdit,
      handleTextInputFocus,
      handleTextInputBlur,
      handleCanvasClick,
      goBackToSegmentSelection,

      // Mobile tab functionality
      activeTab,
      fontOptions,
      selectFont,
>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
    }
  },
})
</script>

<style scoped>
.text-overlay-editor {
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

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}
<<<<<<< HEAD
=======

/* Mobile Text Editing Panel Styles */
.mobile-text-editing-panel {
  background: white !important;
  border-top: 1px solid #dee2e6 !important;
  border-radius: 0 !important;
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  z-index: 9999 !important;
  height: 30vh !important;
  min-height: 250px !important;
  overflow: hidden !important;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1) !important;
  display: flex !important;
  flex-direction: column !important;
  visibility: visible !important;
  pointer-events: auto !important;
}

/* Text Input Bar (~8% of 30vh) */
.mobile-text-input-bar {
  flex: 0 0 auto;
  padding: 8px 12px;
  border-bottom: 1px solid #dee2e6;
  background: #f8f9fa;
  pointer-events: auto;
  z-index: 1000;
  position: relative;
}

.mobile-text-input {
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 14px;
}

.mobile-expand-btn,
.mobile-confirm-btn {
  min-width: 36px;
  height: 36px;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
}

.mobile-expand-btn .kt-icon,
.mobile-confirm-btn .kt-icon {
  font-size: 16px !important;
  color: inherit;
}

/* Tab Navigation (~6% of 30vh) */
.mobile-tab-nav {
  flex: 0 0 auto;
  background: white;
  border-bottom: 1px solid #dee2e6;
}

.mobile-nav-tabs {
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 0;
}

.mobile-nav-tabs .nav-link {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
  color: #6c757d;
  border: none;
  border-bottom: 2px solid transparent;
}

.mobile-nav-tabs .nav-link.active {
  color: #0d6efd;
  border-bottom-color: #0d6efd;
  background: none;
}

/* Tab Content (~16% of 30vh) */
.mobile-tab-content {
  flex: 1 1 auto;
  padding: 12px;
  overflow-y: auto;
}

.mobile-text-editing-full {
  display: block !important;
  visibility: visible !important;
}

.mobile-text-editing-full .form-group {
  margin-bottom: 12px !important;
  display: block !important;
  visibility: visible !important;
}

.mobile-text-editing-full .form-label {
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 4px;
}

.mobile-text-editing-full .form-control,
.mobile-text-editing-full .form-select {
  font-size: 12px;
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  min-height: 32px;
}

.mobile-text-editing-full .form-control-color {
  width: 32px;
  height: 32px;
  padding: 2px;
  border-radius: 4px;
}

.mobile-text-editing-full .color-picker-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-text-editing-full .btn-group .btn {
  padding: 4px 8px;
  font-size: 11px;
  min-height: 28px;
  border-radius: 3px;
}

.mobile-text-editing-full .badge {
  font-size: 10px;
  padding: 2px 6px;
}

.mobile-text-editing-full .form-range {
  height: 20px;
}

.mobile-text-editing-full .form-check-input {
  margin-top: 2px;
}

.mobile-text-editing-full .form-check-label {
  font-size: 11px;
  color: #6c757d;
}

/* Mobile Font Options */
.mobile-font-option {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-font-option:hover {
  border-color: #0d6efd;
  background: #f8f9ff;
}

.mobile-font-option.active {
  border-color: #0d6efd;
  background: #e7f3ff;
  color: #0d6efd;
}

.mobile-font-option span {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Mobile Tab Content Form Elements */
.mobile-tab-content .form-label {
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 4px;
}

.mobile-tab-content .form-control,
.mobile-tab-content .form-select {
  font-size: 12px;
  padding: 6px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  min-height: 32px;
}

.mobile-tab-content .form-control-color {
  width: 40px;
  height: 32px;
  padding: 2px;
  border-radius: 4px;
  border: 1px solid #ced4da;
}

.mobile-tab-content .btn-group .btn {
  padding: 4px 8px;
  font-size: 11px;
  min-height: 28px;
  border-radius: 3px;
}

.mobile-tab-content .badge {
  font-size: 10px;
  padding: 2px 6px;
}

.mobile-tab-content .form-range {
  height: 20px;
}

.mobile-tab-content .form-check-input {
  margin-top: 2px;
}

.mobile-tab-content .form-check-label {
  font-size: 11px;
  color: #6c757d;
}
>>>>>>> bb49b93 (Corrected errors made by Cursor's LLM (missing click)
</style>s
