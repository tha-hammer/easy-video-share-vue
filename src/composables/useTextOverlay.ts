// Text Overlay Management Composable
// This is the CORE composable that handles all text overlay functionality

import { ref, computed, onUnmounted } from 'vue'
import { Canvas, FabricText, FabricImage } from 'fabric'

export function useTextOverlay() {
  // ==================== STATE MANAGEMENT ====================

  const canvas = ref<Canvas | null>(null)
  const canvasElement = ref<HTMLCanvasElement | null>(null)
  const isCanvasReady = ref(false)
  const activeTextObject = ref<FabricText | null>(null)

  // Canvas and video dimensions
  const canvasSize = ref({ width: 800, height: 450 })
  const videoSize = ref({ width: 1920, height: 1080 })
  const scaleFactors = computed(() => ({
    x: videoSize.value.width / canvasSize.value.width,
    y: videoSize.value.height / canvasSize.value.height,
  }))

  // ==================== COMPUTED PROPERTIES ====================

  const hasActiveText = computed(() => activeTextObject.value !== null)

  const textObjectCount = computed(() => {
    if (!canvas.value) return 0
    return canvas.value.getObjects().filter((obj: any) => obj.type === 'text').length
  })

  // ==================== CANVAS INITIALIZATION ====================

  const initializeCanvas = async (
    canvasEl: HTMLCanvasElement,
    backgroundImageUrl: string,
    videoWidth: number = 1920,
    videoHeight: number = 1080,
    maxCanvasWidth: number = 800,
    maxCanvasHeight: number = 450,
  ) => {
    try {
      console.log('🎨 Initializing Fabric.js Canvas...')

      // Store video dimensions
      videoSize.value = { width: videoWidth, height: videoHeight }

      // Calculate aspect ratio and canvas size
      const aspectRatio = videoWidth / videoHeight
      let canvasWidth = maxCanvasWidth
      let canvasHeight = maxCanvasWidth / aspectRatio

      if (canvasHeight > maxCanvasHeight) {
        canvasHeight = maxCanvasHeight
        canvasWidth = maxCanvasHeight * aspectRatio
      }

      canvasSize.value = { width: canvasWidth, height: canvasHeight }

      // Create Fabric.js Canvas
      canvas.value = new Canvas(canvasEl, {
        width: canvasWidth,
        height: canvasHeight,
        backgroundColor: '#ffffff',
        preserveObjectStacking: true,
      })

      // Load background image
      if (backgroundImageUrl) {
        await loadBackgroundImage(backgroundImageUrl)
      }

      // Set up event handlers
      setupEventHandlers()

      isCanvasReady.value = true
      console.log('✅ Canvas initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize canvas:', error)
      throw error
    }
  }

  const loadBackgroundImage = async (imageUrl: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      FabricImage.fromURL(imageUrl, { crossOrigin: 'anonymous' })
        .then((img: FabricImage) => {
          if (!canvas.value) {
            reject(new Error('Canvas not initialized'))
            return
          }

          // Scale image to fit canvas
          const scaleX = canvasSize.value.width / (img.width || 1)
          const scaleY = canvasSize.value.height / (img.height || 1)

          img.set({
            scaleX,
            scaleY,
            selectable: false,
            evented: false,
          })

          canvas.value.backgroundImage = img
          canvas.value.renderAll()
          resolve()
        })
        .catch(reject)
    })
  }

  const setupEventHandlers = () => {
    if (!canvas.value) return

    // Selection events
    canvas.value.on('selection:created', (e: any) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected
      }
    })

    canvas.value.on('selection:updated', (e: any) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected
      }
    })

    canvas.value.on('selection:cleared', () => {
      activeTextObject.value = null
    })

    // Object modification events
    canvas.value.on('object:modified', (e: any) => {
      const obj = e.target
      if (obj && obj.type === 'text') {
        obj.setCoords()
      }
    })
  }

  // ==================== TEXT OBJECT MANAGEMENT ====================

  const addTextObject = async (
    text: string = 'Sample Text',
    left: number = 100,
    top: number = 100,
    options: any = {},
  ): Promise<fabric.Text | null> => {
    if (!canvas.value) {
      console.error('❌ Canvas not initialized')
      return null
    }

    try {
      const textObj = new fabric.Text(text, {
        left,
        top,
        fontFamily: options.fontFamily || 'Arial',
        fontSize: options.fontSize || 24,
        fill: options.fill || '#000000',
        fontWeight: options.fontWeight || 'normal',
        ...options,
      })

      canvas.value.add(textObj)
      canvas.value.setActiveObject(textObj)
      canvas.value.renderAll()

      activeTextObject.value = textObj

      console.log('✅ Text object added:', text)
      return textObj
    } catch (error) {
      console.error('❌ Failed to add text object:', error)
      return null
    }
  }

  const removeTextObject = (textObj: fabric.Text) => {
    if (!canvas.value) return

    canvas.value.remove(textObj)
    canvas.value.renderAll()

    if (activeTextObject.value === textObj) {
      activeTextObject.value = null
    }

    console.log('🗑️ Text object removed')
  }

  const updateTextObject = (textObj: fabric.Text, properties: any) => {
    if (!canvas.value) return

    textObj.set(properties)
    canvas.value.renderAll()
  }

  // ==================== CANVAS MANAGEMENT ====================

  const clearCanvas = () => {
    if (!canvas.value) return

    canvas.value.clear()
    activeTextObject.value = null
  }

  const dispose = () => {
    if (canvas.value) {
      canvas.value.dispose()
      canvas.value = null
    }
    activeTextObject.value = null
    isCanvasReady.value = false
    console.log('🧹 Canvas disposed')
  }

  // ==================== COORDINATE CONVERSION ====================

  const canvasToVideoCoordinates = (canvasX: number, canvasY: number) => {
    return {
      x: canvasX * scaleFactors.value.x,
      y: canvasY * scaleFactors.value.y,
    }
  }

  const videoToCanvasCoordinates = (videoX: number, videoY: number) => {
    return {
      x: videoX / scaleFactors.value.x,
      y: videoY / scaleFactors.value.y,
    }
  }

  // ==================== EXPORT / RETURN ====================

  return {
    // State
    canvas,
    canvasElement,
    isCanvasReady,
    activeTextObject,
    canvasSize,
    videoSize,
    scaleFactors,

    // Computed
    hasActiveText,
    textObjectCount,

    // Methods
    initializeCanvas,
    addTextObject,
    removeTextObject,
    updateTextObject,
    clearCanvas,
    dispose,
    canvasToVideoCoordinates,
    videoToCanvasCoordinates,
  }
}
