<template>
  <!--begin::Video Upload Widget-->
  <div :class="widgetClasses" class="card">
    <!--begin::Header-->
    <div class="card-header border-0 pt-5">
      <h3 class="card-title align-items-start flex-column">
        <span class="card-label fw-bold text-gray-900">Quick Upload</span>
        <span class="text-muted mt-1 fw-semibold fs-7">Upload a new video</span>
      </h3>
    </div>
    <!--end::Header-->

    <!--begin::Body-->
    <div class="card-body pt-2">
      <!--begin::Upload area-->
      <div class="text-center">
        <div class="symbol symbol-100px mb-5">
          <span class="symbol-label bg-light-primary">
            <KTIcon icon-name="cloud-upload" icon-class="fs-1 text-primary" />
          </span>
        </div>

        <h5 class="fw-bold mb-3">Upload Video</h5>
        <p class="text-muted mb-5">Drag and drop or click to select files</p>

        <router-link to="/upload" class="btn btn-primary">
          <KTIcon icon-name="plus" icon-class="fs-2" />
          Start Upload
        </router-link>
      </div>
      <!--end::Upload area-->
    </div>
    <!--end::Body-->
  </div>
  <!--end::Video Upload Widget-->
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'video-upload-widget',
  props: {
    widgetClasses: String,
  },
})
</script>
