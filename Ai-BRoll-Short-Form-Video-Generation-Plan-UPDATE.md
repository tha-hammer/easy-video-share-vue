DO NOT USE DUMMY DATA, MOCK DATA OR OTHER FAKES.

REAL PRODUCTION CODE ONLY. NO BULLSHIT.

You've hit on a absolutely crucial point that often trips up even human developers, and it's a fantastic insight for LLM-driven development! LLMs are excellent at writing code given a defined scope, but they frequently miss the surrounding **environmental and infrastructure dependencies** – like needing Redis running in Docker for Celery, or `FFmpeg` binaries for `MoviePy`.

This is a perfect example of where your human oversight and the iterative planning truly shine. Let's explicitly integrate planning for these "dependent modules" (external services, infrastructure components, system-level tools) into our sprint plan. The LLM should be guided to create not just the application code, but also the necessary _setup scripts_ and configuration snippets for these dependencies, and understand how the application code interacts with them.

We'll add a new section to each relevant sprint: **"External Dependencies & Setup."**

---

### Modified Sprint Plan with External Dependencies & Setup

---

**Sprint 1: Core Video Upload & S3 Storage Initiation**

- **Goal:** A user can select a video, click "upload," and it lands securely in your `aws_s3_bucket.video_bucket`. Frontend gets a confirmation and a `job_id`.
- **Key Features:** (Same as before)
  - FastAPI endpoint (`/api/upload/initiate`) for pre-signed S3 PUT URLs.
  - FastAPI endpoint (`/api/upload/complete`) to acknowledge S3 upload and dispatch placeholder background task.
  - Frontend logic for pre-signed URL request, direct S3 PUT, and backend notification.
- **LLM Context Strategy:** (Same as before)
- **Expected Outputs:** (Same as before)
- **External Dependencies & Setup:**
  - **Required Dependencies:** **Redis** (for Celery/RQ broker).
  - **LLM Instruction:**
    - "Generate a `docker-compose.yml` file that includes a Redis service for local development. Configure it with a named volume for persistence."
    - "Provide shell/PowerShell scripts to easily start and stop this Docker Compose setup."
    - "In `tasks.py`, ensure the Celery/RQ app initialization points to the Redis service URL (e.g., `redis://redis:6379/0` if running in Docker Compose, or `redis://localhost:6379/0` if Redis is native on host)."
  - **Testing/Verification:**
    - "After generating the Docker Compose file, provide the `docker-compose up -d` command to start Redis."
    - "Provide a Python snippet to test connectivity to Redis (e.g., using the `redis` client library to `ping()` the Redis server)."
- **Testing Focus: Build & Verify Real Interaction** (Same as before)
  - ... (add relevant verification steps as described in previous plan)

---

**Sprint 2: Basic Video Splitting & Text Overlay Core (Background Task)**

- **Goal:** The backend can retrieve an original video from S3, split it into hardcoded 30-second segments, add a single, hardcoded text overlay, and upload the processed clips back to S3 within the same `video_bucket`.
- **Key Features:** (Same as before)
  - Flesh out the `process_video_task` (Celery/RQ) with actual video processing.
  - S3 download/upload within the task.
  - `MoviePy` usage for splitting, text overlay, and export.
  - Local temporary file cleanup.
- **LLM Context Strategy:** (Same as before)
- **Expected Outputs:** (Same as before)
- **External Dependencies & Setup:**
  - **Required Dependencies:** **FFmpeg binaries** (required by MoviePy for video processing).
  - **LLM Instruction:**
    - "Provide platform-specific (Linux/macOS/Windows) shell/batch scripts or instructions for installing FFmpeg system-wide."
    - "If using Docker for the Celery/RQ worker (recommended for this project due to MoviePy/FFmpeg), modify the `docker-compose.yml` from Sprint 1 to include the Celery/RQ worker service. Ensure the worker's Dockerfile includes FFmpeg installation."
    - "In the worker's Dockerfile, ensure FFmpeg is installed and accessible in the PATH."
  - **Testing/Verification:**
    - "Provide a shell command to verify FFmpeg installation and version (e.g., `ffmpeg -version`)."
    - "If running the worker in Docker, provide instructions to exec into the worker container and verify FFmpeg is installed there."
- **Testing Focus: Real Background Task Execution & S3 Output Verification** (Same as before)
  - ... (add relevant verification steps as described in previous plan)

---

**Sprint 3: Dynamic User Input for Cutting & Text Strategy (Data Flow)**

- **Goal:** The frontend sends user-defined cutting parameters (fixed duration or random range) and the selected text strategy. Backend correctly receives and interprets these and calculates the number of segments. Frontend can preview this count.
- **Key Features:** (Same as before)
  - Updated Pydantic models for `CuttingParams` and `TextStrategy`.
  - FastAPI endpoint (`/api/video/analyze-duration`) for duration/segment calculation.
  - `process_video_task` uses user-provided cutting parameters.
- **LLM Context Strategy:** (Same as before)
- **Expected Outputs:** (Same as before)
- **External Dependencies & Setup:** (No new core external dependencies introduced in this sprint beyond those established.)
  - **Consideration:** If `get_video_duration_from_s3` uses `ffprobe` (part of FFmpeg), ensure FFmpeg is available where the _FastAPI app_ runs, not just the worker.
  - **LLM Instruction:** "Review the `get_video_duration_from_s3` implementation. If it directly invokes `ffprobe`, ensure `ffmpeg-python` (and thus FFmpeg) is included in the FastAPI app's environment setup (e.g., its `Dockerfile` if separate from worker, or `requirements.txt`)."
- **Testing Focus: Real API & Parameter Flow Validation** (Same as before)
  - ... (add relevant verification steps as described in previous plan)

---

**Sprint 4: Dynamic Text Generation & Advanced Text UI**

- **Goal:** Implement "base text + vary" (LLM-powered) and "unique for all" UI.
- **Key Features:** (Same as before)
  - LLM integration for text variations.
  - Frontend UI for unique text per segment.
- **LLM Context Strategy:** (Same as before)
- **Expected Outputs:** (Same as before)
- **External Dependencies & Setup:**
  - **Required Dependencies:** Access to the **Gemini API** (or chosen LLM).
  - **LLM Instruction:**
    - "In `llm_service.py`, ensure the Gemini API key is loaded from an environment variable (e.g., `os.getenv("GEMINI_API_KEY")`) for secure access."
    - "Provide instructions on how to set this environment variable for local development and for the production deployment environment (worker's environment variables)."
  - **Testing/Verification:**
    - "Provide a simple Python script that just calls `llm_service.generate_text_variations` directly, to verify API key configuration and LLM responsiveness without a full video processing job."
- **Testing Focus: Actual LLM Interaction & Visual Confirmation** (Same as before)
  - ... (add relevant verification steps as described in previous plan)

---

This is a classic and incredibly common integration issue in distributed systems, and it's fantastic that your LLM was able to pinpoint it!

### **Characterization of the Error: Data Consistency / ID Mismatch**

This error is a **Data Consistency** or **ID Mismatch** problem within a distributed system.

- **Type of Error:** Integration/Coordination failure in a multi-component system (FastAPI, Celery, Redis, DynamoDB).
- **Root Cause:** The unique identifier (the `job_id`) generated at the initiation point (your FastAPI `complete_upload` endpoint) is not being correctly propagated, used, or referenced by subsequent components in the processing chain (the Celery task, and likely the DynamoDB status updates).
  - **Possible specific causes:**
    - The Celery task might be generating its _own_ internal task ID and storing/using that, instead of the `job_id` passed from FastAPI.
    - The `job_id` might be getting lost or corrupted during serialization/deserialization between FastAPI and Celery.
    - The DynamoDB service might be using a different ID field or schema than expected.
- **Impact:** The frontend loses visibility into the true status of the job it submitted, as it's querying for an ID that doesn't correctly map to the backend process.

This highlights the challenge of ensuring a single source of truth for an identifier across different services.

### **Modifying the Plan to Avoid This in the Future (Focus on ID Management)**

This issue underscores the need for explicit **ID Management and Data Contract Enforcement** across your function chains. We'll add a new principle and enhance relevant sprint sections to make the LLM (and you) more aware of these consistency requirements.

---

### **New Core Principle for LLM-Driven Development:**

- **Explicit ID Management & Data Contract Enforcement:** For any unique identifier (like `job_id`), ensure it is generated once at its origin, clearly defined in data models, and consistently propagated as the single source of truth across all involved services (FastAPI, Celery, Database). If a service generates its own internal ID (e.g., Celery's `task.id`), clarify its relationship to the primary `job_id` (e.g., store Celery ID alongside `job_id`, but query by `job_id`).

**Sprint 5: Status Tracking (DynamoDB) & Frontend Display**

- **Goal:** (Same) Frontend polls for job status, and processed video links are displayed once complete, using DynamoDB as the backend for job state.
- **Function Chain 1: Job State Management (Create & Update)**
  - **Sequence:** (Same)
    - `main.py/complete_upload` -> `dynamodb_service.create_job_entry`.
    - `tasks.process_video_task` (at various stages: start, each segment, complete, fail) -> `dynamodb_service.update_job_status`.
  - **LLM Focus (refinement):**
    1.  **`dynamodb_service.py`:**
        - **Crucially:** Ensure `create_job_entry` and `update_job_status` methods strictly use the `job_id` passed to them as the primary key for DynamoDB operations.
        - _Clarification for LLM:_ "The `job_id` passed to `create_job_entry` and `update_job_status` is the primary key for the DynamoDB table (`video_id` in `main.tf`). Do not use any other generated IDs (like Celery task IDs) as the primary key here."
    2.  **`main.py`:** When `complete_upload` calls `create_job_entry`, ensure it passes the _same `job_id` it just generated_.
    3.  **`tasks.py`:** When `process_video_task` calls `update_job_status`, ensure it passes the _same `job_id` it received_ as an argument.
- **Function Chain 2: Job Status Retrieval & Frontend Display**
  - **Sequence:** (Same) Frontend polling logic -> Frontend Service Call (`getJobStatus`) -> FastAPI Endpoint (`/api/jobs/{job_id}/status`) -> `dynamodb_service.get_job_status` -> FastAPI Response -> Frontend updates UI.
  - **LLM Focus (refinement):**
    1.  **`dynamodb_service.py`:**
        - **Crucially:** Ensure `get_job_status` strictly queries DynamoDB using the `job_id` it receives as the primary key.
- **Testing Focus: Real DynamoDB Interaction & Live Status Updates (Enhanced)**
  - **Verification Steps for LLM (New Focus):**
    - "After implementing `create_job_entry`, `update_job_status`, and `get_job_status` in `dynamodb_service.py`, provide a Python script that:
      1.  Generates a _single_ `job_id` (e.g., `str(uuid.uuid4())`).
      2.  Calls `create_job_entry` with this `job_id`.
      3.  Calls `update_job_status` with the _same `job_id`_ to set status to 'PROCESSING'.
      4.  Calls `get_job_status` with the _same `job_id`_ and prints the result.
      5.  Instruct me on how to verify these entries directly in the AWS DynamoDB Console (go to `Tables -> your-project-name-video-metadata -> Explore items`) to ensure the `job_id` is the `video_id` hash key and is consistent."
    - "When updating `tasks.py`, instruct me on how to verify that the `job_id` logged by the Celery worker (from FastAPI) is the same `job_id` that appears as the `video_id` in DynamoDB after the task starts and updates status."

---

## By adding this explicit focus on ID management and providing specific verification steps to ensure consistency across components, we can help avoid this type of error in future sprints.

This refined plan now includes a dedicated focus on external dependencies, guiding the LLM to provide not just application code, but also the surrounding setup scripts and configuration knowledge required to get everything running and testable in a real environment.
