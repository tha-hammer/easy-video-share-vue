<template>
  <div class="segment-text-editor">
    <!-- Canvas Container -->
    <div class="canvas-container" ref="canvasContainer">
      <canvas
        ref="fabricCanvas"
        :width="canvasWidth"
        :height="canvasHeight"
        class="fabric-canvas"
      />

      <!-- Loading overlay -->
      <div v-if="!isCanvasReady" class="loading-overlay">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading canvas...</span>
        </div>
        <p class="text-muted mt-3">Initializing canvas...</p>
      </div>
    </div>

    <!-- Text Toolbar -->
    <div class="text-toolbar card mt-4">
      <div class="card-header">
        <h5 class="card-title mb-0">Text Controls</h5>
      </div>
      <div class="card-body">
        <!-- Action Buttons Row -->
        <div class="toolbar-row mb-3">
          <div class="btn-group" role="group">
            <button @click="addText" class="btn btn-primary" :disabled="!isCanvasReady">
              <KTIcon icon-name="plus" icon-class="fs-5" />
              Add Text
            </button>
            <button @click="deleteSelected" class="btn btn-danger" :disabled="!hasSelectedText">
              <KTIcon icon-name="trash" icon-class="fs-5" />
              Delete
            </button>
            <button @click="duplicateText" class="btn btn-info" :disabled="!hasSelectedText">
              <KTIcon icon-name="copy" icon-class="fs-5" />
              Duplicate
            </button>
          </div>
        </div>

        <!-- Text Properties (only show when text is selected) -->
        <div v-if="hasSelectedText" class="text-properties">
          <!-- Font Properties Row -->
          <div class="toolbar-row mb-3">
            <div class="property-group">
              <label class="form-label">Font Family:</label>
              <select v-model="selectedFont" @change="updateFont" class="form-select">
                <option v-for="font in availableFonts" :key="font" :value="font">
                  {{ font }}
                </option>
              </select>
            </div>

            <div class="property-group">
              <label class="form-label">Font Size: {{ fontSize }}px</label>
              <input
                type="range"
                v-model="fontSize"
                min="12"
                max="120"
                class="form-range"
                @input="updateFontSize"
              />
            </div>

            <div class="property-group">
              <label class="form-label">Font Weight:</label>
              <select v-model="fontWeight" @change="updateFontWeight" class="form-select">
                <option value="normal">Normal</option>
                <option value="bold">Bold</option>
                <option value="lighter">Lighter</option>
                <option value="bolder">Bolder</option>
              </select>
            </div>
          </div>

          <!-- Color Properties Row -->
          <div class="toolbar-row mb-3">
            <div class="property-group">
              <label class="form-label">Text Color:</label>
              <div class="color-input-group">
                <input
                  type="color"
                  v-model="textColor"
                  @input="updateTextColor"
                  class="form-control form-control-color"
                />
                <span class="color-value">{{ textColor }}</span>
              </div>
            </div>

            <div class="property-group">
              <label class="form-label">Background Color:</label>
              <div class="background-controls">
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    v-model="hasBackground"
                    @change="toggleBackground"
                    id="backgroundToggle"
                  />
                  <label class="form-check-label" for="backgroundToggle"> Enable Background </label>
                </div>
                <div v-if="hasBackground" class="color-input-group mt-2">
                  <input
                    type="color"
                    v-model="backgroundColor"
                    @input="updateBackgroundColor"
                    class="form-control form-control-color"
                  />
                  <span class="color-value">{{ backgroundColor }}</span>
                </div>
              </div>
            </div>

            <div class="property-group">
              <label class="form-label">Opacity: {{ Math.round(opacity * 100) }}%</label>
              <input
                type="range"
                v-model="opacity"
                min="0"
                max="1"
                step="0.1"
                class="form-range"
                @input="updateOpacity"
              />
            </div>
          </div>

          <!-- Text Effects Row -->
          <div class="toolbar-row">
            <!-- Shadow Controls -->
            <div class="property-group">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="checkbox"
                  v-model="hasShadow"
                  @change="toggleShadow"
                  id="shadowToggle"
                />
                <label class="form-check-label" for="shadowToggle"> Drop Shadow </label>
              </div>
              <div v-if="hasShadow" class="shadow-controls mt-2">
                <div class="row g-2">
                  <div class="col-4">
                    <input
                      type="color"
                      v-model="shadowColor"
                      @input="updateShadow"
                      class="form-control form-control-color"
                      title="Shadow Color"
                    />
                  </div>
                  <div class="col-4">
                    <input
                      type="range"
                      v-model="shadowOffsetX"
                      min="-10"
                      max="10"
                      @input="updateShadow"
                      class="form-range"
                      title="Horizontal Offset"
                    />
                    <small>X: {{ shadowOffsetX }}</small>
                  </div>
                  <div class="col-4">
                    <input
                      type="range"
                      v-model="shadowOffsetY"
                      min="-10"
                      max="10"
                      @input="updateShadow"
                      class="form-range"
                      title="Vertical Offset"
                    />
                    <small>Y: {{ shadowOffsetY }}</small>
                  </div>
                </div>
              </div>
            </div>

            <!-- Stroke Controls -->
            <div class="property-group">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="checkbox"
                  v-model="hasStroke"
                  @change="toggleStroke"
                  id="strokeToggle"
                />
                <label class="form-check-label" for="strokeToggle"> Text Outline </label>
              </div>
              <div v-if="hasStroke" class="stroke-controls mt-2">
                <div class="row g-2">
                  <div class="col-6">
                    <input
                      type="color"
                      v-model="strokeColor"
                      @input="updateStroke"
                      class="form-control form-control-color"
                      title="Stroke Color"
                    />
                  </div>
                  <div class="col-6">
                    <input
                      type="range"
                      v-model="strokeWidth"
                      min="1"
                      max="10"
                      @input="updateStroke"
                      class="form-range"
                      title="Stroke Width"
                    />
                    <small>Width: {{ strokeWidth }}</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Help Text -->
        <div v-if="!hasSelectedText" class="no-selection-help">
          <KTIcon icon-name="information-5" icon-class="fs-2x text-muted mb-2" />
          <p class="text-muted mb-0">
            Click "Add Text" to create a new text element, or click on existing text to edit its
            properties.
          </p>
        </div>
      </div>
    </div>

    <!-- Text Objects List -->
    <div v-if="textObjects.length > 0" class="text-objects-list card mt-4">
      <div class="card-header">
        <h5 class="card-title mb-0">Text Objects ({{ textObjects.length }})</h5>
      </div>
      <div class="card-body">
        <div
          class="text-object-item"
          v-for="(textObj, index) in textObjects"
          :key="index"
          :class="{ active: textObj === selectedTextObject }"
          @click="selectTextObject(textObj)"
        >
          <div class="text-preview">
            <div class="text-content" :style="getTextPreviewStyle(textObj)">
              {{ textObj.text || 'Empty Text' }}
            </div>
          </div>
          <div class="text-actions">
            <button @click.stop="selectTextObject(textObj)" class="btn btn-sm btn-outline-primary">
              Edit
            </button>
            <button @click.stop="deleteTextObject(textObj)" class="btn btn-sm btn-outline-danger">
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Canvas, Text, Image } from 'fabric'

export default defineComponent({
  name: 'SegmentTextEditor',
  props: {
    segmentId: { type: String, required: true },
    thumbnailUrl: { type: String, required: true },
    videoWidth: { type: Number, required: true },
    videoHeight: { type: Number, required: true },
    segmentDuration: { type: Number, default: 30 },
    existingOverlays: { type: Array, default: () => [] },
  },
  emits: ['text-overlays-changed', 'ffmpeg-filters-generated'],
  setup(props, { emit }) {
    // Canvas refs
    const fabricCanvas = ref<HTMLCanvasElement | null>(null)
    const canvasContainer = ref<HTMLDivElement | null>(null)

    // Canvas state
    const canvas = ref<Canvas | null>(null)
    const isCanvasReady = ref(false)
    const canvasWidth = ref(800)
    const canvasHeight = ref(450)

    // Text management
    const selectedTextObject = ref<Text | null>(null)
    const textObjects = ref<Text[]>([])

    // Available fonts
    const availableFonts = [
      'Arial',
      'Helvetica',
      'Times New Roman',
      'Courier New',
      'Georgia',
      'Verdana',
      'Comic Sans MS',
      'Impact',
      'Trebuchet MS',
      'Palatino',
      'Garamond',
      'Bookman',
    ]

    // Text properties (reactive to selected object)
    const selectedFont = ref('Arial')
    const fontSize = ref(24)
    const fontWeight = ref('normal')
    const textColor = ref('#ffffff')
    const hasBackground = ref(false)
    const backgroundColor = ref('#000000')
    const opacity = ref(1)
    const hasShadow = ref(false)
    const shadowColor = ref('#000000')
    const shadowOffsetX = ref(2)
    const shadowOffsetY = ref(2)
    const hasStroke = ref(false)
    const strokeColor = ref('#000000')
    const strokeWidth = ref(2)

    // Computed properties
    const hasSelectedText = computed(() => selectedTextObject.value !== null)

    const scaleFactors = computed(() => ({
      x: props.videoWidth / canvasWidth.value,
      y: props.videoHeight / canvasHeight.value,
    }))

    // ==================== CANVAS INITIALIZATION ====================

    const initializeCanvas = async () => {
      if (!fabricCanvas.value) return

      // Calculate canvas dimensions maintaining aspect ratio
      const aspectRatio = props.videoWidth / props.videoHeight
      const maxWidth = 800
      const maxHeight = 450

      if (aspectRatio > maxWidth / maxHeight) {
        canvasWidth.value = maxWidth
        canvasHeight.value = maxWidth / aspectRatio
      } else {
        canvasHeight.value = maxHeight
        canvasWidth.value = maxHeight * aspectRatio
      }

      // Initialize Fabric.js canvas
      canvas.value = new Canvas(fabricCanvas.value, {
        width: canvasWidth.value,
        height: canvasHeight.value,
        backgroundColor: 'transparent',
        selection: true,
      })

      // Load thumbnail background
      await loadThumbnailBackground()

      // Set up event listeners
      setupCanvasEvents()

      // Load existing overlays
      loadExistingOverlays()

      isCanvasReady.value = true
      console.log('✅ Canvas initialized')
    }

    const loadThumbnailBackground = async () => {
      if (!canvas.value) return

      if (!props.thumbnailUrl || props.thumbnailUrl.trim() === '') {
        canvas.value.backgroundColor = '#4A90E2'
        canvas.value.renderAll()
        return
      }

      try {
        const img = await Image.fromURL(props.thumbnailUrl, {})
        img.set({
          scaleX: canvasWidth.value / props.videoWidth,
          scaleY: canvasHeight.value / props.videoHeight,
          selectable: false,
          evented: false,
        })

        canvas.value.backgroundImage = img
        canvas.value.renderAll()
      } catch (error) {
        console.error('Failed to load thumbnail:', error)
        canvas.value.backgroundColor = '#4A90E2'
        canvas.value.renderAll()
      }
    }

    const setupCanvasEvents = () => {
      if (!canvas.value) return

      // Use any type to avoid complex Fabric.js v6 type issues
      canvas.value.on('selection:created', (options: any) => {
        const selected = options.selected?.[0]
        if (selected && selected.type === 'text') {
          selectTextObject(selected as Text)
        }
      })

      canvas.value.on('selection:updated', (options: any) => {
        const selected = options.selected?.[0]
        if (selected && selected.type === 'text') {
          selectTextObject(selected as Text)
        }
      })

      canvas.value.on('selection:cleared', () => {
        selectedTextObject.value = null
      })

      canvas.value.on('object:modified', (options: any) => {
        const obj = options.target
        if (obj && obj.type === 'text') {
          obj.setCoords()
          emitTextOverlaysChanged()
        }
      })

      canvas.value.on('text:changed', () => {
        emitTextOverlaysChanged()
      })
    }

    // ==================== TEXT MANAGEMENT ====================

    const addText = () => {
      if (!canvas.value) return

      const textObject = new Text('New Text', {
        left: canvasWidth.value / 2,
        top: canvasHeight.value / 2,
        fontSize: 24,
        fontFamily: 'Arial',
        fill: '#ffffff',
        textAlign: 'center',
        originX: 'center',
        originY: 'center',
        editable: true,
      })

      canvas.value.add(textObject)
      canvas.value.setActiveObject(textObject)

      textObjects.value.push(textObject)
      selectTextObject(textObject)

      emitTextOverlaysChanged()
      console.log('✅ Text added')
    }

    const deleteSelected = () => {
      if (!selectedTextObject.value || !canvas.value) return

      deleteTextObject(selectedTextObject.value)
    }

    const deleteTextObject = (textObj: Text) => {
      if (!canvas.value) return

      canvas.value.remove(textObj)

      const index = textObjects.value.indexOf(textObj)
      if (index > -1) {
        textObjects.value.splice(index, 1)
      }

      if (selectedTextObject.value === textObj) {
        selectedTextObject.value = null
      }

      emitTextOverlaysChanged()
      console.log('🗑️ Text deleted')
    }

    const duplicateText = () => {
      if (!selectedTextObject.value || !canvas.value) return

      const original = selectedTextObject.value
      const duplicate = new Text(original.text, {
        left: (original.left || 0) + 20,
        top: (original.top || 0) + 20,
        fontSize: original.fontSize,
        fontFamily: original.fontFamily,
        fill: original.fill,
        backgroundColor: original.backgroundColor,
        textAlign: original.textAlign,
        fontWeight: original.fontWeight,
        fontStyle: original.fontStyle,
        opacity: original.opacity,
        stroke: original.stroke,
        strokeWidth: original.strokeWidth,
        shadow: original.shadow,
        originX: 'center',
        originY: 'center',
        editable: true,
      })

      canvas.value.add(duplicate)
      canvas.value.setActiveObject(duplicate)

      textObjects.value.push(duplicate)
      selectTextObject(duplicate)

      emitTextOverlaysChanged()
      console.log('📋 Text duplicated')
    }

    const selectTextObject = (textObj: Text) => {
      selectedTextObject.value = textObj

      // Update UI controls to match selected object
      selectedFont.value = textObj.fontFamily || 'Arial'
      fontSize.value = textObj.fontSize || 24
      fontWeight.value = (textObj.fontWeight as string) || 'normal'
      textColor.value = (textObj.fill as string) || '#ffffff'
      hasBackground.value = !!textObj.backgroundColor
      backgroundColor.value = (textObj.backgroundColor as string) || '#000000'
      opacity.value = textObj.opacity || 1

      // Shadow properties
      if (textObj.shadow) {
        hasShadow.value = true
        const shadow = textObj.shadow as { color?: string; offsetX?: number; offsetY?: number }
        shadowColor.value = shadow.color || '#000000'
        shadowOffsetX.value = shadow.offsetX || 2
        shadowOffsetY.value = shadow.offsetY || 2
      } else {
        hasShadow.value = false
      }

      // Stroke properties
      if (textObj.stroke && textObj.strokeWidth) {
        hasStroke.value = true
        strokeColor.value = textObj.stroke as string
        strokeWidth.value = textObj.strokeWidth
      } else {
        hasStroke.value = false
      }

      // Select on canvas
      if (canvas.value) {
        canvas.value.setActiveObject(textObj)
        canvas.value.renderAll()
      }
    }

    // ==================== PROPERTY UPDATES ====================

    const updateFont = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set('fontFamily', selectedFont.value)
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateFontSize = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set('fontSize', parseInt(fontSize.value.toString()))
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateFontWeight = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set('fontWeight', fontWeight.value)
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateTextColor = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set('fill', textColor.value)
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const toggleBackground = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set(
        'backgroundColor',
        hasBackground.value ? backgroundColor.value : '',
      )
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateBackgroundColor = () => {
      if (!selectedTextObject.value || !canvas.value || !hasBackground.value) return

      selectedTextObject.value.set('backgroundColor', backgroundColor.value)
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateOpacity = () => {
      if (!selectedTextObject.value || !canvas.value) return

      selectedTextObject.value.set('opacity', parseFloat(opacity.value.toString()))
      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const toggleShadow = () => {
      if (!selectedTextObject.value || !canvas.value) return

      if (hasShadow.value) {
        selectedTextObject.value.set('shadow', {
          color: shadowColor.value,
          offsetX: shadowOffsetX.value,
          offsetY: shadowOffsetY.value,
          blur: 3,
        })
      } else {
        selectedTextObject.value.set('shadow', null)
      }

      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateShadow = () => {
      if (!selectedTextObject.value || !canvas.value || !hasShadow.value) return

      selectedTextObject.value.set('shadow', {
        color: shadowColor.value,
        offsetX: parseInt(shadowOffsetX.value.toString()),
        offsetY: parseInt(shadowOffsetY.value.toString()),
        blur: 3,
      })

      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const toggleStroke = () => {
      if (!selectedTextObject.value || !canvas.value) return

      if (hasStroke.value) {
        selectedTextObject.value.set({
          stroke: strokeColor.value,
          strokeWidth: strokeWidth.value,
        })
      } else {
        selectedTextObject.value.set({
          stroke: '',
          strokeWidth: 0,
        })
      }

      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    const updateStroke = () => {
      if (!selectedTextObject.value || !canvas.value || !hasStroke.value) return

      selectedTextObject.value.set({
        stroke: strokeColor.value,
        strokeWidth: parseInt(strokeWidth.value.toString()),
      })

      canvas.value.renderAll()
      emitTextOverlaysChanged()
    }

    // ==================== HELPER FUNCTIONS ====================

    const getTextPreviewStyle = (textObj: Text) => {
      return {
        color: (textObj.fill as string) || '#ffffff',
        fontFamily: textObj.fontFamily || 'Arial',
        fontSize: '14px',
        fontWeight: textObj.fontWeight || 'normal',
        backgroundColor: textObj.backgroundColor || 'transparent',
        padding: '2px 6px',
        borderRadius: '3px',
        maxWidth: '200px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }
    }

    const loadExistingOverlays = () => {
      // TODO: Load existing overlays from props
      console.log('Loading existing overlays:', props.existingOverlays)
    }

    const emitTextOverlaysChanged = () => {
      if (!canvas.value) return

      const overlays = textObjects.value.map((textObj, index) => ({
        id: `text_${index}_${Date.now()}`,
        segmentId: props.segmentId,
        text: textObj.text || '',
        x: Math.round((textObj.left || 0) * scaleFactors.value.x),
        y: Math.round((textObj.top || 0) * scaleFactors.value.y),
        width: Math.round((textObj.width || 0) * scaleFactors.value.x),
        height: Math.round((textObj.height || 0) * scaleFactors.value.y),
        fontSize: Math.round(
          (textObj.fontSize || 24) * Math.min(scaleFactors.value.x, scaleFactors.value.y),
        ),
        fontFamily: textObj.fontFamily || 'Arial',
        fontWeight: (textObj.fontWeight as string) || 'normal',
        fontStyle: 'normal',
        color: (textObj.fill as string) || '#ffffff',
        backgroundColor: (textObj.backgroundColor as string) || null,
        opacity: textObj.opacity || 1,
        rotation: textObj.angle || 0,
        scaleX: textObj.scaleX || 1,
        scaleY: textObj.scaleY || 1,
        shadow: textObj.shadow
          ? {
              enabled: true,
              color: (textObj.shadow as { color?: string }).color || '#000000',
              offsetX: (textObj.shadow as { offsetX?: number }).offsetX || 0,
              offsetY: (textObj.shadow as { offsetY?: number }).offsetY || 0,
              blur: (textObj.shadow as { blur?: number }).blur || 0,
            }
          : { enabled: false },
        stroke:
          textObj.stroke && textObj.strokeWidth
            ? {
                enabled: true,
                color: textObj.stroke as string,
                width: textObj.strokeWidth,
              }
            : { enabled: false },
        startTime: 0,
        endTime: props.segmentDuration,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }))

      emit('text-overlays-changed', overlays)
    }

    // ==================== LIFECYCLE ====================

    onMounted(async () => {
      await nextTick()
      await initializeCanvas()
    })

    onUnmounted(() => {
      if (canvas.value) {
        canvas.value.dispose()
      }
    })

    return {
      // Refs
      fabricCanvas,
      canvasContainer,

      // State
      isCanvasReady,
      canvasWidth,
      canvasHeight,
      selectedTextObject,
      textObjects,
      hasSelectedText,

      // Properties
      availableFonts,
      selectedFont,
      fontSize,
      fontWeight,
      textColor,
      hasBackground,
      backgroundColor,
      opacity,
      hasShadow,
      shadowColor,
      shadowOffsetX,
      shadowOffsetY,
      hasStroke,
      strokeColor,
      strokeWidth,

      // Methods
      addText,
      deleteSelected,
      deleteTextObject,
      duplicateText,
      selectTextObject,
      updateFont,
      updateFontSize,
      updateFontWeight,
      updateTextColor,
      toggleBackground,
      updateBackgroundColor,
      updateOpacity,
      toggleShadow,
      updateShadow,
      toggleStroke,
      updateStroke,
      getTextPreviewStyle,
    }
  },
})
</script>

<style scoped>
.segment-text-editor {
  max-width: 1200px;
  margin: 0 auto;
}

.canvas-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8f9fa;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  min-height: 400px;
}

.fabric-canvas {
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
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

.text-toolbar {
  background: white;
}

.toolbar-row {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.property-group {
  min-width: 200px;
  flex: 1;
}

.property-group label {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 4px;
  display: block;
}

.color-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-control-color {
  width: 50px;
  height: 38px;
  border-radius: 4px;
  border: 1px solid #ced4da;
  cursor: pointer;
}

.color-value {
  font-family: monospace;
  font-size: 0.875rem;
  color: #6c757d;
}

.background-controls,
.shadow-controls,
.stroke-controls {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.no-selection-help {
  text-align: center;
  padding: 40px 20px;
}

.text-objects-list {
  background: white;
}

.text-object-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.text-object-item:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.text-object-item.active {
  background: #e3f2fd;
  border-color: #007bff;
}

.text-preview {
  flex: 1;
}

.text-content {
  display: inline-block;
}

.text-actions {
  display: flex;
  gap: 8px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .toolbar-row {
    flex-direction: column;
    gap: 16px;
  }

  .property-group {
    min-width: unset;
    width: 100%;
  }
}
</style>
