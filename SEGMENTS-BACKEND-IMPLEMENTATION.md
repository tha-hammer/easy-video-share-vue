# Segments Backend Implementation

This document outlines the comprehensive backend implementation for the video segments feature, including database schema changes, API endpoints, Celery tasks, and deployment procedures.

## Overview

The segments backend implementation adds support for:

- Individual video segment management
- Social media usage tracking
- Advanced filtering and analytics
- Automated segment creation after video processing
- Real-time social media metrics syncing

## Architecture Changes

### 1. Database Schema Updates

#### DynamoDB Table Modifications

The existing `easy-video-share-video-metadata` table has been enhanced with new attributes and Global Secondary Indexes (GSIs):

**New Attributes:**

- `segment_id` (String) - Unique segment identifier
- `segment_type` (String) - Type of segment (processed, original, thumbnail, audio)
- `created_at` (String) - ISO timestamp for creation date

**New Global Secondary Indexes:**

- `video_id-segment_type-index` - Query segments by video_id and segment_type
- `user_id-segment_type-index` - Query segments by user_id and segment_type
- `user_id-created_at-index` - Query segments by user_id and creation date

### 2. Data Models

#### New Pydantic Models

**VideoSegment** - Core segment model:

```python
class VideoSegment(BaseModel):
    segment_id: str
    video_id: str
    user_id: str
    segment_type: SegmentType
    segment_number: int
    s3_key: str
    duration: float
    file_size: int
    content_type: str
    title: Optional[str]
    description: Optional[str]
    tags: List[str]
    social_media_usage: List[SocialMediaUsage]
```

**SocialMediaUsage** - Social media tracking:

```python
class SocialMediaUsage(BaseModel):
    platform: SocialMediaPlatform
    post_id: Optional[str]
    post_url: Optional[str]
    posted_at: Optional[str]
    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: Optional[float]
    last_synced: Optional[str]
```

**SegmentFilters** - Advanced filtering:

```python
class SegmentFilters(BaseModel):
    segment_type: Optional[SegmentType]
    min_duration: Optional[float]
    max_duration: Optional[float]
    tags: Optional[List[str]]
    has_social_media: Optional[bool]
    platform: Optional[SocialMediaPlatform]
    sort_by: str
    sort_order: str
```

### 3. API Endpoints

#### Segment Management Endpoints

| Method | Endpoint                          | Description                       |
| ------ | --------------------------------- | --------------------------------- |
| POST   | `/api/segments`                   | Create a new segment              |
| GET    | `/api/segments/{segment_id}`      | Get a specific segment            |
| GET    | `/api/videos/{video_id}/segments` | List segments for a video         |
| GET    | `/api/segments`                   | List user segments with filtering |
| PUT    | `/api/segments/{segment_id}`      | Update a segment                  |
| DELETE | `/api/segments/{segment_id}`      | Delete a segment                  |

#### Social Media Endpoints

| Method | Endpoint                                  | Description                |
| ------ | ----------------------------------------- | -------------------------- |
| POST   | `/api/segments/{segment_id}/social-media` | Sync social media metrics  |
| GET    | `/api/segments/{segment_id}/analytics`    | Get social media analytics |
| GET    | `/api/segments/{segment_id}/download`     | Get presigned download URL |

### 4. Celery Tasks

#### New Background Tasks

**create_segments_from_video_task**

- Automatically creates segment records after video processing
- Extracts metadata from S3 (file size, duration)
- Generates unique segment IDs
- Links segments to parent video

**sync_social_media_metrics_task**

- Syncs social media metrics for individual segments
- Currently uses mock data (ready for API integration)
- Supports Instagram, TikTok, YouTube, Facebook, Twitter

**batch_sync_social_media_task**

- Batch syncs metrics for all user segments
- Queues individual sync tasks for each segment/platform
- Provides progress tracking

### 5. DynamoDB Service Functions

#### New Database Operations

- `create_segment()` - Create new segment record
- `get_segment()` - Retrieve segment by ID
- `list_segments_by_video()` - Get all segments for a video
- `list_segments_by_user()` - Get user segments with filtering
- `update_segment()` - Update segment metadata
- `delete_segment()` - Delete segment record
- `add_social_media_usage()` - Add/update social media metrics
- `get_social_media_analytics()` - Calculate analytics

## Deployment

### Prerequisites

1. **Terraform** - For infrastructure changes
2. **AWS CLI** - Configured with appropriate permissions
3. **Python 3.8+** - For backend services
4. **Redis** - For Celery task queue

### Deployment Steps

1. **Apply Terraform Changes**

   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Deploy Backend Updates**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start Services**

   ```bash
   # Start FastAPI server
   python -m uvicorn main:app --host 0.0.0.0 --port 8000

   # Start Celery worker
   celery -A tasks worker --loglevel=info
   ```

### Automated Deployment

Use the provided deployment script:

```bash
./scripts/deploy-segments-backend.sh
```

This script will:

- Apply Terraform changes
- Verify database structure
- Test backend endpoints
- Provide deployment summary

## Integration Points

### 1. Video Processing Pipeline

The video processing task (`process_video_task`) has been updated to:

- Automatically queue segment creation after processing
- Pass video metadata to segment creation task
- Maintain backward compatibility

### 2. Frontend Integration

The backend provides endpoints that integrate with the existing frontend:

- Segment listing and filtering
- Social media analytics display
- Download functionality
- Real-time updates via SSE

### 3. Social Media APIs

The system is designed for future social media API integration:

- Instagram Graph API
- TikTok API
- YouTube Data API
- Facebook Graph API
- Twitter API v2

## Testing

### API Testing

Test the new endpoints:

```bash
# Test segment creation
curl -X POST "http://localhost:8000/api/segments" \
  -H "Content-Type: application/json" \
  -d '{"video_id": "test_video", "segment_type": "processed", ...}'

# Test segment listing
curl "http://localhost:8000/api/segments?user_id=test_user"

# Test social media sync
curl -X POST "http://localhost:8000/api/segments/test_segment/social-media" \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram", "post_id": "123456"}'
```

### Celery Task Testing

Test background tasks:

```python
from tasks import create_segments_from_video_task, sync_social_media_metrics_task

# Test segment creation
result = create_segments_from_video_task.delay(
    video_id="test_video",
    user_id="test_user",
    output_s3_keys=["processed/test_video/segment_001.mp4"],
    video_metadata={"title": "Test Video"}
)

# Test social media sync
result = sync_social_media_metrics_task.delay("test_segment", "instagram")
```

## Monitoring

### Key Metrics to Monitor

1. **Segment Creation Success Rate**

   - Track `create_segments_from_video_task` completion
   - Monitor DynamoDB write operations

2. **Social Media Sync Performance**

   - Track API response times
   - Monitor rate limiting

3. **Database Performance**
   - Monitor GSI query performance
   - Track DynamoDB read/write capacity

### Logging

The implementation includes comprehensive logging:

- Segment creation events
- Social media sync attempts
- Database operation errors
- API endpoint access

## Security Considerations

### Authentication & Authorization

- All endpoints require user authentication
- Segment access is restricted to owner
- Social media data is user-scoped

### Data Protection

- S3 presigned URLs with expiration
- Sensitive data encryption at rest
- Secure API key management

### Rate Limiting

- Implement rate limiting for social media sync
- Protect against API abuse
- Monitor for unusual activity

## Future Enhancements

### Phase 2: Social Media Integration

1. **Instagram Integration**

   - Graph API authentication
   - Post creation and metrics retrieval
   - Hashtag analytics

2. **TikTok Integration**

   - TikTok API access
   - Video upload and tracking
   - Trend analysis

3. **YouTube Integration**
   - YouTube Data API
   - Channel analytics
   - SEO optimization

### Phase 3: Advanced Analytics

1. **Performance Analytics**

   - Cross-platform comparison
   - Engagement rate analysis
   - Best posting time recommendations

2. **Content Optimization**
   - A/B testing framework
   - Content performance prediction
   - Automated optimization suggestions

### Phase 4: AI-Powered Features

1. **Content Analysis**

   - Video content analysis
   - Automatic tagging
   - Content categorization

2. **Predictive Analytics**
   - Performance prediction
   - Optimal posting times
   - Audience insights

## Troubleshooting

### Common Issues

1. **DynamoDB GSI Creation Fails**

   - Check AWS permissions
   - Verify table exists
   - Monitor capacity limits

2. **Celery Task Failures**

   - Check Redis connection
   - Verify task imports
   - Monitor worker logs

3. **S3 Access Issues**
   - Verify IAM permissions
   - Check bucket policies
   - Validate presigned URLs

### Debug Commands

```bash
# Check DynamoDB table structure
aws dynamodb describe-table --table-name easy-video-share-video-metadata

# Test Redis connection
redis-cli ping

# Check Celery worker status
celery -A tasks inspect active

# Monitor API logs
tail -f backend/logs/app.log
```

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review application logs
3. Test individual components
4. Contact the development team

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Status:** Production Ready
