# Text Overlay UI Planning View - Implementation Plan

## Overview
Enhance the existing "text customization for video segments" step with thumbnail-based visual preview, allowing users to design text overlays on a lightweight thumbnail that will be applied to actual video segments during processing.

## Backend Implementation

### 1. Thumbnail Generation for Preview
- **Location**: `backend/thumbnail_service.py`
- **Integration Point**: Called during video upload completion
- **Technology**: FFmpeg to extract single frame at video midpoint
- **Purpose**: Generate lightweight preview image for text overlay design
- **Storage**: Save thumbnail to S3, reference in existing video job record

### 2. Enhanced Text Input Models
- **Update**: `backend/models.py` - Extend existing `TextInput` class
- **New Fields**: 
  - `font_family`: Font selection (web-safe fonts)
  - `font_size`: Size in pixels/points
  - `text_color`: Hex color code
  - `outline_color`: Optional text outline
  - `position`: Text position (top-left, center, bottom-right, etc.)
  - `background_opacity`: Optional text background

### 3. Preview Generation Endpoint
- **Location**: `backend/main.py` - New endpoint in existing API structure
- **Endpoint**: `POST /api/videos/{video_id}/text-overlay-preview`
- **Purpose**: Generate thumbnail with text overlay applied for preview
- **Technology**: Pillow (PIL) to composite text on thumbnail
- **Response**: Base64 encoded preview image or S3 URL

## Frontend Implementation

### 4. Enhanced Upload.vue - Step 3 Expansion
- **Current**: Step 3 is "Text Customization for Video Segments"
- **Enhancement**: Add visual preview panel alongside existing text inputs
- **Layout**: Split view - text controls on left, thumbnail preview on right
- **Maintain**: All existing text strategy functionality (one_for_all, base_vary, unique_for_all)

### 5. Text Overlay Designer Component
- **Location**: `src/components/text-overlay/TextOverlayDesigner.vue`
- **Integration**: Embedded within existing Upload.vue Step 3
- **Features**:
  - Display video thumbnail as background
  - Real-time text overlay preview
  - Font/color/size/position controls
  - Live updates as user adjusts settings

### 6. Enhanced Text Input Interface
- **Extend Existing**: Current text input areas in Upload.vue
- **Add Visual Controls**:
  - Font family dropdown
  - Color picker for text and outline
  - Font size slider with preview
  - Position grid (3x3) for text placement
  - Preview button to generate thumbnail with overlay

## Integration with Existing Workflow

### 7. Upload Flow Enhancement
- **Step 1**: Video Selection (unchanged)
- **Step 2**: Upload (unchanged) + thumbnail generation
- **Step 3**: Text Customization (enhanced with visual preview)
- **Step 4**: Segment Selection (unchanged)
- **Step 5**: Processing (uses enhanced text settings)

### 8. Processing Pipeline Integration
- **Update**: `backend/video_processing_utils_sprint4.py`
- **Enhancement**: Use detailed text styling from enhanced TextInput
- **Technology**: Apply same styling to video using FFmpeg text filters
- **Consistency**: Ensure thumbnail preview exactly matches video output

## Technical Implementation

### 9. Thumbnail Storage Strategy
- **S3 Path**: `thumbnails/{video_id}/preview.jpg`
- **Database**: Add `thumbnail_s3_key` to existing job record
- **Lifecycle**: Generate once per video, reuse for all preview requests

### 10. Preview Generation Flow
1. User modifies text settings in Step 3
2. Frontend calls preview endpoint with settings
3. Backend applies text to stored thumbnail using Pillow
4. Returns preview image to frontend
5. User sees immediate visual feedback
6. Settings saved to enhanced TextInput model

## Mobile Considerations

### 11. Responsive Design
- **Mobile**: Stack text controls above preview
- **Desktop**: Side-by-side layout
- **Touch**: Larger control elements for mobile interaction
- **Performance**: Debounced preview updates to reduce API calls

## Risk Mitigation

### 12. Fallback Strategies
- **No Thumbnail**: Default to text-only preview if thumbnail generation fails
- **Preview Failure**: Allow progression with text-only settings
- **Font Compatibility**: Ensure selected fonts available in FFmpeg
- **Performance**: Cache preview images to reduce regeneration

## Implementation Priority

### Phase 1: Core Infrastructure
1. Create thumbnail generation service
2. Extend TextInput model with styling fields
3. Add preview generation endpoint

### Phase 2: Frontend Integration
1. Create TextOverlayDesigner component
2. Integrate into existing Upload.vue Step 3
3. Implement responsive design

### Phase 3: Processing Pipeline
1. Update video processing to use enhanced text settings
2. Ensure consistency between preview and final output
3. Add error handling and fallbacks

## Technical Considerations

### Font Management
- Use web-safe fonts that are also available in FFmpeg
- Fallback font hierarchy for compatibility
- Consider font file hosting for custom fonts

### Performance Optimization
- Cache thumbnails and preview images
- Debounce preview generation requests
- Optimize image sizes for web display
- Progressive loading for better UX

### Cross-Platform Compatibility
- Ensure font rendering consistency across platforms
- Test preview accuracy on different devices
- Handle different screen densities and sizes

---

*Implementation Plan for Text Overlay UI Planning View - Date: 2025-07-06*