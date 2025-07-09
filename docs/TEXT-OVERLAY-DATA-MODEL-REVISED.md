# Text Overlay UI Planning - Revised Data Model Design

## Infrastructure Context
Based on the Terraform configuration and backend analysis:
- **Cloud Deployment**: Hybrid architecture with Railway (backend) + AWS Lambda (video processing) + AWS (S3, DynamoDB, Cognito)
- **Database**: Single DynamoDB table `video-metadata` with multiple GSIs
- **Storage**: S3 bucket with organized folder structure
- **Authentication**: AWS Cognito User Pools
- **Backend**: FastAPI on Railway with intelligent routing to AWS Lambda for video processing
- **Video Processing**: Hybrid model using `lambda_integration.py` to route between Railway and Lambda based on file size and configuration

## Current Database Schema Analysis

### Existing DynamoDB Table Structure
```
Table: easy-video-share-video-metadata
Primary Key: video_id (partition key)

Global Secondary Indexes:
1. user_id-upload_date-index (user_id, upload_date)
2. video_id-segment_type-index (video_id, segment_type) 
3. user_id-segment_type-index (user_id, segment_type)
4. user_id-created_at-index (user_id, created_at)
5. segment_id-index (segment_id)
```

### Current Item Types in Single Table
1. **Video Jobs** (Primary items)
2. **Video Segments** (Secondary items with segment_id as identifier)

## Enhanced Data Model for Text Overlay

### 1. Extended TextInput Model (Backend)
**File**: `backend/models.py` - Enhance existing `TextInput` class

```python
class TextOverlayStyle(BaseModel):
    """Visual styling properties for text overlay"""
    font_family: str = Field(default="Arial", description="Font family name")
    font_size: int = Field(default=24, ge=12, le=72, description="Font size in pixels")
    text_color: str = Field(default="#FFFFFF", pattern="^#[0-9A-Fa-f]{6}$", description="Text color in hex")
    outline_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Text outline color")
    outline_width: int = Field(default=2, ge=0, le=5, description="Outline width in pixels")
    position: TextPosition = Field(default=TextPosition.BOTTOM_CENTER, description="Text position")
    shadow_enabled: bool = Field(default=True, description="Enable text shadow")
    shadow_color: str = Field(default="#000000", description="Shadow color")
    shadow_offset_x: int = Field(default=2, description="Shadow X offset")
    shadow_offset_y: int = Field(default=2, description="Shadow Y offset")

class TextPosition(str, Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center" 
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    MIDDLE_CENTER = "middle_center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

class EnhancedTextInput(TextInput):
    """Extended TextInput with visual styling"""
    style: TextOverlayStyle = Field(default_factory=TextOverlayStyle)
```

### 2. Video Job Record Enhancement
**Current Video Job Record** + **New Thumbnail Fields**:

```python
# Existing fields in video_id record
{
    "video_id": "vid_123456789",        # Partition key
    "user_id": "user_123",
    "status": "COMPLETED",
    "upload_date": "2024-01-15T10:30:00Z",
    "filename": "sample.mp4",
    "file_size": 52428800,
    "duration": 120.5,
    "bucket_location": "uploads/vid_123456789.mp4",
    "output_s3_urls": ["processed/vid_123456789/segment_001.mp4"],
    
    # NEW THUMBNAIL FIELDS
    "thumbnail_s3_key": "thumbnails/vid_123456789/preview.jpg",
    "thumbnail_metadata": {
        "width": 640,
        "height": 360,
        "timestamp_seconds": 60.25,
        "file_size": 45120,
        "created_at": "2024-01-15T10:31:00Z"
    }
}
```

### 3. S3 Storage Structure Enhancement
**Current S3 Bucket Organization** + **New Thumbnail Paths**:

```
easy-video-share-bucket/
├── uploads/
│   └── {video_id}.mp4                    # Original uploads
├── processed/
│   └── {video_id}/
│       ├── segment_001.mp4               # Processed segments
│       └── segment_002.mp4
├── thumbnails/                           # NEW FOLDER
│   └── {video_id}/
│       ├── preview.jpg                   # Video thumbnail
│       └── overlay_preview_{hash}.jpg    # Text overlay previews
└── temp/                                 # NEW FOLDER
    └── overlay_previews/
        └── {preview_id}.jpg              # Temporary preview cache
```

### 4. DynamoDB Access Patterns for Thumbnails

#### Using Existing GSIs for Thumbnail Operations:
1. **Get video thumbnail**: Query video_id (primary key) → thumbnail_s3_key
2. **List user videos with thumbnails**: Use `user_id-upload_date-index` GSI
3. **No new GSI needed** - thumbnail data stored in existing video record

### 5. API Endpoints (Hybrid Backend)

```python
# Add to backend/main.py

@router.post("/videos/{video_id}/thumbnail")
async def generate_video_thumbnail(video_id: str):
    """Generate thumbnail for video using Lambda (preferred) or Railway FFmpeg"""
    # Use lambda_integration.py to determine processor
    # Lambda: FFmpeg layer for thumbnail extraction
    # Railway: Local FFmpeg fallback
    
@router.post("/videos/{video_id}/text-overlay-preview") 
async def generate_text_overlay_preview(
    video_id: str, 
    request: TextOverlayPreviewRequest
):
    """Generate text overlay preview using available processor"""
    # Lambda: FFmpeg drawtext filter (when text overlay implemented)
    # Railway: Pillow for text compositing

@router.get("/videos/{video_id}/thumbnail")
async def get_video_thumbnail(video_id: str):
    """Get presigned URL for video thumbnail"""
```

### 6. Backend Services

#### Hybrid Thumbnail Service (`backend/thumbnail_service.py`)
```python
import subprocess
from PIL import Image, ImageDraw, ImageFont
import hashlib
from lambda_integration import use_lambda_processing, trigger_lambda_processing

class ThumbnailService:
    @staticmethod
    def extract_video_thumbnail(video_s3_key: str, timestamp: float = None) -> str:
        """Extract thumbnail using Lambda (preferred) or Railway FFmpeg"""
        # Determine processor using lambda_integration.py logic
        if use_lambda_processing({"video_s3_key": video_s3_key}):
            # Lambda: Use FFmpeg layer for thumbnail extraction
            return trigger_lambda_thumbnail_extraction(video_s3_key, timestamp)
        else:
            # Railway: Local FFmpeg processing
            return extract_thumbnail_railway(video_s3_key, timestamp)
        
    @staticmethod  
    def generate_text_overlay_preview(
        thumbnail_s3_key: str,
        text_content: str,
        style: TextOverlayStyle
    ) -> str:
        """Generate text overlay preview using available processor"""
        # Check if Lambda has text overlay capability
        if lambda_has_text_overlay() and use_lambda_processing({}):
            # Lambda: Use FFmpeg drawtext filter
            return trigger_lambda_text_overlay(thumbnail_s3_key, text_content, style)
        else:
            # Railway: Use Pillow for text compositing
            return generate_preview_railway(thumbnail_s3_key, text_content, style)
```

### 7. Data Migration Strategy

#### Backward Compatibility
```python
# In dynamodb_service.py - enhance existing functions

def create_job_entry(
    job_id: str,
    # ... existing parameters ...
    thumbnail_s3_key: Optional[str] = None,
    thumbnail_metadata: Optional[dict] = None
):
    """Enhanced job creation with thumbnail support"""
    item = {
        # ... existing fields ...
    }
    
    # Add thumbnail fields if provided
    if thumbnail_s3_key:
        item["thumbnail_s3_key"] = thumbnail_s3_key
    if thumbnail_metadata:
        item["thumbnail_metadata"] = thumbnail_metadata
        
    table.put_item(Item=item)
```

### 8. Enhanced Upload Workflow Integration

#### Modified Upload Steps:
1. **Video Selection & Upload** (unchanged)
2. **Thumbnail Generation** (NEW - automatic after upload using Lambda preferred)
3. **Text Customization** (enhanced with visual preview using hybrid processing)
4. **Segment Selection** (unchanged)  
5. **Processing** (uses enhanced text styling via intelligent routing)

#### Hybrid Workflow Data Flow:
```
1. Video uploaded to S3 → video_id created in DynamoDB
2. Thumbnail extraction:
   - Lambda preferred: Use FFmpeg layer for efficient extraction
   - Railway fallback: Local FFmpeg processing
3. Text overlay preview:
   - Lambda: FFmpeg drawtext filter (when implemented)
   - Railway: Pillow compositing (current)
4. Video processing:
   - Route via lambda_integration.py based on file size/config
   - Apply enhanced TextInput styling in chosen processor
```

### 9. Performance Optimizations

#### Caching Strategy:
- **Thumbnail Generation**: Once per video, stored permanently
- **Preview Generation**: Hash-based caching, TTL cleanup
- **S3 Presigned URLs**: 1-hour expiration for thumbnails/previews
- **Processor Selection**: Cache Lambda availability checks

#### Memory Management:
- **Railway Environment**: Optimize for limited memory in fallback scenarios
- **Lambda Environment**: Leverage serverless scalability for thumbnail generation
- **Temp File Cleanup**: Automatic cleanup in both environments
- **Image Processing**: Optimize for target environment (Railway vs Lambda)

#### Performance Benefits:
- **Thumbnail Generation**: Lambda scalability reduces bottlenecks
- **Large Files**: Lambda handles >100MB files more efficiently
- **Concurrent Processing**: Lambda auto-scaling vs Railway worker limits
- **Cost Optimization**: Pay-per-use Lambda for thumbnail generation

### 10. Security Considerations

#### S3 Permissions:
- **Thumbnails**: Public read access for web display
- **Preview Cache**: Public read, automatic cleanup
- **CORS**: Allow thumbnail/preview requests from frontend domain

#### Input Validation:
- **Font Families**: Whitelist of safe fonts available in FFmpeg
- **Text Content**: Length limits and sanitization
- **File Sizes**: Thumbnail size limits for performance

## Implementation Priority

### Phase 1: Core Infrastructure
1. **Hybrid Thumbnail Service**: Implement Lambda-preferred thumbnail generation with Railway fallback
2. **Enhanced Data Models**: Add thumbnail fields to existing video records
3. **Lambda Integration**: Leverage existing FFmpeg layer for thumbnail extraction

### Phase 2: Preview System  
1. **Hybrid Preview Generation**: Railway Pillow + Lambda FFmpeg (when text overlay implemented)
2. **Smart Routing**: Use `lambda_integration.py` for optimal processor selection
3. **Preview Caching**: Hash-based caching system with S3 storage

### Phase 3: Text Overlay Parity
1. **Lambda Text Overlay**: Implement FFmpeg drawtext functionality in Lambda
2. **Feature Consistency**: Ensure consistent output between processors
3. **Processing Optimization**: Complete migration to Lambda for large files

### Phase 4: Frontend Integration
1. **Enhanced Upload.vue**: Step 3 with visual preview using hybrid backend
2. **TextOverlayDesigner**: Component that works with both processors
3. **Processing Indicators**: Show user which processor will handle their job

## Risks and Mitigation

### Hybrid Architecture Considerations:
- **Processor Availability**: Implement robust fallback between Lambda and Railway
- **Feature Parity**: Ensure consistent text overlay output across processors
- **Cost Management**: Monitor Lambda usage vs Railway costs for optimization
- **Cold Starts**: Minimize Lambda cold start impact on thumbnail generation

### Railway Deployment Considerations:
- **Memory Limits**: Optimize image processing for Railway's memory constraints (fallback scenarios)
- **Storage**: Use S3 for all file storage, not local filesystem
- **Processing Time**: Ensure thumbnail/preview generation completes within request timeouts

### Lambda Integration Risks:
- **Text Overlay Gap**: Lambda currently lacks text overlay functionality
- **Font Management**: Ensure fonts available in Lambda layers
- **Error Handling**: Robust error handling between processors
- **Monitoring**: Track success rates across both processing paths

### DynamoDB Single Table:
- **No Schema Changes**: Thumbnail data added as optional fields to existing records
- **GSI Limits**: Reuse existing GSIs, no new indexes needed
- **Backward Compatibility**: Existing records work without thumbnail data

## Architecture Decision Framework

### Processing Selection Logic
```python
# Integration with existing lambda_integration.py

def select_thumbnail_processor(video_data):
    """Determine optimal processor for thumbnail generation"""
    # Always prefer Lambda for thumbnails (scalability)
    if lambda_available():
        return "lambda"
    return "railway"
    
def select_preview_processor(text_overlay_data):
    """Determine optimal processor for text overlay preview"""
    # Use Lambda if text overlay implemented
    if lambda_has_text_overlay():
        return "lambda"
    # Fall back to Railway Pillow processing
    return "railway"
```

### Migration Strategy
1. **Phase 1**: Use Lambda for thumbnail generation (all files)
2. **Phase 2**: Implement text overlay in Lambda for feature parity
3. **Phase 3**: Migrate text overlay processing to Lambda (large files first)
4. **Phase 4**: Optimize routing based on performance metrics

---

*Revised Data Model for Hybrid Railway + Lambda Architecture - Date: 2025-07-09*