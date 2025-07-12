<template>
  <!--begin::Page title-->
  <div
    v-if="pageTitleDisplay && !shouldHideOnMobile"
    :class="`page-title d-flex flex-${pageTitleDirection} justify-content-center flex-wrap me-3`"
  >
    <template v-if="pageTitle">
      <!--begin::Title-->
      <h1
        class="page-heading d-flex text-gray-900 fw-bold fs-3 flex-column justify-content-center my-0"
      >
        {{ pageTitle }}
      </h1>
      <!--end::Title-->

      <span
        v-if="pageTitleDirection === 'row' && pageTitleBreadcrumbDisplay"
        class="h-20px border-gray-200 border-start mx-3"
      ></span>

      <!--begin::Breadcrumb-->
      <ul
        v-if="breadcrumbs && pageTitleBreadcrumbDisplay"
        class="breadcrumb breadcrumb-separatorless fw-semibold fs-7 my-0 pt-1"
      >
        <!--begin::Item-->
        <li class="breadcrumb-item text-muted">
          <router-link to="/" class="text-muted text-hover-primary">Home</router-link>
        </li>
        <!--end::Item-->
        <template v-for="(item, i) in breadcrumbs" :key="i">
          <!--begin::Item-->
          <li class="breadcrumb-item">
            <span class="bullet bg-gray-500 w-5px h-2px"></span>
          </li>
          <!--end::Item-->
          <!--begin::Item-->
          <li class="breadcrumb-item text-muted">{{ item }}</li>
          <!--end::Item-->
        </template>
      </ul>
      <!--end::Breadcrumb-->
    </template>
  </div>
  <div v-else class="align-items-stretch"></div>
  <!--end::Page title-->
</template>

<script lang="ts">
import { computed, defineComponent, ref, onMounted, onUnmounted } from 'vue'
import {
  pageTitleBreadcrumbDisplay,
  pageTitleDirection,
  pageTitleDisplay,
} from '@/layouts/default-layout/config/helper'
import { useRoute } from 'vue-router'

export default defineComponent({
  name: 'layout-page-title',
  components: {},
  setup() {
    const route = useRoute()
    const windowWidth = ref(window.innerWidth)

    const pageTitle = computed(() => {
      return route.meta.pageTitle
    })

    const breadcrumbs = computed(() => {
      return route.meta.breadcrumbs
    })

    // Update window width on resize
    const handleResize = () => {
      windowWidth.value = window.innerWidth
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    // Hide PageTitle on mobile for text overlay editor
    const shouldHideOnMobile = computed(() => {
      const isMobile = windowWidth.value <= 768
      const isTextOverlayEditor = route.name === 'text-overlay-editor'
      return isMobile && isTextOverlayEditor
    })

    return {
      pageTitle,
      breadcrumbs,
      pageTitleDisplay,
      pageTitleBreadcrumbDisplay,
      pageTitleDirection,
      shouldHideOnMobile,
    }
  },
})
</script>
