This is an excellent way to think about LLM-driven development for a complex application. By focusing on "function chains," you can ensure the LLM receives precisely the context it needs for a specific piece of logic, minimizing irrelevant information and maximizing the chances of correct generation.

Let's break down the sprint plan into these function chains. For each chain, I'll describe the sequence of calls and how you'd guide the LLM through generating each part, adhering to the "Provide Only Necessary Context" principle.

### Strategy for LLM-Focused Function Chains

When tackling a function chain with an LLM:

1.  **Start from the "Entry Point":** Begin with the outermost function in the chain (e.g., a FastAPI endpoint or a Celery task).
2.  **Define Signatures & Data Models:** Provide the LLM with the exact function signature (name, parameters with type hints) and any Pydantic models or other data structures involved in the input/output of this entry point.
3.  **Outline Internal Calls:** Within the entry point, indicate _where_ other functions in the chain will be called, providing their anticipated signatures or just placeholder comments.
4.  **Generate Top-Down, Implement Bottom-Up (often):** You define the top-level function first, then you generate the helper functions it calls. Often, you'll ask the LLM to generate the helper functions first, and then integrate them into the top-level function.
5.  **Context for Helpers:** When generating a helper function, _only_ provide its signature, its docstring, and the interfaces (e.g., class definitions, Pydantic models, relevant `boto3` client initialization) of any external dependencies it needs.

---

### Sprint 1: Core Video Upload & S3 Storage Initiation

**Goal:** User can upload a video, it lands in S3. Frontend gets a job ID.

**Function Chain 1: Initiating S3 Direct Upload**

- **Sequence:** Frontend Action (user clicks upload) -> Frontend Service Call (`initiateUpload`) -> FastAPI Endpoint (`/api/upload/initiate`) -> `s3_utils.generate_presigned_url` -> FastAPI Response -> Frontend updates.
- **LLM Focus:**
  1.  **`models.py`:** Define `InitiateUploadRequest` and `InitiateUploadResponse` Pydantic models.
      - _LLM Context:_ `from pydantic import BaseModel`, desired fields and types.
  2.  **`s3_utils.py`:** Generate `generate_presigned_url` helper function.
      - _LLM Context:_ `import boto3`, `s3_client = boto3.client('s3')`, function signature `def generate_presigned_url(bucket_name: str, object_key: str, content_type: str, expiration: int = 3600) -> str:`, and a docstring explaining its purpose.
  3.  **`main.py` (or `api/endpoints.py`):** Generate `initiate_upload` FastAPI endpoint.
      - _LLM Context:_ `from fastapi import APIRouter`, `from .models import InitiateUploadRequest, InitiateUploadResponse`, `from .s3_utils import generate_presigned_url`, router initialization, endpoint decorator (`@router.post(...)`), and function signature `async def initiate_upload(request: InitiateUploadRequest) -> InitiateUploadResponse:`. Instruct it to call `generate_presigned_url`.

**Function Chain 2: Completing S3 Upload & Dispatching Task**

- **Sequence:** Frontend (after direct S3 upload success) -> Frontend Service Call (`completeUpload`) -> FastAPI Endpoint (`/api/upload/complete`) -> Celery/RQ `send_task` -> FastAPI Response (with `job_id`).
- **LLM Focus:**
  1.  **`models.py`:** Define `CompleteUploadRequest` (with `s3_key`, `job_id`) and `JobCreatedResponse` Pydantic models. (You'll define `job_id` generation in the backend).
      - _LLM Context:_ `from pydantic import BaseModel`, relevant fields.
  2.  **`tasks.py` (basic setup):** Generate Celery/RQ app initialization. A placeholder function for `process_video_task`.
      - _LLM Context:_ `from celery import Celery`, `celery_app = Celery(...)`, and the signature `def process_video_task(s3_input_key: str, job_id: str): pass`.
  3.  **`main.py` (or `api/endpoints.py`):** Generate `complete_upload` FastAPI endpoint.
      - _LLM Context:_ `from fastapi import APIRouter`, `from .models import CompleteUploadRequest, JobCreatedResponse`, `from .tasks import process_video_task`, `import uuid` (for `job_id` generation), and the endpoint signature. Instruct it to generate a `UUID` for `job_id` and call `process_video_task.delay()`.

---

**Sprint 2: Basic Video Splitting & Text Overlay Core (Background Task)**

**Goal:** The backend can retrieve an original video from S3, split it into hardcoded 30-second segments, add a single, hardcoded text overlay, and upload the processed clips back to S3 within the same `video_bucket`.

**Function Chain 1: Core Video Processing Task**

- **Sequence:** Celery Worker -> `tasks.process_video_task` -> `s3_utils.download_file_from_s3` -> `video_processing_utils.split_and_overlay_hardcoded` -> `s3_utils.upload_file_to_s3` (for each segment) -> Cleanup.
- **LLM Focus:**
  1.  **`s3_utils.py`:** Generate `download_file_from_s3` and `upload_file_to_s3` helper functions.
      - _LLM Context:_ `import boto3`, `s3_client`, function signatures (`def download_file_from_s3(bucket: str, key: str, local_path: str):`, `def upload_file_to_s3(local_path: str, bucket: str, key: str):`), docstrings.
  2.  **`video_processing_utils.py` (new file):** Generate `split_and_overlay_hardcoded` function.
      - _LLM Context:_ `from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip`, `import os`, `import tempfile`. Provide the function signature (`def split_and_overlay_hardcoded(input_path: str, output_prefix: str) -> List[str]:`) and detailed instructions on using `MoviePy` for `subclip`, `TextClip`, `CompositeVideoClip`, `write_videofile` with hardcoded text and segment duration.
  3.  **`tasks.py`:** Implement `process_video_task`.
      - _LLM Context:_ `from .s3_utils import download_file_from_s3, upload_file_to_s3`, `from .video_processing_utils import split_and_overlay_hardcoded`, `import tempfile`, `import os`. Provide the task decorator and function signature. Instruct it to tie together the S3 download, call `split_and_overlay_hardcoded`, then iterate through returned paths to upload to S3, and finally clean up local files.

---

**Sprint 3: Dynamic User Input for Cutting & Text Strategy (Data Flow)**

**Goal:** Frontend sends user-defined cutting parameters (fixed duration or random range) and the selected text strategy. Backend correctly receives and interprets these and calculates the number of segments. Frontend can preview this count.

**Function Chain 1: Video Duration Analysis & Segment Count Preview**

- **Sequence:** Frontend UI Action -> Frontend Service Call (`analyzeVideoDuration`) -> FastAPI Endpoint (`/api/video/analyze-duration`) -> `video_processing_utils.get_video_duration_from_s3` -> `video_processing_utils.calculate_segments` -> FastAPI Response -> Frontend updates UI.
- **LLM Focus:**
  1.  **`models.py`:** Define `FixedCuttingParams`, `RandomCuttingParams`, `CuttingOptions` (using `Union`, `Literal`). Define `AnalyzeDurationRequest` (with S3 key and cutting options) and `AnalyzeDurationResponse` (with estimated `num_segments`).
      - _LLM Context:_ Provide `BaseModel`, `Field`, `Union`, `Literal` imports. Clearly define the desired structure.
  2.  **`video_processing_utils.py`:** Generate `get_video_duration_from_s3` (which can efficiently read just enough data from S3, perhaps using `ffprobe` or a minimal `MoviePy` read) and `calculate_segments` functions.
      - _LLM Context:_ `from moviepy.editor import VideoFileClip` (or `ffmpeg-python`), `import random`, `import math`. Provide function signatures: `def get_video_duration_from_s3(s3_bucket: str, s3_key: str) -> float:`, `def calculate_segments(total_duration: float, cutting_options: CuttingOptions) -> int:`. Instruct on the random and fixed logic.
  3.  **`main.py`:** Generate `analyze_duration` endpoint.
      - _LLM Context:_ `from .models import AnalyzeDurationRequest, AnalyzeDurationResponse, CuttingOptions`, `from .video_processing_utils import get_video_duration_from_s3, calculate_segments`. Provide the endpoint signature. Instruct it to call the helper functions and return the count.

**Function Chain 2: Core Processing with Dynamic Parameters**

- **Sequence:** (Extends Sprint 2 Chain 1) `tasks.process_video_task` receives `cutting_options` and `text_strategy` -> `video_processing_utils.calculate_segments` -> loop using these segments and text strategy.
- **LLM Focus:**
  1.  **`models.py`:** Define `TextStrategy` Enum (e.g., `ONE_FOR_ALL`, `BASE_VARY`, `UNIQUE_FOR_ALL`). Update the `process_video_task` parameters.
  2.  **`tasks.py`:** Modify `process_video_task` signature to accept `cutting_options` and `text_strategy` (passing the Pydantic models directly). Update the internal logic to use `calculate_segments` from `video_processing_utils` to generate the actual cut points for `MoviePy` subclips. Add placeholder conditional logic for `text_strategy`.
      - _LLM Context:_ Show the new `process_video_task` signature, `from .models import CuttingOptions, TextStrategy`. Provide the logic to pass `CuttingOptions` to `calculate_segments` and then iterate based on results.

---

**Sprint 4: Dynamic Text Generation & Advanced Text UI**

**Goal:** Implement "base text + vary" (LLM-powered) and "unique for all" UI.

**Function Chain 1: LLM Text Variation for "Base + Vary"**

- **Sequence:** `tasks.process_video_task` (during processing loop for each segment) -> `llm_service.generate_text_variations` (if `BASE_VARY` strategy) -> `video_processing_utils.add_text_to_video` (with LLM text).
- **LLM Focus:**
  1.  **`llm_service.py` (new file):** Generate `generate_text_variations` function.
      - _LLM Context:_ `import google.generativeai as genai`, `from typing import List`, `genai.configure(api_key=...)`, `model = genai.GenerativeModel(...)`. Provide the function signature `def generate_text_variations(base_text: str, count: int) -> List[str]:` and a detailed prompt strategy for the LLM call to get variations.
  2.  **`tasks.py`:** Update `process_video_task`.
      - _LLM Context:_ Provide `from .llm_service import generate_text_variations`. Show the conditional logic based on `TextStrategy` enum. If `BASE_VARY`, call `generate_text_variations` once at the start of the task, then iterate through the returned list for each segment. If `UNIQUE_FOR_ALL`, iterate through the `text_params` array provided by the frontend.
  3.  **`video_processing_utils.py`:** Ensure `add_text_to_video` (or similar) is generic enough to accept any text string. (Likely already done from Sprint 2).

**Function Chain 2: Frontend Unique Text Input (UI-driven)**

- **Sequence:** Frontend `analyzeVideoDuration` response -> Frontend UI logic renders segment cards -> User inputs text -> Frontend constructs data payload -> Frontend calls `process-video` endpoint with `unique_for_all` strategy and array of texts.
- **LLM Focus:** (Primarily frontend-side logic, less direct backend function generation here.)
  - **Backend `models.py`:** Update `CompleteUploadRequest` to accept an optional `List[str]` for `unique_texts` if `TextStrategy` is `UNIQUE_FOR_ALL`.
  - **Frontend Vue Components:** Provide context of the Vue component where the segment count is displayed, and ask for logic to dynamically render input fields and collect their values.

---

**Sprint 5: Status Tracking (DynamoDB) & Frontend Display**

**Goal:** Frontend polls for job status, and processed video links are displayed once complete, using DynamoDB as the backend for job state.

**Function Chain 1: Job State Management (Create & Update)**

- **Sequence:**
  - `main.py/complete_upload` -> `dynamodb_service.create_job_entry`.
  - `tasks.process_video_task` (at various stages: start, each segment, complete, fail) -> `dynamodb_service.update_job_status`.
- **LLM Focus:**
  1.  **`dynamodb_service.py` (new file):** Generate `create_job_entry`, `update_job_status`, `get_job_status` functions.
      - _LLM Context:_ `import boto3`, `from datetime import datetime`, `from typing import List, Dict, Any`, `DYNAMODB_TABLE_NAME = "your-project-name-video-metadata"`. Provide `dynamodb_resource = boto3.resource('dynamodb')` and `table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)`. Give function signatures with docstrings. Ensure `update_job_status` can handle status changes and adding `output_s3_urls` as a list.
  2.  **`main.py`:** Update `complete_upload` to call `create_job_entry`.
      - _LLM Context:_ Show `from .dynamodb_service import create_job_entry`. Update the endpoint's implementation.
  3.  **`tasks.py`:** Update `process_video_task` to use `dynamodb_service.update_job_status`.
      - _LLM Context:_ Show `from .dynamodb_service import update_job_status`. Instruct where to add calls for "PROCESSING", "COMPLETED", "FAILED" states, and passing the list of S3 output URLs upon completion.

**Function Chain 2: Job Status Retrieval & Frontend Display**

- **Sequence:** Frontend polling logic -> Frontend Service Call (`getJobStatus`) -> FastAPI Endpoint (`/api/jobs/{job_id}/status`) -> `dynamodb_service.get_job_status` -> FastAPI Response -> Frontend updates UI.
- **LLM Focus:**
  1.  **`models.py`:** Define `JobStatusResponse` Pydantic model (with `job_id`, `status`, `output_urls` (optional)).
  2.  **`main.py`:** Generate `get_job_status` FastAPI endpoint.
      - _LLM Context:_ `from .models import JobStatusResponse`, `from .dynamodb_service import get_job_status`. Provide the endpoint signature (`@router.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)`). Instruct it to call `get_job_status` and return the data.
  3.  **Frontend (Vue/TS):** Describe the desired polling mechanism (e.g., `setInterval` or a reactive polling library) and how to display the status and then the video links.

---

By breaking down the development into these specific function chains, you're creating highly focused tasks for the LLM. Each task is a small, manageable problem with clear inputs and expected outputs, which is the ideal scenario for effective LLM code generation.
