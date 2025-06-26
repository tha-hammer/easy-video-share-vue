<template>
  <div class="card">
    <!-- Header -->
    <div class="card-header">
      <div class="card-title">
        <h3 class="fw-bolder">
          <i class="fas fa-magic text-primary me-2"></i>
          AI Video Generation
        </h3>
        <p class="text-muted mb-0">Transform your audio into engaging short-form videos</p>
      </div>
    </div>

    <div class="card-body">
      <!-- Progress Stepper -->
      <div
        class="stepper stepper-pills stepper-column d-flex flex-column flex-xl-row flex-row-fluid"
        id="kt_create_account_stepper"
      >
        <!-- Nav -->
        <div
          class="d-flex justify-content-center justify-content-xl-start flex-row-auto w-100 w-xl-300px"
        >
          <div class="stepper-nav ps-lg-10">
            <!-- Step 1: Select Audio -->
            <div
              class="stepper-item"
              :class="{ current: currentStep === 1, completed: currentStep > 1 }"
            >
              <div class="stepper-wrapper">
                <div class="stepper-icon">
                  <i class="stepper-check fas fa-check"></i>
                  <span class="stepper-number">1</span>
                </div>
                <div class="stepper-label">
                  <h3 class="stepper-title">Select Audio</h3>
                  <div class="stepper-desc">Choose your audio file</div>
                </div>
              </div>
            </div>

            <!-- Step 2: Configure -->
            <div
              class="stepper-item"
              :class="{ current: currentStep === 2, completed: currentStep > 2 }"
            >
              <div class="stepper-wrapper">
                <div class="stepper-icon">
                  <i class="stepper-check fas fa-check"></i>
                  <span class="stepper-number">2</span>
                </div>
                <div class="stepper-label">
                  <h3 class="stepper-title">Configure</h3>
                  <div class="stepper-desc">Set video parameters</div>
                </div>
              </div>
            </div>

            <!-- Step 3: Processing -->
            <div
              class="stepper-item"
              :class="{ current: currentStep === 3, completed: currentStep > 3 }"
            >
              <div class="stepper-wrapper">
                <div class="stepper-icon">
                  <i class="stepper-check fas fa-check"></i>
                  <span class="stepper-number">3</span>
                </div>
                <div class="stepper-label">
                  <h3 class="stepper-title">Processing</h3>
                  <div class="stepper-desc">AI generation in progress</div>
                </div>
              </div>
            </div>

            <!-- Step 4: Complete -->
            <div
              class="stepper-item"
              :class="{ current: currentStep === 4, completed: currentStep > 4 }"
            >
              <div class="stepper-wrapper">
                <div class="stepper-icon">
                  <i class="stepper-check fas fa-check"></i>
                  <span class="stepper-number">4</span>
                </div>
                <div class="stepper-label">
                  <h3 class="stepper-title">Complete</h3>
                  <div class="stepper-desc">Your video is ready!</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-row-fluid py-lg-5 px-lg-15">
          <!-- Step 1: Select Audio File -->
          <div v-if="currentStep === 1" class="current">
            <div class="w-100">
              <div class="pb-10 pb-lg-15">
                <h2 class="fw-bolder text-dark">Select Your Audio File</h2>
                <div class="text-muted fw-bold fs-6">
                  Choose an audio file to transform into a video. We support MP3, WAV, M4A, and MP4
                  files.
                </div>
              </div>

              <!-- Audio File Selection -->
              <div class="row g-6 g-xl-9" v-if="userVideos.length > 0">
                <div class="col-md-6 col-lg-4" v-for="video in userVideos" :key="video.video_id">
                  <div
                    class="card cursor-pointer border-2 h-100"
                    :class="{
                      'border-primary bg-light-primary': selectedVideo?.video_id === video.video_id,
                    }"
                    @click="selectVideo(video)"
                  >
                    <div class="card-body d-flex flex-column">
                      <div class="d-flex align-items-center mb-3">
                        <i class="fas fa-music text-primary fs-3x me-3"></i>
                        <div class="flex-grow-1">
                          <h5 class="fw-bold mb-1">{{ video.title }}</h5>
                          <p class="text-muted mb-0 fs-7">{{ video.filename }}</p>
                        </div>
                        <div
                          v-if="selectedVideo?.video_id === video.video_id"
                          class="badge badge-circle badge-primary"
                        >
                          <i class="fas fa-check"></i>
                        </div>
                      </div>

                      <div class="d-flex justify-content-between text-muted fs-7">
                        <span>{{ formatDate(video.upload_date) }}</span>
                        <span v-if="video.duration">{{ formatDuration(video.duration) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No Videos Message -->
              <div v-else class="text-center">
                <i class="fas fa-music display-4 text-muted mb-4"></i>
                <h4>No Audio Files Found</h4>
                <p class="text-muted">
                  Please upload some audio files first to get started with AI video generation.
                </p>
                <router-link to="/upload" class="btn btn-primary">
                  <i class="fas fa-upload me-2"></i>Upload Audio Files
                </router-link>
              </div>

              <!-- Continue Button -->
              <div class="d-flex flex-stack pt-15" v-if="userVideos.length > 0">
                <div></div>
                <div>
                  <button
                    class="btn btn-lg btn-primary"
                    :disabled="!selectedVideo"
                    @click="nextStep"
                  >
                    Continue
                    <i class="fas fa-arrow-right fs-4 ms-1"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 2: Configure AI Generation -->
          <div v-if="currentStep === 2" class="current">
            <div class="w-100">
              <div class="pb-10 pb-lg-15">
                <h2 class="fw-bolder text-dark">Configure Your AI Video</h2>
                <div class="text-muted fw-bold fs-6">
                  Describe what kind of video you want to create and set your preferences.
                </div>
              </div>

              <div class="mb-10">
                <!-- Selected Audio Info -->
                <div class="card bg-light-info border-info mb-8">
                  <div class="card-body">
                    <div class="d-flex align-items-center">
                      <i class="fas fa-info-circle text-info fs-3x me-4"></i>
                      <div>
                        <h5 class="fw-bold text-info mb-1">Selected Audio</h5>
                        <p class="mb-0">{{ selectedVideo?.title }}</p>
                        <small class="text-muted">{{ selectedVideo?.filename }}</small>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Video Description/Prompt -->
                <div class="mb-8">
                  <label class="form-label fs-6 fw-bolder text-dark"
                    >Video Description & Creative Direction</label
                  >
                  <textarea
                    class="form-control form-control-lg form-control-solid"
                    rows="4"
                    v-model="aiConfig.prompt"
                    placeholder="Describe the type of video you want to create. Be specific about the style, mood, and visual elements you envision..."
                  ></textarea>
                  <div class="form-text">
                    Example: "Create a dynamic, cinematic video with urban backgrounds and modern
                    aesthetics. Focus on close-up shots with dramatic lighting."
                  </div>
                </div>

                <!-- Video Settings -->
                <div class="row g-6">
                  <div class="col-md-6">
                    <label class="form-label fs-6 fw-bolder text-dark">Target Duration</label>
                    <select
                      class="form-select form-select-lg form-select-solid"
                      v-model="aiConfig.targetDuration"
                    >
                      <option value="15">15 seconds - Quick & Punchy</option>
                      <option value="30">30 seconds - Standard</option>
                      <option value="45">45 seconds - Extended</option>
                      <option value="60">60 seconds - Full Length</option>
                    </select>
                    <div class="form-text">Estimated processing time: {{ getEstimatedTime() }}</div>
                  </div>

                  <div class="col-md-6">
                    <label class="form-label fs-6 fw-bolder text-dark">Visual Style</label>
                    <select
                      class="form-select form-select-lg form-select-solid"
                      v-model="aiConfig.style"
                    >
                      <option value="realistic">Realistic - Photographic quality</option>
                      <option value="cinematic">Cinematic - Movie-like scenes</option>
                      <option value="animated">Animated - Stylized animation</option>
                      <option value="artistic">Artistic - Creative & abstract</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Navigation -->
              <div class="d-flex flex-stack pt-15">
                <div>
                  <button class="btn btn-lg btn-light-primary" @click="previousStep">
                    <i class="fas fa-arrow-left fs-4 me-1"></i>
                    Previous
                  </button>
                </div>
                <div>
                  <button
                    class="btn btn-lg btn-primary"
                    :disabled="!aiConfig.prompt.trim()"
                    @click="startAIGeneration"
                  >
                    Generate AI Video
                    <i class="fas fa-magic fs-4 ms-1"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Processing -->
          <div v-if="currentStep === 3" class="current">
            <div class="w-100">
              <div class="pb-10 pb-lg-15">
                <h2 class="fw-bolder text-dark">AI Video Generation in Progress</h2>
                <div class="text-muted fw-bold fs-6">
                  Please wait while we transform your audio into an amazing video.
                </div>
              </div>

              <!-- Progress Bar -->
              <div class="mb-8">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <span class="fw-bold fs-6">{{ currentProcessingMessage }}</span>
                  <span class="fw-bold fs-6">{{ processingProgress }}%</span>
                </div>
                <div class="progress bg-light-primary" style="height: 15px">
                  <div
                    class="progress-bar bg-primary progress-bar-striped progress-bar-animated"
                    :style="{ width: `${processingProgress}%` }"
                  ></div>
                </div>
              </div>

              <!-- Processing Steps -->
              <div class="card">
                <div class="card-body">
                  <h5 class="card-title mb-6">Processing Steps</h5>
                  <div class="row g-6">
                    <div class="col-md-6 col-lg-3" v-for="step in processingSteps" :key="step.step">
                      <div class="d-flex align-items-center">
                        <div class="symbol symbol-45px me-4">
                          <div
                            class="symbol-label rounded-circle"
                            :class="{
                              'bg-success': step.status === 'completed',
                              'bg-primary': step.status === 'processing',
                              'bg-light-danger': step.status === 'failed',
                              'bg-light': step.status === 'pending',
                            }"
                          >
                            <i
                              class="fas"
                              :class="{
                                'fa-check text-white': step.status === 'completed',
                                'fa-spinner fa-spin text-white': step.status === 'processing',
                                'fa-times text-danger': step.status === 'failed',
                                'fa-clock text-muted': step.status === 'pending',
                              }"
                            ></i>
                          </div>
                        </div>
                        <div>
                          <div class="fw-bold">{{ getStepDisplayName(step.step) }}</div>
                          <div class="text-muted text-capitalize">{{ step.status }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Cancel Option -->
              <div class="text-center pt-10">
                <p class="text-muted">
                  This process typically takes {{ getEstimatedTime() }}. You can safely close this
                  page and check back later.
                </p>
              </div>
            </div>
          </div>

          <!-- Step 4: Completed -->
          <div v-if="currentStep === 4" class="current">
            <div class="w-100 text-center">
              <div class="pb-10 pb-lg-15">
                <i class="fas fa-check-circle text-success" style="font-size: 5rem"></i>
                <h2 class="fw-bolder text-dark mt-6">Your AI Video is Ready!</h2>
                <div class="text-muted fw-bold fs-6">
                  We've successfully transformed your audio into an engaging video.
                </div>
              </div>

              <!-- Video Preview -->
              <div v-if="generatedVideo?.ai_generation_data?.final_video_url" class="mb-10">
                <div class="card bg-light-primary border-primary">
                  <div class="card-body">
                    <h5 class="card-title text-primary mb-4">Generated Video Preview</h5>
                    <div class="d-flex justify-content-center">
                      <video
                        controls
                        class="rounded"
                        style="max-width: 400px; max-height: 600px"
                        :src="generatedVideo.ai_generation_data.final_video_url"
                      >
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Generation Details -->
              <div v-if="generatedVideo?.ai_generation_data" class="card mb-8">
                <div class="card-body">
                  <h5 class="card-title mb-4">Generation Details</h5>
                  <div class="row g-3 text-start">
                    <div class="col-md-6">
                      <strong>Processing Time:</strong>
                      <span class="ms-2">{{
                        formatProcessingTime(generatedVideo.ai_generation_data.generation_time)
                      }}</span>
                    </div>
                    <div class="col-md-6">
                      <strong>Video Theme:</strong>
                      <span class="ms-2">{{
                        generatedVideo.ai_generation_data.scene_beats?.overall_theme ||
                        'AI Generated'
                      }}</span>
                    </div>
                    <div class="col-md-6">
                      <strong>Total Scenes:</strong>
                      <span class="ms-2">{{
                        generatedVideo.ai_generation_data.vertex_ai_tasks?.length || 1
                      }}</span>
                    </div>
                    <div class="col-md-6">
                      <strong>Completed:</strong>
                      <span class="ms-2">{{
                        formatDate(generatedVideo.ai_generation_data.completed_at)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="d-flex flex-center flex-wrap">
                <button class="btn btn-lg btn-primary me-4" @click="downloadVideo">
                  <i class="fas fa-download me-2"></i>
                  Download Video
                </button>
                <button class="btn btn-lg btn-light-primary me-4" @click="shareVideo">
                  <i class="fas fa-share me-2"></i>
                  Share Video
                </button>
                <button class="btn btn-lg btn-light-success" @click="createAnother">
                  <i class="fas fa-magic me-2"></i>
                  Create Another
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVideosStore } from '@/stores/videos'
import AIVideoService from '@/core/services/AIVideoService'
import type {
  AIVideoGenerationRequest,
  ProcessingStep,
  AIVideoStatus,
} from '@/core/services/AIVideoService'
import type { VideoMetadata } from '@/stores/videos'

// Store
const videosStore = useVideosStore()

// Component state
const currentStep = ref(1)
const selectedVideo = ref<VideoMetadata | null>(null)
const aiConfig = ref<AIVideoGenerationRequest>({
  videoId: '',
  prompt: '',
  targetDuration: 30,
  style: 'realistic',
})

const processingStatus = ref<AIVideoStatus | null>(null)
const generatedVideo = ref<VideoMetadata | null>(null)
const pollingInterval = ref<NodeJS.Timeout | null>(null)

// Computed properties
const userVideos = computed(() => videosStore.userVideos.filter((video) => !video.ai_project_type))

const processingSteps = computed(
  () => processingStatus.value?.video.ai_generation_data?.processing_steps || [],
)

const processingProgress = computed(() => AIVideoService.calculateProgress(processingSteps.value))

const currentProcessingMessage = computed(() =>
  AIVideoService.getProcessingMessage(processingSteps.value),
)

// Methods
const selectVideo = (video: VideoMetadata) => {
  selectedVideo.value = video
}

const nextStep = () => {
  currentStep.value++
}

const previousStep = () => {
  currentStep.value--
}

const startAIGeneration = async () => {
  if (!selectedVideo.value) return

  try {
    currentStep.value = 3

    const request: AIVideoGenerationRequest = {
      videoId: selectedVideo.value.video_id,
      prompt: aiConfig.value.prompt,
      targetDuration: aiConfig.value.targetDuration,
      style: aiConfig.value.style,
    }

    await AIVideoService.generateAIVideo(request)

    // Start polling for status
    startPolling()
  } catch (error) {
    console.error('Error starting AI generation:', error)
    alert('Failed to start AI video generation. Please try again.')
    currentStep.value = 2
  }
}

const startPolling = () => {
  if (!selectedVideo.value) return

  pollingInterval.value = setInterval(async () => {
    try {
      const status = await AIVideoService.getAIVideoStatus(selectedVideo.value!.video_id)
      processingStatus.value = status

      if (status.video.ai_generation_status === 'completed') {
        stopPolling()
        generatedVideo.value = status.video as VideoMetadata
        currentStep.value = 4
      } else if (status.video.ai_generation_status === 'failed') {
        stopPolling()
        alert('AI video generation failed. Please try again.')
        currentStep.value = 2
      }
    } catch (error) {
      console.error('Error polling status:', error)
    }
  }, 3000) // Poll every 3 seconds
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

const getStepDisplayName = (step: string): string => {
  return AIVideoService.getStepDisplayName(step)
}

const getEstimatedTime = (): string => {
  return AIVideoService.getEstimatedProcessingTime(aiConfig.value.targetDuration || 30)
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const formatDuration = (duration?: number): string => {
  if (!duration) return 'N/A'
  const minutes = Math.floor(duration / 60)
  const seconds = Math.floor(duration % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const formatProcessingTime = (timeMs?: number): string => {
  if (!timeMs) return 'N/A'
  const seconds = Math.floor(timeMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

const downloadVideo = () => {
  if (generatedVideo.value?.ai_generation_data?.final_video_url) {
    // Create a temporary link to download the video
    const link = document.createElement('a')
    link.href = generatedVideo.value.ai_generation_data.final_video_url
    link.download = `ai-video-${generatedVideo.value.video_id}.mp4`
    link.click()
  }
}

const shareVideo = async () => {
  if (!generatedVideo.value?.ai_generation_data?.final_video_url) return

  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Check out my AI-generated video!',
        text: 'I created this amazing video using AI. Take a look!',
        url: generatedVideo.value.ai_generation_data.final_video_url,
      })
    } catch (error) {
      console.error('Error sharing:', error)
    }
  } else {
    // Fallback: copy URL to clipboard
    try {
      await navigator.clipboard.writeText(generatedVideo.value.ai_generation_data.final_video_url)
      alert('Video URL copied to clipboard!')
    } catch (error) {
      console.error('Error copying to clipboard:', error)
    }
  }
}

const createAnother = () => {
  // Reset the component state
  currentStep.value = 1
  selectedVideo.value = null
  aiConfig.value = {
    videoId: '',
    prompt: '',
    targetDuration: 30,
    style: 'realistic',
  }
  processingStatus.value = null
  generatedVideo.value = null
  stopPolling()
}

// Lifecycle
onMounted(async () => {
  await videosStore.loadUserVideos()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.stepper-item.current .stepper-wrapper .stepper-icon {
  background-color: var(--bs-primary);
}

.stepper-item.current .stepper-wrapper .stepper-icon .stepper-number {
  color: white;
}

.stepper-item.completed .stepper-wrapper .stepper-icon {
  background-color: var(--bs-success);
}

.stepper-item.completed .stepper-wrapper .stepper-icon .stepper-check {
  color: white;
  display: block;
}

.stepper-item.completed .stepper-wrapper .stepper-icon .stepper-number {
  display: none;
}

.card.border-primary {
  box-shadow: 0 0 20px rgba(var(--bs-primary-rgb), 0.2);
}

.cursor-pointer {
  cursor: pointer;
  transition: all 0.3s ease;
}

.cursor-pointer:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
</style>
