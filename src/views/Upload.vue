<template>
  <div class="d-flex flex-column gap-7 gap-lg-10">
    <div class="card card-flush">
      <div class="card-header">
        <div class="card-title">
          <h2 class="text-gray-900">AI B-Roll Video Generation</h2>
        </div>
      </div>
    </div>
    <div class="card card-flush">
      <div class="card-body">
        <!-- Wizard Steps -->
        <div class="mb-8">
          <ul class="nav nav-pills nav-pills-custom nav-pills-active-primary gap-4">
            <li class="nav-item" v-for="(step, idx) in steps" :key="step">
              <button class="nav-link" :class="{ active: currentStep === idx }" disabled>
                <span class="fw-bold">{{ step }}</span>
              </button>
            </li>
          </ul>
        </div>
        <!-- Step 1: Video Selection & Title -->
        <form
          v-if="currentStep === 0"
          @submit.prevent="goToUploadStep"
          class="form fv-plugins-bootstrap5"
        >
          <div class="row mb-8">
            <div class="col-xl-3">
              <div class="fs-6 fw-semibold mt-2 mb-3">
                Video Title <span class="text-danger">*</span>
              </div>
            </div>
            <div class="col-xl-9">
              <input
                v-model="videoTitle"
                type="text"
                class="form-control"
                :class="{ 'is-invalid': titleError }"
                placeholder="Enter a descriptive title for your video..."
                maxlength="100"
                required
              />
              <div v-if="titleError" class="invalid-feedback">{{ titleError }}</div>
              <div class="form-text">Maximum 100 characters</div>
            </div>
          </div>
          <div class="row mb-8">
            <div class="col-xl-3">
              <div class="fs-6 fw-semibold mt-2 mb-3">
                Video File <span class="text-danger">*</span>
              </div>
            </div>
            <div class="col-xl-9">
              <div
                class="dropzone"
                :class="{ 'dropzone-dragover': isDragOver }"
                @drop="handleDrop"
                @dragover.prevent="isDragOver = true"
                @dragleave="isDragOver = false"
                @click="triggerFileSelect"
              >
                <div class="dz-message needsclick">
                  <div v-if="!selectedFile">
                    <KTIcon icon-name="file-up" icon-class="fs-3x text-primary mb-5" />
                    <h3 class="fs-5 fw-bold text-gray-900 mb-1">
                      Drop files here or click to upload
                    </h3>
                    <span class="fs-7 fw-semibold text-gray-500">
                      Supported formats: MP4, MOV, AVI, WebM (Max: 2GB)
                    </span>
                  </div>
                  <div v-else>
                    <KTIcon icon-name="file-text" icon-class="fs-3x text-success mb-5" />
                    <h3 class="fs-5 fw-bold text-gray-900 mb-1">{{ selectedFile.name }}</h3>
                    <span class="fs-7 fw-semibold text-gray-500">
                      {{ formatFileSize(selectedFile.size) }} • Ready to upload
                    </span>
                  </div>
                </div>
              </div>
              <input
                ref="fileInput"
                type="file"
                class="d-none"
                accept="video/mp4,video/mov,video/avi,video/webm"
                @change="handleFileSelect"
              />
              <div v-if="fileError" class="alert alert-danger mt-3">{{ fileError }}</div>
              <div class="form-text mt-2">
                Maximum file size: 2GB. Supported formats: MP4, MOV, AVI, WebM
              </div>

              <!-- Upload Status Indicator -->
              <div v-if="uploadStatus" class="alert mt-3" :class="uploadStatusClass">
                <div class="d-flex align-items-center">
                  <span
                    v-if="uploadStatus === 'starting'"
                    class="spinner-border spinner-border-sm me-2"
                  ></span>
                  <span
                    v-else-if="uploadStatus === 'initiating'"
                    class="spinner-border spinner-border-sm me-2"
                  ></span>
                  <span
                    v-else-if="uploadStatus === 'uploading'"
                    class="spinner-border spinner-border-sm me-2"
                  ></span>
                  <span v-else-if="uploadStatus === 'complete'" class="text-success me-2">✅</span>
                  <span v-else-if="uploadStatus === 'error'" class="text-danger me-2">❌</span>
                  <strong>{{ uploadStatusMessage }}</strong>
                </div>
                <div v-if="uploadStatus === 'uploading' && currentProgress" class="mt-2">
                  <div class="progress" style="height: 4px">
                    <div class="progress-bar" :style="{ width: uploadProgressBar + '%' }"></div>
                  </div>
                  <small class="text-muted">{{ uploadProgressBar.toFixed(1) }}% complete</small>
                </div>
                <!-- Network Status -->
                <div v-if="uploadStatus === 'uploading'" class="mt-2">
                  <small class="text-muted">
                    <span v-if="isOnline" class="text-success">🟢 Online</span>
                    <span v-else class="text-danger">🔴 Offline</span>
                    <span v-if="connectionType" class="ms-2">• {{ connectionType }}</span>
                  </small>
                </div>
              </div>

              <!-- Debug Panel for Mobile Testing -->
              <div v-if="showDebugPanel" class="mt-4">
                <div class="card card-flush">
                  <div class="card-header">
                    <h5 class="card-title">Debug Information</h5>
                    <button
                      type="button"
                      @click="showDebugPanel = false"
                      class="btn btn-sm btn-icon btn-light"
                    >
                      <KTIcon icon-name="cross" icon-class="fs-2" />
                    </button>
                  </div>
                  <div class="card-body">
                    <div class="mb-3">
                      <strong>User Agent:</strong>
                      <div class="text-muted fs-7">{{ userAgent }}</div>
                    </div>
                    <div class="mb-3">
                      <strong>File Details:</strong>
                      <div v-if="selectedFile" class="text-muted fs-7">
                        Name: {{ selectedFile.name }}<br />
                        Size: {{ formatFileSize(selectedFile.size) }}<br />
                        Type: {{ selectedFile.type }}
                      </div>
                    </div>
                    <div class="mb-3">
                      <strong>Last Error:</strong>
                      <div v-if="fileError" class="text-danger fs-7">{{ fileError }}</div>
                    </div>
                    <button
                      type="button"
                      @click="clearConsole"
                      class="btn btn-sm btn-secondary me-2"
                    >
                      Clear Console
                    </button>
                    <button type="button" @click="copyDebugInfo" class="btn btn-sm btn-primary">
                      Copy Debug Info
                    </button>
                  </div>
                </div>
              </div>

              <!-- Debug Toggle Button -->
              <div class="mt-3">
                <button
                  type="button"
                  @click="showDebugPanel = !showDebugPanel"
                  class="btn btn-sm btn-light-warning"
                >
                  <KTIcon icon-name="bug" icon-class="fs-4 me-1" />
                  {{ showDebugPanel ? 'Hide' : 'Show' }} Debug Panel
                </button>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-xl-3"></div>
            <div class="col-xl-9">
              <div class="d-flex justify-content-start gap-3">
                <button type="submit" class="btn btn-primary" :disabled="!canProceedToUpload">
                  Next: Upload Video
                </button>
              </div>
            </div>
          </div>
        </form>
        <!-- Step 2: Upload Progress -->
        <div v-else-if="currentStep === 1">
          <div class="text-center mb-6">
            <KTIcon icon-name="cloud-upload" icon-class="fs-3x text-primary mb-5" />
            <h3 class="fs-5 fw-bold text-gray-900 mb-3">Uploading to S3...</h3>
            <div class="progress mb-3" style="height: 6px">
              <div
                class="progress-bar bg-primary"
                role="progressbar"
                :style="{ width: uploadProgressBar + '%' }"
              ></div>
            </div>
            <div class="d-flex justify-content-between text-muted fs-7 mb-3">
              <span>{{ uploadProgressBar.toFixed(1) }}% complete</span>
              <span v-if="currentProgress && currentProgress.completedChunks > 0">
                {{ currentProgress.completedChunks }}/{{ currentProgress.totalChunks }} chunks
                uploaded
              </span>
            </div>
          </div>
          <div class="d-flex justify-content-end">
            <button class="btn btn-primary" :disabled="!uploadComplete" @click="goToCuttingOptions">
              Next: Cutting Options
            </button>
          </div>
        </div>
        <!-- Step 3: Configure & Review (Cutting Options, Segment Analysis, Text Customization) -->
        <div v-else-if="currentStep === 2">
          <form @submit.prevent="startProcessing">
            <div class="mb-6">
              <label class="form-label fw-bold">Cutting Strategy</label>
              <div class="form-check form-check-custom form-check-solid mb-2">
                <input
                  class="form-check-input"
                  type="radio"
                  id="fixed"
                  value="fixed"
                  v-model="cuttingOptions.strategy"
                />
                <label class="form-check-label" for="fixed">Fixed Duration</label>
              </div>
              <div class="form-check form-check-custom form-check-solid mb-2">
                <input
                  class="form-check-input"
                  type="radio"
                  id="random"
                  value="random"
                  v-model="cuttingOptions.strategy"
                />
                <label class="form-check-label" for="random">Random Duration</label>
              </div>
            </div>
            <div v-if="cuttingOptions.strategy === 'fixed'" class="mb-6">
              <label class="form-label">Segment Duration (seconds)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="cuttingOptions.params.duration_seconds"
                min="5"
                max="600"
                required
              />
              <div class="form-text">Each segment will be this length (5-600 seconds).</div>
            </div>
            <div v-else class="mb-6">
              <label class="form-label">Min Duration (seconds)</label>
              <input
                type="number"
                class="form-control mb-2"
                v-model.number="cuttingOptions.params.min_seconds"
                min="5"
                max="600"
                required
              />
              <label class="form-label">Max Duration (seconds)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="cuttingOptions.params.max_seconds"
                min="5"
                max="600"
                required
              />
              <div class="form-text">
                Segments will be randomly between min and max (5-600 seconds).
              </div>
            </div>
            <!-- Segment Analysis Display -->
            <div class="mb-6">
              <h4 class="fw-bold">
                Estimated Segments: <span class="text-primary">{{ estimatedSegments }}</span>
              </h4>
              <div class="text-muted">Video duration: {{ videoDuration }} seconds</div>
            </div>
            <!-- Text Customization UI -->
            <div class="mb-6">
              <label class="form-label fw-bold">Text Customization Strategy</label>
              <div class="form-check form-check-custom form-check-solid mb-2">
                <input
                  class="form-check-input"
                  type="radio"
                  id="one_for_all"
                  value="one_for_all"
                  v-model="textStrategy"
                />
                <label class="form-check-label" for="one_for_all">One For All</label>
              </div>
              <div class="form-check form-check-custom form-check-solid mb-2">
                <input
                  class="form-check-input"
                  type="radio"
                  id="base_vary"
                  value="base_vary"
                  v-model="textStrategy"
                />
                <label class="form-check-label" for="base_vary">Base Vary</label>
              </div>
              <div class="form-check form-check-custom form-check-solid mb-2">
                <input
                  class="form-check-input"
                  type="radio"
                  id="unique_for_all"
                  value="unique_for_all"
                  v-model="textStrategy"
                />
                <label class="form-check-label" for="unique_for_all">Unique For All</label>
              </div>
            </div>
            <div v-if="textStrategy === 'one_for_all'" class="mb-6">
              <label class="form-label">Base Text</label>
              <input type="text" class="form-control" v-model="baseText" required />
            </div>
            <div v-if="textStrategy === 'base_vary'" class="mb-6">
              <label class="form-label">Base Text</label>
              <input type="text" class="form-control mb-2" v-model="baseText" required />
              <label class="form-label">Context</label>
              <input type="text" class="form-control" v-model="context" required />
            </div>
            <div
              v-if="textStrategy === 'unique_for_all' && estimatedSegments && estimatedSegments > 0"
              class="mb-6"
            >
              <label class="form-label">Unique Texts (one per segment)</label>
              <div v-for="idx in estimatedSegments" :key="idx" class="input-group mb-2">
                <input type="text" class="form-control" v-model="uniqueTexts[idx - 1]" required />
              </div>
            </div>
            <div class="d-flex justify-content-end">
              <button type="submit" class="btn btn-primary">Start Processing</button>
            </div>
          </form>
        </div>
        <!-- Step 4: Processing Dashboard -->
        <div v-else-if="currentStep === 3">
          <div class="text-center my-10">
            <span class="spinner-border text-primary mb-4" style="width: 3rem; height: 3rem"></span>
            <h4 class="fw-bold mt-4">Processing your video...</h4>
            <div class="text-muted">This may take a few moments. Please wait.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useVideoUpload } from '@/composables/useVideoUpload'

export default defineComponent({
  name: 'upload-page',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const videoUpload = useVideoUpload()

    // Wizard state
    const steps = ['Select Video', 'Upload', 'Cutting Options', 'Segment Analysis', 'Processing']
    const currentStep = ref(0)

    // Form data
    const videoTitle = ref('')
    const selectedFile = ref<File | null>(null)
    const fileInput = ref<HTMLInputElement>()
    const isDragOver = ref(false)
    const titleError = ref('')
    const fileError = ref('')
    const isPaused = ref(false)

    // Debug panel state
    const showDebugPanel = ref(false)

    // Browser info for debugging
    const userAgent = ref(navigator.userAgent)

    // Network status tracking
    const isOnline = ref(navigator.onLine)
    const connectionType = ref(
      (navigator as Navigator & { connection?: { effectiveType?: string } }).connection
        ?.effectiveType || 'unknown',
    )

    // Listen for online/offline events
    const updateNetworkStatus = () => {
      isOnline.value = navigator.onLine
      connectionType.value =
        (navigator as Navigator & { connection?: { effectiveType?: string } }).connection
          ?.effectiveType || 'unknown'
      console.log('🔍 Debug: Network status changed:', {
        online: isOnline.value,
        type: connectionType.value,
      })
    }

    // Add event listeners
    window.addEventListener('online', updateNetworkStatus)
    window.addEventListener('offline', updateNetworkStatus)

    // Upload status tracking
    const uploadStatus = ref<'starting' | 'initiating' | 'uploading' | 'complete' | 'error' | null>(
      null,
    )
    const uploadStatusMessage = ref('')
    const uploadStatusClass = computed(() => {
      switch (uploadStatus.value) {
        case 'starting':
        case 'initiating':
        case 'uploading':
          return 'alert-info'
        case 'complete':
          return 'alert-success'
        case 'error':
          return 'alert-danger'
        default:
          return 'alert-info'
      }
    })

    // Cutting options (sync with composable)
    type CuttingOptionsPayload =
      | { strategy: 'fixed'; params: { duration_seconds: number } }
      | { strategy: 'random'; params: { min_seconds: number; max_seconds: number } }
    const cuttingOptions = ref<CuttingOptionsPayload>({
      strategy: 'fixed',
      params: { duration_seconds: 30 },
    })

    // Text customization state
    const textStrategy = ref<'one_for_all' | 'base_vary' | 'unique_for_all'>('one_for_all')
    const baseText = ref('')
    const context = ref('')
    const uniqueTexts = ref<string[]>([''])

    // Step 1 validation
    const canProceedToUpload = computed(() => {
      return videoTitle.value.trim() && selectedFile.value
    })

    // Step 2 upload progress
    const currentProgress = videoUpload.currentProgress
    const uploadProgressBar = computed(() => currentProgress.value?.percentage || 0)
    const uploadComplete = computed(() => currentProgress.value?.status === 'completed')

    // Auto-advance to next step when upload completes
    watch(uploadComplete, (val) => {
      if (val && currentStep.value === 1) {
        // Optionally, call goToCuttingOptions() here to also notify backend
        // For now, just advance to next step
        // currentStep.value = 2
        // If you want to keep the button, comment out the above line
      }
    })

    // Step 4 segment analysis
    const estimatedSegments = videoUpload.estimatedSegments
    const videoDuration = videoUpload.videoDuration

    // File validation
    const validateFile = (file: File): boolean => {
      fileError.value = ''
      const maxSize = 2 * 1024 * 1024 * 1024 // 2GB
      if (file.size > maxSize) {
        fileError.value = 'File size exceeds 2GB limit'
        return false
      }
      const allowedTypes = ['video/mp4', 'video/mov', 'video/avi', 'video/webm']
      if (!allowedTypes.includes(file.type)) {
        fileError.value = 'Unsupported file format. Please use MP4, MOV, AVI, or WebM'
        return false
      }
      return true
    }
    const validateTitle = (): boolean => {
      titleError.value = ''
      if (!videoTitle.value.trim()) {
        titleError.value = 'Video title is required'
        return false
      }
      if (videoTitle.value.length > 100) {
        titleError.value = 'Title must be 100 characters or less'
        return false
      }
      return true
    }
    // File handling
    const handleFileSelect = (event: Event) => {
      const input = event.target as HTMLInputElement
      if (input.files && input.files[0]) {
        const file = input.files[0]
        if (validateFile(file)) {
          selectedFile.value = file
        } else {
          selectedFile.value = null
        }
      }
    }
    const handleDrop = (event: DragEvent) => {
      event.preventDefault()
      isDragOver.value = false
      if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
        const file = event.dataTransfer.files[0]
        if (validateFile(file)) {
          selectedFile.value = file
        } else {
          selectedFile.value = null
        }
      }
    }
    const triggerFileSelect = () => {
      fileInput.value?.click()
    }
    // Step 1 -> Step 2
    const goToUploadStep = async () => {
      if (!validateTitle() || !selectedFile.value) return

      // Immediately show we're starting
      console.log('🚀 Starting upload process...')
      fileError.value = '' // Clear any previous errors

      // Set initial status
      uploadStatus.value = 'starting'
      uploadStatusMessage.value = 'Starting upload process...'

      // Add immediate visual feedback
      const uploadButton = document.querySelector('button[type="submit"]') as HTMLButtonElement
      if (uploadButton) {
        uploadButton.disabled = true
        uploadButton.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2"></span>Starting Upload...'
      }

      try {
        console.log('🔍 Debug: File details:', {
          name: selectedFile.value.name,
          size: selectedFile.value.size,
          type: selectedFile.value.type,
          lastModified: new Date(selectedFile.value.lastModified).toISOString(),
        })
        console.log('🔍 Debug: User agent:', navigator.userAgent)
        console.log('🔍 Debug: Connection info:', {
          effectiveType:
            (
              navigator as Navigator & {
                connection?: { effectiveType?: string; downlink?: number; rtt?: number }
              }
            ).connection?.effectiveType || 'unknown',
          downlink:
            (
              navigator as Navigator & {
                connection?: { effectiveType?: string; downlink?: number; rtt?: number }
              }
            ).connection?.downlink || 'unknown',
          rtt:
            (
              navigator as Navigator & {
                connection?: { effectiveType?: string; downlink?: number; rtt?: number }
              }
            ).connection?.rtt || 'unknown',
        })

        // Check if we should use multi-part upload
        const shouldUseMultipart = videoUpload.shouldUseMultipart(selectedFile.value.size)
        console.log(
          `🔍 Debug: Should use multipart: ${shouldUseMultipart} (file size: ${selectedFile.value.size} bytes)`,
        )

        // Update status to initiating
        uploadStatus.value = 'initiating'
        uploadStatusMessage.value = 'Initiating upload...'

        // Update button text to show current step
        if (uploadButton) {
          uploadButton.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Initiating Upload...'
        }

        if (shouldUseMultipart) {
          console.log('📦 Using multi-part upload for large file')
          // Initiate multi-part upload
          await videoUpload.initiateMultipartUpload(selectedFile.value)
        } else {
          console.log('📤 Using single-part upload for smaller file')
          // Initiate single-part upload
          await videoUpload.initiateUpload(selectedFile.value)
        }

        // Update status to uploading
        uploadStatus.value = 'uploading'
        uploadStatusMessage.value = 'Uploading to S3...'

        // Update button text to show upload progress
        if (uploadButton) {
          uploadButton.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Uploading to S3...'
        }

        // Start S3 upload using composable (uses presignedUrl, s3Key)
        // Compose minimal metadata for S3 upload
        const user = authStore.user
        if (!user) throw new Error('User not authenticated')
        const metadata = {
          video_id: videoUpload.jobId.value!,
          user_id: user.userId,
          user_email: user.email,
          title: videoTitle.value.trim(),
          filename: selectedFile.value.name,
          bucket_location: videoUpload.s3Key.value!,
          upload_date: new Date().toISOString(),
          file_size: selectedFile.value.size,
          content_type: selectedFile.value.type,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        console.log('🔍 Debug: Upload metadata:', metadata)

        await videoUpload.uploadVideo(selectedFile.value, metadata)
        console.log('✅ Upload completed successfully')

        // Update status to complete
        uploadStatus.value = 'complete'
        uploadStatusMessage.value = 'Upload completed successfully!'

        // Update button text to show completion
        if (uploadButton) {
          uploadButton.innerHTML = '<span class="text-success me-2">✅</span>Upload Complete!'
        }

        currentStep.value = 2 // Only advance to Cutting Options, do NOT call completeUpload here
      } catch (e) {
        console.error('❌ Upload failed with error:', e)
        console.error('❌ Error details:', {
          message: (e as Error).message,
          stack: (e as Error).stack,
          name: (e as Error).name,
        })
        fileError.value = (e as Error).message

        // Update status to error
        uploadStatus.value = 'error'
        uploadStatusMessage.value = `Upload failed: ${(e as Error).message}`

        // Reset button on error
        if (uploadButton) {
          uploadButton.disabled = false
          uploadButton.innerHTML = 'Next: Upload Video'
        }
      }
    }
    // Step 2 -> Step 3
    const goToCuttingOptions = async () => {
      try {
        currentStep.value = 2 // Only advance, do NOT call completeUpload here
      } catch (e) {
        fileError.value = (e as Error).message
      }
    }
    // Step 3 -> Step 4
    const startProcessing = async () => {
      try {
        currentStep.value = 3 // Show processing step
        // Only pass the nested object, do NOT spread or add extra fields
        const cuttingOptionsPayload = cuttingOptions.value
        type TextInput = {
          strategy: 'one_for_all' | 'base_vary' | 'unique_for_all'
          base_text: string | null
          context: string | null
          unique_texts: string[] | null
        }
        let text_input: TextInput
        if (textStrategy.value === 'one_for_all') {
          text_input = {
            strategy: 'one_for_all',
            base_text: baseText.value,
            context: null,
            unique_texts: null,
          }
        } else if (textStrategy.value === 'base_vary') {
          text_input = {
            strategy: 'base_vary',
            base_text: baseText.value,
            context: context.value,
            unique_texts: null,
          }
        } else {
          text_input = {
            strategy: 'unique_for_all',
            base_text: null,
            context: null,
            unique_texts: uniqueTexts.value,
          }
        }
        // Get logged-in user ID
        const user = authStore.user // Assuming authStore.user is correctly populated
        const userId = user?.userId || 'anonymous' // Use a fallback if user is somehow null

        // Create video metadata for the complete upload request
        const videoMetadata = {
          video_id: videoUpload.jobId.value!,
          user_id: user?.userId || 'anonymous',
          user_email: user?.email || 'unknown@example.com',
          title: videoTitle.value.trim(),
          filename: selectedFile.value?.name || 'unknown.mp4',
          bucket_location: videoUpload.s3Key.value!,
          upload_date: new Date().toISOString(),
          file_size: selectedFile.value?.size || 0,
          content_type: selectedFile.value?.type || 'video/mp4',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }

        // Only pass the nested object, do NOT spread or add extra fields
        await videoUpload.completeUpload(
          cuttingOptionsPayload,
          textStrategy.value,
          text_input,
          userId,
          videoMetadata,
        )
        setTimeout(() => {
          router.push({ name: 'TextCustomization', params: { jobId: videoUpload.jobId.value } })
        }, 1200)
      } catch (e) {
        fileError.value = (e as Error).message
      }
    }
    // Step 2: Auto-analyze segments when entering Configure & Review or when cutting options change
    watch(
      () => [
        currentStep.value,
        cuttingOptions.value.strategy,
        cuttingOptions.value.strategy === 'fixed'
          ? cuttingOptions.value.params.duration_seconds
          : undefined,
        cuttingOptions.value.strategy === 'random'
          ? cuttingOptions.value.params.min_seconds
          : undefined,
        cuttingOptions.value.strategy === 'random'
          ? cuttingOptions.value.params.max_seconds
          : undefined,
      ],
      async ([step]) => {
        if (step === 2) {
          try {
            let payload: CuttingOptionsPayload
            if (
              cuttingOptions.value.strategy === 'fixed' &&
              cuttingOptions.value.params.duration_seconds != null
            ) {
              payload = {
                strategy: 'fixed',
                params: { duration_seconds: cuttingOptions.value.params.duration_seconds },
              }
            } else if (
              cuttingOptions.value.strategy === 'random' &&
              cuttingOptions.value.params.min_seconds != null &&
              cuttingOptions.value.params.max_seconds != null
            ) {
              payload = {
                strategy: 'random',
                params: {
                  min_seconds: cuttingOptions.value.params.min_seconds,
                  max_seconds: cuttingOptions.value.params.max_seconds,
                },
              }
            } else {
              videoUpload.estimatedSegments.value = 0
              videoUpload.videoDuration.value = 0
              return
            }
            const result = await videoUpload.analyzeDuration(videoUpload.s3Key.value!, payload)
            videoUpload.estimatedSegments.value = result.estimated_num_segments
            videoUpload.videoDuration.value = result.duration_seconds
            // Sync uniqueTexts array for UNIQUE_FOR_ALL
            if (textStrategy.value === 'unique_for_all') {
              const n = result.estimated_num_segments || 0
              if (uniqueTexts.value.length !== n) {
                uniqueTexts.value = Array.from({ length: n }, (_, i) => uniqueTexts.value[i] || '')
              }
            }
          } catch (e) {
            fileError.value = (e as Error).message
            videoUpload.estimatedSegments.value = 0
            videoUpload.videoDuration.value = 0
          }
        }
      },
      { immediate: true },
    )
    // Watch strategy to reset params when switching
    watch(
      () => cuttingOptions.value.strategy,
      (newStrategy) => {
        if (newStrategy === 'fixed') {
          cuttingOptions.value.params = { duration_seconds: 30 }
        } else if (newStrategy === 'random') {
          cuttingOptions.value.params = { min_seconds: 28, max_seconds: 56 }
        }
      },
      { immediate: true },
    )
    // Utils
    const formatFileSize = videoUpload.formatFileSize
    const formatTime = videoUpload.formatTime

    // Debug methods
    const clearConsole = () => {
      console.clear()
      console.log('🔍 Debug: Console cleared')
    }

    const copyDebugInfo = async () => {
      const debugInfo = {
        userAgent: navigator.userAgent,
        fileDetails: selectedFile.value
          ? {
              name: selectedFile.value.name,
              size: selectedFile.value.size,
              type: selectedFile.value.type,
            }
          : null,
        lastError: fileError.value,
        timestamp: new Date().toISOString(),
      }

      try {
        await navigator.clipboard.writeText(JSON.stringify(debugInfo, null, 2))
        console.log('✅ Debug info copied to clipboard')
      } catch (error) {
        console.error('❌ Failed to copy debug info:', error)
      }
    }

    return {
      steps,
      currentStep,
      videoTitle,
      selectedFile,
      fileInput,
      isDragOver,
      titleError,
      fileError,
      isPaused, // can be removed if not used elsewhere
      cuttingOptions,
      textStrategy,
      baseText,
      context,
      uniqueTexts,
      canProceedToUpload,
      currentProgress,
      uploadProgressBar,
      uploadComplete,
      estimatedSegments,
      videoDuration,
      showDebugPanel,
      userAgent,
      isOnline,
      connectionType,
      uploadStatus,
      uploadStatusMessage,
      uploadStatusClass,
      handleFileSelect,
      handleDrop,
      triggerFileSelect,
      goToUploadStep,
      goToCuttingOptions,
      startProcessing,
      clearConsole,
      copyDebugInfo,
      formatFileSize,
      formatTime,
    }
  },
})
</script>

<style scoped>
.dropzone {
  border: 2px dashed #d1d3e0;
  border-radius: 0.475rem;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dropzone:hover,
.dropzone-dragover {
  border-color: #009ef7;
  background-color: #f8faff;
}
.dropzone-uploading {
  cursor: default;
  border-color: #50cd89;
  background-color: #f8fff8;
}
.progress {
  width: 300px;
  max-width: 100%;
  margin: 0 auto;
}
</style>
