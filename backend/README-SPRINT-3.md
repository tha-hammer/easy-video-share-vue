# Sprint 3 Implementation: Dynamic User Input for Cutting & Text Strategy

## Overview

Sprint 3 successfully implements dynamic user input for video cutting parameters and text strategy selection. The implementation follows the function chain approach outlined in the plan and adds the necessary infrastructure for the frontend to preview segment counts and configure processing parameters.

## Key Features Implemented

### 1. Dynamic Cutting Parameters

- **Fixed Duration Cutting**: Users can specify exact segment duration (e.g., 30 seconds)
- **Random Duration Cutting**: Users can specify min/max duration range (e.g., 15-45 seconds)
- **Segment Preview**: Frontend can preview how many segments will be created before processing

### 2. Text Strategy Support

- **ONE_FOR_ALL**: Single text overlay for all segments (current implementation)
- **BASE_VARY**: Base text with LLM-generated variations (placeholder for Sprint 4)
- **UNIQUE_FOR_ALL**: Unique text per segment (placeholder for Sprint 4)

### 3. New API Endpoints

- `/api/video/analyze-duration`: Analyze video and preview segment count
- Updated `/api/upload/complete`: Accept cutting options and text strategy

## Implementation Details

### Function Chain 1: Video Duration Analysis & Segment Count Preview

#### New Pydantic Models (`models.py`)

```python
class TextStrategy(str, Enum):
    ONE_FOR_ALL = "one_for_all"
    BASE_VARY = "base_vary"
    UNIQUE_FOR_ALL = "unique_for_all"

class FixedCuttingParams(BaseModel):
    type: Literal["fixed"] = "fixed"
    duration_seconds: int

class RandomCuttingParams(BaseModel):
    type: Literal["random"] = "random"
    min_duration: int
    max_duration: int

CuttingOptions = Union[FixedCuttingParams, RandomCuttingParams]

class AnalyzeDurationRequest(BaseModel):
    s3_key: str
    cutting_options: CuttingOptions

class AnalyzeDurationResponse(BaseModel):
    total_duration: float
    num_segments: int
    segment_durations: List[float]
```

#### Video Processing Utilities (`video_processing_utils.py`)

```python
def get_video_duration_from_s3(s3_bucket: str, s3_key: str) -> float:
    """Get video duration using ffprobe for efficient metadata extraction"""
    # Downloads video temporarily, uses ffprobe, cleans up

def calculate_segments(total_duration: float, cutting_options: CuttingOptions) -> Tuple[int, List[Tuple[float, float]]]:
    """Calculate video segments based on cutting options"""
    # Returns (num_segments, [(start_time, end_time), ...])
```

#### API Endpoint (`main.py`)

```python
@router.post("/video/analyze-duration", response_model=AnalyzeDurationResponse)
async def analyze_duration(request: AnalyzeDurationRequest):
    """Analyze video duration and calculate segment count"""
    # Uses ffprobe for fast duration extraction
    # Calculates segments without processing video
    # Returns preview information to frontend
```

### Function Chain 2: Core Processing with Dynamic Parameters

#### Updated Task Signature (`tasks.py`)

```python
@celery_app.task(bind=True)
def process_video_task(self, s3_input_key: str, job_id: str, cutting_options: dict = None, text_strategy: str = None):
    """Enhanced video processing with dynamic parameters"""
    # Converts dict back to Pydantic models
    # Uses calculate_segments for precise cutting
    # Applies text strategy (Sprint 4 will expand this)
```

#### Updated Complete Upload (`main.py`)

```python
class CompleteUploadRequest(BaseModel):
    s3_key: str
    job_id: str
    cutting_options: Optional[CuttingOptions] = None
    text_strategy: Optional[TextStrategy] = None

@router.post("/upload/complete")
async def complete_upload(request: CompleteUploadRequest):
    """Enhanced complete upload with cutting options and text strategy"""
    # Serializes Pydantic models for Celery
    # Passes parameters to updated process_video_task
```

## API Usage Examples

### 1. Analyze Video Duration (Fixed Cutting)

```bash
curl -X POST "http://localhost:8000/api/video/analyze-duration" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/my-video.mp4",
    "cutting_options": {
      "type": "fixed",
      "duration_seconds": 30
    }
  }'
```

Response:

```json
{
  "total_duration": 120.5,
  "num_segments": 5,
  "segment_durations": [30.0, 30.0, 30.0, 30.0, 0.5]
}
```

### 2. Analyze Video Duration (Random Cutting)

```bash
curl -X POST "http://localhost:8000/api/video/analyze-duration" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/my-video.mp4",
    "cutting_options": {
      "type": "random",
      "min_duration": 15,
      "max_duration": 45
    }
  }'
```

### 3. Complete Upload with Cutting Options

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/my-video.mp4",
    "job_id": "abc-123-def",
    "cutting_options": {
      "type": "fixed",
      "duration_seconds": 20
    },
    "text_strategy": "one_for_all"
  }'
```

## Error Handling

### Video Not Found (404)

```json
{
  "detail": "Video file not found in S3"
}
```

### Invalid Video Format (400)

```json
{
  "detail": "Invalid video file format or corrupted: [ffprobe error details]"
}
```

### Video Too Short (400)

```json
{
  "detail": "Video is too short (5.2s) to generate segments with duration 30s"
}
```

## Testing

Two test scripts are provided:

### 1. API Endpoint Testing (`test_sprint3_validation.py`)

Tests all new API endpoints and error handling:

```bash
python test_sprint3_validation.py
```

### 2. Utility Function Testing (`test_sprint3_utils.py`)

Tests video processing utilities independently:

```bash
python test_sprint3_utils.py
```

## External Dependencies

### FFmpeg/ffprobe Requirement

The `get_video_duration_from_s3` function uses `ffprobe` for efficient video metadata extraction. Ensure FFmpeg is installed and available in the PATH where the FastAPI application runs.

#### Installation:

- **Windows**: Download from https://ffmpeg.org/download.html
- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`

#### Verification:

```bash
ffprobe -version
```

## Backward Compatibility

The implementation maintains full backward compatibility:

- `process_video_task` accepts optional parameters
- Default cutting options: 30-second fixed segments
- Default text strategy: `ONE_FOR_ALL`
- Existing Sprint 2 functionality unchanged

## Next Steps (Sprint 4)

1. **LLM Text Generation**: Implement `llm_service.py` for `BASE_VARY` strategy
2. **Unique Text UI**: Frontend support for `UNIQUE_FOR_ALL` strategy
3. **Enhanced Video Processing**: Update video processing to use precise segment times
4. **Text Overlay Improvements**: Replace hardcoded text with dynamic text generation

## Architecture Notes

### ID Management

Following the updated plan's focus on ID management:

- The `analyze-duration` endpoint is independent of the job workflow
- Job IDs are still generated in `complete_upload` endpoint
- Celery task IDs are used for job tracking (consistent with Sprint 2)

### Function Chain Separation

- **Analysis Chain**: Independent, read-only video analysis for UI preview
- **Processing Chain**: Full video processing with user parameters
- Clear separation allows frontend to analyze videos before committing to processing
