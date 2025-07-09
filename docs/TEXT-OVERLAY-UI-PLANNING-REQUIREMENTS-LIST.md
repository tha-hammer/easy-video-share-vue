● Development Plan: Segment-Page Text Overlay System

Phase 1: Core Infrastructure (Requirements 1.x)

Requirement 1.01 - Install and Configure Fabric.js

Work: Install Fabric.js package and create base TypeScript types for text overlay objects
User Benefit: Enables interactive text editing capabilities on video thumbnails

Requirement 1.02 - Create Base Text Overlay Data Models

Work: Define TypeScript interfaces for TextOverlay, FabricTextObject, and FFmpegTextFilter with proper typing
User Benefit: Ensures type safety and consistent data structure for text overlays across the application

Requirement 1.03 - Create TextOverlayService Composable

Work: Develop a Vue composable that manages Fabric.js canvas lifecycle, text object creation, and coordinate calculations
User Benefit: Provides centralized text overlay management with reactive state updates

Requirement 1.04 - Implement Coordinate Translation System

Work: Create functions to convert Fabric.js aCoords (absolute coordinates) to FFmpeg drawtext coordinates, accounting for
canvas-to-video scaling
User Benefit: Ensures text appears in the exact same position on the final video as designed on the thumbnail

Phase 2: Fabric.js Canvas Integration (Requirements 2.x)

Requirement 2.01 - Create SegmentTextEditor Component

Work: Build Vue component that renders Fabric.js canvas with video thumbnail as background image
User Benefit: Provides visual interface for placing text directly on video preview

Requirement 2.02 - Implement Text Object Creation

Work: Add functionality to create new Fabric.Text objects on canvas click, with default styling properties
User Benefit: Allows users to add new text elements to their video segments with simple clicks

Requirement 2.03 - Enable Text Selection and Editing

Work: Configure Fabric.js for text selection, inline editing (double-click), and object manipulation (drag, resize,
rotate)
User Benefit: Users can modify text content, position, and size using familiar drag-and-drop interactions

Requirement 2.04 - Add Text Property Controls

Work: Create toolbar with font family dropdown, font size slider, color picker, and text styling options
User Benefit: Users can customize text appearance with professional typography controls

Requirement 2.05 - Implement Text Effects System

Work: Add shadow, stroke/outline, and background options with real-time preview on canvas
User Benefit: Users can apply visual effects to make text more readable over video content

Phase 3: Canvas Coordinate Management (Requirements 3.x)

Requirement 3.01 - Implement Canvas Scaling System

Work: Create responsive canvas that maintains video aspect ratio and scales text objects proportionally
User Benefit: Text positioning remains accurate across different screen sizes and device orientations

Requirement 3.02 - Create aCoords Extraction Function

Work: Develop function that extracts Fabric.js aCoords (tl, tr, bl, br corners) and calculates text bounding box
dimensions
User Benefit: Provides precise positioning data for accurate FFmpeg text placement

Requirement 3.03 - Build Video-to-Canvas Scale Calculator

Work: Create utility that calculates scaling ratios between canvas dimensions and actual video resolution
User Benefit: Ensures text appears at correct size and position in final video output

Requirement 3.04 - Implement FFmpeg Coordinate Converter

Work: Transform Fabric.js absolute coordinates to FFmpeg drawtext x,y positions, accounting for font metrics and anchor
points
User Benefit: Guarantees pixel-perfect text positioning in processed video segments

Requirement 3.05 - Add Coordinate Validation System

Work: Validate that text positions fall within video boundaries and adjust for text overflow
User Benefit: Prevents text from being cut off or appearing outside video frame

Phase 4: Text Styling Translation (Requirements 4.x)

Requirement 4.01 - Create Font Family Mapping

Work: Map Fabric.js web fonts to available FFmpeg font files with fallback system
User Benefit: Ensures selected fonts render consistently in final video output

Requirement 4.02 - Implement Font Size Translation

Work: Convert Fabric.js fontSize (CSS pixels) to FFmpeg fontsize (video pixels) based on video resolution
User Benefit: Text appears at intended size regardless of video resolution or canvas display size

Requirement 4.03 - Build Color Format Converter

Work: Convert Fabric.js color formats (hex, rgba) to FFmpeg-compatible color strings
User Benefit: Maintains exact color accuracy from design to final video

Requirement 4.04 - Create Shadow Effect Translator

Work: Convert Fabric.js shadow properties to FFmpeg shadow filters with offset and blur calculations
User Benefit: Drop shadows render identically in final video as shown in preview

Requirement 4.05 - Implement Stroke/Outline Converter

Work: Transform Fabric.js stroke properties to FFmpeg bordercolor and borderw parameters
User Benefit: Text outlines provide consistent readability enhancement in final video

Phase 5: State Management (Requirements 5.x)

Requirement 5.01 - Create Text Overlay Store

Work: Implement Pinia store for managing text overlays across multiple segments with persistence
User Benefit: Text designs are saved automatically and persist across browser sessions

Requirement 5.02 - Add Undo/Redo System

Work: Implement command pattern for text operations with history stack management
User Benefit: Users can safely experiment with text designs knowing they can undo changes

Requirement 5.03 - Implement Auto-Save Functionality

Work: Automatically save text overlay changes to backend with debounced API calls
User Benefit: No manual save required - designs are preserved without user intervention

Requirement 5.04 - Create Multi-Segment Management

Work: Track text overlays for multiple video segments with segment-specific state isolation
User Benefit: Users can design different text for each segment while maintaining organized workflow

Requirement 5.05 - Add Template System

Work: Allow saving and applying text styles as reusable templates across segments
User Benefit: Speeds up design process by reusing common text styling configurations

Phase 6: Integration with Existing Components (Requirements 6.x)

Requirement 6.01 - Enhance VideoSegmentCard

Work: Add text overlay indicators, preview thumbnails, and edit buttons to existing segment cards
User Benefit: Users can see which segments have text overlays and access editing from main segments view

Requirement 6.02 - Update UniversalVideoPlayer

Work: Integrate text overlay editor mode into existing video player modal with toggle functionality
User Benefit: Seamless transition between video playback and text editing in unified interface

Requirement 6.03 - Modify SegmentsLibrary View

Work: Add text overlay status filters and bulk text operations to segments library
User Benefit: Users can manage text overlays across multiple videos and segments efficiently

Requirement 6.04 - Create Text Preview System

Work: Generate preview images showing text overlay on video thumbnail for quick verification
User Benefit: Users can verify text designs without opening full editor interface

Requirement 6.05 - Implement Batch Operations

Work: Allow applying text styles or templates to multiple segments simultaneously
User Benefit: Efficient workflow for applying consistent branding across multiple video segments

Phase 7: Backend API Integration (Requirements 7.x)

Requirement 7.01 - Create Text Overlay Endpoints

Work: Implement REST endpoints for CRUD operations on text overlay data with validation
User Benefit: Text designs are securely stored and retrievable across devices and sessions

Requirement 7.02 - Add Thumbnail Generation API

Work: Create endpoint that generates video thumbnails optimized for text overlay design
User Benefit: High-quality reference images for accurate text placement design

Requirement 7.03 - Implement FFmpeg Integration

Work: Build service that converts text overlay data to FFmpeg drawtext filters and processes videos
User Benefit: Seamless conversion from visual design to final video with text overlays

Requirement 7.04 - Add Processing Status Tracking

Work: Implement WebSocket or polling system for real-time processing status updates
User Benefit: Users receive immediate feedback on video processing progress and completion

Requirement 7.05 - Create Error Handling System

Work: Comprehensive error handling for font issues, coordinate problems, and processing failures
User Benefit: Clear error messages and automatic fallbacks ensure reliable text overlay application

Phase 8: Performance and Polish (Requirements 8.x)

Requirement 8.01 - Optimize Canvas Performance

Work: Implement canvas object pooling, efficient rendering, and memory management for large text counts
User Benefit: Smooth, responsive text editing experience even with complex overlay designs

Requirement 8.02 - Add Mobile Responsiveness

Work: Adapt Fabric.js controls for touch devices with larger hit targets and gesture support
User Benefit: Text overlay editing works seamlessly on tablets and mobile devices

Requirement 8.03 - Implement Accessibility Features

Work: Add keyboard navigation, screen reader support, and high contrast mode for text editing
User Benefit: Text overlay tools are accessible to users with disabilities

Requirement 8.04 - Create Performance Monitoring

Work: Add analytics for canvas performance, API response times, and user interaction patterns
User Benefit: Continuous improvement of user experience based on real usage data

Requirement 8.05 - Polish User Experience

Work: Add animations, loading states, tooltips, and contextual help for text overlay features
User Benefit: Intuitive, professional-grade text editing experience that guides users effectively

---

Total Requirements: 40 detailed requirements across 8 phases
Estimated Timeline: 6-8 weeks for full implementation
Primary Focus: Phase 3 (Coordinate Management) is the most critical and complex portion requiring detailed Fabric.js
aCoords understanding
