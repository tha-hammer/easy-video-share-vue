<template>
  <div class="text-overlay-architecture">
    <!-- Header Section -->
    <div class="architecture-header mb-8">
      <div class="row align-items-center">
        <div class="col-lg-8">
          <h1 class="display-6 fw-bold text-gray-900 mb-2">Text Overlay System Architecture</h1>
          <p class="text-muted fs-5 mb-0">
            Interactive text overlay system for video segments using Fabric.js and FFmpeg
            integration
          </p>
        </div>
        <div class="col-lg-4 text-end">
          <div class="system-stats">
            <div class="stat-item">
              <span class="stat-value">{{ totalOverlayCount }}</span>
              <span class="stat-label">Total Overlays</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ segmentsWithOverlays.length }}</span>
              <span class="stat-label">Segments with Text</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Control Panel -->
    <div class="control-panel card mb-6">
      <div class="card-header">
        <h3 class="card-title">System Controls</h3>
        <div class="card-toolbar">
          <button
            @click="loadSampleData"
            class="btn btn-sm btn-light-primary me-2"
            :disabled="isLoading"
          >
            <KTIcon icon-name="refresh" icon-class="fs-5" />
            Load Sample Data
          </button>
          <button
            @click="clearAllOverlays"
            class="btn btn-sm btn-light-danger"
            :disabled="totalOverlayCount === 0"
          >
            <KTIcon icon-name="trash" icon-class="fs-5" />
            Clear All
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="row g-4">
          <!-- Video Selection -->
          <div class="col-md-4">
            <label class="form-label">Select Video Segment:</label>
            <select v-model="selectedSegmentId" class="form-select" @change="onSegmentChanged">
              <option value="">Choose a segment...</option>
              <option v-for="segment in availableSegments" :key="segment.id" :value="segment.id">
                {{ segment.title }} ({{ segment.duration }}s)
              </option>
            </select>
          </div>

          <!-- Auto-save Status -->
          <div class="col-md-4">
            <label class="form-label">Auto-save:</label>
            <div class="form-check form-switch">
              <input
                class="form-check-input"
                type="checkbox"
                v-model="autoSaveEnabled"
                id="autoSaveSwitch"
              />
              <label class="form-check-label" for="autoSaveSwitch">
                {{ autoSaveEnabled ? 'Enabled' : 'Disabled' }}
              </label>
            </div>
            <small class="text-muted d-block">
              Last saved: {{ lastSaved ? formatTime(lastSaved) : 'Never' }}
            </small>
          </div>

          <!-- Undo/Redo Controls -->
          <div class="col-md-4">
            <label class="form-label">History:</label>
            <div class="btn-group w-100" role="group">
              <button
                @click="undo"
                class="btn btn-outline-secondary"
                :disabled="!canUndo"
                title="Undo (Ctrl+Z)"
              >
                <KTIcon icon-name="arrow-left" icon-class="fs-5" />
                Undo
              </button>
              <button
                @click="redo"
                class="btn btn-outline-secondary"
                :disabled="!canRedo"
                title="Redo (Ctrl+Y)"
              >
                Redo
                <KTIcon icon-name="arrow-right" icon-class="fs-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Editor Area -->
    <div class="editor-area card">
      <div class="card-header">
        <h3 class="card-title">
          Text Overlay Editor
          <span v-if="selectedSegmentId" class="badge badge-light-primary ms-2">
            Segment: {{ selectedSegment?.title }}
          </span>
        </h3>
        <div class="card-toolbar">
          <div class="btn-group" role="group">
            <button
              @click="exportFilters"
              class="btn btn-sm btn-success"
              :disabled="!selectedSegmentId || selectedOverlays.length === 0"
            >
              <KTIcon icon-name="code" icon-class="fs-5" />
              Export FFmpeg
            </button>
            <button
              @click="showExportedFilters = !showExportedFilters"
              class="btn btn-sm btn-light-info"
              :disabled="!exportedFilters.length"
            >
              <KTIcon icon-name="eye" icon-class="fs-5" />
              View Filters
            </button>
          </div>
        </div>
      </div>

      <div class="card-body p-0">
        <div v-if="!selectedSegmentId" class="empty-state text-center py-15">
          <KTIcon icon-name="video" icon-class="fs-4x text-muted mb-5" />
          <h3 class="text-muted">Select a video segment to start editing</h3>
          <p class="text-muted">
            Choose a segment from the dropdown above to begin adding text overlays
          </p>
        </div>

        <div v-else class="editor-container">
          <!-- Text Overlay Editor Component -->
          <SegmentTextEditor
            :segment-id="selectedSegmentId"
            :thumbnail-url="selectedSegment?.thumbnailUrl || ''"
            :video-width="selectedSegment?.videoWidth || 1920"
            :video-height="selectedSegment?.videoHeight || 1080"
            :segment-duration="selectedSegment?.duration || 30"
            :existing-overlays="selectedOverlays"
            :show-debug-info="showDebugInfo"
            @text-overlays-changed="onTextOverlaysChanged"
            @ffmpeg-filters-generated="onFFmpegFiltersGenerated"
          />
        </div>
      </div>
    </div>

    <!-- Current Overlays Panel -->
    <div v-if="selectedSegmentId && selectedOverlays.length > 0" class="overlays-panel card mt-6">
      <div class="card-header">
        <h3 class="card-title">Current Overlays ({{ selectedOverlays.length }})</h3>
        <div class="card-toolbar">
          <button @click="showDebugInfo = !showDebugInfo" class="btn btn-sm btn-light-secondary">
            <KTIcon icon-name="information" icon-class="fs-5" />
            {{ showDebugInfo ? 'Hide' : 'Show' }} Debug
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-row-bordered table-row-gray-100 align-middle">
            <thead>
              <tr class="fw-bold fs-6 text-gray-800">
                <th>Text</th>
                <th>Position</th>
                <th>Font</th>
                <th>Color</th>
                <th>Duration</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="overlay in selectedOverlays" :key="overlay.id">
                <td>
                  <div class="d-flex align-items-center">
                    <div
                      class="overlay-preview"
                      :style="{
                        color: overlay.color,
                        fontFamily: overlay.fontFamily,
                        fontSize: '12px',
                        fontWeight: overlay.fontWeight,
                        fontStyle: overlay.fontStyle,
                        backgroundColor: overlay.backgroundColor || 'transparent',
                        padding: '2px 4px',
                        borderRadius: '2px',
                      }"
                    >
                      {{ overlay.text }}
                    </div>
                  </div>
                </td>
                <td>
                  <small class="text-muted">
                    X: {{ Math.round(overlay.x) }}, Y: {{ Math.round(overlay.y) }}<br />
                    {{ Math.round(overlay.width) }}×{{ Math.round(overlay.height) }}
                  </small>
                </td>
                <td>
                  <small class="text-muted">
                    {{ overlay.fontFamily }}<br />
                    {{ overlay.fontSize }}px
                  </small>
                </td>
                <td>
                  <div
                    class="color-swatch"
                    :style="{ backgroundColor: overlay.color }"
                    :title="overlay.color"
                  ></div>
                </td>
                <td>
                  <small class="text-muted">
                    {{ overlay.startTime }}s - {{ overlay.endTime }}s
                  </small>
                </td>
                <td>
                  <div class="btn-group" role="group">
                    <button
                      @click="duplicateOverlay(overlay.id)"
                      class="btn btn-sm btn-light-primary"
                      title="Duplicate"
                    >
                      <KTIcon icon-name="copy" icon-class="fs-6" />
                    </button>
                    <button
                      @click="removeOverlay(overlay.id)"
                      class="btn btn-sm btn-light-danger"
                      title="Delete"
                    >
                      <KTIcon icon-name="trash" icon-class="fs-6" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- FFmpeg Filters Output -->
    <div v-if="showExportedFilters && exportedFilters.length > 0" class="filters-output card mt-6">
      <div class="card-header">
        <h3 class="card-title">Generated FFmpeg Filters</h3>
        <div class="card-toolbar">
          <button @click="copyFiltersToClipboard" class="btn btn-sm btn-light-primary">
            <KTIcon icon-name="copy" icon-class="fs-5" />
            Copy to Clipboard
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="code-block">
          <pre class="language-bash"><code>{{ exportedFiltersText }}</code></pre>
        </div>
      </div>
    </div>

    <!-- Progress/Status Messages -->
    <div v-if="statusMessage" class="status-message mt-4">
      <div class="alert alert-info d-flex align-items-center">
        <KTIcon icon-name="information-5" icon-class="fs-2x text-info me-4" />
        <div><strong>Status:</strong> {{ statusMessage }}</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useTextOverlayStore } from '@/stores/textOverlays'
import SegmentTextEditor from '@/components/video/SegmentTextEditor.vue'
import type { TextOverlay, FFmpegTextFilter } from '@/types/textOverlay'

interface VideoSegment {
  id: string
  title: string
  thumbnailUrl: string
  videoWidth: number
  videoHeight: number
  duration: number
}

export default defineComponent({
  name: 'TextOverlayArchitecture',
  components: {
    SegmentTextEditor,
  },
  setup() {
    // Store
    const overlayStore = useTextOverlayStore()

    // Local state
    const selectedSegmentId = ref<string>('')
    const showDebugInfo = ref(false)
    const showExportedFilters = ref(false)
    const exportedFilters = ref<FFmpegTextFilter[]>([])
    const statusMessage = ref<string>('')

    // Sample data for architecture
    const availableSegments = ref<VideoSegment[]>([
      {
        id: 'segment_1',
        title: 'Intro Scene',
        thumbnailUrl: 'https://via.placeholder.com/800x450/333333/ffffff?text=Intro+Scene',
        videoWidth: 1920,
        videoHeight: 1080,
        duration: 15,
      },
      {
        id: 'segment_2',
        title: 'Main Content',
        thumbnailUrl: 'https://via.placeholder.com/800x450/666666/ffffff?text=Main+Content',
        videoWidth: 1920,
        videoHeight: 1080,
        duration: 45,
      },
      {
        id: 'segment_3',
        title: 'Call to Action',
        thumbnailUrl: 'https://via.placeholder.com/800x450/999999/ffffff?text=Call+to+Action',
        videoWidth: 1920,
        videoHeight: 1080,
        duration: 10,
      },
    ])

    // ==================== COMPUTED ====================

    const selectedSegment = computed(() => {
      return availableSegments.value.find((s) => s.id === selectedSegmentId.value)
    })

    const selectedOverlays = computed(() => {
      return overlayStore.getOverlaysForSegment(selectedSegmentId.value)
    })

    const totalOverlayCount = computed(() => overlayStore.totalOverlayCount)

    const segmentsWithOverlays = computed(() => overlayStore.segmentsWithOverlays)

    const canUndo = computed(() => overlayStore.canUndo)

    const canRedo = computed(() => overlayStore.canRedo)

    const autoSaveEnabled = computed({
      get: () => overlayStore.autoSaveEnabled,
      set: (value) => {
        overlayStore.autoSaveEnabled = value
      },
    })

    const lastSaved = computed(() => overlayStore.lastSaved)

    const isLoading = computed(() => overlayStore.isLoading)

    const exportedFiltersText = computed(() => {
      return exportedFilters.value.map((filter) => filter.drawTextFilter).join(' \\\n  ')
    })

    // ==================== METHODS ====================

    const onSegmentChanged = () => {
      if (selectedSegmentId.value) {
        overlayStore.selectedSegmentId = selectedSegmentId.value
        statusMessage.value = `Switched to segment: ${selectedSegment.value?.title}`
        setTimeout(() => {
          statusMessage.value = ''
        }, 3000)
      }
    }

    const onTextOverlaysChanged = (overlays: TextOverlay[]) => {
      if (selectedSegmentId.value) {
        overlayStore.setOverlaysForSegment(selectedSegmentId.value, overlays)
        statusMessage.value = `Updated ${overlays.length} text overlays`
        setTimeout(() => {
          statusMessage.value = ''
        }, 2000)
      }
    }

    const onFFmpegFiltersGenerated = (filters: FFmpegTextFilter[]) => {
      exportedFilters.value = filters
      showExportedFilters.value = true
      statusMessage.value = `Generated ${filters.length} FFmpeg filters`
      setTimeout(() => {
        statusMessage.value = ''
      }, 3000)
    }

    const exportFilters = () => {
      if (selectedSegmentId.value) {
        const filters = overlayStore.generateFFmpegFilters(selectedSegmentId.value)
        exportedFilters.value = filters
        showExportedFilters.value = true
        statusMessage.value = `Exported ${filters.length} FFmpeg filters for ${selectedSegment.value?.title}`
        setTimeout(() => {
          statusMessage.value = ''
        }, 3000)
      }
    }

    const copyFiltersToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(exportedFiltersText.value)
        statusMessage.value = 'FFmpeg filters copied to clipboard!'
        setTimeout(() => {
          statusMessage.value = ''
        }, 2000)
      } catch (error) {
        console.error('Failed to copy to clipboard:', error)
        statusMessage.value = 'Failed to copy to clipboard'
        setTimeout(() => {
          statusMessage.value = ''
        }, 2000)
      }
    }

    const loadSampleData = () => {
      // Load some sample text overlays for architecture
      const sampleOverlays: TextOverlay[] = [
        {
          id: 'sample_1',
          segmentId: 'segment_1',
          text: 'Welcome to our system!',
          x: 100,
          y: 100,
          width: 200,
          height: 50,
          fontSize: 32,
          fontFamily: 'Arial',
          fontWeight: 'bold',
          fontStyle: 'normal',
          color: '#ffffff',
          backgroundColor: '#000000',
          opacity: 0.9,
          rotation: 0,
          scaleX: 1,
          scaleY: 1,
          shadow: {
            enabled: false,
            color: '#000000',
            offsetX: 0,
            offsetY: 0,
            blur: 0,
          },
          stroke: {
            enabled: false,
            color: '#000000',
            width: 0,
          },
          startTime: 0,
          endTime: 15,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'sample_2',
          segmentId: 'segment_2',
          text: 'Learn more about text overlays',
          x: 300,
          y: 200,
          width: 300,
          height: 60,
          fontSize: 24,
          fontFamily: 'Arial',
          fontWeight: 'normal',
          fontStyle: 'italic',
          color: '#ffff00',
          opacity: 1.0,
          rotation: 0,
          scaleX: 1,
          scaleY: 1,
          shadow: {
            enabled: false,
            color: '#000000',
            offsetX: 0,
            offsetY: 0,
            blur: 0,
          },
          stroke: {
            enabled: true,
            color: '#000000',
            width: 2,
          },
          startTime: 5,
          endTime: 40,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ]

      // Set sample overlays
      overlayStore.setOverlaysForSegment('segment_1', [sampleOverlays[0]])
      overlayStore.setOverlaysForSegment('segment_2', [sampleOverlays[1]])

      // Select first segment
      selectedSegmentId.value = 'segment_1'
      onSegmentChanged()

      statusMessage.value = 'Loaded sample text overlays!'
      setTimeout(() => {
        statusMessage.value = ''
      }, 3000)
    }

    const clearAllOverlays = () => {
      for (const segment of availableSegments.value) {
        overlayStore.clearSegmentOverlays(segment.id)
      }
      statusMessage.value = 'Cleared all text overlays'
      setTimeout(() => {
        statusMessage.value = ''
      }, 2000)
    }

    const duplicateOverlay = (overlayId: string) => {
      const overlay = overlayStore.getOverlayById(overlayId)
      if (overlay && selectedSegmentId.value) {
        const duplicated: TextOverlay = {
          ...overlay,
          id: `duplicate_${Date.now()}`,
          x: overlay.x + 20,
          y: overlay.y + 20,
          text: `${overlay.text} (Copy)`,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }

        overlayStore.addOverlay(selectedSegmentId.value, duplicated)
        statusMessage.value = 'Overlay duplicated'
        setTimeout(() => {
          statusMessage.value = ''
        }, 2000)
      }
    }

    const removeOverlay = (overlayId: string) => {
      if (selectedSegmentId.value) {
        overlayStore.removeOverlay(selectedSegmentId.value, overlayId)
        statusMessage.value = 'Overlay removed'
        setTimeout(() => {
          statusMessage.value = ''
        }, 2000)
      }
    }

    const undo = () => {
      overlayStore.undo()
      statusMessage.value = 'Undid last action'
      setTimeout(() => {
        statusMessage.value = ''
      }, 1500)
    }

    const redo = () => {
      overlayStore.redo()
      statusMessage.value = 'Redid last action'
      setTimeout(() => {
        statusMessage.value = ''
      }, 1500)
    }

    const formatTime = (date: Date): string => {
      return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(date)
    }

    // ==================== LIFECYCLE ====================

    onMounted(() => {
      // Load sample data on mount for architecture
      loadSampleData()
    })

    // Keyboard shortcuts
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'z':
            event.preventDefault()
            if (event.shiftKey) {
              redo()
            } else {
              undo()
            }
            break
          case 'y':
            event.preventDefault()
            redo()
            break
        }
      }
    }

    onMounted(() => {
      document.addEventListener('keydown', handleKeyDown)
    })

    return {
      // State
      selectedSegmentId,
      showDebugInfo,
      showExportedFilters,
      exportedFilters,
      statusMessage,
      availableSegments,

      // Computed
      selectedSegment,
      selectedOverlays,
      totalOverlayCount,
      segmentsWithOverlays,
      canUndo,
      canRedo,
      autoSaveEnabled,
      lastSaved,
      isLoading,
      exportedFiltersText,

      // Methods
      onSegmentChanged,
      onTextOverlaysChanged,
      onFFmpegFiltersGenerated,
      exportFilters,
      copyFiltersToClipboard,
      loadSampleData,
      clearAllOverlays,
      duplicateOverlay,
      removeOverlay,
      undo,
      redo,
      formatTime,
    }
  },
})
</script>

<style scoped>
.text-overlay-architecture {
  padding: 24px;
}

.architecture-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.system-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  color: #ffffff;
}

.stat-label {
  display: block;
  font-size: 0.875rem;
  color: #e2e8f0;
}

.control-panel .card-body {
  background: #f8f9fa;
}

.editor-container {
  min-height: 500px;
}

.empty-state {
  background: #fafafa;
}

.overlay-preview {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.color-swatch {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  display: inline-block;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.status-message {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1050;
  max-width: 400px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .text-overlay-architecture {
    padding: 16px;
  }

  .system-stats {
    flex-direction: column;
    gap: 12px;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}

/* Animation for status messages */
.status-message .alert {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
