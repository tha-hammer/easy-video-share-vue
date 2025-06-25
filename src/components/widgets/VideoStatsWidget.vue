<template>
  <!--begin::Video Statistics Widget-->
  <a href="#" :class="[widgetClasses, `bg-${color}`]" class="card hoverable">
    <!--begin::Body-->
    <div class="card-body">
      <KTIcon :icon-name="iconName" :icon-class="`text-${iconColor} fs-3x mx-n1`" />

      <div :class="`text-inverse-${color}`" class="fw-bold fs-2 mb-2 mt-5">
        {{ title }}
      </div>

      <div :class="`text-inverse-${color}`" class="fw-semibold fs-7">
        {{ description }}
      </div>
    </div>
    <!--end::Body-->
  </a>
  <!--end::Video Statistics Widget-->
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'video-stats-widget',
  props: {
    widgetClasses: String,
    color: String,
    iconColor: String,
    iconName: String,
    title: String,
    description: String,
  },
})
</script>
