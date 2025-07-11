// Comprehensive Fabric.js v6 Type Declarations
// This file provides proper type support for Fabric.js v6 ESM modules

/* eslint-disable @typescript-eslint/no-explicit-any */

declare module 'fabric' {
  // Core object types
  export type TFiller = string | Gradient | Pattern
  export type TPointerEvent = MouseEvent | TouchEvent
  export type TPointerEventInfo<T = MouseEvent | TouchEvent> = {
    e: T
    target?: FabricObject
    pointer: Point
    absolutePointer: Point
    transform?: Transform
  }

  // Basic utility types
  export interface Point {
    x: number
    y: number
  }

  export interface Transform {
    target: FabricObject
    action: string
    actionHandler: (eventData: TPointerEvent, transform: Transform, x: number, y: number) => boolean
    corner: string
    scaleX: number
    scaleY: number
    skewX: number
    skewY: number
    offsetX: number
    offsetY: number
    originX: string
    originY: string
    ex: number
    ey: number
    lastX: number
    lastY: number
    theta: number
    width: number
    height: number
  }

  // Gradient and Pattern types
  export interface Gradient {
    type: 'linear' | 'radial'
    coords: any
    colorStops: Array<{ offset: number; color: string }>
    offsetX?: number
    offsetY?: number
    gradientTransform?: [number, number, number, number, number, number]
    gradientUnits?: 'pixels' | 'userSpaceOnUse'
    toLive(ctx: CanvasRenderingContext2D): CanvasGradient
  }

  export interface Pattern {
    source: HTMLImageElement | HTMLCanvasElement | HTMLVideoElement
    repeat: 'repeat' | 'repeat-x' | 'repeat-y' | 'no-repeat'
    offsetX?: number
    offsetY?: number
    patternTransform?: [number, number, number, number, number, number]
    toLive(ctx: CanvasRenderingContext2D): CanvasPattern
  }

  // Shadow type
  export interface Shadow {
    color?: string
    blur?: number
    offsetX?: number
    offsetY?: number
    affectStroke?: boolean
    nonScaling?: boolean
  }

  // Base object properties interface
  export interface FabricObjectProps {
    left?: number
    top?: number
    width?: number
    height?: number
    scaleX?: number
    scaleY?: number
    angle?: number
    opacity?: number
    fill?: TFiller
    stroke?: TFiller
    strokeWidth?: number
    strokeDashArray?: number[]
    strokeLineCap?: 'round' | 'butt' | 'square'
    strokeLineJoin?: 'round' | 'bevel' | 'miter'
    strokeMiterLimit?: number
    shadow?: Shadow | null
    visible?: boolean
    selectable?: boolean
    evented?: boolean
    originX?: 'left' | 'center' | 'right'
    originY?: 'top' | 'center' | 'bottom'
    backgroundColor?: string
    borderColor?: string
    cornerColor?: string
    cornerSize?: number
    transparentCorners?: boolean
    hoverCursor?: string
    moveCursor?: string
    padding?: number
    borderOpacityWhenMoving?: number
    borderScaleFactor?: number
    minScaleLimit?: number
    lockMovementX?: boolean
    lockMovementY?: boolean
    lockRotation?: boolean
    lockScalingX?: boolean
    lockScalingY?: boolean
    lockSkewingX?: boolean
    lockSkewingY?: boolean
    lockScalingFlip?: boolean
    excludeFromExport?: boolean
    flipX?: boolean
    flipY?: number
    skewX?: number
    skewY?: number
    clipPath?: FabricObject
    globalCompositeOperation?: string
    paintFirst?: 'fill' | 'stroke'
    centeredScaling?: boolean
    centeredRotation?: boolean
    [key: string]: any
  }

  // Text-specific properties
  export interface TextProps extends FabricObjectProps {
    text?: string
    fontSize?: number
    fontWeight?: string | number
    fontFamily?: string
    fontStyle?: 'normal' | 'italic' | 'oblique'
    textAlign?: 'left' | 'center' | 'right' | 'justify'
    lineHeight?: number
    charSpacing?: number
    textBackgroundColor?: string
    underline?: boolean
    overline?: boolean
    linethrough?: boolean
  }

  // Base FabricObject class
  export class FabricObject {
    // Core properties
    left: number
    top: number
    width: number
    height: number
    scaleX: number
    scaleY: number
    angle: number
    opacity: number
    fill: TFiller
    stroke: TFiller
    strokeWidth: number
    visible: boolean
    selectable: boolean
    evented: boolean
    originX: 'left' | 'center' | 'right'
    originY: 'top' | 'center' | 'bottom'
    shadow: Shadow | null
    backgroundColor: string
    type: string

    // Methods
    constructor(options?: FabricObjectProps)
    set(key: string | FabricObjectProps, value?: any): this
    get(key: string): any
    setCoords(): void
    getBoundingRect(): { left: number; top: number; width: number; height: number }
    clone(): Promise<FabricObject>
    toObject(): any
    toJSON(): any
    animate(property: string | FabricObjectProps, value?: any): void
    dispose(): void

    // Event methods
    on(eventName: string, handler: (...args: any[]) => void): void
    off(eventName: string, handler?: (...args: any[]) => void): void
    fire(eventName: string, options?: any): void

    // Transform methods
    scale(value: number): this
    scaleToWidth(value: number): this
    scaleToHeight(value: number): this
    rotate(angle: number): this
    center(): this
    centerH(): this
    centerV(): this

    // Rendering
    render(ctx: CanvasRenderingContext2D): void

    // Additional properties and methods as needed
    [key: string]: any
  }

  // Text class extending FabricObject
  export class FabricText extends FabricObject {
    text: string
    fontSize: number
    fontWeight: string | number
    fontFamily: string
    fontStyle: 'normal' | 'italic' | 'oblique'
    textAlign: 'left' | 'center' | 'right' | 'justify'
    lineHeight: number
    charSpacing: number
    textBackgroundColor: string
    underline: boolean
    overline: boolean
    linethrough: boolean

    constructor(text: string, options?: TextProps)

    // Text-specific methods
    _setScript(): void
    _forceClearCache(): void
    _extendStyles(): void
    _setStyleDeclaration(): void
    getSelectionStyles(): any
    setSelectionStyles(): void
    getSelectedText(): string
    selectAll(): void
    exitEditing(): void

    // Additional text methods
    [key: string]: any
  }

  // Alias for Text class for compatibility
  export class Text extends FabricText {
    constructor(text: string, options?: TextProps)
  }

  // Image class
  export class FabricImage extends FabricObject {
    constructor(
      element: HTMLImageElement | HTMLCanvasElement | HTMLVideoElement | string,
      options?: FabricObjectProps,
    )

    static fromURL(url: string, options?: any): Promise<FabricImage>
    static fromObject(object: any): Promise<FabricImage>

    setSrc(src: string, callback?: () => void): void
    applyFilters(): void

    // Image properties
    crossOrigin: string | null
    _element: HTMLImageElement | HTMLCanvasElement | HTMLVideoElement;

    [key: string]: any
  }

  // Alias for Image class
  export class Image extends FabricImage {
    constructor(
      element: HTMLImageElement | HTMLCanvasElement | HTMLVideoElement | string,
      options?: FabricObjectProps,
    )
    static fromURL(url: string, options?: any): Promise<Image>
  }

  // Canvas events interface
  export interface CanvasEvents {
    'mouse:down': { e: TPointerEvent; target?: FabricObject; pointer: Point }
    'mouse:move': { e: TPointerEvent; target?: FabricObject; pointer: Point }
    'mouse:up': { e: TPointerEvent; target?: FabricObject; pointer: Point }
    'object:added': { target: FabricObject }
    'object:removed': { target: FabricObject }
    'object:modified': { target: FabricObject }
    'object:moving': { target: FabricObject }
    'object:scaling': { target: FabricObject }
    'object:rotating': { target: FabricObject }
    'selection:created': { selected: FabricObject[] }
    'selection:updated': { selected: FabricObject[]; deselected: FabricObject[] }
    'selection:cleared': { deselected: FabricObject[] }
    'before:render': object
    'after:render': object
    'canvas:cleared': object
    [key: string]: any
  }

  // Canvas class
  export class Canvas {
    // Core properties
    width: number
    height: number
    backgroundColor: string | Gradient | Pattern
    backgroundImage: FabricImage | null
    selection: boolean
    preserveObjectStacking: boolean

    constructor(
      canvasElement: HTMLCanvasElement | string,
      options?: {
        width?: number
        height?: number
        backgroundColor?: string | Gradient | Pattern
        backgroundImage?: FabricImage
        selection?: boolean
        preserveObjectStacking?: boolean
        [key: string]: any
      },
    )

    // Object management
    add(...objects: any[]): this
    remove(...objects: any[]): this
    clear(): this
    getObjects(): any[]
    getActiveObject(): any
    getActiveObjects(): any[]
    setActiveObject(object: any): this
    discardActiveObject(): this

    // Selection methods
    setActiveObject(object: any): this
    getActiveObject(): any
    getActiveObjects(): any[]

    // Rendering
    renderAll(): this
    requestRenderAll(): void

    // Events
    on<K extends keyof CanvasEvents>(eventName: K, handler: (e: CanvasEvents[K]) => void): void
    on(eventName: string, handler: (...args: any[]) => void): void
    off(eventName: string, handler?: (...args: any[]) => void): void
    fire(eventName: string, options?: any): void

    // Disposal
    dispose(): void

    // Coordinate conversion
    getPointer(e: Event): Point
    getViewportTransform(): number[]
    setViewportTransform(vpt: number[]): this

    // JSON/Object serialization
    toJSON(): any
    toObject(): any
    loadFromJSON(json: any, callback?: () => void): void

    // Size and dimensions
    setWidth(value: number): this
    setHeight(value: number): this
    setDimensions(dimensions: { width: number; height: number }): this

    // Additional methods and properties
    [key: string]: any
  }

  // Additional utility exports
  export const util: any
  export const Object: typeof FabricObject
  export const Group: any
  export const Rect: any
  export const Circle: any
  export const Line: any
  export const Polygon: any
  export const Polyline: any
  export const Path: any

  // Color and gradient utilities
  export const Color: any
  export const Gradient: any
  export const Pattern: any

  // Default export (for compatibility)
  const fabric: {
    Canvas: typeof Canvas
    Object: typeof FabricObject
    Text: typeof Text
    Image: typeof Image
    util: any
    [key: string]: any
  }
  export default fabric
}

// Global augmentation for better IDE support
declare global {
  interface Window {
    fabric: any
  }

  // Global type aliases for backward compatibility
  type FabricText = any
  type FabricImage = any
}

export {}
