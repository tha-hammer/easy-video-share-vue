// Text Overlay Management Composable
// This is the CORE composable that handles all text overlay functionality

import { ref, computed, onUnmounted, readonly } from 'vue'
import { Canvas, Text, Image, IEvent } from 'fabric'
import type {
  TextOverlay,
  FFmpegTextFilter,
  CanvasVideoMapping,
  ExtractedCoordinates,
  VideoCoordinates,
} from '@/types/textOverlay'

// Import AVAILABLE_FONTS as a value, not a type
import { AVAILABLE_FONTS } from '@/types/textOverlay'

export function useTextOverlay() {
  // ==================== STATE MANAGEMENT ====================

  const canvas = ref<fabric.Canvas | null>(null)
  const canvasElement = ref<HTMLCanvasElement | null>(null)
  const isCanvasReady = ref(false)
  const activeTextObject = ref<fabric.Text | null>(null)

  // Canvas and video dimensions
  const canvasVideoMapping = ref<CanvasVideoMapping>({
    canvasWidth: 800,
    canvasHeight: 450,
    videoWidth: 1920,
    videoHeight: 1080,
    scaleX: 2.4,
    scaleY: 2.4,
    canvasAspectRatio: 16 / 9,
    videoAspectRatio: 16 / 9,
    offsetX: 0,
    offsetY: 0,
  })

  // Text overlays collection
  const textOverlays = ref<Map<string, TextOverlay>>(new Map())

  // ==================== COMPUTED PROPERTIES ====================

  const hasActiveText = computed(() => activeTextObject.value !== null)

  const canvasSize = computed(() => ({
    width: canvasVideoMapping.value.canvasWidth,
    height: canvasVideoMapping.value.canvasHeight,
  }))

  const videoSize = computed(() => ({
    width: canvasVideoMapping.value.videoWidth,
    height: canvasVideoMapping.value.videoHeight,
  }))

  const scaleFactors = computed(() => ({
    x: canvasVideoMapping.value.scaleX,
    y: canvasVideoMapping.value.scaleY,
  }))

  // ==================== CANVAS LIFECYCLE ====================

  /**
   * Initialize Fabric.js canvas with video thumbnail background
   * Requirement 2.01 - Create SegmentTextEditor Component
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

    // Update canvas-video mapping
    canvasVideoMapping.value = {
      canvasWidth,
      canvasHeight,
      videoWidth,
      videoHeight,
      scaleX: videoWidth / canvasWidth,
      scaleY: videoHeight / canvasHeight,
      canvasAspectRatio: canvasWidth / canvasHeight,
      videoAspectRatio: aspectRatio,
      offsetX: 0,
      offsetY: 0,
    }

    // Initialize Fabric.js canvas
    canvas.value = new fabric.Canvas(canvasEl, {
      width: canvasWidth,
      height: canvasHeight,
      backgroundColor: 'transparent',
      selection: true,
      preserveObjectStacking: true,
    })

    // Load thumbnail as background
    await loadThumbnailBackground(thumbnailUrl)

    // Set up canvas event listeners
    setupCanvasEvents()

    isCanvasReady.value = true

    console.log('✅ Canvas initialized:', {
      canvasSize: `${canvasWidth}x${canvasHeight}`,
      videoSize: `${videoWidth}x${videoHeight}`,
      scaleFactors: `${canvasVideoMapping.value.scaleX.toFixed(2)}x, ${canvasVideoMapping.value.scaleY.toFixed(2)}x`,
    })
  }

  /**
   * Load video thumbnail as canvas background
   */
  const loadThumbnailBackground = async (thumbnailUrl: string): Promise<void> => {
    if (!canvas.value) return

    // If no thumbnail URL provided, use a solid color background
    if (!thumbnailUrl || thumbnailUrl.trim() === '') {
      canvas.value.setBackgroundColor('#4A90E2', canvas.value.renderAll.bind(canvas.value))
      return
    }

    return new Promise((resolve) => {
      fabric.Image.fromURL(thumbnailUrl, (img: fabric.Image) => {
        img.set({
          scaleX: canvasVideoMapping.value.canvasWidth / canvasVideoMapping.value.videoWidth,
          scaleY: canvasVideoMapping.value.canvasHeight / canvasVideoMapping.value.videoHeight,
          selectable: false,
          evented: false,
          excludeFromExport: true,
        })

        canvas.value?.setBackgroundImage(img, canvas.value.renderAll.bind(canvas.value))
        resolve()
      })
    })
  }

  /**
   * Set up canvas event listeners for text interaction
   * Requirement 2.03 - Enable Text Selection and Editing
   */
  const setupCanvasEvents = (): void => {
    if (!canvas.value) return

    // Text selection events
    canvas.value.on('selection:created', (e: fabric.IEvent) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected as fabric.Text
        console.log('📝 Text selected:', activeTextObject.value.text)
      }
    })

    canvas.value.on('selection:updated', (e: fabric.IEvent) => {
      const selected = e.selected?.[0]
      if (selected && selected.type === 'text') {
        activeTextObject.value = selected as fabric.Text
      }
    })

    canvas.value.on('selection:cleared', () => {
      activeTextObject.value = null
    })

    // Text modification events
    canvas.value.on('object:modified', (e: fabric.IEvent) => {
      const obj = e.target
      if (obj && obj.type === 'text') {
        // Force coordinate update after modification
        obj.setCoords()
        console.log('🔄 Text modified, coordinates updated')
      }
    })

    canvas.value.on('text:changed', (e: fabric.IEvent) => {
      const obj = e.target as fabric.Text
      if (obj) {
        console.log('✏️ Text content changed:', obj.text)
      }
    })
  }

  // ==================== COORDINATE EXTRACTION AND TRANSLATION ====================

  /**
   * Extract precise coordinates from Fabric.js text object using aCoords
   * Requirement 3.02 - Create aCoords Extraction Function
   */
  const extractTextCoordinates = (textObj: fabric.Text): ExtractedCoordinates => {
    // Force update of aCoords if needed
    textObj.setCoords()

    // Get current aCoords (absolute coordinates)
    const aCoords = textObj.aCoords

    if (!aCoords) {
      // Fallback to calcACoords if aCoords not available
      const calculatedCoords = textObj.calcACoords()
      return extractFromCalculatedCoords(textObj, calculatedCoords)
    }

    // Extract bounding box from aCoords
    const topLeft = aCoords.tl
    const topRight = aCoords.tr
    const bottomLeft = aCoords.bl
    const bottomRight = aCoords.br

    // Calculate bounding box dimensions
    const minX = Math.min(topLeft.x, topRight.x, bottomLeft.x, bottomRight.x)
    const maxX = Math.max(topLeft.x, topRight.x, bottomLeft.x, bottomRight.x)
    const minY = Math.min(topLeft.y, topRight.y, bottomLeft.y, bottomRight.y)
    const maxY = Math.max(topLeft.y, topRight.y, bottomLeft.y, bottomRight.y)

    return {
      canvasX: minX,
      canvasY: minY,
      canvasWidth: maxX - minX,
      canvasHeight: maxY - minY,
      topLeft: { x: topLeft.x, y: topLeft.y },
      topRight: { x: topRight.x, y: topRight.y },
      bottomLeft: { x: bottomLeft.x, y: bottomLeft.y },
      bottomRight: { x: bottomRight.x, y: bottomRight.y },
      centerX: (minX + maxX) / 2,
      centerY: (minY + maxY) / 2,
      rotation: textObj.angle || 0,
      scaleX: textObj.scaleX || 1,
      scaleY: textObj.scaleY || 1,
    }
  }

  /**
   * Fallback coordinate extraction from calculated coords
   */
  const extractFromCalculatedCoords = (textObj: fabric.Text, coords: any): ExtractedCoordinates => {
    const topLeft = coords.tl
    const topRight = coords.tr
    const bottomLeft = coords.bl
    const bottomRight = coords.br

    const minX = Math.min(topLeft.x, topRight.x, bottomLeft.x, bottomRight.x)
    const maxX = Math.max(topLeft.x, topRight.x, bottomLeft.x, bottomRight.x)
    const minY = Math.min(topLeft.y, topRight.y, bottomLeft.y, bottomRight.y)
    const maxY = Math.max(topLeft.y, topRight.y, bottomLeft.y, bottomRight.y)

    return {
      canvasX: minX,
      canvasY: minY,
      canvasWidth: maxX - minX,
      canvasHeight: maxY - minY,
      topLeft: { x: topLeft.x, y: topLeft.y },
      topRight: { x: topRight.x, y: topRight.y },
      bottomLeft: { x: bottomLeft.x, y: bottomLeft.y },
      bottomRight: { x: bottomRight.x, y: bottomRight.y },
      centerX: (minX + maxX) / 2,
      centerY: (minY + maxY) / 2,
      rotation: textObj.angle || 0,
      scaleX: textObj.scaleX || 1,
      scaleY: textObj.scaleY || 1,
    }
  }

  /**
   * Convert canvas coordinates to video coordinates
   * Requirement 3.04 - Implement FFmpeg Coordinate Converter
   */
  const convertToVideoCoordinates = (canvasCoords: ExtractedCoordinates): VideoCoordinates => {
    const mapping = canvasVideoMapping.value

    // Convert position using scaling factors
    const videoX = Math.round(canvasCoords.canvasX * mapping.scaleX)
    const videoY = Math.round(canvasCoords.canvasY * mapping.scaleY)
    const videoWidth = Math.round(canvasCoords.canvasWidth * mapping.scaleX)
    const videoHeight = Math.round(canvasCoords.canvasHeight * mapping.scaleY)

    // Convert font size (use minimum scale factor to prevent distortion)
    const fontSizeScale = Math.min(mapping.scaleX, mapping.scaleY)
    const fontSize = Math.round((activeTextObject.value?.fontSize || 24) * fontSizeScale)

    // Convert rotation from degrees to radians for FFmpeg
    const rotation = (canvasCoords.rotation * Math.PI) / 180

    // Validate bounds
    const isWithinBounds =
      videoX >= 0 &&
      videoY >= 0 &&
      videoX + videoWidth <= mapping.videoWidth &&
      videoY + videoHeight <= mapping.videoHeight

    // Clamp coordinates if outside bounds
    const clampedX = Math.max(0, Math.min(videoX, mapping.videoWidth - videoWidth))
    const clampedY = Math.max(0, Math.min(videoY, mapping.videoHeight - videoHeight))

    return {
      x: videoX,
      y: videoY,
      width: videoWidth,
      height: videoHeight,
      fontSize,
      rotation,
      isWithinBounds,
      clampedX: !isWithinBounds ? clampedX : undefined,
      clampedY: !isWithinBounds ? clampedY : undefined,
    }
  }

  // ==================== COLOR AND STYLE CONVERSION ====================

  /**
   * Convert Fabric.js color format to FFmpeg-compatible format
   * Requirement 4.03 - Build Color Format Converter
   */
  const convertColorToFFmpeg = (fabricColor: string | any | any): string => {
    // Handle simple string colors
    if (typeof fabricColor === 'string') {
      // Already hex format
      if (fabricColor.startsWith('#')) {
        return fabricColor
      }

      // RGB format - convert to hex
      if (fabricColor.startsWith('rgb')) {
        const matches = fabricColor.match(/\d+/g)
        if (matches && matches.length >= 3) {
          const r = parseInt(matches[0]).toString(16).padStart(2, '0')
          const g = parseInt(matches[1]).toString(16).padStart(2, '0')
          const b = parseInt(matches[2]).toString(16).padStart(2, '0')
          return `#${r}${g}${b}`
        }
      }

      // Named colors
      const colorMap: Record<string, string> = {
        black: '#000000',
        white: '#ffffff',
        red: '#ff0000',
        green: '#00ff00',
        blue: '#0000ff',
        yellow: '#ffff00',
        cyan: '#00ffff',
        magenta: '#ff00ff',
      }

      return colorMap[fabricColor.toLowerCase()] || '#ffffff'
    }

    // For patterns and gradients, return white as fallback
    // TODO: Implement gradient to solid color conversion if needed
    return '#ffffff'
  }

  /**
   * Get FFmpeg font file path for given font family
   * Requirement 4.01 - Create Font Family Mapping
   */
  const getFontFilePath = (fontFamily: string): string => {
    const fontMapping = AVAILABLE_FONTS.find(
      (mapping) => mapping.fabricFont.toLowerCase() === fontFamily.toLowerCase(),
    )

    return fontMapping?.ffmpegFontFile || '/opt/fonts/arial.ttf'
  }

  /**
   * Escape text for FFmpeg drawtext filter
   */
  const escapeFFmpegText = (text: string): string => {
    return text
      .replace(/'/g, "\\'") // Escape single quotes
      .replace(/:/g, '\\:') // Escape colons
      .replace(/\n/g, ' ') // Replace newlines with spaces
      .replace(/\\/g, '\\\\') // Escape backslashes
      .trim()
  }

  // ==================== FFMPEG FILTER GENERATION ====================

  /**
   * Convert Fabric.js text object to complete FFmpeg drawtext filter
   * This is the MAIN CONVERSION function that ties everything together
   * Requirement 1.04 - Implement Coordinate Translation System
   */
  const convertToFFmpegFilter = (
    textObj: fabric.Text,
    startTime: number = 0,
    endTime: number = 30,
  ): FFmpegTextFilter => {
    // Extract coordinates using aCoords
    const canvasCoords = extractTextCoordinates(textObj)
    const videoCoords = convertToVideoCoordinates(canvasCoords)

    // Use clamped coordinates if text is outside bounds
    const finalX = videoCoords.isWithinBounds
      ? videoCoords.x
      : videoCoords.clampedX || videoCoords.x
    const finalY = videoCoords.isWithinBounds
      ? videoCoords.y
      : videoCoords.clampedY || videoCoords.y

    // Convert colors and fonts
    const fontColor = convertColorToFFmpeg(textObj.fill || '#ffffff')
    const fontFile = getFontFilePath(textObj.fontFamily || 'Arial')
    const escapedText = escapeFFmpegText(textObj.text || '')

    // Build filter parts
    const filterParts = [
      `text='${escapedText}'`,
      `x=${finalX}`,
      `y=${finalY}`,
      `fontsize=${videoCoords.fontSize}`,
      `fontcolor=${fontColor}`,
      `fontfile=${fontFile}`,
    ]

    // Add rotation if present
    if (Math.abs(videoCoords.rotation) > 0.01) {
      filterParts.push(`angle=${videoCoords.rotation.toFixed(3)}`)
    }

    // Add shadow if present
    if (textObj.shadow) {
      const shadow = textObj.shadow as any
      const shadowColor = convertColorToFFmpeg(shadow.color || '#000000')
      const shadowX = Math.round((shadow.offsetX || 2) * canvasVideoMapping.value.scaleX)
      const shadowY = Math.round((shadow.offsetY || 2) * canvasVideoMapping.value.scaleY)

      filterParts.push(`shadowcolor=${shadowColor}`)
      filterParts.push(`shadowx=${shadowX}`)
      filterParts.push(`shadowy=${shadowY}`)
    }

    // Add stroke/border if present
    if (textObj.stroke && textObj.strokeWidth && textObj.strokeWidth > 0) {
      const borderColor = convertColorToFFmpeg(textObj.stroke)
      const borderWidth = Math.round(
        (textObj.strokeWidth || 1) *
          Math.min(canvasVideoMapping.value.scaleX, canvasVideoMapping.value.scaleY),
      )

      filterParts.push(`bordercolor=${borderColor}`)
      filterParts.push(`borderw=${borderWidth}`)
    }

    // Add time range
    const timeRange = `between(t,${startTime},${endTime})`
    filterParts.push(`enable='${timeRange}'`)

    // Combine into complete filter
    const drawTextFilter = `drawtext=${filterParts.join(':')}`

    const filter: FFmpegTextFilter = {
      text: escapedText,
      x: finalX,
      y: finalY,
      fontsize: videoCoords.fontSize,
      fontcolor: fontColor,
      fontfile: fontFile,
      alpha: textObj.opacity,
      angle: Math.abs(videoCoords.rotation) > 0.01 ? videoCoords.rotation : undefined,
      enable: timeRange,
      drawTextFilter,
    }

    console.log('🎬 Generated FFmpeg filter:', drawTextFilter)
    return filter
  }

  // ==================== TEXT OBJECT MANAGEMENT ====================

  /**
   * Add new text object to canvas
   * Requirement 2.02 - Implement Text Object Creation
   */
  const addTextObject = async (
    text: string = 'New Text',
    x?: number,
    y?: number,
    options?: Partial<fabric.Text>,
  ): Promise<fabric.Text | null> => {
    if (!canvas.value) return null

    const defaultX = x ?? canvasVideoMapping.value.canvasWidth / 2
    const defaultY = y ?? canvasVideoMapping.value.canvasHeight / 2

    const textObject = new fabric.Text(text, {
      left: defaultX,
      top: defaultY,
      fontSize: 24,
      fontFamily: 'Arial',
      fill: '#ffffff',
      stroke: '#000000',
      strokeWidth: 0,
      selectable: true,
      editable: true,
      ...options,
    })

    canvas.value.add(textObject)
    canvas.value.setActiveObject(textObject)
    canvas.value.renderAll()

    console.log('✅ Text object added:', textObject.text)
    return textObject
  }

  /**
   * Remove text object from canvas
   */
  const removeTextObject = (textObj?: fabric.Text): void => {
    if (!canvas.value) return

    const objToRemove = textObj || activeTextObject.value
    if (objToRemove) {
      canvas.value.remove(objToRemove)
      if (activeTextObject.value === objToRemove) {
        activeTextObject.value = null
      }
      console.log('➖ Removed text object')
    }
  }

  /**
   * Update text object properties
   * Requirement 2.04 - Add Text Property Controls
   */
  const updateTextProperty = (property: string, value: any, textObj?: fabric.Text): void => {
    const obj = textObj || activeTextObject.value
    if (!obj || !canvas.value) return

    obj.set(property as keyof fabric.Text, value)
    canvas.value.renderAll()

    console.log(`🔧 Updated ${property}:`, value)
  }

  // ==================== CLEANUP ====================

  /**
   * Dispose of canvas and clean up resources
   */
  const dispose = (): void => {
    if (canvas.value) {
      canvas.value.dispose()
      canvas.value = null
    }

    isCanvasReady.value = false
    activeTextObject.value = null
    textOverlays.value.clear()

    console.log('🧹 Canvas disposed and resources cleaned up')
  }

  // Cleanup on component unmount
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
    canvasVideoMapping: readonly(canvasVideoMapping),
    textOverlays: readonly(textOverlays),

    // Computed
    hasActiveText,
    canvasSize,
    videoSize,
    scaleFactors,

    // Canvas lifecycle
    initializeCanvas,
    loadThumbnailBackground,
    dispose,

    // Coordinate translation (CORE FUNCTIONALITY)
    extractTextCoordinates,
    convertToVideoCoordinates,
    convertToFFmpegFilter,

    // Color and style conversion
    convertColorToFFmpeg,
    getFontFilePath,
    escapeFFmpegText,

    // Text object management
    addTextObject,
    removeTextObject,
    updateTextProperty,
  }
}
