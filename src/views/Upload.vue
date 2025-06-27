<template>
  <!--begin::Upload Page-->
  <div class="d-flex flex-column gap-7 gap-lg-10">
    <!--begin::Page Header-->
    <div class="card card-flush">
      <div class="card-header">
        <div class="card-title">
          <h2 class="text-gray-900">Upload Video</h2>
        </div>
      </div>
    </div>
    <!--end::Page Header-->

    <!--begin::Upload Form-->
    <div class="card card-flush">
      <div class="card-body">
        <form @submit.prevent="handleUpload" class="form fv-plugins-bootstrap5">
          <!--begin::Video Title-->
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
          <!--end::Video Title-->

          <!--begin::File Upload-->
          <div class="row mb-8">
            <div class="col-xl-3">
              <div class="fs-6 fw-semibold mt-2 mb-3">
                Video File <span class="text-danger">*</span>
              </div>
            </div>
            <div class="col-xl-9">
              <!--begin::Drop Zone-->
              <div
                class="dropzone"
                :class="{
                  'dropzone-dragover': isDragOver,
                  'dropzone-uploading': isUploading,
                }"
                @drop="handleDrop"
                @dragover.prevent="isDragOver = true"
                @dragleave="isDragOver = false"
                @click="triggerFileSelect"
              >
                <div class="dz-message needsclick">
                  <div v-if="!selectedFile && !isUploading">
                    <KTIcon icon-name="file-up" icon-class="fs-3x text-primary mb-5" />
                    <h3 class="fs-5 fw-bold text-gray-900 mb-1">
                      Drop files here or click to upload
                    </h3>
                    <span class="fs-7 fw-semibold text-gray-500">
                      Supported formats: MP4, MOV, AVI, WebM (Max: 2GB)
                    </span>
                  </div>

                  <div v-else-if="selectedFile && !isUploading">
                    <KTIcon icon-name="file-text" icon-class="fs-3x text-success mb-5" />
                    <h3 class="fs-5 fw-bold text-gray-900 mb-1">{{ selectedFile.name }}</h3>
                    <span class="fs-7 fw-semibold text-gray-500">
                      {{ formatFileSize(selectedFile.size) }} • Ready to upload
                    </span>
                  </div>

                  <div v-else-if="isUploading">
                    <!--begin::Upload Progress-->
                    <div class="text-center">
                      <KTIcon icon-name="cloud-upload" icon-class="fs-3x text-primary mb-5" />
                      <h3 class="fs-5 fw-bold text-gray-900 mb-3">Uploading...</h3>

                      <!--begin::Progress Bar-->
                      <div class="progress mb-3" style="height: 6px">
                        <div
                          class="progress-bar bg-primary"
                          role="progressbar"
                          :style="{ width: uploadProgress + '%' }"
                        ></div>
                      </div>
                      <!--end::Progress Bar-->

                      <div class="d-flex justify-content-between text-muted fs-7 mb-3">
                        <span>{{ uploadProgress.toFixed(1) }}% complete</span>
                        <span v-if="uploadSpeed">{{ formatFileSize(uploadSpeed) }}/s</span>
                      </div>

                      <div v-if="estimatedTimeRemaining" class="text-muted fs-7 mb-3">
                        Estimated time remaining: {{ formatTime(estimatedTimeRemaining) }}
                      </div>

                      <!--begin::Upload Controls-->
                      <div class="d-flex justify-content-center gap-3">
                        <button
                          v-if="!isPaused"
                          type="button"
                          class="btn btn-sm btn-light-warning"
                          @click="pauseUpload"
                        >
                          <KTIcon icon-name="pause" icon-class="fs-4" />
                          Pause
                        </button>
                        <button
                          v-else
                          type="button"
                          class="btn btn-sm btn-light-success"
                          @click="resumeUpload"
                        >
                          <KTIcon icon-name="play" icon-class="fs-4" />
                          Resume
                        </button>
                        <button
                          type="button"
                          class="btn btn-sm btn-light-danger"
                          @click="cancelUpload"
                        >
                          <KTIcon icon-name="cross" icon-class="fs-4" />
                          Cancel
                        </button>
                      </div>
                      <!--end::Upload Controls-->
                    </div>
                    <!--end::Upload Progress-->
                  </div>
                </div>
              </div>
              <!--end::Drop Zone-->

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
            </div>
          </div>
          <!--end::File Upload-->

          <!--begin::Form Actions-->
          <div class="row">
            <div class="col-xl-3"></div>
            <div class="col-xl-9">
              <div class="d-flex justify-content-start gap-3">
                <button type="submit" class="btn btn-primary" :disabled="!canUpload">
                  <KTIcon icon-name="cloud-upload" icon-class="fs-2" />
                  {{ isUploading ? 'Uploading...' : 'Upload Video' }}
                </button>
                <router-link to="/videos" class="btn btn-light">Cancel</router-link>
              </div>
            </div>
          </div>
          <!--end::Form Actions-->
        </form>
      </div>
    </div>
    <!--end::Upload Form-->
  </div>
  <!--end::Upload Page-->
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useVideosStore } from '@/stores/videos'
import { useVideoUpload } from '@/composables/useVideoUpload'

export default defineComponent({
  name: 'upload-page',
  setup() {
    const router = useRouter()
    const videosStore = useVideosStore()
    const videoUpload = useVideoUpload()

    // Form data
    const videoTitle = ref('')
    const selectedFile = ref<File | null>(null)
    const fileInput = ref<HTMLInputElement>()

    // Upload state - connect to composable
    const isUploading = computed(() => videoUpload.isUploading.value)
    const currentProgress = computed(() => videoUpload.currentProgress.value)
    const uploadProgress = computed(() => currentProgress.value?.percentage || 0)
    const uploadSpeed = computed(() => currentProgress.value?.uploadSpeed || 0)
    const estimatedTimeRemaining = computed(
      () => currentProgress.value?.estimatedTimeRemaining || 0,
    )

    // Local UI state
    const isPaused = ref(false)
    const isDragOver = ref(false)

    // Error handling
    const titleError = ref('')
    const fileError = ref('')

    // Computed properties
    const canUpload = computed(() => {
      return videoTitle.value.trim() && selectedFile.value && !isUploading.value
    })

    // File validation
    const validateFile = (file: File): boolean => {
      fileError.value = ''

      // Check file size (2GB limit)
      const maxSize = 2 * 1024 * 1024 * 1024 // 2GB
      if (file.size > maxSize) {
        fileError.value = 'File size exceeds 2GB limit'
        return false
      }

      // Check file type
      const allowedTypes = ['video/mp4', 'video/mov', 'video/avi', 'video/webm']
      if (!allowedTypes.includes(file.type)) {
        fileError.value = 'Unsupported file format. Please use MP4, MOV, AVI, or WebM'
        return false
      }

      return true
    }

    // Title validation
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
      if (!isUploading.value) {
        fileInput.value?.click()
      }
    }

    // Upload handling
    const handleUpload = async () => {
      if (!validateTitle() || !selectedFile.value) {
        return
      }

      try {
        // Start the upload with the new simplified API
        const videoMetadata = await videoUpload.uploadVideo(
          selectedFile.value,
          videoTitle.value.trim(),
        )

        console.log('✅ Upload completed:', videoMetadata)

        // Save metadata to store for local state management
        await videosStore.saveVideoMetadata(videoMetadata)

        // Redirect to videos page
        router.push('/videos')
      } catch (error) {
        console.error('Upload failed:', error)

        // Provide specific error messages based on error type
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'

        if (errorMessage.includes('Failed to fetch') || errorMessage.includes('net::ERR_FAILED')) {
          fileError.value =
            'Cannot connect to the server. Please check your internet connection and API configuration.'
        } else if (errorMessage.includes('CORS')) {
          fileError.value =
            'Server access denied. The API needs to be configured to allow requests from this domain.'
        } else if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
          fileError.value = 'Authentication failed. Please log in again.'
        } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
          fileError.value = 'Access denied. You may not have permission to upload videos.'
        } else if (errorMessage.includes('404')) {
          fileError.value = 'API endpoint not found. Please check the server configuration.'
        } else if (errorMessage.includes('500')) {
          fileError.value = 'Server error. Please try again later or contact support.'
        } else {
          fileError.value = `Upload failed: ${errorMessage}`
        }
      }
    }

    const pauseUpload = async () => {
      isPaused.value = true
      await videoUpload.pauseUpload()
    }

    const resumeUpload = async () => {
      isPaused.value = false
      await videoUpload.resumeUpload()
    }

    const cancelUpload = async () => {
      if (confirm('Are you sure you want to cancel the upload?')) {
        await videoUpload.cancelUpload()
        isPaused.value = false
        selectedFile.value = null
      }
    }

    // Utility functions from composable
    const { formatFileSize, formatTime } = videoUpload

    return {
      videoTitle,
      selectedFile,
      fileInput,
      isUploading,
      isPaused,
      isDragOver,
      uploadProgress,
      uploadSpeed,
      estimatedTimeRemaining,
      titleError,
      fileError,
      canUpload,
      handleFileSelect,
      handleDrop,
      triggerFileSelect,
      handleUpload,
      pauseUpload,
      resumeUpload,
      cancelUpload,
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
