// Text Overlay Store - Pinia store for managing text overlays across video segments
// Requirement 5.01 - Create Text Overlay Store

import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type {
  TextOverlay,
  TextOverlayTemplate,
  TextOverlayOperation,
  FFmpegTextFilter,
} from '@/types/textOverlay'

export const useTextOverlayStore = defineStore('textOverlays', () => {
  // ==================== STATE ====================

  // Text overlays organized by segment ID
  const overlaysBySegment = ref<Map<string, TextOverlay[]>>(new Map())

  // Text overlay templates for reuse
  const templates = ref<TextOverlayTemplate[]>([])

  // Operation history for undo/redo (Requirement 5.02)
  const operationHistory = ref<TextOverlayOperation[]>([])
  const historyIndex = ref(-1)
  const maxHistorySize = ref(50)

  // UI state
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const selectedSegmentId = ref<string | null>(null)
  const selectedOverlayId = ref<string | null>(null)

  // Auto-save state (Requirement 5.03)
  const autoSaveEnabled = ref(true)
  const autoSaveInterval = ref(5000) // 5 seconds
  const lastSaved = ref<Date | null>(null)
  const hasUnsavedChanges = ref(false)

  // ==================== GETTERS ====================

  // Get overlays for a specific segment
  const getOverlaysForSegment = computed(() => {
    return (segmentId: string): TextOverlay[] => {
      return overlaysBySegment.value.get(segmentId) || []
    }
  })

  // Get currently selected overlays
  const selectedOverlays = computed(() => {
    if (!selectedSegmentId.value) return []
    return getOverlaysForSegment.value(selectedSegmentId.value)
  })

  // Get specific overlay by ID
  const getOverlayById = computed(() => {
    return (overlayId: string): TextOverlay | null => {
      for (const [_segmentId, overlays] of overlaysBySegment.value) {
        const overlay = overlays.find((o) => o.id === overlayId)
        if (overlay) return overlay
      }
      return null
    }
  })

  // Count overlays across all segments
  const totalOverlayCount = computed(() => {
    let count = 0
    for (const overlays of overlaysBySegment.value.values()) {
      count += overlays.length
    }
    return count
  })

  // Get segments that have overlays
  const segmentsWithOverlays = computed(() => {
    const segments: string[] = []
    for (const [segmentId, overlays] of overlaysBySegment.value) {
      if (overlays.length > 0) {
        segments.push(segmentId)
      }
    }
    return segments
  })

  // Check if undo is possible
  const canUndo = computed(() => historyIndex.value >= 0)

  // Check if redo is possible
  const canRedo = computed(() => historyIndex.value < operationHistory.value.length - 1)

  // Get default template
  const defaultTemplate = computed(() => {
    return templates.value.find((t) => t.isDefault) || null
  })

  // ==================== ACTIONS ====================

  /**
   * Set overlays for a specific segment
   * This is the main method called by SegmentTextEditor
   */
  const setOverlaysForSegment = (segmentId: string, overlays: TextOverlay[]) => {
    console.log(`📝 Setting ${overlays.length} overlays for segment ${segmentId}`)

    const previousOverlays = overlaysBySegment.value.get(segmentId) || []
    overlaysBySegment.value.set(segmentId, [...overlays])

    // Record operation for undo/redo
    recordOperation({
      id: generateOperationId(),
      type: 'update',
      segmentId,
      overlayId: 'multiple',
      previousState: { overlays: previousOverlays },
      newState: { overlays },
      timestamp: new Date().toISOString(),
    })

    hasUnsavedChanges.value = true

    // Trigger auto-save if enabled
    if (autoSaveEnabled.value) {
      scheduleAutoSave()
    }
  }

  /**
   * Add a single overlay to a segment
   */
  const addOverlay = (segmentId: string, overlay: TextOverlay) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)
    const newOverlays = [...currentOverlays, overlay]

    overlaysBySegment.value.set(segmentId, newOverlays)

    recordOperation({
      id: generateOperationId(),
      type: 'create',
      segmentId,
      overlayId: overlay.id,
      newState: overlay,
      timestamp: new Date().toISOString(),
    })

    hasUnsavedChanges.value = true
    console.log(`➕ Added overlay ${overlay.id} to segment ${segmentId}`)
  }

  /**
   * Update a specific overlay
   */
  const updateOverlay = (segmentId: string, overlayId: string, updates: Partial<TextOverlay>) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)
    const overlayIndex = currentOverlays.findIndex((o) => o.id === overlayId)

    if (overlayIndex === -1) {
      console.warn(`⚠️ Overlay ${overlayId} not found in segment ${segmentId}`)
      return
    }

    const previousOverlay = { ...currentOverlays[overlayIndex] }
    const updatedOverlay = {
      ...previousOverlay,
      ...updates,
      updatedAt: new Date().toISOString(),
    }

    const newOverlays = [...currentOverlays]
    newOverlays[overlayIndex] = updatedOverlay

    overlaysBySegment.value.set(segmentId, newOverlays)

    recordOperation({
      id: generateOperationId(),
      type: 'update',
      segmentId,
      overlayId,
      previousState: previousOverlay,
      newState: updatedOverlay,
      timestamp: new Date().toISOString(),
    })

    hasUnsavedChanges.value = true
    console.log(`🔄 Updated overlay ${overlayId}`)
  }

  /**
   * Remove overlay from segment
   */
  const removeOverlay = (segmentId: string, overlayId: string) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)
    const overlayToRemove = currentOverlays.find((o) => o.id === overlayId)

    if (!overlayToRemove) {
      console.warn(`⚠️ Overlay ${overlayId} not found in segment ${segmentId}`)
      return
    }

    const newOverlays = currentOverlays.filter((o) => o.id !== overlayId)
    overlaysBySegment.value.set(segmentId, newOverlays)

    recordOperation({
      id: generateOperationId(),
      type: 'delete',
      segmentId,
      overlayId,
      previousState: overlayToRemove,
      timestamp: new Date().toISOString(),
    })

    hasUnsavedChanges.value = true
    console.log(`➖ Removed overlay ${overlayId}`)
  }

  /**
   * Clear all overlays for a segment
   */
  const clearSegmentOverlays = (segmentId: string) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)

    if (currentOverlays.length === 0) return

    overlaysBySegment.value.set(segmentId, [])

    recordOperation({
      id: generateOperationId(),
      type: 'delete',
      segmentId,
      overlayId: 'all',
      previousState: { overlays: currentOverlays },
      timestamp: new Date().toISOString(),
    })

    hasUnsavedChanges.value = true
    console.log(`🧹 Cleared all overlays for segment ${segmentId}`)
  }

  // ==================== TEMPLATE MANAGEMENT ====================

  /**
   * Save current overlay as template
   */
  const saveAsTemplate = (overlayId: string, templateName: string, description?: string) => {
    const overlay = getOverlayById.value(overlayId)
    if (!overlay) {
      console.warn(`⚠️ Overlay ${overlayId} not found`)
      return
    }

    const template: TextOverlayTemplate = {
      id: `template_${Date.now()}`,
      name: templateName,
      description,
      fontSize: overlay.fontSize,
      fontFamily: overlay.fontFamily,
      fontWeight: overlay.fontWeight,
      fontStyle: overlay.fontStyle,
      color: overlay.color,
      backgroundColor: overlay.backgroundColor,
      shadow: overlay.shadow,
      stroke: overlay.stroke,
      defaultX: 0.5, // Center position
      defaultY: 0.5,
      isDefault: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    templates.value.push(template)
    console.log(`💾 Saved template: ${templateName}`)
  }

  /**
   * Apply template to overlay
   */
  const applyTemplate = (segmentId: string, overlayId: string, templateId: string) => {
    const template = templates.value.find((t) => t.id === templateId)
    const overlay = getOverlayById.value(overlayId)

    if (!template || !overlay) {
      console.warn(`⚠️ Template or overlay not found`)
      return
    }

    const updates: Partial<TextOverlay> = {
      fontSize: template.fontSize,
      fontFamily: template.fontFamily,
      fontWeight: template.fontWeight,
      fontStyle: template.fontStyle,
      color: template.color,
      backgroundColor: template.backgroundColor,
      shadow: template.shadow,
      stroke: template.stroke,
    }

    updateOverlay(segmentId, overlayId, updates)
    console.log(`🎨 Applied template ${template.name} to overlay ${overlayId}`)
  }

  /**
   * Create overlay from template
   */
  const createFromTemplate = (
    segmentId: string,
    templateId: string,
    text: string = 'New Text',
  ): TextOverlay => {
    const template = templates.value.find((t) => t.id === templateId)
    if (!template) {
      throw new Error(`Template ${templateId} not found`)
    }

    const overlay: TextOverlay = {
      id: `overlay_${Date.now()}`,
      segmentId,
      text,
      x: Math.round(template.defaultX * 1920), // Assume 1920px width
      y: Math.round(template.defaultY * 1080), // Assume 1080px height
      width: 200,
      height: 50,
      fontSize: template.fontSize,
      fontFamily: template.fontFamily,
      fontWeight: template.fontWeight,
      fontStyle: template.fontStyle,
      color: template.color,
      backgroundColor: template.backgroundColor,
      opacity: 1.0,
      rotation: 0,
      scaleX: 1,
      scaleY: 1,
      shadow: template.shadow,
      stroke: template.stroke,
      startTime: 0,
      endTime: 30,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    addOverlay(segmentId, overlay)
    return overlay
  }

  // ==================== UNDO/REDO SYSTEM ====================

  /**
   * Record operation for undo/redo
   * Requirement 5.02 - Add Undo/Redo System
   */
  const recordOperation = (operation: TextOverlayOperation) => {
    // Remove any operations after current index (when undoing then making new changes)
    if (historyIndex.value < operationHistory.value.length - 1) {
      operationHistory.value = operationHistory.value.slice(0, historyIndex.value + 1)
    }

    // Add new operation
    operationHistory.value.push(operation)
    historyIndex.value = operationHistory.value.length - 1

    // Limit history size
    if (operationHistory.value.length > maxHistorySize.value) {
      operationHistory.value.shift()
      historyIndex.value--
    }
  }

  /**
   * Undo last operation
   */
  const undo = () => {
    if (!canUndo.value) return

    const operation = operationHistory.value[historyIndex.value]
    if (!operation) return

    console.log(`↶ Undoing operation: ${operation.type} on ${operation.overlayId}`)

    switch (operation.type) {
      case 'create':
        // Remove the created overlay
        removeOverlayFromHistory(operation.segmentId, operation.overlayId)
        break

      case 'update':
        // Restore previous state
        if (operation.previousState) {
          if (operation.overlayId === 'multiple' || operation.overlayId === 'all') {
            // Handle bulk operations
            const previousOverlays = (operation.previousState as any).overlays
            if (previousOverlays) {
              overlaysBySegment.value.set(operation.segmentId, previousOverlays)
            }
          } else {
            // Handle single overlay update
            updateOverlayFromHistory(
              operation.segmentId,
              operation.overlayId,
              operation.previousState,
            )
          }
        }
        break

      case 'delete':
        // Restore deleted overlay
        if (operation.previousState) {
          if (operation.overlayId === 'all') {
            // Restore all overlays
            const previousOverlays = (operation.previousState as any).overlays
            if (previousOverlays) {
              overlaysBySegment.value.set(operation.segmentId, previousOverlays)
            }
          } else {
            // Restore single overlay
            addOverlayFromHistory(operation.segmentId, operation.previousState as TextOverlay)
          }
        }
        break
    }

    historyIndex.value--
    hasUnsavedChanges.value = true
  }

  /**
   * Redo operation
   */
  const redo = () => {
    if (!canRedo.value) return

    historyIndex.value++
    const operation = operationHistory.value[historyIndex.value]
    if (!operation) return

    console.log(`↷ Redoing operation: ${operation.type} on ${operation.overlayId}`)

    switch (operation.type) {
      case 'create':
        // Re-add the overlay
        if (operation.newState) {
          addOverlayFromHistory(operation.segmentId, operation.newState as TextOverlay)
        }
        break

      case 'update':
        // Apply new state
        if (operation.newState) {
          if (operation.overlayId === 'multiple' || operation.overlayId === 'all') {
            // Handle bulk operations
            const newOverlays = (operation.newState as any).overlays
            if (newOverlays) {
              overlaysBySegment.value.set(operation.segmentId, newOverlays)
            }
          } else {
            // Handle single overlay update
            updateOverlayFromHistory(operation.segmentId, operation.overlayId, operation.newState)
          }
        }
        break

      case 'delete':
        // Re-remove the overlay
        removeOverlayFromHistory(operation.segmentId, operation.overlayId)
        break
    }

    hasUnsavedChanges.value = true
  }

  // ==================== AUTO-SAVE FUNCTIONALITY ====================

  let autoSaveTimeout: NodeJS.Timeout | null = null

  /**
   * Schedule auto-save
   * Requirement 5.03 - Implement Auto-Save Functionality
   */
  const scheduleAutoSave = () => {
    if (!autoSaveEnabled.value) return

    // Clear existing timeout
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout)
    }

    // Schedule new auto-save
    autoSaveTimeout = setTimeout(() => {
      saveToBackend()
    }, autoSaveInterval.value)
  }

  /**
   * Save overlays to backend
   */
  const saveToBackend = async () => {
    if (!hasUnsavedChanges.value) return

    try {
      isLoading.value = true
      error.value = null

      // Convert overlays to saveable format
      const overlaysData: Record<string, TextOverlay[]> = {}
      for (const [segmentId, overlays] of overlaysBySegment.value) {
        overlaysData[segmentId] = overlays
      }

      // TODO: Implement actual API call to save overlays
      // await VideoService.saveTextOverlays(overlaysData)

      console.log('💾 Auto-saved text overlays to backend')

      hasUnsavedChanges.value = false
      lastSaved.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save overlays'
      console.error('❌ Failed to save overlays:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load overlays from backend
   */
  const loadFromBackend = async (_videoId?: string) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Implement actual API call to load overlays
      // const overlaysData = await VideoService.loadTextOverlays(videoId)

      // For now, just clear state
      overlaysBySegment.value.clear()

      console.log('📂 Loaded text overlays from backend')
      hasUnsavedChanges.value = false
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load overlays'
      console.error('❌ Failed to load overlays:', err)
    } finally {
      isLoading.value = false
    }
  }

  // ==================== UTILITY FUNCTIONS ====================

  /**
   * Generate unique operation ID
   */
  const generateOperationId = (): string => {
    return `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Helper functions for undo/redo that don't trigger new operations
   */
  const addOverlayFromHistory = (segmentId: string, overlay: TextOverlay) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)
    overlaysBySegment.value.set(segmentId, [...currentOverlays, overlay])
  }

  const updateOverlayFromHistory = (
    segmentId: string,
    overlayId: string,
    updates: Partial<TextOverlay>,
  ) => {
    const currentOverlays = getOverlaysForSegment.value(segmentId)
    const overlayIndex = currentOverlays.findIndex((o) => o.id === overlayId)

    if (overlayIndex !== -1) {
      const newOverlays = [...currentOverlays]
      newOverlays[overlayIndex] = { ...newOverlays[overlayIndex], ...updates }
      overlaysBySegment.value.set(segmentId, newOverlays)
    }
  }

  const removeOverlayFromHistory = (segmentId: string, overlayId: string) => {
    if (overlayId === 'all') {
      overlaysBySegment.value.set(segmentId, [])
    } else {
      const currentOverlays = getOverlaysForSegment.value(segmentId)
      const newOverlays = currentOverlays.filter((o) => o.id !== overlayId)
      overlaysBySegment.value.set(segmentId, newOverlays)
    }
  }

  /**
   * Generate FFmpeg filters for all overlays in a segment
   */
  const generateFFmpegFilters = (segmentId: string): FFmpegTextFilter[] => {
    const overlays = getOverlaysForSegment.value(segmentId)

    // TODO: Implement actual FFmpeg filter generation
    // This would use the convertToFFmpegFilter function from useTextOverlay

    return overlays.map((overlay) => ({
      text: overlay.text,
      x: overlay.x,
      y: overlay.y,
      fontsize: overlay.fontSize,
      fontcolor: overlay.color,
      fontfile: '/opt/fonts/arial.ttf', // Default font
      enable: `between(t,${overlay.startTime},${overlay.endTime})`,
      drawTextFilter: `drawtext=text='${overlay.text}':x=${overlay.x}:y=${overlay.y}:fontsize=${overlay.fontSize}:fontcolor=${overlay.color}:fontfile=/opt/fonts/arial.ttf:enable='between(t,${overlay.startTime},${overlay.endTime})'`,
    }))
  }

  /**
   * Reset store to initial state
   */
  const reset = () => {
    overlaysBySegment.value.clear()
    templates.value = []
    operationHistory.value = []
    historyIndex.value = -1
    selectedSegmentId.value = null
    selectedOverlayId.value = null
    hasUnsavedChanges.value = false
    lastSaved.value = null
    error.value = null

    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout)
      autoSaveTimeout = null
    }

    console.log('🔄 Text overlay store reset')
  }

  // ==================== PUBLIC API ====================

  return {
    // State
    overlaysBySegment: readonly(overlaysBySegment),
    templates: readonly(templates),
    isLoading: readonly(isLoading),
    error: readonly(error),
    selectedSegmentId,
    selectedOverlayId,
    hasUnsavedChanges: readonly(hasUnsavedChanges),
    lastSaved: readonly(lastSaved),
    autoSaveEnabled,
    autoSaveInterval,

    // Getters
    getOverlaysForSegment,
    selectedOverlays,
    getOverlayById,
    totalOverlayCount,
    segmentsWithOverlays,
    canUndo,
    canRedo,
    defaultTemplate,

    // Overlay management
    setOverlaysForSegment,
    addOverlay,
    updateOverlay,
    removeOverlay,
    clearSegmentOverlays,

    // Template management
    saveAsTemplate,
    applyTemplate,
    createFromTemplate,

    // Undo/redo
    undo,
    redo,

    // Persistence
    saveToBackend,
    loadFromBackend,

    // Utilities
    generateFFmpegFilters,
    reset,
  }
})
