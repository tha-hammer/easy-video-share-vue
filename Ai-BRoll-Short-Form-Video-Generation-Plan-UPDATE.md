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

**Sprint 5: Status Tracking (DynamoDB) & Frontend Display**

- **Goal:** Frontend polls for job status, and processed video links are displayed once complete, using DynamoDB as the backend for job state.
- **Key Features:** (Same as before)
  - `boto3` DynamoDB client integration.
  - FastAPI endpoint (`/api/jobs/{job_id}/status`) to retrieve job status.
  - Background task updates job status in DynamoDB.
  - Frontend polling/display logic.
- **LLM Context Strategy:** (Same as before)
- **Expected Outputs:** (Same as before)
- **External Dependencies & Setup:**
  - **Required Dependencies:** AWS Credentials (IAM Role/Access Keys) with DynamoDB permissions for both the FastAPI application and the Celery/RQ worker.
  - **LLM Instruction:**
    - "Ensure `boto3` in `dynamodb_service.py` is configured to pick up credentials securely (e.g., via IAM roles for EC2/Fargate, or environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` for local development)."
    - "Provide a minimal Python script to test direct connectivity to DynamoDB and perform a sample `put_item` and `get_item` operation on the `video_metadata` table, using the table name from `main.tf`."
  - **Testing/Verification:**
    - "Provide AWS CLI commands to verify successful DynamoDB interactions (e.g., `aws dynamodb get-item --table-name ... --key ...`)."
- **Testing Focus: Real DynamoDB Interaction & Live Status Updates** (Same as before)
  - ... (add relevant verification steps as described in previous plan)

---

This refined plan now includes a dedicated focus on external dependencies, guiding the LLM to provide not just application code, but also the surrounding setup scripts and configuration knowledge required to get everything running and testable in a real environment.
