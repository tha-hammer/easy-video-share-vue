# Text Overlay UI Planning - Revised Data Model Design

## Infrastructure Context
Based on the Terraform configuration and backend analysis:
- **Cloud Deployment**: Railway (backend) + AWS (S3, DynamoDB, Cognito)
- **Database**: Single DynamoDB table `video-metadata` with multiple GSIs
- **Storage**: S3 bucket with organized folder structure
- **Authentication**: AWS Cognito User Pools
- **Backend**: FastAPI on Railway (not AWS Lambda/API Gateway)

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

### 5. API Endpoints (Railway Backend)

```python
# Add to backend/main.py

@router.post("/videos/{video_id}/thumbnail")
async def generate_video_thumbnail(video_id: str):
    """Generate thumbnail for video using FFmpeg"""
    
@router.post("/videos/{video_id}/text-overlay-preview") 
async def generate_text_overlay_preview(
    video_id: str, 
    request: TextOverlayPreviewRequest
):
    """Generate text overlay preview on thumbnail using Pillow"""

@router.get("/videos/{video_id}/thumbnail")
async def get_video_thumbnail(video_id: str):
    """Get presigned URL for video thumbnail"""
```

### 6. Backend Services

#### Thumbnail Service (`backend/thumbnail_service.py`)
```python
import subprocess
from PIL import Image, ImageDraw, ImageFont
import hashlib

class ThumbnailService:
    @staticmethod
    def extract_video_thumbnail(video_s3_key: str, timestamp: float = None) -> str:
        """Extract thumbnail from S3 video using FFmpeg"""
        # Download video temporarily
        # Use FFmpeg to extract frame at timestamp (default: midpoint)
        # Upload thumbnail to S3
        # Return thumbnail S3 key
        
    @staticmethod  
    def generate_text_overlay_preview(
        thumbnail_s3_key: str,
        text_content: str,
        style: TextOverlayStyle
    ) -> str:
        """Generate text overlay preview using Pillow"""
        # Download thumbnail from S3
        # Apply text overlay with styling
        # Generate cache key based on style hash
        # Upload preview to S3
        # Return preview S3 key
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
2. **Thumbnail Generation** (NEW - automatic after upload)
3. **Text Customization** (enhanced with visual preview)
4. **Segment Selection** (unchanged)  
5. **Processing** (uses enhanced text styling)

#### Workflow Data Flow:
```
1. Video uploaded to S3 → video_id created in DynamoDB
2. Thumbnail extracted → stored in S3 → thumbnail_s3_key added to video record
3. User designs text overlay → preview generated → cached in S3
4. Processing uses enhanced TextInput with styling → applied to video segments
```

### 9. Performance Optimizations

#### Caching Strategy:
- **Thumbnail Generation**: Once per video, stored permanently
- **Preview Generation**: Hash-based caching, TTL cleanup
- **S3 Presigned URLs**: 1-hour expiration for thumbnails/previews

#### Memory Management:
- **Railway Environment**: Optimize for limited memory
- **Temp File Cleanup**: Automatic cleanup of downloaded files
- **Image Processing**: Resize thumbnails for web optimization

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
1. Add thumbnail fields to existing video records
2. Implement thumbnail generation service with FFmpeg
3. Add thumbnail generation to upload workflow

### Phase 2: Preview System  
1. Implement text overlay preview generation with Pillow
2. Add preview API endpoints
3. Create preview caching system

### Phase 3: Frontend Integration
1. Enhance Upload.vue Step 3 with visual preview
2. Create TextOverlayDesigner component
3. Integrate with existing text strategy system

## Risks and Mitigation

### Railway Deployment Considerations:
- **Memory Limits**: Optimize image processing for Railway's memory constraints
- **Storage**: Use S3 for all file storage, not local filesystem
- **Processing Time**: Ensure thumbnail/preview generation completes within request timeouts

### DynamoDB Single Table:
- **No Schema Changes**: Thumbnail data added as optional fields to existing records
- **GSI Limits**: Reuse existing GSIs, no new indexes needed
- **Backward Compatibility**: Existing records work without thumbnail data

---

*Revised Data Model for Railway + AWS Architecture - Date: 2025-07-06*