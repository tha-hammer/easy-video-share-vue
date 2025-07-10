// Text Overlay Type Definitions for Video Segment Text Editing

import type { fabric } from 'fabric'

// Temporary fix for fabric types
declare module 'fabric' {
  export namespace fabric {
    interface Point {
      x: number
      y: number
    }
    interface Shadow {
      color?: string
      offsetX?: number
      offsetY?: number
      blur?: number
    }
    interface Pattern {
      // Pattern properties - using object type instead of empty interface
      [key: string]: unknown
    }
    interface Gradient {
      // Gradient properties - using object type instead of empty interface
      [key: string]: unknown
    }
  }
}

// Core Text Overlay Interface
export interface TextOverlay {
  id: string
  segmentId: string
  text: string

  // Position and dimensions (in video coordinates)
  x: number
  y: number
  width: number
  height: number

  // Font properties
  fontSize: number
  fontFamily: string
  fontWeight: 'normal' | 'bold' | 'lighter' | 'bolder' | string
  fontStyle: 'normal' | 'italic' | 'oblique'

  // Colors and appearance
  color: string
  backgroundColor?: string
  opacity: number

  // Transformations
  rotation: number // in degrees
  scaleX: number
  scaleY: number
  skewX?: number
  skewY?: number

  // Text effects
  shadow?: TextShadow
  stroke?: TextStroke

  // Timing (for video playback)
  startTime: number // seconds
  endTime: number // seconds

  // Metadata
  createdAt: string
  updatedAt: string
}

// Shadow effect properties
export interface TextShadow {
  enabled: boolean
  color: string
  offsetX: number
  offsetY: number
  blur: number
  opacity?: number
}

// Stroke/outline properties
export interface TextStroke {
  enabled: boolean
  color: string
  width: number
  opacity?: number
}

// Fabric.js Text Object Extended Interface
export interface FabricTextObject {
  // Basic text properties
  text: string
  left: number
  top: number
  width: number
  height: number

  // Font properties
  fontSize: number
  fontFamily: string
  fontWeight: string | number
  fontStyle: string

  // Colors and appearance
  fill: string | fabric.Pattern | fabric.Gradient
  backgroundColor?: string
  opacity: number

  // Transformations
  angle: number // in degrees
  scaleX: number
  scaleY: number
  skewX: number
  skewY: number

  // Stroke properties
  stroke?: string | fabric.Pattern | fabric.Gradient
  strokeWidth: number

  // Shadow properties
  shadow?: fabric.Shadow | string

  // Fabric.js specific coordinates (CRITICAL for coordinate translation)
  aCoords: {
    tl: fabric.Point // top-left corner
    tr: fabric.Point // top-right corner
    bl: fabric.Point // bottom-left corner
    br: fabric.Point // bottom-right corner
  }

  // Object state
  visible: boolean
  selectable: boolean
  evented: boolean

  // Methods for coordinate calculation
  setCoords(): void
  calcACoords(): {
    tl: fabric.Point // top-left corner
    tr: fabric.Point // top-right corner
    bl: fabric.Point // bottom-left corner
    br: fabric.Point // bottom-right corner
  }
}

// FFmpeg drawtext filter representation
export interface FFmpegTextFilter {
  // Core text properties
  text: string
  x: number
  y: number

  // Font properties
  fontsize: number
  fontcolor: string
  fontfile: string

  // Optional properties
  alpha?: number // opacity (0.0 - 1.0)
  angle?: number // rotation in radians

  // Shadow properties
  shadowcolor?: string
  shadowx?: number
  shadowy?: number

  // Border/stroke properties
  bordercolor?: string
  borderw?: number

  // Timing properties
  enable?: string // time range expression

  // Complete filter string for FFmpeg
  drawTextFilter: string
}

// Canvas and video dimension information
export interface CanvasVideoMapping {
  // Canvas dimensions (what user sees)
  canvasWidth: number
  canvasHeight: number

  // Video dimensions (actual video resolution)
  videoWidth: number
  videoHeight: number

  // Scaling factors
  scaleX: number // videoWidth / canvasWidth
  scaleY: number // videoHeight / canvasHeight

  // Aspect ratio information
  canvasAspectRatio: number
  videoAspectRatio: number

  // Letterboxing/pillarboxing offsets (if needed)
  offsetX: number
  offsetY: number
}

// Text overlay template for reusability
export interface TextOverlayTemplate {
  id: string
  name: string
  description?: string

  // Style properties that can be applied to new text
  fontSize: number
  fontFamily: string
  fontWeight: string
  fontStyle: 'normal' | 'italic' | 'oblique'
  color: string
  backgroundColor?: string
  shadow?: TextShadow
  stroke?: TextStroke

  // Default positioning (relative to video dimensions)
  defaultX: number // 0.0 - 1.0 (percentage of video width)
  defaultY: number // 0.0 - 1.0 (percentage of video height)

  // Metadata
  isDefault: boolean
  createdAt: string
  updatedAt: string
}

// Text overlay operation for undo/redo system
export interface TextOverlayOperation {
  id: string
  type: 'create' | 'update' | 'delete' | 'move' | 'style'
  segmentId: string
  overlayId: string

  // State before and after operation - can be single overlay or bulk operation
  previousState?: Partial<TextOverlay> | { overlays: TextOverlay[] }
  newState?: Partial<TextOverlay> | { overlays: TextOverlay[] }

  timestamp: string
}

// Coordinate extraction result from Fabric.js
export interface ExtractedCoordinates {
  // Bounding box in canvas coordinates
  canvasX: number
  canvasY: number
  canvasWidth: number
  canvasHeight: number

  // Transformed coordinates (accounting for rotation, scale, etc.)
  topLeft: { x: number; y: number }
  topRight: { x: number; y: number }
  bottomLeft: { x: number; y: number }
  bottomRight: { x: number; y: number }

  // Center point
  centerX: number
  centerY: number

  // Transformation properties
  rotation: number
  scaleX: number
  scaleY: number
}

// Video coordinates after translation
export interface VideoCoordinates {
  // Position in video pixels
  x: number
  y: number
  width: number
  height: number

  // Transformed properties for FFmpeg
  fontSize: number
  rotation: number // in radians for FFmpeg

  // Validation information
  isWithinBounds: boolean
  clampedX?: number
  clampedY?: number
}

// Font mapping for FFmpeg compatibility
export interface FontMapping {
  fabricFont: string
  ffmpegFontFile: string
  fallbackFont: string
  isAvailable: boolean
}

// Available fonts configuration
export const AVAILABLE_FONTS: FontMapping[] = [
  {
    fabricFont: 'Arial',
    ffmpegFontFile: '/opt/fonts/arial.ttf',
    fallbackFont: 'sans-serif',
    isAvailable: true,
  },
  {
    fabricFont: 'Helvetica',
    ffmpegFontFile: '/opt/fonts/helvetica.ttf',
    fallbackFont: 'Arial',
    isAvailable: true,
  },
  {
    fabricFont: 'Times New Roman',
    ffmpegFontFile: '/opt/fonts/times.ttf',
    fallbackFont: 'serif',
    isAvailable: true,
  },
  {
    fabricFont: 'Georgia',
    ffmpegFontFile: '/opt/fonts/georgia.ttf',
    fallbackFont: 'Times New Roman',
    isAvailable: true,
  },
  {
    fabricFont: 'Verdana',
    ffmpegFontFile: '/opt/fonts/verdana.ttf',
    fallbackFont: 'Arial',
    isAvailable: true,
  },
  {
    fabricFont: 'Impact',
    ffmpegFontFile: '/opt/fonts/impact.ttf',
    fallbackFont: 'Arial',
    isAvailable: true,
  },
]

// Color format definitions
export type ColorFormat = 'hex' | 'rgb' | 'rgba' | 'hsl' | 'hsla' | 'named'

// Text alignment options
export type TextAlignment = 'left' | 'center' | 'right' | 'justify'

// Text transformation options
export type TextTransform = 'none' | 'uppercase' | 'lowercase' | 'capitalize'

// Export utility type for partial text overlay updates
export type TextOverlayUpdate = Partial<Omit<TextOverlay, 'id' | 'segmentId' | 'createdAt'>>
