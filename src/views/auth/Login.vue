<template>
  <div class="d-flex flex-column flex-column-fluid">
    <!-- Content -->
    <div class="d-flex flex-center flex-column flex-column-fluid">
      <!-- Wrapper -->
      <div class="w-lg-500px bg-body rounded shadow-sm p-10 p-lg-15 mx-auto">
        <!-- Logo -->
        <div class="text-center mb-11">
          <h1 class="text-dark fw-bolder mb-3">
            <i class="bi bi-camera-video text-primary me-2"></i>
            Easy Video Share
          </h1>
          <div class="text-gray-500 fw-semibold fs-6">
            Welcome back! Please sign in to your account
          </div>
        </div>

        <!-- Passwordless Login Form -->
        <form
          v-if="currentStep === 'email'"
          @submit.prevent="handlePasswordlessLogin"
          class="form w-100"
        >
          <div class="fv-row mb-8">
            <label class="form-label fs-6 fw-bolder text-dark">
              <i class="bi bi-envelope me-1"></i>Email for Passwordless Login
            </label>
            <input
              v-model="email"
              type="email"
              class="form-control bg-transparent"
              :class="{ 'is-invalid': emailError }"
              placeholder="Enter your email address"
              required
              :disabled="isLoading"
            />
            <div v-if="emailError" class="invalid-feedback">
              {{ emailError }}
            </div>
          </div>

          <div class="d-grid mb-10">
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="isLoading"
              :class="{ 'indicator-progress': isLoading }"
            >
              <span v-if="!isLoading" class="indicator-label">
                <i class="bi bi-send me-2"></i>Send Login Code
              </span>
              <span v-else class="indicator-progress">
                Please wait...
                <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
              </span>
            </button>
          </div>
        </form>

        <!-- Verification Code Form -->
        <form
          v-if="currentStep === 'verify'"
          @submit.prevent="handlePasswordlessVerification"
          class="form w-100"
        >
          <div class="fv-row mb-8">
            <label class="form-label fs-6 fw-bolder text-dark">
              <i class="bi bi-shield-check me-1"></i>Verification Code
            </label>
            <input
              v-model="verificationCode"
              type="text"
              class="form-control bg-transparent text-center"
              :class="{ 'is-invalid': codeError }"
              placeholder="Enter 6-digit code"
              maxlength="6"
              required
              :disabled="isLoading"
              style="letter-spacing: 0.5rem; font-size: 1.2rem"
            />
            <div v-if="codeError" class="invalid-feedback">
              {{ codeError }}
            </div>
            <div class="form-text text-muted">
              <i class="bi bi-info-circle me-1"></i>Check your email for the verification code
            </div>
          </div>

          <div class="d-grid mb-5">
            <button
              type="submit"
              class="btn btn-success"
              :disabled="isLoading"
              :class="{ 'indicator-progress': isLoading }"
            >
              <span v-if="!isLoading" class="indicator-label">
                <i class="bi bi-check-circle me-2"></i>Verify & Sign In
              </span>
              <span v-else class="indicator-progress">
                Verifying...
                <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
              </span>
            </button>
          </div>

          <div class="d-grid mb-10">
            <button type="button" @click="backToEmail" class="btn btn-light" :disabled="isLoading">
              <i class="bi bi-arrow-left me-2"></i>Back to Send Code
            </button>
          </div>
        </form>

        <!-- Register Link -->
        <div class="text-center">
          <div class="text-gray-500 fw-semibold fs-6">Don't have an account?</div>
          <router-link to="/auth/register" class="link-primary fw-bold fs-6">
            Create Account
          </router-link>
        </div>

        <!-- Configuration Notice -->
        <div v-if="!hasValidConfig" class="mt-8">
          <div class="alert alert-warning" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            <strong>Configuration Required:</strong> To use authentication, please create a
            <code>.env.local</code> file with your AWS Cognito configuration.
            <details class="mt-2">
              <summary class="fw-bold">Setup Instructions</summary>
              <div class="mt-2">
                <p>Create <code>.env.local</code> in your project root with:</p>
                <pre class="bg-light p-3 rounded">
VITE_COGNITO_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=your-actual-pool-id
VITE_COGNITO_CLIENT_ID=your-actual-client-id</pre
                >
              </div>
            </details>
          </div>
        </div>

        <!-- Status Messages -->
        <div v-if="statusMessage" class="mt-8">
          <div class="alert" :class="getAlertClass(statusType)" role="alert">
            <i :class="getStatusIcon(statusType)" class="me-2"></i>
            {{ statusMessage }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'LoginPage',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    // Form state
    const currentStep = ref<'email' | 'verify'>('email')
    const email = ref('')
    const verificationCode = ref('')
    const isLoading = ref(false)

    // Error handling
    const emailError = ref('')
    const codeError = ref('')
    const statusMessage = ref('')
    const statusType = ref<'success' | 'error' | 'info'>('info')

    // Configuration check
    const hasValidConfig = computed(() => {
      return (
        import.meta.env.VITE_COGNITO_USER_POOL_ID &&
        import.meta.env.VITE_COGNITO_USER_POOL_ID !== 'your-user-pool-id'
      )
    })

    // Clear errors when inputs change
    const clearErrors = () => {
      emailError.value = ''
      codeError.value = ''
      statusMessage.value = ''
    }

    // Handle passwordless login initiation
    const handlePasswordlessLogin = async () => {
      clearErrors()

      if (!email.value || !email.value.includes('@')) {
        emailError.value = 'Please enter a valid email address'
        return
      }

      try {
        isLoading.value = true

        // Use real Cognito passwordless authentication
        const result = await authStore.startPasswordlessLogin(email.value)

        if (result.success) {
          currentStep.value = 'verify'
          statusMessage.value = result.message || `Verification code sent to ${email.value}`
          statusType.value = 'success'
        } else {
          statusMessage.value =
            result.error || 'Failed to send verification code. Please try again.'
          statusType.value = 'error'
        }
      } catch (error) {
        console.error('Passwordless login failed:', error)
        statusMessage.value = 'Failed to send verification code. Please try again.'
        statusType.value = 'error'
      } finally {
        isLoading.value = false
      }
    }

    // Handle verification code submission
    const handlePasswordlessVerification = async () => {
      clearErrors()

      if (!verificationCode.value || verificationCode.value.length !== 6) {
        codeError.value = 'Please enter a 6-digit verification code'
        return
      }

      try {
        isLoading.value = true

        // Use real Cognito passwordless verification
        const result = await authStore.confirmPasswordlessLogin(verificationCode.value)

        if (result.success) {
          statusMessage.value = result.message || 'Login successful!'
          statusType.value = 'success'

          // Redirect to dashboard after successful login
          setTimeout(() => {
            router.push('/dashboard')
          }, 1000)
        } else {
          codeError.value = result.error || 'Invalid verification code. Please try again.'
          statusMessage.value = result.error || 'Verification failed. Please check your code.'
          statusType.value = 'error'
        }
      } catch (error) {
        console.error('Verification failed:', error)
        codeError.value = 'Invalid verification code. Please try again.'
        statusMessage.value = 'Verification failed. Please check your code.'
        statusType.value = 'error'
      } finally {
        isLoading.value = false
      }
    }

    // Go back to email step
    const backToEmail = () => {
      currentStep.value = 'email'
      verificationCode.value = ''
      clearErrors()
    }

    // Utility functions for styling
    const getAlertClass = (type: string) => {
      switch (type) {
        case 'success':
          return 'alert-success'
        case 'error':
          return 'alert-danger'
        case 'info':
          return 'alert-info'
        default:
          return 'alert-info'
      }
    }

    const getStatusIcon = (type: string) => {
      switch (type) {
        case 'success':
          return 'bi bi-check-circle'
        case 'error':
          return 'bi bi-exclamation-triangle'
        case 'info':
          return 'bi bi-info-circle'
        default:
          return 'bi bi-info-circle'
      }
    }

    return {
      currentStep,
      email,
      verificationCode,
      isLoading,
      emailError,
      codeError,
      statusMessage,
      statusType,
      hasValidConfig,
      handlePasswordlessLogin,
      handlePasswordlessVerification,
      backToEmail,
      getAlertClass,
      getStatusIcon,
    }
  },
})
</script>

<style scoped>
.form {
  width: 100%;
}

.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}
</style>
