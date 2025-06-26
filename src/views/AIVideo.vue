<template>
  <!--begin::Layout-->
  <div id="kt_app_content" class="app-content flex-column-fluid">
    <!--begin::Content container-->
    <div id="kt_app_content_container" class="app-container container-fluid">
      <!--begin::Card-->
      <div class="card">
        <!--begin::Card header-->
        <div class="card-header border-0 pt-6">
          <!--begin::Card title-->
          <div class="card-title">
            <div class="d-flex align-items-center position-relative my-1">
              <i class="ki-duotone ki-abstract-26 fs-1 position-absolute ms-6">
                <span class="path1"></span>
                <span class="path2"></span>
              </i>
              <div class="ms-15">
                <h1 class="fw-bold text-dark m-0">AI Shorts Generator</h1>
                <p class="text-muted fs-6 m-0">
                  Transform your audio into engaging short-form videos for social media
                </p>
              </div>
            </div>
          </div>
          <!--end::Card title-->

          <!--begin::Card toolbar-->
          <div class="card-toolbar">
            <!--begin::Toolbar-->
            <div class="d-flex justify-content-end" data-kt-user-table-toolbar="base">
              <div class="badge badge-lg badge-light-primary">
                <i class="fas fa-magic me-2"></i>
                AI-Powered
              </div>
            </div>
            <!--end::Toolbar-->
          </div>
          <!--end::Card toolbar-->
        </div>
        <!--end::Card header-->

        <!--begin::Card body-->
        <div class="card-body py-4">
          <!--begin::Notice-->
          <div
            class="notice d-flex bg-light-info rounded border-info border border-dashed p-6 mb-10"
          >
            <!--begin::Icon-->
            <i class="ki-duotone ki-information-5 fs-2tx text-info me-4">
              <span class="path1"></span>
              <span class="path2"></span>
              <span class="path3"></span>
            </i>
            <!--end::Icon-->

            <!--begin::Wrapper-->
            <div class="d-flex flex-stack flex-grow-1">
              <!--begin::Content-->
              <div class="fw-semibold">
                <h4 class="text-gray-900 fw-bold">Ready to Create AI Videos!</h4>
                <div class="fs-6 text-gray-700">
                  Your infrastructure is deployed and ready. Upload audio files and transform them
                  into vertical videos perfect for Instagram Reels, YouTube Shorts, and TikTok.

                  <div class="mt-3">
                    <div class="badge badge-light-success me-2">
                      <i class="fas fa-check me-1"></i>
                      Audio Upload API
                    </div>
                    <div class="badge badge-light-success me-2">
                      <i class="fas fa-check me-1"></i>
                      S3 Storage
                    </div>
                    <div class="badge badge-light-warning me-2">
                      <i class="fas fa-clock me-1"></i>
                      AI Processing (Next Phase)
                    </div>
                  </div>
                </div>
              </div>
              <!--end::Content-->
            </div>
            <!--end::Wrapper-->
          </div>
          <!--end::Notice-->

          <!--begin::AI Video Generator Component-->
          <AIVideoGenerator />
          <!--end::AI Video Generator Component-->
        </div>
        <!--end::Card body-->
      </div>
      <!--end::Card-->
    </div>
    <!--end::Content container-->
  </div>
  <!--end::Layout-->
</template>

<script setup lang="ts">
import AIVideoGenerator from '@/components/ai-video/AIVideoGenerator.vue'
</script>

<style scoped>
.notice {
  background: rgba(113, 166, 255, 0.1);
}

.badge-light-success {
  background-color: rgba(80, 205, 137, 0.1);
  color: #50cd89;
  border: 1px solid rgba(80, 205, 137, 0.25);
}

.badge-light-warning {
  background-color: rgba(255, 199, 0, 0.1);
  color: #ffc700;
  border: 1px solid rgba(255, 199, 0, 0.25);
}

.badge-light-primary {
  background-color: rgba(113, 166, 255, 0.1);
  color: #71a6ff;
  border: 1px solid rgba(113, 166, 255, 0.25);
}
</style>
