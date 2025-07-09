# Text Overlay UI Planning View - Implementation Plan

## Overview
Enhance the existing "text customization for video segments" step with thumbnail-based visual preview, allowing users to design text overlays on a lightweight thumbnail that will be applied to actual video segments during processing.

**Architecture Update**: The system now uses a hybrid processing model with intelligent routing between Railway (full-featured) and AWS Lambda (scalable processing) based on file size and configuration flags.

## Backend Implementation

### 1. Thumbnail Generation for Preview
- **Primary Location**: AWS Lambda function (`terraform/lambda/video-processor/lambda_function.py`)
- **Fallback Location**: `backend/thumbnail_service.py` (Railway)
- **Integration Point**: Called during video upload completion
- **Technology**: FFmpeg to extract single frame at video midpoint
- **Purpose**: Generate lightweight preview image for text overlay design
- **Storage**: Save thumbnail to S3, reference in existing video job record
- **Architecture**: Leverage Lambda's FFmpeg layer for efficient thumbnail generation regardless of final processing choice

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
- **Technology**: 
  - **Railway**: Pillow (PIL) to composite text on thumbnail
  - **Lambda**: FFmpeg drawtext filter for text rendering
- **Response**: Base64 encoded preview image or S3 URL
- **Processing Logic**: Use `lambda_integration.py` routing to determine processor

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
- **Railway Processing**: `backend/video_processing_utils_sprint4.py`
- **Lambda Processing**: `terraform/lambda/video-processor/lambda_function.py` (requires text overlay implementation)
- **Enhancement**: Use detailed text styling from enhanced TextInput
- **Technology**: Apply same styling to video using FFmpeg text filters
- **Consistency**: Ensure thumbnail preview exactly matches video output across both processors
- **Feature Parity**: Lambda implementation needs text overlay functionality to match Railway capabilities

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
1. **Thumbnail Generation**: Leverage Lambda's FFmpeg layer for efficient thumbnail extraction
2. **Text Overlay in Lambda**: Implement text rendering capability in Lambda function to achieve feature parity with Railway
3. **Enhanced TextInput Model**: Extend with styling fields for both processing paths
4. **Preview Generation**: Create unified preview endpoint that works with both processors

### Phase 2: Frontend Integration
1. **TextOverlayDesigner Component**: Create visual text overlay designer
2. **Upload.vue Enhancement**: Integrate into existing Step 3 workflow
3. **Processing Indicator**: Show user which processor will handle their job
4. **Responsive Design**: Optimize for mobile and desktop

### Phase 3: Processing Pipeline
1. **Hybrid Processing**: Ensure consistent text overlay output between Railway and Lambda
2. **Smart Routing**: Use `lambda_integration.py` logic for optimal processor selection
3. **Feature Parity**: Complete Lambda text overlay implementation
4. **Error Handling**: Robust fallback between processing systems

## Technical Considerations

### Font Management
- **Railway**: Use web-safe fonts available in system FFmpeg
- **Lambda**: Include font files in Lambda layer or S3 storage
- **Consistency**: Ensure same fonts available in both processing environments
- **Fallback**: Implement font hierarchy for compatibility across processors

### Performance Optimization
- **Thumbnail Generation**: Leverage Lambda's scalability for thumbnail extraction
- **Preview Caching**: Cache thumbnails and preview images in S3
- **Smart Routing**: Use file size and processing requirements to optimize processor selection
- **Debouncing**: Reduce API calls with intelligent request batching

### Cross-Platform Compatibility
- **Processing Consistency**: Ensure text rendering matches between Railway and Lambda
- **Font Rendering**: Test consistency across different processing environments
- **Mobile Optimization**: Handle different screen densities and sizes
- **Fallback Strategy**: Graceful degradation if preferred processor unavailable

### Lambda-Specific Considerations
- **Layer Management**: Include necessary fonts in Lambda layers
- **Memory Optimization**: Efficient text rendering within Lambda constraints
- **Cold Start**: Minimize impact on thumbnail generation performance
- **Error Handling**: Robust fallback to Railway if Lambda processing fails

## Architecture Decision Points

### Processing Strategy Selection
- **Large Files (>100MB)**: Route to Lambda for scalability
- **Complex Text Processing**: Consider Railway for full-featured text handling
- **Feature Flags**: Use `USE_LAMBDA_PROCESSING` for gradual migration
- **User Preferences**: Support user-specific processor selection

### Development Approach
1. **Phase 1**: Implement thumbnail generation using Lambda (all files)
2. **Phase 2**: Add text overlay preview using hybrid approach
3. **Phase 3**: Implement full text overlay in Lambda for feature parity
4. **Phase 4**: Optimize routing logic based on performance metrics

---

*Implementation Plan for Text Overlay UI Planning View - Updated for Lambda Architecture - Date: 2025-07-09*