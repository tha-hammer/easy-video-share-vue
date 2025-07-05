<template>
  <!--begin::Filters Card-->
  <div class="card mb-8">
    <div class="card-header">
      <h3 class="card-title">Filters & Sorting</h3>
    </div>
    <div class="card-body">
      <div class="row g-4">
        <!--begin::Search-->
        <div class="col-md-6">
          <label class="form-label">Search</label>
          <div class="input-group">
            <span class="input-group-text">
              <KTIcon icon-name="magnifier" icon-class="fs-4" />
            </span>
            <input
              v-model="localFilters.search"
              type="text"
              class="form-control"
              placeholder="Search segments..."
              @input="debouncedApplyFilters"
            />
          </div>
        </div>
        <!--end::Search-->

        <!--begin::Sort By-->
        <div class="col-md-3">
          <label class="form-label">Sort By</label>
          <select v-model="localFilters.sort_by" class="form-select" @change="applyFilters">
            <option value="date">Date</option>
            <option value="name">Name</option>
            <option value="size">File Size</option>
            <option value="duration">Duration</option>
            <option value="downloads">Downloads</option>
          </select>
        </div>
        <!--end::Sort By-->

        <!--begin::Sort Order-->
        <div class="col-md-3">
          <label class="form-label">Order</label>
          <select v-model="localFilters.order" class="form-select" @change="applyFilters">
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
        <!--end::Sort Order-->

        <!--begin::Duration Range-->
        <div class="col-md-6">
          <label class="form-label">Duration Range (seconds)</label>
          <div class="row g-2">
            <div class="col-6">
              <input
                v-model.number="localFilters.min_duration"
                type="number"
                class="form-control"
                placeholder="Min duration"
                min="0"
                step="0.1"
                @input="debouncedApplyFilters"
              />
            </div>
            <div class="col-6">
              <input
                v-model.number="localFilters.max_duration"
                type="number"
                class="form-control"
                placeholder="Max duration"
                min="0"
                step="0.1"
                @input="debouncedApplyFilters"
              />
            </div>
          </div>
        </div>
        <!--end::Duration Range-->

        <!--begin::Min Downloads-->
        <div class="col-md-3">
          <label class="form-label">Min Downloads</label>
          <input
            v-model.number="localFilters.min_downloads"
            type="number"
            class="form-control"
            placeholder="Min downloads"
            min="0"
            @input="debouncedApplyFilters"
          />
        </div>
        <!--end::Min Downloads-->

        <!--begin::Clear Filters-->
        <div class="col-md-3 d-flex align-items-end">
          <button class="btn btn-light-primary w-100" @click="clearFilters">
            <KTIcon icon-name="refresh" icon-class="fs-4" />
            Clear Filters
          </button>
        </div>
        <!--end::Clear Filters-->
      </div>
    </div>
  </div>
  <!--end::Filters Card-->
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted, onUnmounted } from 'vue'
import type { SegmentFilters } from '@/stores/segments'

export default defineComponent({
  name: 'segment-filters',
  props: {
    filters: {
      type: Object as () => SegmentFilters,
      required: true,
    },
  },
  emits: ['update-filters'],
  setup(props, { emit }) {
    const localFilters = ref<SegmentFilters>({
      sort_by: 'date',
      order: 'desc',
    })

    let debounceTimer: NodeJS.Timeout | null = null

    // Initialize local filters from props
    const initializeFilters = () => {
      localFilters.value = { ...props.filters }
    }

    // Apply filters with debouncing
    const debouncedApplyFilters = () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
      debounceTimer = setTimeout(() => {
        applyFilters()
      }, 300)
    }

    // Apply filters immediately
    const applyFilters = () => {
      emit('update-filters', { ...localFilters.value })
    }

    // Clear all filters
    const clearFilters = () => {
      localFilters.value = {
        sort_by: 'date',
        order: 'desc',
      }
      applyFilters()
    }

    // Watch for prop changes
    watch(
      () => props.filters,
      () => {
        initializeFilters()
      },
      { deep: true },
    )

    // Cleanup on unmount
    onUnmounted(() => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
    })

    // Initialize on mount
    onMounted(() => {
      initializeFilters()
    })

    return {
      localFilters,
      debouncedApplyFilters,
      applyFilters,
      clearFilters,
    }
  },
})
</script>

<style scoped>
.form-label {
  font-weight: 600;
  color: var(--kt-gray-700);
}

.input-group-text {
  background-color: var(--kt-gray-100);
  border-color: var(--kt-gray-300);
}
</style>
