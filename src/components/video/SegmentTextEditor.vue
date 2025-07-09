<template>
  <div class="segment-text-editor">
    <!-- Canvas Container -->
    <div class="canvas-container" ref="canvasContainer">
      <canvas
        ref="fabricCanvasEl"
        :width="canvasSize.width"
        :height="canvasSize.height"
        class="fabric-canvas"
      />

      <!-- Canvas Overlay Controls -->
      <div v-if="!isCanvasReady" class="canvas-loading">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading canvas...</span>
        </div>
        <p class="mt-2 text-muted">Initializing text editor...</p>
      </div>
    </div>

    <!-- Text Editing Toolbar -->
    <div class="text-toolbar" v-if="isCanvasReady">
      <!-- Primary Actions -->
      <div class="toolbar-section">
        <h6 class="toolbar-title">Text Actions</h6>
        <div class="btn-group" role="group">
          <button @click="addNewText" class="btn btn-sm btn-primary" title="Add New Text">
            <KTIcon icon-name="plus" icon-class="fs-5" />
            Add Text
          </button>
          <button
            @click="deleteSelectedText"
            class="btn btn-sm btn-danger"
            :disabled="!hasActiveText"
            title="Delete Selected Text"
          >
            <KTIcon icon-name="trash" icon-class="fs-5" />
            Delete
          </button>
          <button
            @click="duplicateText"
            class="btn btn-sm btn-info"
            :disabled="!hasActiveText"
            title="Duplicate Selected Text"
          >
            <KTIcon icon-name="copy" icon-class="fs-5" />
            Duplicate
          </button>
        </div>
      </div>

      <!-- Font Controls -->
      <div class="toolbar-section" v-if="hasActiveText">
        <h6 class="toolbar-title">Font Properties</h6>

        <!-- Font Family -->
        <div class="control-group">
          <label class="control-label">Font:</label>
          <select
            v-model="currentFontFamily"
            @change="updateFont"
            class="form-select form-select-sm"
          >
            <option v-for="font in availableFonts" :key="font" :value="font">
              {{ font }}
            </option>
          </select>
        </div>

        <!-- Font Size -->
        <div class="control-group">
          <label class="control-label">Size:</label>
          <div class="range-input-group">
            <input
              type="range"
              v-model="currentFontSize"
              @input="updateFontSize"
              min="12"
              max="120"
              step="1"
              class="form-range"
            />
            <input
              type="number"
              v-model="currentFontSize"
              @input="updateFontSize"
              min="12"
              max="120"
              class="form-control form-control-sm size-input"
            />
            <span class="size-unit">px</span>
          </div>
        </div>

        <!-- Font Style -->
        <div class="control-group">
          <label class="control-label">Style:</label>
          <div class="btn-group btn-group-sm" role="group">
            <input
              type="checkbox"
              class="btn-check"
              id="font-bold"
              v-model="isBold"
              @change="updateFontWeight"
            />
            <label class="btn btn-outline-secondary" for="font-bold">
              <KTIcon icon-name="text-bold" icon-class="fs-6" />
            </label>

            <input
              type="checkbox"
              class="btn-check"
              id="font-italic"
              v-model="isItalic"
              @change="updateFontStyle"
            />
            <label class="btn btn-outline-secondary" for="font-italic">
              <KTIcon icon-name="text-italic" icon-class="fs-6" />
            </label>
          </div>
        </div>
      </div>

      <!-- Color Controls -->
      <div class="toolbar-section" v-if="hasActiveText">
        <h6 class="toolbar-title">Colors</h6>

        <!-- Text Color -->
        <div class="control-group">
          <label class="control-label">Text Color:</label>
          <div class="color-input-group">
            <input
              type="color"
              v-model="currentTextColor"
              @input="updateTextColor"
              class="form-control form-control-color"
            />
            <input
              type="text"
              v-model="currentTextColor"
              @input="updateTextColor"
              class="form-control form-control-sm color-text-input"
              placeholder="#ffffff"
            />
          </div>
        </div>

        <!-- Background Color -->
        <div class="control-group">
          <label class="control-label">
            <input
              type="checkbox"
              v-model="hasBackgroundColor"
              @change="toggleBackgroundColor"
              class="form-check-input me-2"
            />
            Background:
          </label>
          <div class="color-input-group" v-if="hasBackgroundColor">
            <input
              type="color"
              v-model="currentBackgroundColor"
              @input="updateBackgroundColor"
              class="form-control form-control-color"
            />
            <input
              type="text"
              v-model="currentBackgroundColor"
              @input="updateBackgroundColor"
              class="form-control form-control-sm color-text-input"
              placeholder="#000000"
            />
          </div>
        </div>

        <!-- Opacity -->
        <div class="control-group">
          <label class="control-label">Opacity:</label>
          <div class="range-input-group">
            <input
              type="range"
              v-model="currentOpacity"
              @input="updateOpacity"
              min="0"
              max="1"
              step="0.1"
              class="form-range"
            />
            <span class="opacity-value">{{ Math.round(currentOpacity * 100) }}%</span>
          </div>
        </div>
      </div>

      <!-- Text Effects -->
      <div class="toolbar-section" v-if="hasActiveText">
        <h6 class="toolbar-title">Effects</h6>

        <!-- Shadow -->
        <div class="control-group">
          <label class="control-label">
            <input
              type="checkbox"
              v-model="hasShadow"
              @change="toggleShadow"
              class="form-check-input me-2"
            />
            Drop Shadow
          </label>
          <div v-if="hasShadow" class="effect-controls">
            <div class="shadow-controls">
              <input
                type="color"
                v-model="shadowColor"
                @input="updateShadow"
                class="form-control form-control-color"
                title="Shadow Color"
              />
              <input
                type="range"
                v-model="shadowOffsetX"
                @input="updateShadow"
                min="-10"
                max="10"
                step="1"
                class="form-range"
                title="Horizontal Offset"
              />
              <input
                type="range"
                v-model="shadowOffsetY"
                @input="updateShadow"
                min="-10"
                max="10"
                step="1"
                class="form-range"
                title="Vertical Offset"
              />
            </div>
          </div>
        </div>

        <!-- Stroke/Outline -->
        <div class="control-group">
          <label class="control-label">
            <input
              type="checkbox"
              v-model="hasStroke"
              @change="toggleStroke"
              class="form-check-input me-2"
            />
            Text Outline
          </label>
          <div v-if="hasStroke" class="effect-controls">
            <div class="stroke-controls">
              <input
                type="color"
                v-model="strokeColor"
                @input="updateStroke"
                class="form-control form-control-color"
                title="Outline Color"
              />
              <input
                type="range"
                v-model="strokeWidth"
                @input="updateStroke"
                min="1"
                max="10"
                step="1"
                class="form-range"
                title="Outline Width"
              />
              <span class="stroke-width-value">{{ strokeWidth }}px</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Position and Transform -->
      <div class="toolbar-section" v-if="hasActiveText">
        <h6 class="toolbar-title">Position & Transform</h6>

        <!-- Position Controls -->
        <div class="control-group">
          <label class="control-label">Position:</label>
          <div class="position-controls">
            <button
              @click="alignText('left')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Left"
            >
              <KTIcon icon-name="text-align-left" icon-class="fs-6" />
            </button>
            <button
              @click="alignText('center')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Center"
            >
              <KTIcon icon-name="text-align-center" icon-class="fs-6" />
            </button>
            <button
              @click="alignText('right')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Right"
            >
              <KTIcon icon-name="text-align-right" icon-class="fs-6" />
            </button>
          </div>
        </div>

        <!-- Vertical Position -->
        <div class="control-group">
          <label class="control-label">Vertical:</label>
          <div class="position-controls">
            <button
              @click="alignText('top')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Top"
            >
              Top
            </button>
            <button
              @click="alignText('middle')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Middle"
            >
              Middle
            </button>
            <button
              @click="alignText('bottom')"
              class="btn btn-sm btn-outline-secondary"
              title="Align Bottom"
            >
              Bottom
            </button>
          </div>
        </div>
      </div>

      <!-- Debug Information (Development Only) -->
      <div class="toolbar-section" v-if="showDebugInfo && hasActiveText">
        <h6 class="toolbar-title">Debug Info</h6>
        <div class="debug-info">
          <small class="text-muted">
            Canvas: {{ Math.round(debugCoords.canvasX) }}, {{ Math.round(debugCoords.canvasY)
            }}<br />
            Video: {{ Math.round(debugCoords.videoX) }}, {{ Math.round(debugCoords.videoY) }}<br />
            Scale: {{ scaleFactors.x.toFixed(2) }}x, {{ scaleFactors.y.toFixed(2) }}x
          </small>
        </div>
      </div>
    </div>

    <!-- Preview and Export -->
    <div class="text-preview-section" v-if="isCanvasReady">
      <div class="d-flex justify-content-between align-items-center">
        <div class="preview-info">
          <small class="text-muted">
            Text objects: {{ textObjectCount }} | Canvas: {{ canvasSize.width }}×{{
              canvasSize.height
            }}
            | Video: {{ videoSize.width }}×{{ videoSize.height }}
          </small>
        </div>
        <div class="preview-actions">
          <button
            @click="generatePreview"
            class="btn btn-sm btn-light me-2"
            :disabled="generatingPreview"
          >
            <KTIcon
              :icon-name="generatingPreview ? 'spinner' : 'eye'"
              :icon-class="generatingPreview ? 'fs-5 fa-spin' : 'fs-5'"
            />
            Preview
          </button>
          <button
            @click="exportFFmpegFilters"
            class="btn btn-sm btn-success"
            :disabled="textObjectCount === 0"
          >
            <KTIcon icon-name="code" icon-class="fs-5" />
            Export FFmpeg
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useTextOverlay } from '@/composables/useTextOverlay'
import { AVAILABLE_FONTS } from '@/types/textOverlay'
import type { FFmpegTextFilter } from '@/types/textOverlay'

export default defineComponent({
  name: 'SegmentTextEditor',
  props: {
    segmentId: {
      type: String,
      required: true,
    },
    thumbnailUrl: {
      type: String,
      required: true,
    },
    videoWidth: {
      type: Number,
      required: true,
    },
    videoHeight: {
      type: Number,
      required: true,
    },
    defaultText: {
      type: String,
      default: 'Add your text here',
    },
    segmentDuration: {
      type: Number,
      default: 30,
    },
    existingOverlays: {
      type: Array,
      default: () => [],
    },
    showDebugInfo: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['text-overlays-changed', 'ffmpeg-filters-generated'],
  setup(props, { emit }) {
    // Fabric.js canvas element reference
    const fabricCanvasEl = ref<HTMLCanvasElement | null>(null)
    const canvasContainer = ref<HTMLDivElement | null>(null)

    // Text overlay composable (CORE FUNCTIONALITY)
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
      updateTextProperty,
      extractTextCoordinates,
      convertToVideoCoordinates,
      convertToFFmpegFilter,
      dispose,
    } = useTextOverlay()

    // ==================== REACTIVE STATE ====================

    // Font properties
    const currentFontFamily = ref('Arial')
    const currentFontSize = ref(24)
    const isBold = ref(false)
    const isItalic = ref(false)

    // Color properties
    const currentTextColor = ref('#ffffff')
    const currentBackgroundColor = ref('#000000')
    const hasBackgroundColor = ref(false)
    const currentOpacity = ref(1.0)

    // Effect properties
    const hasShadow = ref(false)
    const shadowColor = ref('#000000')
    const shadowOffsetX = ref(2)
    const shadowOffsetY = ref(2)

    const hasStroke = ref(false)
    const strokeColor = ref('#000000')
    const strokeWidth = ref(2)

    // UI state
    const generatingPreview = ref(false)
    const availableFonts = AVAILABLE_FONTS.map((f) => f.fabricFont)

    // ==================== COMPUTED PROPERTIES ====================

    const textObjectCount = computed(() => {
      if (!canvas.value) return 0
      return canvas.value.getObjects().filter((obj) => obj.type === 'text').length
    })

    const debugCoords = computed(() => {
      if (!activeTextObject.value) {
        return { canvasX: 0, canvasY: 0, videoX: 0, videoY: 0 }
      }

      const canvasCoords = extractTextCoordinates(activeTextObject.value)
      const videoCoords = convertToVideoCoordinates(canvasCoords)

      return {
        canvasX: canvasCoords.canvasX,
        canvasY: canvasCoords.canvasY,
        videoX: videoCoords.x,
        videoY: videoCoords.y,
      }
    })

    // ==================== CANVAS INITIALIZATION ====================

    const initializeEditor = async () => {
      await nextTick()

      if (!fabricCanvasEl.value) {
        console.error('❌ Canvas element not found')
        return
      }

      console.log('🎨 Initializing SegmentTextEditor')

      initializeCanvas(
        fabricCanvasEl.value,
        props.thumbnailUrl,
        props.videoWidth,
        props.videoHeight,
      )

      // Load existing overlays if provided
      if (props.existingOverlays.length > 0) {
        loadExistingOverlays()
      }
    }

    const loadExistingOverlays = () => {
      // TODO: Implement loading of existing text overlays
      console.log('📂 Loading existing overlays:', props.existingOverlays.length)
    }

    // ==================== TEXT OBJECT MANAGEMENT ====================

    const addNewText = () => {
      const textObj = addTextObject(props.defaultText)
      if (textObj) {
        // Update reactive properties to match new text
        updateReactivePropertiesFromText(textObj)
        emitTextOverlaysChanged()
      }
    }

    const deleteSelectedText = () => {
      if (activeTextObject.value) {
        removeTextObject(activeTextObject.value)
        emitTextOverlaysChanged()
      }
    }

    const duplicateText = () => {
      if (!activeTextObject.value) return

      const originalText = activeTextObject.value
      const newText = addTextObject(
        originalText.text || 'Duplicated Text',
        (originalText.left || 0) + 20,
        (originalText.top || 0) + 20,
        {
          fontSize: originalText.fontSize,
          fontFamily: originalText.fontFamily,
          fill: originalText.fill,
          stroke: originalText.stroke,
          strokeWidth: originalText.strokeWidth,
          shadow: originalText.shadow,
        },
      )

      if (newText) {
        emitTextOverlaysChanged()
      }
    }

    // ==================== PROPERTY UPDATES ====================

    const updateFont = () => {
      updateTextProperty('fontFamily', currentFontFamily.value)
      emitTextOverlaysChanged()
    }

    const updateFontSize = () => {
      updateTextProperty('fontSize', parseInt(currentFontSize.value.toString()))
      emitTextOverlaysChanged()
    }

    const updateFontWeight = () => {
      updateTextProperty('fontWeight', isBold.value ? 'bold' : 'normal')
      emitTextOverlaysChanged()
    }

    const updateFontStyle = () => {
      updateTextProperty('fontStyle', isItalic.value ? 'italic' : 'normal')
      emitTextOverlaysChanged()
    }

    const updateTextColor = () => {
      updateTextProperty('fill', currentTextColor.value)
      emitTextOverlaysChanged()
    }

    const updateBackgroundColor = () => {
      if (hasBackgroundColor.value) {
        updateTextProperty('backgroundColor', currentBackgroundColor.value)
      } else {
        updateTextProperty('backgroundColor', '')
      }
      emitTextOverlaysChanged()
    }

    const toggleBackgroundColor = () => {
      if (hasBackgroundColor.value) {
        updateTextProperty('backgroundColor', currentBackgroundColor.value)
      } else {
        updateTextProperty('backgroundColor', '')
      }
      emitTextOverlaysChanged()
    }

    const updateOpacity = () => {
      updateTextProperty('opacity', parseFloat(currentOpacity.value.toString()))
      emitTextOverlaysChanged()
    }

    // ==================== TEXT EFFECTS ====================

    const toggleShadow = () => {
      if (hasShadow.value) {
        updateShadow()
      } else {
        updateTextProperty('shadow', null)
      }
      emitTextOverlaysChanged()
    }

    const updateShadow = () => {
      if (hasShadow.value) {
        updateTextProperty('shadow', {
          color: shadowColor.value,
          blur: 3,
          offsetX: parseInt(shadowOffsetX.value.toString()),
          offsetY: parseInt(shadowOffsetY.value.toString()),
        })
      }
      emitTextOverlaysChanged()
    }

    const toggleStroke = () => {
      if (hasStroke.value) {
        updateStroke()
      } else {
        updateTextProperty('stroke', null)
        updateTextProperty('strokeWidth', 0)
      }
      emitTextOverlaysChanged()
    }

    const updateStroke = () => {
      if (hasStroke.value) {
        updateTextProperty('stroke', strokeColor.value)
        updateTextProperty('strokeWidth', parseInt(strokeWidth.value.toString()))
      }
      emitTextOverlaysChanged()
    }

    // ==================== TEXT ALIGNMENT ====================

    const alignText = (alignment: string) => {
      if (!activeTextObject.value || !canvas.value) return

      const canvasWidth = canvas.value.width || 800
      const canvasHeight = canvas.value.height || 450
      const textObj = activeTextObject.value

      switch (alignment) {
        case 'left':
          updateTextProperty('left', 50)
          break
        case 'center':
          updateTextProperty('left', canvasWidth / 2)
          break
        case 'right':
          updateTextProperty('left', canvasWidth - 50)
          break
        case 'top':
          updateTextProperty('top', 50)
          break
        case 'middle':
          updateTextProperty('top', canvasHeight / 2)
          break
        case 'bottom':
          updateTextProperty('top', canvasHeight - 50)
          break
      }

      emitTextOverlaysChanged()
    }

    // ==================== REACTIVE PROPERTY UPDATES ====================

    const updateReactivePropertiesFromText = (textObj: fabric.Text) => {
      currentFontFamily.value = textObj.fontFamily || 'Arial'
      currentFontSize.value = textObj.fontSize || 24
      isBold.value = textObj.fontWeight === 'bold'
      isItalic.value = textObj.fontStyle === 'italic'
      currentTextColor.value = (textObj.fill as string) || '#ffffff'
      currentOpacity.value = textObj.opacity || 1.0

      hasBackgroundColor.value = !!textObj.backgroundColor
      if (hasBackgroundColor.value) {
        currentBackgroundColor.value = textObj.backgroundColor as string
      }

      hasShadow.value = !!textObj.shadow
      if (hasShadow.value && textObj.shadow) {
        const shadow = textObj.shadow as any
        shadowColor.value = shadow.color || '#000000'
        shadowOffsetX.value = shadow.offsetX || 2
        shadowOffsetY.value = shadow.offsetY || 2
      }

      hasStroke.value = !!(textObj.stroke && textObj.strokeWidth)
      if (hasStroke.value) {
        strokeColor.value = textObj.stroke as string
        strokeWidth.value = textObj.strokeWidth || 2
      }
    }

    // Watch for active text changes to update reactive properties
    watch(activeTextObject, (newText) => {
      if (newText) {
        updateReactivePropertiesFromText(newText)
      }
    })

    // ==================== EVENT HANDLING ====================

    const emitTextOverlaysChanged = () => {
      if (!canvas.value) return

      const textObjects = canvas.value.getObjects().filter((obj) => obj.type === 'text')
      const overlays = textObjects.map((obj, index) => {
        const textObj = obj as fabric.Text
        const canvasCoords = extractTextCoordinates(textObj)
        const videoCoords = convertToVideoCoordinates(canvasCoords)

        return {
          id: `text_${props.segmentId}_${index}`,
          segmentId: props.segmentId,
          text: textObj.text || '',
          x: videoCoords.x,
          y: videoCoords.y,
          width: videoCoords.width,
          height: videoCoords.height,
          fontSize: videoCoords.fontSize,
          fontFamily: textObj.fontFamily || 'Arial',
          fontWeight: textObj.fontWeight || 'normal',
          fontStyle: textObj.fontStyle || 'normal',
          color: (textObj.fill as string) || '#ffffff',
          backgroundColor: textObj.backgroundColor as string,
          opacity: textObj.opacity || 1.0,
          rotation: videoCoords.rotation * (180 / Math.PI), // Convert back to degrees
          scaleX: textObj.scaleX || 1,
          scaleY: textObj.scaleY || 1,
          shadow: textObj.shadow
            ? {
                enabled: true,
                color: (textObj.shadow as any).color || '#000000',
                offsetX: (textObj.shadow as any).offsetX || 2,
                offsetY: (textObj.shadow as any).offsetY || 2,
                blur: (textObj.shadow as any).blur || 3,
              }
            : { enabled: false },
          stroke: textObj.stroke
            ? {
                enabled: true,
                color: textObj.stroke as string,
                width: textObj.strokeWidth || 2,
              }
            : { enabled: false },
          startTime: 0,
          endTime: props.segmentDuration,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
      })

      emit('text-overlays-changed', overlays)
    }

    // ==================== EXPORT FUNCTIONALITY ====================

    const generatePreview = async () => {
      generatingPreview.value = true
      try {
        // Generate preview image of canvas
        if (canvas.value) {
          const dataURL = canvas.value.toDataURL('image/png')
          console.log('🖼️ Generated preview image')
          // Could emit preview data or save to store
        }
      } catch (error) {
        console.error('❌ Failed to generate preview:', error)
      } finally {
        generatingPreview.value = false
      }
    }

    const exportFFmpegFilters = () => {
      if (!canvas.value) return

      const textObjects = canvas.value.getObjects().filter((obj) => obj.type === 'text')
      const filters: FFmpegTextFilter[] = textObjects.map((obj) => {
        const textObj = obj as fabric.Text
        return convertToFFmpegFilter(textObj, 0, props.segmentDuration)
      })

      console.log('🎬 Generated FFmpeg filters:', filters)
      emit('ffmpeg-filters-generated', filters)
    }

    // ==================== LIFECYCLE ====================

    onMounted(() => {
      initializeEditor()
    })

    onUnmounted(() => {
      dispose()
    })

    // Watch for thumbnail URL changes
    watch(
      () => props.thumbnailUrl,
      () => {
        if (isCanvasReady.value) {
          initializeEditor()
        }
      },
    )

    return {
      // Refs
      fabricCanvasEl,
      canvasContainer,

      // Canvas state
      canvas,
      isCanvasReady,
      activeTextObject,
      hasActiveText,
      canvasSize,
      videoSize,
      scaleFactors,

      // Font properties
      currentFontFamily,
      currentFontSize,
      isBold,
      isItalic,
      availableFonts,

      // Color properties
      currentTextColor,
      currentBackgroundColor,
      hasBackgroundColor,
      currentOpacity,

      // Effect properties
      hasShadow,
      shadowColor,
      shadowOffsetX,
      shadowOffsetY,
      hasStroke,
      strokeColor,
      strokeWidth,

      // UI state
      generatingPreview,
      textObjectCount,
      debugCoords,

      // Methods
      addNewText,
      deleteSelectedText,
      duplicateText,
      updateFont,
      updateFontSize,
      updateFontWeight,
      updateFontStyle,
      updateTextColor,
      updateBackgroundColor,
      toggleBackgroundColor,
      updateOpacity,
      toggleShadow,
      updateShadow,
      toggleStroke,
      updateStroke,
      alignText,
      generatePreview,
      exportFFmpegFilters,
    }
  },
})
</script>

<style scoped>
.segment-text-editor {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Canvas Container */
.canvas-container {
  position: relative;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
}

.fabric-canvas {
  display: block;
}

.canvas-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

/* Toolbar Styles */
.text-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.toolbar-section {
  flex: 1;
  min-width: 200px;
}

.toolbar-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
  padding-bottom: 4px;
  border-bottom: 1px solid #dee2e6;
}

.control-group {
  margin-bottom: 12px;
}

.control-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6c757d;
  margin-bottom: 4px;
}

/* Input Groups */
.range-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.size-input {
  width: 60px;
}

.size-unit {
  font-size: 0.75rem;
  color: #6c757d;
}

.opacity-value {
  font-size: 0.75rem;
  color: #6c757d;
  min-width: 35px;
}

.color-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.color-text-input {
  width: 80px;
  font-size: 0.75rem;
}

/* Position Controls */
.position-controls {
  display: flex;
  gap: 4px;
}

/* Effect Controls */
.effect-controls {
  margin-top: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.shadow-controls,
.stroke-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stroke-width-value {
  font-size: 0.75rem;
  color: #6c757d;
  min-width: 30px;
}

/* Preview Section */
.text-preview-section {
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.preview-info {
  flex: 1;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

/* Debug Info */
.debug-info {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-family: monospace;
}

/* Responsive Design */
@media (max-width: 768px) {
  .text-toolbar {
    flex-direction: column;
  }

  .toolbar-section {
    min-width: unset;
  }

  .range-input-group,
  .color-input-group {
    flex-wrap: wrap;
  }
}
</style>
