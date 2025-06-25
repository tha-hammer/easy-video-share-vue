<template>
  <div
    class="modal fade"
    :class="{ show: show, 'd-block': show }"
    style="z-index: 1055"
    tabindex="-1"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header border-0 pb-0">
          <h1 class="modal-title fs-4 fw-bold text-gray-800" id="deleteModalLabel">
            Confirm {{ itemType === 'video' ? 'Video' : 'User' }} Deletion
          </h1>
          <button
            type="button"
            class="btn-close"
            @click="$emit('cancel')"
            aria-label="Close"
          ></button>
        </div>

        <div class="modal-body py-5">
          <div class="text-center">
            <!-- Warning Icon -->
            <div class="mb-5">
              <KTIcon
                :icon-name="itemType === 'video' ? 'video' : 'user'"
                :icon-class="`fs-3x text-${itemType === 'video' ? 'danger' : 'warning'}`"
              />
            </div>

            <!-- Warning Message -->
            <h3 class="text-gray-800 fw-bold mb-3">
              Are you sure you want to delete this {{ itemType }}?
            </h3>

            <div class="text-muted fs-6 mb-5">
              <div class="fw-semibold mb-2">
                {{ itemType === 'video' ? 'Video:' : 'User:' }} "{{ itemName }}"
              </div>
              <div
                v-if="itemType === 'video'"
                class="alert alert-light-danger d-flex align-items-center"
              >
                <KTIcon icon-name="warning-2" icon-class="fs-3 text-danger me-3" />
                <div class="text-start">
                  <div class="fw-bold">This action cannot be undone!</div>
                  <div class="fs-7">
                    The video file will be permanently deleted from storage and all metadata will be
                    removed from the database.
                  </div>
                </div>
              </div>
              <div v-else class="alert alert-light-warning d-flex align-items-center">
                <KTIcon icon-name="warning-2" icon-class="fs-3 text-warning me-3" />
                <div class="text-start">
                  <div class="fw-bold">This will disable the user account!</div>
                  <div class="fs-7">
                    The user will no longer be able to access the platform. This action can be
                    reversed later.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light-secondary" @click="$emit('cancel')">
            Cancel
          </button>
          <button
            type="button"
            :class="`btn btn-${itemType === 'video' ? 'danger' : 'warning'} ms-3`"
            @click="handleConfirm"
            :disabled="isDeleting"
          >
            <span
              v-if="isDeleting"
              class="spinner-border spinner-border-sm me-2"
              role="status"
            ></span>
            <KTIcon
              v-else
              :icon-name="itemType === 'video' ? 'trash' : 'user-cross'"
              icon-class="fs-4 me-2"
            />
            {{
              isDeleting ? 'Deleting...' : itemType === 'video' ? 'Delete Video' : 'Disable User'
            }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal Backdrop -->
  <div v-if="show" class="modal-backdrop fade show" @click="$emit('cancel')"></div>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'

export default defineComponent({
  name: 'delete-confirmation-modal',
  props: {
    show: {
      type: Boolean,
      default: false,
    },
    itemType: {
      type: String as () => 'video' | 'user',
      required: true,
    },
    itemName: {
      type: String,
      required: true,
    },
  },
  emits: ['confirm', 'cancel'],
  setup(props, { emit }) {
    const isDeleting = ref(false)

    const handleConfirm = async () => {
      isDeleting.value = true

      try {
        await new Promise((resolve) => setTimeout(resolve, 500)) // Small delay for UX
        emit('confirm')
      } finally {
        isDeleting.value = false
      }
    }

    // Close modal on Escape key
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && props.show) {
        emit('cancel')
      }
    }

    // Add/remove event listener when modal shows/hides
    const setupEventListeners = () => {
      if (props.show) {
        document.addEventListener('keydown', handleKeydown)
        document.body.style.overflow = 'hidden'
      } else {
        document.removeEventListener('keydown', handleKeydown)
        document.body.style.overflow = 'auto'
      }
    }

    // Watch for show prop changes
    watch(() => props.show, setupEventListeners, { immediate: true })

    return {
      isDeleting,
      handleConfirm,
    }
  },
})
</script>

<style scoped>
.modal {
  background: rgba(0, 0, 0, 0.5);
}

.modal.show {
  display: block !important;
}

.modal-backdrop {
  z-index: 1040;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

/* Animation for modal */
.modal.show .modal-dialog {
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
