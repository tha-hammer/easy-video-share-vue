We'll add **two new "Frontend Sprints"** to the overall plan. These sprints will detail the UI features and how they integrate with the backend APIs. While the LLM's primary role in these sprints would be to assist _you_ in generating Vue/TypeScript code snippets, you (the human developer) would lead the integration and overall UI/UX design.

---

### **New Sprints: Dedicated UI Development Phases**

These sprints will occur sequentially after **Backend Sprint 5** is complete, providing a stable API for the frontend to build upon.

---

#### **Frontend Sprint 1: Video Upload & Analysis UI**

- **Goal:** Users can select a video, choose their cutting options, and preview the estimated number of segments in the application's UI.
- **Dependencies:** Backend Sprint 1 (Upload APIs) and Backend Sprint 3 (Analysis APIs and models) must be complete and stable.
- **Key Features:**
  1.  **Video Upload Component:**
      - Implement a robust file input component (e.g., drag-and-drop area, file selector button).
      - Integrate frontend service calls (`axios`/`fetch`) with the `/api/upload/initiate` endpoint to get pre-signed S3 URLs.
      - Implement direct `PUT` upload of the video file to S3.
      - Integrate frontend service calls with the `/api/upload/complete` endpoint to notify the backend and receive the `job_id`.
      - Display upload progress (e.g., progress bar).
  2.  **Cutting Options UI:**
      - Add UI elements (e.g., radio buttons, dropdown) for selecting between "Fixed Duration" and "Random Duration" cutting strategies.
      - Provide input fields for `duration_seconds` (for fixed) or `min_seconds`/`max_seconds` (for random).
  3.  **Estimated Segments Preview:**
      - When a video is uploaded and cutting options are selected, make an API call to the `/api/video/analyze-duration` endpoint.
      - Display the `estimated_num_segments` received from the backend to the user in the UI.
  4.  **Initial Workflow Integration:**
      - Implement a "Next" or "Proceed" button that becomes active once a video is uploaded and analysis is complete, leading to the text input stage.
- **LLM Context Strategy (for generating Vue/TypeScript snippets):**
  - For specific Vue component logic (e.g., file input handling, data binding, API calls): Provide the relevant `.vue` file's `<script setup>` or `data`/`methods` sections.
  - Provide the TypeScript interfaces for `InitiateUploadRequest`, `InitiateUploadResponse`, `CompleteUploadRequest`, `AnalyzeDurationRequest`, `AnalyzeDurationResponse`, `CuttingOptions` (Fixed/Random params) as defined by the backend Pydantic models.
  - Ask for `axios` or `fetch` call implementations for each endpoint.
  - Ask for reactive properties and computed properties in Vue to manage UI state.
- **Testing Focus:** End-to-end user flow for video selection, upload, cutting option input, and successful display of estimated segment count. Verify network calls in browser dev tools.

---

#### **Frontend Sprint 2: Text Customization & Job Status UI**

- **Goal:** Users can input text context, define unique text per segment, submit the full job, and track its status with secure, downloadable links.
- **Dependencies:** Backend Sprint 3 (Dynamic Input), Backend Sprint 4 (LLM Text Integration), and Backend Sprint 5 (DynamoDB Status, Pre-signed Download URLs) must be complete and stable.
- **Key Features:**
  1.  **Context Input UI:**
      - Add a `textarea` or input field for the "Context for AI Text Generation."
      - Include clear help text guiding the user on the purpose of this field.
  2.  **Text Strategy Selection UI:**
      - Implement UI elements (e.g., radio buttons, dropdown) for selecting `ONE_FOR_ALL`, `BASE_VARY`, or `UNIQUE_FOR_ALL` text strategies.
      - Provide an input field for the `base_text` when `ONE_FOR_ALL` or `BASE_VARY` is selected.
  3.  **Dynamic "Unique for All" Segment Cards:**
      - If `UNIQUE_FOR_ALL` is selected, dynamically render a UI card or section for _each estimated segment_ (using the `estimated_num_segments` from Frontend Sprint 1).
      - Each card should contain a text input field for the user to enter specific text for that segment.
  4.  **Job Submission:**
      - Implement the final "Submit for Processing" button.
      - Construct the complete `ProcessVideoRequest` payload, including `s3_key`, `job_id`, `cutting_options`, `text_strategy`, `context`, and `unique_texts` (if applicable).
      - Send this payload to the backend's processing endpoint.
  5.  **Job Status Tracking UI:**
      - Display a dedicated area for job status (e.g., a simple card or list).
      - Implement polling logic (e.g., `setInterval`) to repeatedly call the `/api/jobs/{job_id}/status` endpoint.
      - Update the UI to reflect the `status` (PENDING, PROCESSING, COMPLETED, FAILED).
      - Display a progress indicator during the "PROCESSING" phase.
  6.  **Processed Video Display & Download:**
      - When a job's status is `COMPLETED`, display clickable elements (e.g., video players, download links) for each processed segment using the `download_urls` received from the backend.
      - Handle `FAILED` status with appropriate error messages.
- **LLM Context Strategy (for Vue/TypeScript snippets):**
  - Provide the backend's final `ProcessVideoRequest` and `JobStatusResponse` TypeScript interfaces.
  - Ask for conditional rendering logic (`v-if`, `v-for`) for dynamic UI elements.
  - Ask for methods to collect and validate user input for text fields.
  - Ask for implementation of the polling mechanism for job status.
  - Ask for dynamic rendering of video player/download links.
- **Testing Focus:** Comprehensive end-to-end user journey, from video upload to viewing/downloading processed clips, including testing all text strategies and live status updates.

---

This structured approach for UI development ensures you can tackle the frontend work systematically, building on the robust backend APIs you're developing with the LLM.
