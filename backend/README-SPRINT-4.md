# Sprint 4 Update

# Sprint 4: LLM-Powered Text Generation & Enhanced Video Processing

## Overview

Sprint 4 delivers a robust, production-ready pipeline for dynamic, context-aware text overlays on video segments, powered by Google Vertex AI Gemini. The backend now supports multi-line overlays, precise segment timing, and three flexible text strategies, all fully integrated with Celery and the API.

---

## Key Features

### 1. LLM Integration (Vertex AI Gemini)

- **Service:** `llm_service_vertexai.py` provides context-driven, robust prompt construction and error handling.
- **Text Variation:** BASE_VARY strategy generates unique, context-aware text for each segment.
- **Fallbacks:** If LLM fails, falls back to user base text.

### 2. Text Overlay Strategies

- **ONE_FOR_ALL:** Single user-provided text for all segments.
- **BASE_VARY:** LLM-generated variations from a base text (context-aware).
- **UNIQUE_FOR_ALL:** User provides unique text for each segment (multi-line supported).

### 3. Multi-line & Dynamic Text Overlay

- **Multi-line Support:** Overlays now support explicit newlines and automatic wrapping for long lines.
- **Correct Line Order:** Text is rendered top-down, as expected for readable overlays.
- **Font Size:** Font size is dynamically calculated for each video, ensuring overlays are visually appropriate and never overwhelm the frame.

### 4. Precise Video Processing

- **Exact Segment Timing:** Uses precise start/end times for each segment.
- **Direct FFmpeg Integration:** Ensures accurate cutting and overlay, with robust error handling.

### 5. API & Celery Integration

- **API Models:** All endpoints support the new `text_input` parameter and dynamic cutting options.
- **Celery Tasks:** Fully compatible with JSON-serializable arguments; robust error handling and logging.

---

## Usage Examples

### 1. ONE_FOR_ALL Strategy

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "abc-123",
    "cutting_options": { "type": "fixed", "duration_seconds": 30 },
    "text_strategy": "one_for_all",
    "text_input": { "strategy": "one_for_all", "base_text": "Transform your business with AI!" }
  }'
```

### 2. BASE_VARY Strategy (LLM-Powered)

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "def-456",
    "cutting_options": { "type": "random", "min_duration": 20, "max_duration": 40 },
    "text_strategy": "base_vary",
    "text_input": { "strategy": "base_vary", "base_text": "Start your fitness journey today" }
  }'
```

### 3. UNIQUE_FOR_ALL Strategy (Multi-line Example)

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "ghi-789",
    "cutting_options": { "type": "fixed", "duration_seconds": 25 },
    "text_strategy": "unique_for_all",
    "text_input": {
      "strategy": "unique_for_all",
      "segment_texts": [
        "Welcome to our product demo!\nSee these amazing features",
        "Join 10,000+ happy customers",
        "Order now and save 50%!"
      ]
    }
  }'
```

---

## Troubleshooting & Notes

- **Font Size/Line Wrapping:** Font size and wrapping are dynamically calculated for each video. If overlays are still too large or wrap too early, adjust the divisor or max_chars_per_line in `video_processing_utils_sprint4.py`.
- **Line Order:** Overlays are rendered top-down for natural reading order.
- **Celery/LLM Errors:** All arguments to Celery tasks must be plain dicts/strings. LLM errors are logged and fallback text is used.
- **FFmpeg Requirements:** Ensure FFmpeg is installed with text rendering support and the required fonts are available.

---

## Testing

- `python test_sprint4_llm.py` — LLM service and text variation tests.
- `python test_sprint4_e2e.py` — End-to-end API and backend tests for all strategies.
- `python test_multiline_celery.py` — Celery worker test for multi-line overlays.
- `python test_multiline_text.py` — Standalone multi-line overlay test.

---

## Next Steps

- Frontend UI for rich text input and preview.
- Advanced text styling and font management.
- Caching and performance optimizations for LLM calls.

---

# Original Sprint 4 README

# Sprint 4 Implementation: LLM-Powered Text Generation & Enhanced Video Processing

## Overview

Sprint 4 successfully implements LLM-powered text generation using the Gemini API, enhanced text strategies (BASE_VARY, UNIQUE_FOR_ALL), and precise video segment timing. This sprint transforms the video processing pipeline from hardcoded text overlays to dynamic, AI-generated content tailored to user inputs.

## Key Features Implemented

### 1. LLM Integration (Gemini API)

- **LLM Service** (`llm_service.py`): Complete Gemini API integration
- **Text Variation Generation**: AI-powered text variations for BASE_VARY strategy
- **Secure API Key Management**: Environment variable-based configuration
- **Error Handling & Fallbacks**: Robust error handling with fallback to base text

### 2. Enhanced Text Strategies

- **ONE_FOR_ALL**: Single user-provided text for all segments
- **BASE_VARY**: AI-generated variations from user's base text using Gemini
- **UNIQUE_FOR_ALL**: User-provided unique text for each segment

### 3. Precise Video Processing

- **Exact Segment Timing**: Uses precise start/end times from `calculate_segments()`
- **Dynamic Text Overlay**: Text content determined by strategy and user input
- **FFmpeg Integration**: Direct FFmpeg calls for precise video cutting and text overlay

### 4. Enhanced API Models

- **TextInput Model**: Structured input for different text strategies
- **Updated Request Models**: Support for text_input parameter
- **Backward Compatibility**: Maintains compatibility with previous sprint APIs

## Implementation Details

### LLM Service (`llm_service.py`)

```python
class LLMService:
    def generate_text_variations(self, base_text: str, num_variations: int) -> List[str]:
        """Generate text variations using Gemini API"""
        # AI-powered text generation with social media optimization

    def validate_api_connection(self) -> bool:
        """Test Gemini API connectivity"""
```

Key features:

- Secure API key loading from environment variables
- Social media-optimized prompting for engaging variations
- Comprehensive error handling with intelligent fallbacks
- Connection validation and testing capabilities

### Enhanced Models (`models.py`)

```python
class TextInput(BaseModel):
    strategy: TextStrategy
    base_text: Optional[str] = None  # For ONE_FOR_ALL and BASE_VARY
    segment_texts: Optional[List[str]] = None  # For UNIQUE_FOR_ALL

class CompleteUploadRequest(BaseModel):
    # ...existing fields...
    text_input: Optional[TextInput] = None
```

### Precise Video Processing (`video_processing_utils_sprint4.py`)

```python
def split_video_with_precise_timing_and_dynamic_text(
    input_path: str,
    output_prefix: str,
    segment_times: List[Tuple[float, float]],
    text_strategy: TextStrategy,
    text_input: Optional[TextInput] = None
) -> List[str]:
    """Process video with exact timing and dynamic text"""
```

Key improvements:

- Uses exact segment start/end times instead of fixed durations
- Dynamic text preparation based on strategy
- Direct FFmpeg integration for precise processing
- Comprehensive text escaping for FFmpeg compatibility

## API Usage Examples

### 1. ONE_FOR_ALL Strategy

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "abc-123",
    "cutting_options": {
      "type": "fixed",
      "duration_seconds": 30
    },
    "text_strategy": "one_for_all",
    "text_input": {
      "strategy": "one_for_all",
      "base_text": "Transform your business with AI!"
    }
  }'
```

### 2. BASE_VARY Strategy (LLM-Powered)

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "def-456",
    "cutting_options": {
      "type": "random",
      "min_duration": 20,
      "max_duration": 40
    },
    "text_strategy": "base_vary",
    "text_input": {
      "strategy": "base_vary",
      "base_text": "Start your fitness journey today"
    }
  }'
```

**Result**: Gemini AI generates variations like:

- "Start your fitness journey today" (original)
- "Begin your transformation now - your body will thank you!"
- "Ready to get fit? Your journey starts with one step!"
- "Turn your fitness dreams into reality today!"

### 3. UNIQUE_FOR_ALL Strategy

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/video.mp4",
    "job_id": "ghi-789",
    "cutting_options": {
      "type": "fixed",
      "duration_seconds": 25
    },
    "text_strategy": "unique_for_all",
    "text_input": {
      "strategy": "unique_for_all",
      "segment_texts": [
        "Welcome to our product demo!",
        "See these amazing features",
        "Join 10,000+ happy customers",
        "Order now and save 50%!"
      ]
    }
  }'
```

## External Dependencies & Setup

### 1. Gemini API Key

**Required**: Valid Google AI (Gemini) API key

**Setup**:

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env` file: `GEMINI_API_KEY=your_api_key_here`
3. Verify with: `python test_sprint4_llm.py`

### 2. FFmpeg (Enhanced Requirement)

Sprint 4 requires FFmpeg with text rendering support:

**Windows**:

```powershell
# Chocolatey (recommended - includes font support)
choco install ffmpeg

# Verify text rendering capability
ffmpeg -filters | findstr drawtext
```

**Linux**:

```bash
sudo apt update
sudo apt install ffmpeg fontconfig fonts-dejavu-core
```

**Font Requirements**:

- Arial font (Windows: built-in, Linux: `fonts-liberation`)
- For custom fonts, ensure they're accessible to FFmpeg

### 3. Redis & Celery (Unchanged)

Same requirements as Sprint 2 & 3:

```powershell
.\scripts\start-redis.ps1
.\scripts\start-worker.ps1
```

## Testing

### 1. LLM Service Test

```bash
cd backend
python test_sprint4_llm.py
```

Tests:

- Gemini API connectivity
- Text variation generation with multiple test cases
- Error handling and fallback scenarios

### 2. End-to-End API Test

```bash
cd backend
python test_sprint4_e2e.py
```

Tests:

- All three text strategies via API
- Different cutting options
- Complete workflow simulation

### 3. Video Processing Test

```bash
cd backend
python test_actual_upload.py  # With Sprint 4 parameters
```

## Error Handling

### LLM Service Errors

```json
{
  "detail": "Video processing completed with fallback text due to LLM error"
}
```

**Fallback Strategy**: If Gemini API fails, the system:

1. Logs the error for debugging
2. Uses the provided base text for all segments
3. Continues processing without interruption

### Text Input Validation

```json
{
  "detail": "BASE_VARY strategy requires base_text in text_input"
}
```

```json
{
  "detail": "UNIQUE_FOR_ALL strategy requires segment_texts in text_input"
}
```

## Performance Considerations

### 1. LLM API Calls

- **Optimization**: Single API call generates all variations at once
- **Caching**: Could be added for repeated base texts (future enhancement)
- **Timeout**: 30-second timeout for LLM requests

### 2. Video Processing

- **Precision**: Exact segment timing eliminates overlap/gaps
- **Memory**: Processes one segment at a time to manage memory usage
- **FFmpeg**: Direct calls avoid Python subprocess overhead

## Backward Compatibility

Sprint 4 maintains full backward compatibility:

- **text_input parameter**: Optional - defaults to hardcoded text if not provided
- **Sprint 2/3 APIs**: Continue to work without modification
- **Default behavior**: ONE_FOR_ALL strategy with "AI Generated Video" text

## Next Steps (Sprint 5)

Potential enhancements for Sprint 5:

1. **Frontend UI**: Rich text input interfaces for all strategies
2. **Text Caching**: Cache LLM-generated variations for performance
3. **Advanced Prompting**: Custom prompting templates for different industries
4. **Font Management**: Custom font support and text styling options
5. **Preview Mode**: Text variation preview before processing

## Architecture Notes

### Function Chain Separation

- **LLM Service**: Independent, reusable text generation
- **Video Processing**: Precise timing with dynamic content
- **API Layer**: Clean parameter validation and serialization
- **Error Handling**: Graceful degradation maintains service availability

### ID Management

- Maintains consistent job_id tracking from Sprint 3
- LLM operations are stateless and don't affect job tracking
- Text generation errors don't interrupt video processing pipeline

## Verification Commands

```bash
# Test environment setup
python -c "from config import settings; print('✅ Gemini API Key:', settings.GEMINI_API_KEY[:10] + '...')"

# Test LLM integration
python test_sprint4_llm.py

# Test API endpoints
python test_sprint4_e2e.py

# Verify FFmpeg text support
ffmpeg -f lavfi -i color=black:size=320x240:duration=1 -vf "drawtext=text='Test':fontsize=24:fontcolor=white:x=10:y=10" -y test_text_overlay.mp4
```

Sprint 4 delivers a fully functional, LLM-powered video processing pipeline that transforms static text overlays into dynamic, engaging content optimized for social media and marketing use cases.
