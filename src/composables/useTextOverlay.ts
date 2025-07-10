// Text Overlay Management Composable
// This is the CORE composable that handles all text overlay functionality

import { ref, computed, onUnmounted } from 'vue'
import { Canvas, Text, Image } from 'fabric'
import type { TEvent } from 'fabric'

export function useTextOverlay() {
  // ==================== STATE MANAGEMENT ====================

  const canvas = ref<Canvas | null>(null)
  const canvasElement = ref<HTMLCanvasElement | null>(null)
  const isCanvasReady = ref(false)
  const activeTextObject = ref<Text | null>(null)

  // Canvas and video dimensions
  const canvasSize = ref({ width: 800, height: 450 })
  const videoSize = ref({ width: 1920, height: 1080 })
  const scaleFactors = computed(() => ({
    x: videoSize.value.width / canvasSize.value.width,
    y: videoSize.value.height / canvasSize.value.height,
  }))

  // ==================== COMPUTED PROPERTIES ====================

  const hasActiveText = computed(() => activeTextObject.value !== null)

  // ==================== CANVAS LIFECYCLE ====================

  /**
   * Initialize Fabric.js canvas with video thumbnail background
   */
  const initializeCanvas = async (
    canvasEl: HTMLCanvasElement,
    thumbnailUrl: string,
    videoWidth: number,
    videoHeight: number,
    maxCanvasWidth: number = 800,
    maxCanvasHeight: number = 450,
  ): Promise<void> => {
    canvasElement.value = canvasEl

    // Calculate optimal canvas dimensions maintaining aspect ratio
    const aspectRatio = videoWidth / videoHeight
    let canvasWidth: number
    let canvasHeight: number

    if (aspectRatio > maxCanvasWidth / maxCanvasHeight) {
      canvasWidth = maxCanvasWidth
      canvasHeight = maxCanvasWidth / aspectRatio
    } else {
      canvasHeight = maxCanvasHeight
      canvasWidth = maxCanvasHeight * aspectRatio
    }

    // Update dimensions
    canvasSize.value = { width: canvasWidth, height: canvasHeight }
    videoSize.value = { width: videoWidth, height: videoHeight }

    // Initialize Fabric.js canvas
    canvas.value = new Canvas(canvasEl, {
      width: canvasWidth,
      height: canvasHeight,
      backgroundColor: 'transparent',
      selection: true,
    })

    // Load thumbnail as background
    await loadThumbnailBackground(thumbnailUrl)

    // Set up canvas event listeners
    setupCanvasEvents()

    isCanvasReady.value = true

    console.log('✅ Canvas initialized:', {
      canvasSize: `${canvasWidth}x${canvasHeight}`,
      videoSize: `${videoWidth}x${videoHeight}`,
      scaleFactors: `${scaleFactors.value.x.toFixed(2)}x, ${scaleFactors.value.y.toFixed(2)}x`,
    })
  }

  /**
   * Load video thumbnail as canvas background
   */
  const loadThumbnailBackground = async (thumbnailUrl: string): Promise<void> => {
    if (!canvas.value) return

    // If no thumbnail URL provided, use a solid color background
    if (!thumbnailUrl || thumbnailUrl.trim() === '') {
      canvas.value.backgroundColor = '#4A90E2'
      canvas.value.renderAll()
      return
    }

    return new Promise((resolve) => {
      Image.fromURL(thumbnailUrl, {}).then((img: Image) => {
        img.set({
          scaleX: canvasSize.value.width / videoSize.value.width,
          scaleY: canvasSize.value.height / videoSize.value.height,
          selectable: false,
          evented: false,
        })

        canvas.value!.backgroundImage = img
        canvas.value!.renderAll()
        resolve()
      })
    })
  }

  /**
   * Set up canvas event listeners for text interaction
   */
  const setupCanvasEvents = (): void => {
    if (!canvas.value) return

    // Text selection events
    canvas.value.on('selection:created', (e: TEvent) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected as Text
        console.log('📝 Text selected:', activeTextObject.value.text)
      }
    })

    canvas.value.on('selection:updated', (e: TEvent) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected as Text
      }
    })

    canvas.value.on('selection:cleared', () => {
      activeTextObject.value = null
    })

    // Text modification events
    canvas.value.on('object:modified', (e: TEvent) => {
      const obj = e.target
      if (obj && obj.type === 'text') {
        // Force coordinate update after modification
        obj.setCoords()
        console.log('🔄 Text modified, coordinates updated')
      }
    })

    canvas.value.on('text:changed', (e: TEvent) => {
      const obj = e.target as Text
      if (obj) {
        console.log('✏️ Text content changed:', obj.text)
      }
    })
  }

  // ==================== TEXT OBJECT MANAGEMENT ====================

  /**
   * Add new text object to canvas
   */
  const addTextObject = async (
    text: string = 'New Text',
    x?: number,
    y?: number,
    options?: Partial<Text>,
  ): Promise<Text | null> => {
    if (!canvas.value) return null

    const defaultX = x ?? canvasSize.value.width / 2
    const defaultY = y ?? canvasSize.value.height / 2

    const textObject = new Text(text, {
      left: defaultX,
      top: defaultY,
      fontSize: 24,
      fontFamily: 'Arial',
      fill: '#ffffff',
      textAlign: 'center',
      originX: 'center',
      originY: 'center',
      editable: true,
      ...options,
    })

    canvas.value.add(textObject)
    canvas.value.setActiveObject(textObject)
    activeTextObject.value = textObject

    console.log('✅ Text object added:', text)
    return textObject
  }

  /**
   * Remove text object from canvas
   */
  const removeTextObject = (textObj?: Text): void => {
    if (!canvas.value) return

    const obj = textObj || activeTextObject.value
    if (obj) {
      canvas.value.remove(obj)
      if (obj === activeTextObject.value) {
        activeTextObject.value = null
      }
      console.log('🗑️ Text object removed')
    }
  }

  /**
   * Update text object properties
   */
  const updateTextProperty = (property: string, value: any, textObj?: Text): void => {
    const obj = textObj || activeTextObject.value
    if (!obj || !canvas.value) return

    obj.set(property as keyof Text, value)
    canvas.value.renderAll()

    console.log(`🎨 Text property updated: ${property} = ${value}`)
  }

  /**
   * Set text background color
   */
  const setTextBackground = (color: string | null): void => {
    if (!activeTextObject.value || !canvas.value) return

    activeTextObject.value.set('backgroundColor', color)
    canvas.value.renderAll()
  }

  /**
   * Set text shadow
   */
  const setTextShadow = (
    enabled: boolean,
    options?: { color?: string; offsetX?: number; offsetY?: number; blur?: number },
  ): void => {
    if (!activeTextObject.value || !canvas.value) return

    if (enabled && options) {
      activeTextObject.value.set('shadow', {
        color: options.color || '#000000',
        offsetX: options.offsetX || 2,
        offsetY: options.offsetY || 2,
        blur: options.blur || 3,
      })
    } else {
      activeTextObject.value.set('shadow', null)
    }

    canvas.value.renderAll()
  }

  /**
   * Set text stroke/outline
   */
  const setTextStroke = (enabled: boolean, options?: { color?: string; width?: number }): void => {
    if (!activeTextObject.value || !canvas.value) return

    if (enabled && options) {
      activeTextObject.value.set({
        stroke: options.color || '#000000',
        strokeWidth: options.width || 2,
      })
    } else {
      activeTextObject.value.set({
        stroke: '',
        strokeWidth: 0,
      })
    }

    canvas.value.renderAll()
  }

  // ==================== COORDINATE EXTRACTION ====================

  /**
   * Extract coordinates from Fabric.js text object
   */
  const extractTextCoordinates = (textObj: Text) => {
    textObj.setCoords()

    return {
      canvasX: textObj.left || 0,
      canvasY: textObj.top || 0,
      canvasWidth: textObj.width || 0,
      canvasHeight: textObj.height || 0,
      videoX: Math.round((textObj.left || 0) * scaleFactors.value.x),
      videoY: Math.round((textObj.top || 0) * scaleFactors.value.y),
      videoWidth: Math.round((textObj.width || 0) * scaleFactors.value.x),
      videoHeight: Math.round((textObj.height || 0) * scaleFactors.value.y),
    }
  }

  // ==================== CLEANUP ====================

  /**
   * Dispose of canvas and cleanup
   */
  const dispose = (): void => {
    if (canvas.value) {
      canvas.value.dispose()
      canvas.value = null
    }
    canvasElement.value = null
    activeTextObject.value = null
    isCanvasReady.value = false

    console.log('🧹 Canvas disposed')
  }

  // Cleanup on unmount
  onUnmounted(() => {
    dispose()
  })

  // ==================== PUBLIC API ====================

  return {
    // State
    canvas: readonly(canvas),
    canvasElement: readonly(canvasElement),
    isCanvasReady: readonly(isCanvasReady),
    activeTextObject: readonly(activeTextObject),
    canvasSize: readonly(canvasSize),
    videoSize: readonly(videoSize),
    scaleFactors: readonly(scaleFactors),

    // Computed
    hasActiveText,

    // Methods
    initializeCanvas,
    addTextObject,
    removeTextObject,
    updateTextProperty,
    setTextBackground,
    setTextShadow,
    setTextStroke,
    extractTextCoordinates,
    dispose,
  }
}
