<template>
  <div class="card">
    <!-- Header with Status -->
    <div class="card-header">
      <div class="card-title">
        <h3 class="fw-bolder">
          <i class="fas fa-magic text-primary me-2"></i>
          AI Shorts Generator
        </h3>
        <p class="text-muted mb-0">
          Transform your audio into engaging short-form videos for Instagram Reels & YouTube Shorts
        </p>
      </div>
      <div class="card-toolbar" v-if="currentStep > 1">
        <div class="badge badge-lg" :class="getStatusBadgeClass()">
          {{ getStatusText() }}
        </div>
      </div>
    </div>

    <div class="card-body">
      <!-- Step 1: Audio Upload -->
      <div v-if="currentStep === 1" class="upload-section">
        <div class="text-center mb-10">
          <h2 class="fw-bolder text-dark">Upload Audio for AI Shorts</h2>
          <p class="text-muted fs-4">
            Upload audio that will be transformed into a 30-60 second vertical video for social
            media
          </p>
        </div>

        <!-- Audio Upload Area -->
        <div class="row justify-content-center mb-10">
          <div class="col-md-8 col-lg-6">
            <div class="card border-dashed border-2 border-primary bg-light-primary">
              <div class="card-body text-center py-10">
                <div v-if="!audioUploading && !selectedAudio" class="upload-prompt">
                  <div class="mb-6">
                    <KTIcon icon-name="cloud-upload" icon-class="fs-5tx text-primary" />
                  </div>
                  <h4 class="fw-bold text-primary mb-4">Upload Audio File</h4>
                  <p class="text-muted mb-6">
                    Drag and drop your audio file here, or click to browse<br />
                    <small
                      >Supported formats: {{ supportedFormats.join(', ') }} • Max size: 100MB</small
                    >
                  </p>

                  <!-- File Input -->
                  <input
                    ref="audioFileInput"
                    type="file"
                    accept="audio/*"
                    class="d-none"
                    @change="handleAudioFileSelect"
                  />

                  <button class="btn btn-primary btn-lg" @click="triggerFileSelect">
                    <KTIcon icon-name="folder-down" icon-class="fs-4 me-2" />
                    Choose Audio File
                  </button>
                </div>

                <!-- Upload Progress -->
                <div v-else-if="audioUploading" class="upload-progress">
                  <div class="mb-6">
                    <div
                      class="spinner-border text-primary"
                      role="status"
                      style="width: 4rem; height: 4rem"
                    >
                      <span class="visually-hidden">Uploading...</span>
                    </div>
                  </div>
                  <h5 class="fw-bold text-primary mb-2">Uploading Audio...</h5>
                  <p class="text-muted mb-4">{{ currentUploadFile?.name }}</p>

                  <div class="progress bg-white mb-4" style="height: 20px">
                    <div
                      class="progress-bar bg-primary progress-bar-striped progress-bar-animated"
                      :style="{ width: `${uploadProgress}%` }"
                    ></div>
                  </div>

                  <div class="d-flex justify-content-between text-muted fs-7">
                    <span
                      >{{ formatFileSize(uploadedBytes) }} / {{ formatFileSize(totalBytes) }}</span
                    >
                    <span>{{ uploadProgress }}%</span>
                  </div>
                </div>

                <!-- Upload Success -->
                <div v-else-if="selectedAudio" class="upload-success">
                  <div class="mb-6">
                    <KTIcon icon-name="check-circle" icon-class="fs-5tx text-success" />
                  </div>
                  <h5 class="fw-bold text-success mb-2">Audio Uploaded Successfully!</h5>
                  <div class="card bg-white border-0 shadow-sm">
                    <div class="card-body">
                      <div class="d-flex align-items-center">
                        <div class="symbol symbol-40px me-3">
                          <div class="symbol-label bg-light-success">
                            <i class="fas fa-music text-success"></i>
                          </div>
                        </div>
                        <div class="flex-grow-1 text-start">
                          <h6 class="fw-bold mb-1">{{ selectedAudio.title }}</h6>
                          <div class="d-flex gap-4 text-muted fs-7">
                            <span
                              ><i class="fas fa-file me-1"></i>{{ selectedAudio.filename }}</span
                            >
                            <span
                              ><i class="fas fa-hdd me-1"></i
                              >{{ formatFileSize(selectedAudio.file_size || 0) }}</span
                            >
                            <span v-if="selectedAudio.duration"
                              ><i class="fas fa-clock me-1"></i
                              >{{ formatDuration(selectedAudio.duration) }}</span
                            >
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6">
                    <button class="btn btn-light-primary me-3" @click="resetUpload">
                      <KTIcon icon-name="arrow-clockwise" icon-class="fs-4 me-2" />
                      Upload Different File
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Existing Audio Files -->
        <div v-if="userAudioFiles.length > 0 && !audioUploading">
          <div class="separator my-8"></div>

          <div class="text-center mb-6">
            <h5 class="fw-bold text-gray-800">Or choose from your existing audio files</h5>
          </div>

          <div class="row g-4">
            <div class="col-md-6 col-lg-4" v-for="audio in userAudioFiles" :key="audio.audio_id">
              <div
                class="card cursor-pointer border-2 h-100 existing-audio-card"
                :class="{
                  'border-primary bg-light-primary': selectedAudio?.audio_id === audio.audio_id,
                }"
                @click="selectExistingAudio(audio)"
              >
                <div class="card-body">
                  <div class="d-flex align-items-center mb-3">
                    <div class="symbol symbol-40px me-3">
                      <div class="symbol-label bg-light-info">
                        <i class="fas fa-music text-info"></i>
                      </div>
                    </div>
                    <div class="flex-grow-1">
                      <h6 class="fw-bold mb-1">{{ audio.title }}</h6>
                      <p class="text-muted mb-0 fs-7">{{ audio.filename }}</p>
                    </div>
                    <div v-if="selectedAudio?.audio_id === audio.audio_id" class="ms-2">
                      <i class="fas fa-check-circle text-primary fs-3"></i>
                    </div>
                  </div>

                  <div class="d-flex justify-content-between text-muted fs-7">
                    <span>{{ formatDate(audio.upload_date) }}</span>
                    <span v-if="audio.duration">{{ formatDuration(audio.duration) }}</span>
                    <span>{{ formatFileSize(audio.file_size || 0) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Continue Button -->
        <div class="text-center mt-10" v-if="selectedAudio">
          <button class="btn btn-lg btn-primary" @click="nextStep">
            <KTIcon icon-name="arrow-right" icon-class="fs-4 me-2" />
            Continue with Selected Audio
          </button>
        </div>
      </div>

      <!-- Step 2: AI Configuration -->
      <div v-if="currentStep === 2" class="config-section">
        <div class="text-center mb-10">
          <h2 class="fw-bolder text-dark">Configure Your AI Video</h2>
          <p class="text-muted fs-4">
            Customize the style and parameters for your AI-generated short video
          </p>
        </div>

        <!-- Selected Audio Info -->
        <div v-if="selectedAudio" class="card bg-light-info border-info mb-8">
          <div class="card-body">
            <div class="d-flex align-items-center">
              <div class="symbol symbol-50px me-4">
                <div class="symbol-label bg-info">
                  <i class="fas fa-music text-white"></i>
                </div>
              </div>
              <div>
                <h5 class="fw-bold text-info mb-1">Selected Audio</h5>
                <p class="mb-0">{{ selectedAudio.title }}</p>
                <small class="text-muted">{{ selectedAudio.filename }}</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Configuration Form -->
        <div class="row">
          <div class="col-md-8 mx-auto">
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

            <div class="row g-6">
              <div class="col-md-6">
                <label class="form-label fs-6 fw-bolder text-dark">Target Duration</label>
                <select
                  class="form-select form-select-lg form-select-solid"
                  v-model="aiConfig.targetDuration"
                >
                  <option
                    v-for="duration in supportedDurations"
                    :key="duration.value"
                    :value="duration.value"
                  >
                    {{ duration.label }}
                  </option>
                </select>
                <div class="form-text">Estimated processing time: {{ estimatedTime }}</div>
              </div>

              <div class="col-md-6">
                <label class="form-label fs-6 fw-bolder text-dark">Visual Style</label>
                <select
                  class="form-select form-select-lg form-select-solid"
                  v-model="aiConfig.style"
                >
                  <option v-for="style in videoStyles" :key="style.value" :value="style.value">
                    {{ style.label }} - {{ style.description }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Navigation -->
            <div class="d-flex justify-content-between pt-15">
              <button class="btn btn-lg btn-light-primary" @click="previousStep">
                <KTIcon icon-name="arrow-left" icon-class="fs-4 me-2" />
                Previous
              </button>
              <button
                class="btn btn-lg btn-primary"
                :disabled="!aiConfig.prompt.trim()"
                @click="startAIGeneration"
              >
                <KTIcon icon-name="magic" icon-class="fs-4 me-2" />
                Generate AI Video
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Processing Animation with Real-time Updates -->
      <div v-if="currentStep === 3" class="processing-section">
        <div class="text-center mb-10">
          <h2 class="fw-bolder text-dark">AI Processing Your Audio</h2>
          <p class="text-muted fs-4">Creating your short-form video script and scene plan...</p>
        </div>

        <!-- Processing Animation -->
        <div class="text-center mb-10">
          <div class="processing-animation">
            <div class="ai-brain-animation">
              <div class="pulse-ring"></div>
              <div class="pulse-ring delay-1"></div>
              <div class="pulse-ring delay-2"></div>
              <KTIcon icon-name="abstract-26" icon-class="fs-5tx text-primary" />
            </div>
          </div>
        </div>

        <!-- Progress Steps -->
        <div class="row g-6 mb-10">
          <div class="col-md-3" v-for="step in processingSteps" :key="step.step">
            <div class="card h-100" :class="getStepCardClass(step)">
              <div class="card-body text-center">
                <div class="mb-4">
                  <div class="symbol symbol-50px mx-auto">
                    <div class="symbol-label" :class="getStepIconClass(step)">
                      <i class="fas" :class="getStepIcon(step)"></i>
                    </div>
                  </div>
                </div>
                <h5 class="fw-bold">{{ getStepDisplayName(step.step) }}</h5>
                <p class="text-muted fs-7 mb-0">{{ getStepDescription(step.step) }}</p>
                <div class="mt-3">
                  <span class="badge" :class="getStepStatusBadge(step)">
                    {{ step.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Overall Progress -->
        <div class="card bg-light-primary border-primary">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h5 class="fw-bold text-primary mb-0">Overall Progress</h5>
              <span class="fw-bold text-primary">{{ processingProgress }}%</span>
            </div>
            <div class="progress bg-white" style="height: 20px">
              <div
                class="progress-bar bg-primary progress-bar-striped progress-bar-animated"
                :style="{ width: `${processingProgress}%` }"
              ></div>
            </div>
            <div class="mt-4 text-center">
              <p class="fw-bold text-primary mb-1">{{ currentProcessingMessage }}</p>
              <p class="text-muted fs-7 mb-0">Estimated time remaining: {{ estimatedTime }}</p>
            </div>
          </div>
        </div>

        <!-- Debug Panel (Development Only) -->
        <div v-if="isDevelopment" class="card bg-light-warning border-warning mt-6">
          <div class="card-header">
            <h6 class="card-title mb-0">Debug Information</h6>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <p class="mb-1"><strong>Current Step:</strong> {{ currentStep }}</p>
                <p class="mb-1"><strong>Polling Active:</strong> {{ pollingActive }}</p>
                <p class="mb-1"><strong>Fallback Progress:</strong> {{ fallbackProgress }}%</p>
                <p class="mb-1">
                  <strong>API Progress:</strong>
                  {{ AIVideoService.calculateProgress(processingSteps) }}%
                </p>
              </div>
              <div class="col-md-6">
                <p class="mb-1">
                  <strong>Processing Status:</strong>
                  {{ processingStatus?.ai_generation_status || 'none' }}
                </p>
                <p class="mb-1"><strong>Processing Steps:</strong> {{ processingSteps.length }}</p>
                <p class="mb-1">
                  <strong>Last Successful Poll:</strong>
                  {{
                    lastSuccessfulPoll ? new Date(lastSuccessfulPoll).toLocaleTimeString() : 'never'
                  }}
                </p>
                <p class="mb-1">
                  <strong>Selected Audio:</strong> {{ selectedAudio?.audio_id || 'none' }}
                </p>
              </div>
            </div>
            <div class="mt-3">
              <button
                class="btn btn-sm btn-warning me-2"
                @click="manualRefresh"
                :disabled="!processingStatus?.video_id"
              >
                <KTIcon icon-name="arrow-clockwise" icon-class="fs-4 me-1" />
                Manual Refresh
              </button>
              <button class="btn btn-sm btn-info" @click="stopPolling" :disabled="!pollingActive">
                <KTIcon icon-name="stop" icon-class="fs-4 me-1" />
                Stop Polling
              </button>
              <button class="btn btn-sm btn-danger ms-2" @click="resetComponent">
                <KTIcon icon-name="cross" icon-class="fs-4 me-1" />
                Reset Component
              </button>
              <button class="btn btn-sm btn-success ms-2" @click="testEndpoints">
                <KTIcon icon-name="abstract-26" icon-class="fs-4 me-1" />
                Test Endpoints
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Scene Plan Display -->
      <div v-if="currentStep === 4" class="scene-plan-section">
        <div class="text-center mb-10">
          <h2 class="fw-bolder text-dark">AI-Generated Scene Plan</h2>
          <p class="text-muted fs-4">Review the intelligent scene breakdown for your short video</p>
        </div>

        <!-- Scene Plan Overview -->
        <div v-if="scenePlan" class="card bg-light-info border-info mb-8">
          <div class="card-body">
            <div class="row align-items-center">
              <div class="col-md-8">
                <h4 class="fw-bold text-info mb-2">{{ scenePlan.overall_theme }}</h4>
                <p class="text-muted mb-0">
                  {{ scenePlan.scenes?.length || 0 }} scenes • {{ scenePlan.total_duration }}s
                  duration
                </p>
              </div>
              <div class="col-md-4 text-end">
                <div class="badge badge-lg badge-light-info">
                  <KTIcon icon-name="abstract-26" icon-class="fs-4 me-1" />
                  AI Generated
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Scene Breakdown -->
        <div v-if="scenePlan?.scenes" class="row g-6 mb-10">
          <div class="col-md-6" v-for="scene in scenePlan.scenes" :key="scene.sequence">
            <div class="card h-100 scene-card">
              <div class="card-header">
                <div class="card-title">
                  <h5 class="fw-bold mb-0">
                    Scene {{ scene.sequence }}
                    <span class="badge badge-sm badge-light-primary ms-2">
                      {{ scene.duration }}s
                    </span>
                  </h5>
                </div>
              </div>
              <div class="card-body">
                <div class="mb-4">
                  <h6 class="fw-bold text-gray-800 mb-2">Audio Text:</h6>
                  <p class="text-muted fs-7 fst-italic mb-0">"{{ scene.audio_text }}"</p>
                </div>

                <div class="mb-4">
                  <h6 class="fw-bold text-gray-800 mb-2">Visual Description:</h6>
                  <p class="text-gray-700 fs-7 mb-0">{{ scene.scene_description }}</p>
                </div>

                <div class="mb-4">
                  <h6 class="fw-bold text-gray-800 mb-2">AI Prompt:</h6>
                  <p class="text-muted fs-8 mb-0">{{ scene.vertex_ai_prompt }}</p>
                </div>

                <div class="d-flex justify-content-between align-items-center">
                  <span class="badge badge-light-success">{{ scene.visual_style }}</span>
                  <small class="text-muted">{{ scene.start_time }}s - {{ scene.end_time }}s</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="text-center">
          <button class="btn btn-light-primary me-4" @click="regenerateScenePlan">
            <KTIcon icon-name="arrow-clockwise" icon-class="fs-4 me-2" />
            Regenerate Plan
          </button>
          <button class="btn btn-primary" @click="approveScenePlan">
            <KTIcon icon-name="check" icon-class="fs-4 me-2" />
            Approve & Generate Video
          </button>
        </div>
      </div>

      <!-- Step 5: Video Generation Grid -->
      <div v-if="currentStep === 5" class="video-generation-section">
        <div class="text-center mb-10">
          <h2 class="fw-bolder text-dark">Generating Video Scenes</h2>
          <p class="text-muted fs-4">AI is creating each scene based on your approved plan</p>
        </div>

        <!-- Scene Generation Grid -->
        <div v-if="generatedScenes" class="row g-6 mb-10">
          <div class="col-md-6 col-lg-4" v-for="scene in generatedScenes" :key="scene.task_id">
            <div class="card h-100 scene-generation-card">
              <div class="card-header">
                <div class="card-title">
                  <h6 class="fw-bold mb-0">Scene {{ scene.sequence }}</h6>
                  <span class="badge badge-sm" :class="getSceneStatusBadge(scene)">
                    {{ scene.status }}
                  </span>
                </div>
              </div>
              <div class="card-body">
                <!-- Video Preview or Placeholder -->
                <div class="scene-preview mb-4">
                  <div v-if="scene.status === 'completed' && scene.video_url" class="video-preview">
                    <video
                      :src="scene.video_url"
                      class="w-100 rounded"
                      style="aspect-ratio: 9/16; max-height: 200px"
                      controls
                      muted
                    ></video>
                  </div>
                  <div v-else-if="scene.status === 'processing'" class="text-center py-10">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted mt-3 mb-0">Generating...</p>
                  </div>
                  <div v-else-if="scene.status === 'failed'" class="text-center py-10">
                    <KTIcon icon-name="cross-circle" icon-class="fs-3x text-danger" />
                    <p class="text-danger mt-3 mb-0">Generation Failed</p>
                  </div>
                  <div v-else class="text-center py-10">
                    <KTIcon icon-name="time" icon-class="fs-3x text-muted" />
                    <p class="text-muted mt-3 mb-0">Waiting...</p>
                  </div>
                </div>

                <!-- Scene Details -->
                <div class="scene-details">
                  <p class="fw-bold text-gray-800 mb-1">
                    {{ scene.scene_description || scene.prompt }}
                  </p>
                  <p class="text-muted fs-7 mb-2">Duration: {{ scene.duration || 'N/A' }}s</p>
                  <p class="text-muted fs-8 mb-0">
                    {{ scene.created_at ? formatDate(scene.created_at) : '' }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Overall Generation Progress -->
        <div class="card bg-light-primary border-primary">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h5 class="fw-bold text-primary mb-0">Video Generation Progress</h5>
              <span class="fw-bold text-primary">{{ getGenerationProgress() }}%</span>
            </div>
            <div class="progress bg-white" style="height: 15px">
              <div
                class="progress-bar bg-primary progress-bar-striped progress-bar-animated"
                :style="{ width: `${getGenerationProgress()}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 6: Final Video Display -->
      <div v-if="currentStep === 6" class="final-video-section">
        <div class="text-center mb-10">
          <div class="mb-6">
            <KTIcon icon-name="check-circle" icon-class="fs-5tx text-success" />
          </div>
          <h2 class="fw-bolder text-dark">Your AI Short is Ready!</h2>
          <p class="text-muted fs-4">Perfect for Instagram Reels, YouTube Shorts, and TikTok</p>
        </div>

        <!-- Final Video Display -->
        <div class="row justify-content-center">
          <div class="col-md-6 col-lg-4">
            <div class="card">
              <div class="card-body text-center">
                <div v-if="finalVideoUrl" class="final-video-preview mb-6">
                  <video
                    :src="finalVideoUrl"
                    class="w-100 rounded shadow"
                    style="aspect-ratio: 9/16; max-height: 500px"
                    controls
                    autoplay
                    muted
                    loop
                  ></video>
                </div>

                <!-- Video Details -->
                <div class="video-info mb-6">
                  <h4 class="fw-bold text-gray-800 mb-2">{{ selectedAudio?.title }}</h4>
                  <div class="d-flex justify-content-center gap-4 text-muted fs-7">
                    <span><i class="fas fa-clock me-1"></i>{{ getFinalDuration() }}s</span>
                    <span><i class="fas fa-mobile-alt me-1"></i>9:16 Vertical</span>
                    <span><i class="fas fa-eye me-1"></i>Social Ready</span>
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="d-flex flex-wrap justify-content-center gap-3">
                  <button class="btn btn-primary" @click="downloadVideo">
                    <KTIcon icon-name="cloud-download" icon-class="fs-4 me-2" />
                    Download
                  </button>
                  <button class="btn btn-light-primary" @click="shareVideo">
                    <KTIcon icon-name="share" icon-class="fs-4 me-2" />
                    Share
                  </button>
                  <button class="btn btn-light-success" @click="createAnother">
                    <KTIcon icon-name="plus" icon-class="fs-4 me-2" />
                    Create Another
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Processing Summary -->
        <div v-if="generatedVideo?.ai_generation_data" class="row mt-10">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">Generation Summary</h5>
              </div>
              <div class="card-body">
                <div class="row g-6">
                  <div class="col-md-3">
                    <div class="d-flex align-items-center">
                      <KTIcon icon-name="time" icon-class="fs-2 text-primary me-3" />
                      <div>
                        <p class="fw-bold mb-0">Processing Time</p>
                        <p class="text-muted fs-7 mb-0">
                          {{
                            formatProcessingTime(generatedVideo.ai_generation_data.generation_time)
                          }}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="d-flex align-items-center">
                      <KTIcon icon-name="abstract-26" icon-class="fs-2 text-info me-3" />
                      <div>
                        <p class="fw-bold mb-0">AI Scenes</p>
                        <p class="text-muted fs-7 mb-0">
                          {{ generatedVideo.ai_generation_data.vertex_ai_tasks?.length || 1 }}
                          generated
                        </p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="d-flex align-items-center">
                      <KTIcon icon-name="subtitle" icon-class="fs-2 text-success me-3" />
                      <div>
                        <p class="fw-bold mb-0">Transcription</p>
                        <p class="text-muted fs-7 mb-0">
                          {{
                            (
                              generatedVideo.ai_generation_data.audio_transcription?.confidence *
                              100
                            )?.toFixed(1) || 'N/A'
                          }}% accuracy
                        </p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="d-flex align-items-center">
                      <KTIcon icon-name="check-circle" icon-class="fs-2 text-success me-3" />
                      <div>
                        <p class="fw-bold mb-0">Completed</p>
                        <p class="text-muted fs-7 mb-0">
                          {{ formatDate(generatedVideo.ai_generation_data.completed_at) }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
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
import { useAudioStore } from '@/stores/audio'
import AudioService from '@/core/services/AudioService'
import AIVideoService from '@/core/services/AIVideoService'
import { API_CONFIG } from '@/core/config/config'
import type { AIVideoGenerationRequest, VideoMetadata } from '@/core/services/AIVideoService'
import type { AudioMetadata } from '@/core/services/AudioService'
import KTIcon from '@/core/helpers/kt-icon/KTIcon.vue'

// Stores
const audioStore = useAudioStore()

// Component state
const currentStep = ref(1)
const selectedAudio = ref<AudioMetadata | null>(null)
const audioUploading = ref(false)
const currentUploadFile = ref<File | null>(null)
const uploadProgress = ref(0)
const uploadedBytes = ref(0)
const totalBytes = ref(0)
const audioFileInput = ref<HTMLInputElement | null>(null)

const aiConfig = ref({
  prompt:
    'Create an engaging vertical video optimized for social media with dynamic visuals and modern aesthetics',
  targetDuration: 30,
  style: 'cinematic',
})

const processingStatus = ref<VideoMetadata | null>(null)
const generatedVideo = ref<VideoMetadata | null>(null)
const pollingInterval = ref<NodeJS.Timeout | null>(null)
const pollingActive = ref(false)
const fallbackProgress = ref(0)
const lastSuccessfulPoll = ref<Date | null>(null)

// Computed properties
const userAudioFiles = computed(() => audioStore.userAudioFiles)

const supportedFormats = computed(() => AudioService.getSupportedFormats())

const processingSteps = computed(
  () => processingStatus.value?.ai_generation_data?.processing_steps || [],
)

const processingProgress = computed(() => {
  const apiProgress = AIVideoService.calculateProgress(processingSteps.value)
  // Use fallback progress if API progress is 0 and we're actively polling
  return pollingActive.value && apiProgress === 0 ? fallbackProgress.value : apiProgress
})

const currentProcessingMessage = computed(() => {
  const apiMessage = AIVideoService.getCurrentStepMessage(processingSteps.value)
  // Use fallback message if no API data and we're polling
  if (pollingActive.value && (!processingSteps.value || processingSteps.value.length === 0)) {
    const timeSinceLastPoll = lastSuccessfulPoll.value
      ? Math.floor((Date.now() - lastSuccessfulPoll.value.getTime()) / 1000)
      : 0

    if (timeSinceLastPoll > 30) {
      return 'Connecting to AI services...'
    } else {
      return 'Initializing AI processing...'
    }
  }
  return apiMessage
})

const scenePlan = computed(() => processingStatus.value?.ai_generation_data?.scene_beats || null)

const generatedScenes = computed(
  () => processingStatus.value?.ai_generation_data?.vertex_ai_tasks || [],
)

const finalVideoUrl = computed(
  () => generatedVideo.value?.ai_generation_data?.final_video_url || null,
)

const estimatedTime = computed(() =>
  AIVideoService.getEstimatedTime(processingSteps.value, aiConfig.value.targetDuration),
)

const videoStyles = computed(() => AIVideoService.getVideoStyles())

const supportedDurations = computed(() => AIVideoService.getSupportedDurations())

// Development mode check
const isDevelopment = computed(() => import.meta.env.DEV)

// Audio upload methods
const triggerFileSelect = () => {
  audioFileInput.value?.click()
}

const handleAudioFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  if (!AudioService.isValidAudioFile(file)) {
    alert('Invalid file type. Please select an audio file.')
    return
  }

  try {
    audioUploading.value = true
    currentUploadFile.value = file
    totalBytes.value = file.size
    uploadedBytes.value = 0
    uploadProgress.value = 0

    // Generate title from filename (remove extension)
    const title = file.name.replace(/\.[^/.]+$/, '')

    const uploadedAudio = await audioStore.uploadAudio({
      title,
      file,
      onProgress: (progress) => {
        uploadProgress.value = progress
        uploadedBytes.value = Math.round((file.size * progress) / 100)
      },
    })

    selectedAudio.value = uploadedAudio
  } catch (error) {
    console.error('Upload error:', error)
    alert('Failed to upload audio file. Please try again.')
  } finally {
    audioUploading.value = false
    currentUploadFile.value = null

    // Reset file input
    if (input) {
      input.value = ''
    }
  }
}

const selectExistingAudio = (audio: AudioMetadata) => {
  selectedAudio.value = audio
}

const resetUpload = () => {
  selectedAudio.value = null
  uploadProgress.value = 0
  uploadedBytes.value = 0
  totalBytes.value = 0
}

// Navigation methods
const nextStep = () => {
  if (currentStep.value === 1 && selectedAudio.value) {
    currentStep.value = 2
  } else {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const startAIGeneration = async () => {
  if (!selectedAudio.value) {
    alert('Please select an audio file first')
    return
  }

  // Validate request
  const request: AIVideoGenerationRequest = {
    audioId: selectedAudio.value.audio_id,
    prompt: aiConfig.value.prompt,
    targetDuration: aiConfig.value.targetDuration,
    style: aiConfig.value.style,
  }

  console.log('🚀 Starting AI generation with request:', request)

  const errors = AIVideoService.validateRequest(request)
  if (errors.length > 0) {
    console.error('❌ Validation errors:', errors)
    alert(`Please fix the following errors:\n- ${errors.join('\n- ')}`)
    return
  }

  try {
    console.log('🔄 Moving to processing step (step 3)')
    currentStep.value = 3
    pollingActive.value = true

    console.log('🌐 Calling AIVideoService.generateAIVideo...')
    const response = await AIVideoService.generateAIVideo(request)
    console.log('✅ AI generation started successfully:', response)

    // Start polling for completion
    console.log('🔄 Starting polling with video ID:', response.videoId)
    startPolling(response.videoId)
  } catch (error) {
    console.error('❌ Error starting AI generation:', error)
    console.error('❌ Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
    })
    pollingActive.value = false
    alert('Failed to start AI video generation. Please try again.')
    currentStep.value = 2
  }
}

const startPolling = (videoId: string) => {
  if (!pollingActive.value) return

  console.log('🔄 Starting polling for video ID:', videoId)
  console.log('🔄 Polling interval: 3000ms')
  console.log('🔄 Max wait time: 15 minutes')

  // Initialize fallback progress
  fallbackProgress.value = 5
  lastSuccessfulPoll.value = new Date()

  pollingInterval.value = setInterval(async () => {
    try {
      console.log('🔄 Polling status for video:', videoId)
      const status = await AIVideoService.getAIVideoStatus(videoId)
      console.log('✅ Polling response received:', status)

      // Update processing status and reset fallback
      processingStatus.value = status.video
      lastSuccessfulPoll.value = new Date()
      fallbackProgress.value = Math.min(fallbackProgress.value + 10, 90) // Increment fallback progress

      console.log('📊 Updated processing status:', {
        ai_generation_status: status.video.ai_generation_status,
        processing_steps: status.video.ai_generation_data?.processing_steps?.length || 0,
        current_step:
          status.video.ai_generation_data?.processing_steps?.find((s) => s.status === 'processing')
            ?.step || 'none',
        fallback_progress: fallbackProgress.value,
      })

      // Check for transcription and scene planning completion
      const steps = status.video.ai_generation_data?.processing_steps || []
      const transcriptionDone =
        steps.find((s) => s.step === 'transcription')?.status === 'completed'
      const scenePlanningDone =
        steps.find((s) => s.step === 'scene_planning')?.status === 'completed'
      const videoGenerationDone =
        steps.find((s) => s.step === 'video_generation')?.status === 'completed'

      console.log('📋 Step completion status:', {
        transcriptionDone,
        scenePlanningDone,
        videoGenerationDone,
        currentStep: currentStep.value,
      })

      if (transcriptionDone && scenePlanningDone && currentStep.value === 3) {
        console.log('🎬 Moving to scene plan step (step 4)')
        currentStep.value = 4 // Show scene plan
      }

      if (videoGenerationDone && currentStep.value < 5) {
        console.log('🎥 Moving to video generation step (step 5)')
        currentStep.value = 5 // Show video generation grid
      }

      if (status.video.ai_generation_status === 'completed') {
        console.log('✅ AI generation completed successfully')
        fallbackProgress.value = 100
        stopPolling()
        generatedVideo.value = status.video
        currentStep.value = 6
      } else if (status.video.ai_generation_status === 'failed') {
        console.error('❌ AI generation failed')
        stopPolling()
        const errorMessage =
          status.video.ai_generation_data?.error_message || 'AI video generation failed'
        alert(`AI video generation failed: ${errorMessage}`)
        currentStep.value = 2
      } else {
        console.log('⏳ AI generation still in progress...')
      }
    } catch (error) {
      console.error('❌ Error polling status:', error)
      console.error('❌ Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      })

      // Increment fallback progress even on errors to show activity
      fallbackProgress.value = Math.min(fallbackProgress.value + 5, 95)
      console.log('📊 Fallback progress updated to:', fallbackProgress.value)

      // Don't stop polling on network errors, but log them
      // Only stop if it's a persistent authentication error
      if (error instanceof Error && error.message.includes('authentication')) {
        console.error('❌ Authentication error detected, stopping polling')
        stopPolling()
        alert('Authentication error. Please refresh the page and try again.')
        currentStep.value = 2
      }
    }
  }, 3000)

  // Stop polling after 15 minutes
  setTimeout(() => {
    if (pollingActive.value) {
      console.log('⏰ Polling timeout reached (15 minutes)')
      stopPolling()
      alert('AI video generation timed out. Please try again.')
      currentStep.value = 2
    }
  }, 900000)
}

const stopPolling = () => {
  pollingActive.value = false
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

// Status and display methods
const getStatusBadgeClass = () => {
  if (!processingStatus.value) return 'badge-light-primary'

  switch (processingStatus.value.ai_generation_status) {
    case 'processing':
      return 'badge-light-warning'
    case 'completed':
      return 'badge-light-success'
    case 'failed':
      return 'badge-light-danger'
    default:
      return 'badge-light-primary'
  }
}

const getStatusText = () => {
  if (!processingStatus.value) return 'Ready'

  switch (processingStatus.value.ai_generation_status) {
    case 'processing':
      return 'Processing'
    case 'completed':
      return 'Complete'
    case 'failed':
      return 'Failed'
    default:
      return 'Ready'
  }
}

const getSceneStatusBadge = (scene: { status: string }) => {
  switch (scene.status) {
    case 'completed':
      return 'badge-light-success'
    case 'processing':
      return 'badge-light-warning'
    case 'failed':
      return 'badge-light-danger'
    default:
      return 'badge-light-secondary'
  }
}

const getGenerationProgress = () => {
  const scenes = generatedScenes.value
  if (!scenes.length) return 0

  const completedScenes = scenes.filter((s) => s.status === 'completed').length
  return Math.round((completedScenes / scenes.length) * 100)
}

const regenerateScenePlan = async () => {
  // This would trigger a new scene plan generation
  alert('Scene plan regeneration will be implemented in the full AI processing Lambda')
}

const approveScenePlan = () => {
  // Move to video generation step
  currentStep.value = 5
}

const getFinalDuration = () => {
  return scenePlan.value?.target_duration || aiConfig.value.targetDuration || 30
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const formatDuration = (duration?: number): string => {
  return AudioService.formatDuration(duration || 0)
}

const formatFileSize = (size: number): string => {
  return AudioService.formatFileSize(size)
}

const formatProcessingTime = (timeMs?: number): string => {
  if (!timeMs) return 'N/A'
  const seconds = Math.floor(timeMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

const downloadVideo = () => {
  if (finalVideoUrl.value) {
    const link = document.createElement('a')
    link.href = finalVideoUrl.value
    link.download = `ai-short-${selectedAudio.value?.audio_id}.mp4`
    link.click()
  }
}

const shareVideo = async () => {
  if (!finalVideoUrl.value) return

  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Check out my AI-generated short video!',
        text: 'Created with AI - perfect for social media!',
        url: finalVideoUrl.value,
      })
    } catch (error) {
      console.error('Error sharing:', error)
    }
  } else {
    try {
      await navigator.clipboard.writeText(finalVideoUrl.value)
      alert('Video URL copied to clipboard!')
    } catch (error) {
      console.error('Error copying to clipboard:', error)
    }
  }
}

const createAnother = () => {
  currentStep.value = 1
  selectedAudio.value = null
  processingStatus.value = null
  generatedVideo.value = null
  resetUpload()
  stopPolling()
}

// Missing methods that are called in the template
const getStepCardClass = (step: { status: string }) => {
  switch (step.status) {
    case 'completed':
      return 'border-success bg-light-success'
    case 'processing':
      return 'border-warning bg-light-warning'
    case 'failed':
      return 'border-danger bg-light-danger'
    default:
      return 'border-light bg-light'
  }
}

const getStepIconClass = (step: { status: string }) => {
  switch (step.status) {
    case 'completed':
      return 'bg-success'
    case 'processing':
      return 'bg-warning'
    case 'failed':
      return 'bg-danger'
    default:
      return 'bg-light'
  }
}

const getStepIcon = (step: { step: string; status: string }) => {
  if (step.status === 'failed') return 'fa-times'
  if (step.status === 'completed') return 'fa-check'
  if (step.status === 'processing') return 'fa-spinner fa-spin'

  // Default icons based on step type
  switch (step.step) {
    case 'transcription':
      return 'fa-microphone'
    case 'scene_planning':
      return 'fa-lightbulb'
    case 'video_generation':
      return 'fa-video'
    default:
      return 'fa-cog'
  }
}

const getStepDisplayName = (step: string) => {
  switch (step) {
    case 'transcription':
      return 'Audio Transcription'
    case 'scene_planning':
      return 'Scene Planning'
    case 'video_generation':
      return 'Video Generation'
    default:
      return step.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  }
}

const getStepDescription = (step: string) => {
  switch (step) {
    case 'transcription':
      return 'Converting audio to text with high accuracy'
    case 'scene_planning':
      return 'Creating intelligent scene breakdown'
    case 'video_generation':
      return 'Generating video scenes with AI'
    default:
      return 'Processing step'
  }
}

const getStepStatusBadge = (step: { status: string }) => {
  switch (step.status) {
    case 'completed':
      return 'badge-light-success'
    case 'processing':
      return 'badge-light-warning'
    case 'failed':
      return 'badge-light-danger'
    default:
      return 'badge-light-secondary'
  }
}

// Lifecycle
onMounted(async () => {
  await audioStore.loadUserAudioFiles()
})

onUnmounted(() => {
  stopPolling()
})

// New methods
const manualRefresh = async () => {
  if (!processingStatus.value?.video_id) {
    alert('No video ID available for refresh')
    return
  }

  try {
    console.log('🔄 Manual refresh requested for video:', processingStatus.value.video_id)
    const status = await AIVideoService.getAIVideoStatus(processingStatus.value.video_id)
    console.log('✅ Manual refresh response:', status)

    processingStatus.value = status.video
    lastSuccessfulPoll.value = new Date()

    alert(
      `Manual refresh successful!\nStatus: ${status.video.ai_generation_status}\nSteps: ${status.video.ai_generation_data?.processing_steps?.length || 0}`,
    )
  } catch (error) {
    console.error('❌ Manual refresh failed:', error)
    alert(`Manual refresh failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

const resetComponent = () => {
  console.log('🔄 Resetting component state')

  // Stop polling
  stopPolling()

  // Reset all state
  currentStep.value = 1
  selectedAudio.value = null
  processingStatus.value = null
  generatedVideo.value = null
  fallbackProgress.value = 0
  lastSuccessfulPoll.value = null
  pollingActive.value = false

  // Reset upload state
  audioUploading.value = false
  currentUploadFile.value = null
  uploadProgress.value = 0
  uploadedBytes.value = 0
  totalBytes.value = 0

  // Reset AI config
  aiConfig.value = {
    prompt:
      'Create an engaging vertical video optimized for social media with dynamic visuals and modern aesthetics',
    targetDuration: 30,
    style: 'cinematic',
  }

  console.log('✅ Component reset complete')
  alert('Component has been reset to initial state')
}

const testEndpoints = async () => {
  console.log('🚀 Testing AI video API endpoints')

  try {
    // Test 1: Check if we can get auth headers
    console.log('🔑 Testing authentication...')
    const headers = await AIVideoService['getAuthHeaders']()
    console.log('✅ Auth headers obtained:', !!headers.Authorization)

    // Test 2: Test the base URL
    const baseUrl = `${API_CONFIG.baseUrl}/ai-video`
    console.log('🌐 Testing base URL:', baseUrl)

    // Test 3: Make a simple OPTIONS request to check CORS
    console.log('🔄 Testing CORS with OPTIONS request...')
    const optionsResponse = await fetch(baseUrl, {
      method: 'OPTIONS',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    console.log('✅ OPTIONS response status:', optionsResponse.status)

    // Test 4: Try to make a POST request with minimal data
    console.log('📤 Testing POST endpoint...')
    const testRequest = {
      audioId: 'test-audio-id',
      prompt: 'Test prompt',
      targetDuration: 30,
      style: 'cinematic',
    }

    const postResponse = await fetch(baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: headers.Authorization,
      },
      body: JSON.stringify(testRequest),
    })

    console.log('✅ POST response status:', postResponse.status)

    if (postResponse.ok) {
      const postData = await postResponse.json()
      console.log('✅ POST response data:', postData)
      alert(
        `✅ Endpoints are working!\n\nPOST Status: ${postResponse.status}\nResponse: ${JSON.stringify(postData, null, 2)}`,
      )
    } else {
      const errorText = await postResponse.text()
      console.log('❌ POST error response:', errorText)
      alert(`❌ POST endpoint failed!\n\nStatus: ${postResponse.status}\nError: ${errorText}`)
    }
  } catch (error) {
    console.error('❌ Endpoint test failed:', error)
    alert(
      `❌ Endpoint test failed!\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
    )
  }
}
</script>

<style scoped>
.audio-card,
.existing-audio-card {
  transition: all 0.3s ease;
}

.audio-card:hover,
.existing-audio-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.processing-animation {
  position: relative;
  display: inline-block;
}

.ai-brain-animation {
  position: relative;
  display: inline-block;
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border: 3px solid var(--bs-primary);
  border-radius: 50%;
  animation: pulse 2s infinite;
  opacity: 0.6;
}

.pulse-ring.delay-1 {
  animation-delay: 0.5s;
  width: 140px;
  height: 140px;
  opacity: 0.4;
}

.pulse-ring.delay-2 {
  animation-delay: 1s;
  width: 160px;
  height: 160px;
  opacity: 0.2;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0.8;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.4;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.3);
    opacity: 0;
  }
}

.scene-card {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.scene-card:hover {
  border-color: var(--bs-primary);
  transform: translateY(-2px);
}

.scene-generation-card {
  transition: all 0.3s ease;
}

.scene-generation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.video-preview video {
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.final-video-preview video {
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.scene-preview {
  background: #f8f9fa;
  border-radius: 8px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e4e6ea, transparent);
}

.upload-prompt,
.upload-progress,
.upload-success {
  transition: all 0.3s ease;
}

.border-dashed {
  border-style: dashed !important;
}
</style>
