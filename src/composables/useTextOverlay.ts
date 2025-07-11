// Text Overlay Management Composable
// This is the CORE composable that handles all text overlay functionality

/* eslint-disable @typescript-eslint/no-explicit-any */

import { ref, computed, onUnmounted } from 'vue'
import { Canvas, Text, Image } from 'fabric'

export function useTextOverlay() {
  // ==================== STATE MANAGEMENT ====================

  const canvas = ref<Canvas | null>(null)
  const canvasElement = ref<HTMLCanvasElement | null>(null)
  const isCanvasReady = ref(false)
  const activeTextObject = ref<any>(null)

  // Canvas and video dimensions (vertical format)
  const canvasSize = ref({ width: 540, height: 960 })
  const videoSize = ref({ width: 1080, height: 1920 })
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

  const isInitializing = ref(false)

  const initializeCanvas = async (
    canvasEl: HTMLCanvasElement,
    backgroundImageUrl: string,
    videoWidth: number = 1080,
    videoHeight: number = 1920,
    maxCanvasWidth: number = 540,
    maxCanvasHeight: number = 960,
  ) => {
    // Prevent multiple simultaneous initializations
    if (isInitializing.value) {
      console.warn('⚠️ Canvas initialization already in progress, skipping...')
      return
    }

    if (canvas.value) {
      console.log('🎨 Canvas already exists, disposing first...')
      canvas.value.dispose()
      canvas.value = null
    }

    try {
      isInitializing.value = true
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
      isCanvasReady.value = false
      throw error
    } finally {
      isInitializing.value = false
    }
  }

  const loadBackgroundImage = async (imageUrl: string): Promise<void> => {
    console.log('🖼️ Loading background image:', imageUrl)

    // Check if the URL is a video file
    if (imageUrl.includes('.mp4') || imageUrl.includes('video/mp4')) {
      console.log('🎬 Detected video URL, extracting frame as thumbnail...')
      return loadVideoThumbnail(imageUrl)
    }

    return new Promise((resolve, reject) => {
      Image.fromURL(imageUrl, { crossOrigin: 'anonymous' })
        .then((img: any) => {
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

  const loadVideoThumbnail = async (videoUrl: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      console.log('🎬 Loading video thumbnail from:', videoUrl)

      const video = document.createElement('video')
      video.crossOrigin = 'anonymous'
      video.muted = true

      let hasResolved = false // Prevent multiple resolves

      const cleanup = () => {
        video.removeEventListener('loadeddata', onLoadedData)
        video.removeEventListener('seeked', onSeeked)
        video.removeEventListener('error', onError)
        video.removeEventListener('canplay', onCanPlay)
        video.src = ''
        video.load() // Clear the video
      }

      const onLoadedData = () => {
        if (hasResolved) return

        try {
          const seekTime = Math.min(1, video.duration * 0.1)
          console.log(`🎬 Video loaded, seeking to ${seekTime}s`)
          video.currentTime = seekTime
        } catch (error) {
          console.warn('Could not seek video, using first frame')
          video.currentTime = 0
        }
      }

      const onSeeked = () => {
        if (hasResolved) return
        hasResolved = true

        console.log('🎬 Video seeked, extracting frame...')

        try {
          // Create a canvas to extract the frame
          const tempCanvas = document.createElement('canvas')
          const ctx = tempCanvas.getContext('2d')

          if (!ctx) {
            cleanup()
            reject(new Error('Could not get canvas context'))
            return
          }

          // Set canvas size to match video
          tempCanvas.width = video.videoWidth
          tempCanvas.height = video.videoHeight

          // Draw video frame to canvas
          ctx.drawImage(video, 0, 0)

          // Convert to data URL
          const dataUrl = tempCanvas.toDataURL('image/jpeg', 0.8)
          console.log('🎬 Frame extracted, loading into Fabric.js...')

          // Load the extracted frame as background image
          Image.fromURL(dataUrl)
            .then((img: any) => {
              if (!canvas.value) {
                cleanup()
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

              console.log('✅ Video thumbnail loaded successfully (ONCE)')
              cleanup()
              resolve()
            })
            .catch((error: any) => {
              cleanup()
              reject(error)
            })
        } catch (error) {
          console.error('❌ Failed to extract video frame:', error)
          cleanup()
          reject(error)
        }
      }

      const onError = (error: Event) => {
        if (hasResolved) return
        hasResolved = true

        console.error('❌ Video load error:', error)
        cleanup()
        reject(new Error(`Failed to load video: ${error}`))
      }

      const onCanPlay = () => {
        if (hasResolved) return

        // Only seek if we haven't already done so
        if (video.currentTime === 0) {
          try {
            const seekTime = Math.min(1, video.duration * 0.1)
            video.currentTime = seekTime
          } catch (error) {
            video.currentTime = 0
          }
        }
      }

      // Set up event listeners
      video.addEventListener('loadeddata', onLoadedData)
      video.addEventListener('seeked', onSeeked)
      video.addEventListener('error', onError)
      video.addEventListener('canplay', onCanPlay)

      // Start loading the video
      video.src = videoUrl
      video.load()

      // Timeout after 10 seconds
      setTimeout(() => {
        if (!hasResolved) {
          hasResolved = true
          console.warn('⏰ Video thumbnail loading timed out')
          cleanup()
          reject(new Error('Video thumbnail loading timed out'))
        }
      }, 10000)
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
  ): Promise<any> => {
    if (!canvas.value) {
      console.error('❌ Canvas not initialized')
      return null
    }

    try {
      const textObj = new Text(text, {
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

  const removeTextObject = (textObj: any) => {
    if (!canvas.value) return

    canvas.value.remove(textObj)
    canvas.value.renderAll()

    if (activeTextObject.value === textObj) {
      activeTextObject.value = null
    }

    console.log('🗑️ Text object removed')
  }

  const updateTextObject = (textObj: any, properties: any) => {
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
    isInitializing.value = false
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

  // ==================== FABRIC.JS ACOORDS EXTRACTION ====================

  /**
   * Extract precise coordinates from Fabric.js text object using aCoords
   * aCoords represents the absolute corner coordinates after all transformations
   */
  const extractTextCoordinates = (textObj: any): { x: number; y: number } => {
    // Force update of coordinates to ensure accuracy
    textObj.setCoords()

    // Get current aCoords (absolute coordinates)
    const aCoords = textObj.aCoords

    if (!aCoords) {
      // Fallback to calcACoords if aCoords not available
      const calculatedCoords = textObj.calcACoords()
      return { x: calculatedCoords.tl.x, y: calculatedCoords.tl.y }
    }

    // Use top-left corner as reference point for FFmpeg
    return { x: aCoords.tl.x, y: aCoords.tl.y }
  }

  // ==================== FFMPEG FILTER GENERATION ====================

  /**
   * Convert Fabric.js color formats to FFmpeg color format
   */
  const convertColorToFFmpeg = (fabricColor: string | object): string => {
    if (typeof fabricColor !== 'string') {
      return '#ffffff' // Default fallback
    }

    if (fabricColor.startsWith('#')) {
      return fabricColor // "#ffffff" works in FFmpeg
    }

    if (fabricColor.startsWith('rgb')) {
      // Convert rgb(255,255,255) to #ffffff
      const matches = fabricColor.match(/\d+/g)
      if (matches && matches.length >= 3) {
        const r = parseInt(matches[0]).toString(16).padStart(2, '0')
        const g = parseInt(matches[1]).toString(16).padStart(2, '0')
        const b = parseInt(matches[2]).toString(16).padStart(2, '0')
        return `#${r}${g}${b}`
      }
    }

    // Color name mapping
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

  /**
   * Map font family to available FFmpeg font file paths
   */
  const getFontFilePath = (fontFamily: string): string => {
    const fontMap: Record<string, string> = {
      Arial: '/opt/fonts/arial.ttf',
      Helvetica: '/opt/fonts/helvetica.ttf',
      'Times New Roman': '/opt/fonts/times.ttf',
      'Courier New': '/opt/fonts/courier.ttf',
      Georgia: '/opt/fonts/georgia.ttf',
      Verdana: '/opt/fonts/verdana.ttf',
      'Comic Sans MS': '/opt/fonts/comic.ttf',
      Impact: '/opt/fonts/impact.ttf',
    }

    return fontMap[fontFamily] || '/opt/fonts/arial.ttf'
  }

  /**
   * Escape text for FFmpeg (handle special characters)
   */
  const escapeFFmpegText = (text: string): string => {
    return text
      .replace(/'/g, "\\'") // Escape single quotes
      .replace(/:/g, '\\:') // Escape colons
      .replace(/\n/g, ' ') // Replace newlines with spaces
      .replace(/\\/g, '\\\\') // Escape backslashes
      .trim()
  }

  /**
   * Handle text effects translation (shadow, stroke)
   */
  const handleTextEffects = (textObj: any): string[] => {
    const effects: string[] = []

    // Handle shadow
    if (textObj.shadow) {
      const shadow = textObj.shadow as { color?: string; offsetX?: number; offsetY?: number }
      const shadowColor = convertColorToFFmpeg(shadow.color || '#000000')
      const shadowX = Math.round((shadow.offsetX || 0) * scaleFactors.value.x)
      const shadowY = Math.round((shadow.offsetY || 0) * scaleFactors.value.y)

      effects.push(`shadowcolor=${shadowColor}`)
      effects.push(`shadowx=${shadowX}`)
      effects.push(`shadowy=${shadowY}`)
    }

    // Handle stroke/outline
    if (textObj.stroke && textObj.strokeWidth) {
      const strokeColor = convertColorToFFmpeg(textObj.stroke as string)
      const strokeWidth = Math.round(
        (textObj.strokeWidth || 0) * Math.min(scaleFactors.value.x, scaleFactors.value.y),
      )

      effects.push(`bordercolor=${strokeColor}`)
      effects.push(`borderw=${strokeWidth}`)
    }

    return effects
  }

  /**
   * CORE FUNCTION: Convert Fabric.js text object to FFmpeg drawtext filter
   * This is the critical function that makes text overlay positioning work
   */
  const convertToFFmpegFilter = (
    textObj: any,
    segmentDuration: number = 30,
    startTime: number = 0,
  ): string => {
    try {
      // Step 1: Extract precise coordinates using aCoords
      const coordinates = extractTextCoordinates(textObj)
      const videoX = Math.round(coordinates.x * scaleFactors.value.x)
      const videoY = Math.round(coordinates.y * scaleFactors.value.y)

      // Step 2: Convert font size to video scale
      const fontSize = textObj.fontSize || 24
      const videoFontSize = Math.round(
        fontSize * Math.min(scaleFactors.value.x, scaleFactors.value.y),
      )

      // Step 3: Handle color conversion
      const fontColor = convertColorToFFmpeg((textObj.fill as string) || '#ffffff')

      // Step 4: Map font family to available font file
      const fontFile = getFontFilePath(textObj.fontFamily || 'Arial')

      // Step 5: Handle rotation if present
      const rotation = textObj.angle || 0

      // Step 6: Create time range for text display
      const endTime = startTime + segmentDuration
      const timeRange = `between(t,${startTime},${endTime})`

      // Step 7: Build the complete FFmpeg filter
      const filterParts = [
        `text='${escapeFFmpegText(textObj.text || '')}'`,
        `x=${videoX}`,
        `y=${videoY}`,
        `fontsize=${videoFontSize}`,
        `fontcolor=${fontColor}`,
        `fontfile=${fontFile}`,
      ]

      // Add font weight
      if (textObj.fontWeight && textObj.fontWeight !== 'normal') {
        // Note: FFmpeg doesn't have direct fontweight, but some fonts support variants
        // This is a limitation we'll document
      }

      // Add font style
      if (textObj.fontStyle === 'italic') {
        // Note: FFmpeg doesn't have direct italic, but some fonts support variants
        // This is a limitation we'll document
      }

      // Add rotation if present
      if (rotation !== 0) {
        // FFmpeg text rotation is in radians
        const radians = (rotation * Math.PI) / 180
        filterParts.push(`angle=${radians}`)
      }

      // Add text effects (shadow, stroke)
      const effects = handleTextEffects(textObj)
      filterParts.push(...effects)

      // Add time range
      filterParts.push(`enable='${timeRange}'`)

      const drawTextFilter = `drawtext=${filterParts.join(':')}`

      console.log('🎬 Generated FFmpeg filter:', drawTextFilter)
      return drawTextFilter
    } catch (error) {
      console.error('❌ Failed to convert text to FFmpeg filter:', error)
      return ''
    }
  }

  /**
   * Convert all text objects on canvas to FFmpeg filters
   */
  const convertAllTextToFFmpegFilters = (segmentDuration: number = 30): string[] => {
    if (!canvas.value) return []

    const textObjects = canvas.value.getObjects().filter((obj: any) => obj.type === 'text')

    return textObjects.map((textObj) => convertToFFmpegFilter(textObj, segmentDuration))
  }

  /**
   * Generate complete FFmpeg command for applying text overlays
   */
  const generateFFmpegCommand = (
    inputVideoPath: string,
    outputVideoPath: string,
    segmentDuration: number = 30,
  ): string => {
    const filters = convertAllTextToFFmpegFilters(segmentDuration)

    if (filters.length === 0) {
      return `ffmpeg -i "${inputVideoPath}" -c copy "${outputVideoPath}"`
    }

    // For multiple text overlays, we need to chain them
    let filterComplex = ''

    if (filters.length === 1) {
      // Single text overlay
      filterComplex = `-vf "${filters[0]}"`
    } else {
      // Multiple text overlays - chain them
      const chainedFilters = []
      for (let i = 0; i < filters.length; i++) {
        if (i === 0) {
          chainedFilters.push(`[0:v]${filters[i]}[v${i + 1}]`)
        } else if (i === filters.length - 1) {
          chainedFilters.push(`[v${i}]${filters[i]}[vout]`)
        } else {
          chainedFilters.push(`[v${i}]${filters[i]}[v${i + 1}]`)
        }
      }
      filterComplex = `-filter_complex "${chainedFilters.join(';')}" -map "[vout]" -map 0:a`
    }

    return `ffmpeg -i "${inputVideoPath}" ${filterComplex} -c:a copy "${outputVideoPath}"`
  }

  // ==================== EXPORT / RETURN ====================

  return {
    // State
    canvas,
    canvasElement,
    isCanvasReady,
    isInitializing,
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

    // FFmpeg Translation Methods
    extractTextCoordinates,
    convertToFFmpegFilter,
    convertAllTextToFFmpegFilters,
    generateFFmpegCommand,
    convertColorToFFmpeg,
    getFontFilePath,
    escapeFFmpegText,
  }
}
