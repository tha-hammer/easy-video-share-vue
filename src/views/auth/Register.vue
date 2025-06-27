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
            Create your account to start sharing videos
          </div>
        </div>

        <!-- Register Form -->
        <form v-if="currentStep === 'register'" @submit.prevent="handleRegister" class="form w-100">
          <div class="fv-row mb-8">
            <label class="form-label fs-6 fw-bolder text-dark">
              <i class="bi bi-envelope me-1"></i>Email Address
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

          <div class="fv-row mb-8">
            <label class="form-label fs-6 fw-bolder text-dark">
              <i class="bi bi-lock me-1"></i>Password
            </label>
            <input
              v-model="password"
              type="password"
              class="form-control bg-transparent"
              :class="{ 'is-invalid': passwordError }"
              placeholder="Choose a strong password"
              minlength="8"
              required
              :disabled="isLoading"
            />
            <div v-if="passwordError" class="invalid-feedback">
              {{ passwordError }}
            </div>
            <div class="form-text text-muted">
              <i class="bi bi-info-circle me-1"></i>
              Password must be at least 8 characters with uppercase, lowercase, number, and symbol
            </div>
          </div>

          <div class="fv-row mb-8">
            <label class="form-label fs-6 fw-bolder text-gray-900">
              <i class="bi bi-person me-1"></i>Full Name (Optional)
            </label>
            <input
              v-model="fullName"
              type="text"
              class="form-control bg-transparent"
              placeholder="Your full name"
              :disabled="isLoading"
            />
          </div>

          <div class="d-grid mb-10">
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="isLoading"
              :class="{ 'indicator-progress': isLoading }"
            >
              <span v-if="!isLoading" class="indicator-label">
                <i class="bi bi-person-plus me-2"></i>Create Account
              </span>
              <span v-else class="indicator-progress">
                Creating account...
                <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
              </span>
            </button>
          </div>
        </form>

        <!-- Verification Form -->
        <form
          v-if="currentStep === 'verify'"
          @submit.prevent="handleVerification"
          class="form w-100"
        >
          <div class="text-center mb-8">
            <div class="mb-4">
              <i class="bi bi-envelope-check text-primary" style="font-size: 3rem"></i>
            </div>
            <h3 class="text-dark fw-bolder mb-3">Verify Your Email</h3>
            <div class="alert alert-info border-0" role="alert">
              <i class="bi bi-info-circle me-2"></i>
              We've sent a verification code to <strong>{{ email }}</strong>
            </div>
          </div>

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
          </div>

          <div class="d-grid mb-5">
            <button
              type="submit"
              class="btn btn-success"
              :disabled="isLoading"
              :class="{ 'indicator-progress': isLoading }"
            >
              <span v-if="!isLoading" class="indicator-label">
                <i class="bi bi-check-circle me-2"></i>Verify Account
              </span>
              <span v-else class="indicator-progress">
                Verifying...
                <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
              </span>
            </button>
          </div>

          <div class="d-grid mb-5">
            <button
              type="button"
              @click="resendCode"
              class="btn btn-light"
              :disabled="isLoading || resendCooldown > 0"
            >
              <i class="bi bi-arrow-clockwise me-2"></i>
              <span v-if="resendCooldown > 0">Resend Code ({{ resendCooldown }}s)</span>
              <span v-else>Resend Code</span>
            </button>
          </div>

          <div class="d-grid mb-10">
            <button
              type="button"
              @click="backToRegister"
              class="btn btn-light"
              :disabled="isLoading"
            >
              <i class="bi bi-arrow-left me-2"></i>Back to Registration
            </button>
          </div>
        </form>

        <!-- Login Link -->
        <div class="text-center">
          <div class="text-gray-500 fw-semibold fs-6">Already have an account?</div>
          <router-link to="/auth/login" class="link-primary fw-bold fs-6"> Sign In </router-link>
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
import { defineComponent, ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'RegisterPage',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    // Form state
    const currentStep = ref<'register' | 'verify'>('register')
    const email = ref('')
    const password = ref('')
    const fullName = ref('')
    const verificationCode = ref('')
    const isLoading = ref(false)
    const resendCooldown = ref(0)

    // Error handling
    const emailError = ref('')
    const passwordError = ref('')
    const codeError = ref('')
    const statusMessage = ref('')
    const statusType = ref<'success' | 'error' | 'info'>('info')

    // Resend cooldown timer
    let resendTimer: ReturnType<typeof setInterval> | null = null

    // Clear errors when inputs change
    const clearErrors = () => {
      emailError.value = ''
      passwordError.value = ''
      codeError.value = ''
      statusMessage.value = ''
    }

    // Validate password strength
    const validatePassword = (pwd: string): boolean => {
      const minLength = pwd.length >= 8
      const hasUpper = /[A-Z]/.test(pwd)
      const hasLower = /[a-z]/.test(pwd)
      const hasNumber = /\d/.test(pwd)
      const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/.test(pwd)

      return minLength && hasUpper && hasLower && hasNumber && hasSymbol
    }

    // Handle registration
    const handleRegister = async () => {
      clearErrors()

      // Validate email
      if (!email.value || !email.value.includes('@')) {
        emailError.value = 'Please enter a valid email address'
        return
      }

      // Validate password
      if (!validatePassword(password.value)) {
        passwordError.value =
          'Password must be at least 8 characters with uppercase, lowercase, number, and symbol'
        return
      }

      try {
        isLoading.value = true

        // Use real auth manager for registration
        const result = await authStore.register(email.value, password.value, fullName.value)

        if (result.success) {
          currentStep.value = 'verify'
          statusMessage.value = result.message || `Verification code sent to ${email.value}`
          statusType.value = 'success'
        } else {
          statusMessage.value = result.error || 'Registration failed. Please try again.'
          statusType.value = 'error'
        }
      } catch (error) {
        console.error('Registration failed:', error)
        statusMessage.value = 'Registration failed. Please try again.'
        statusType.value = 'error'
      } finally {
        isLoading.value = false
      }
    }

    // Handle verification
    const handleVerification = async () => {
      clearErrors()

      if (!verificationCode.value || verificationCode.value.length !== 6) {
        codeError.value = 'Please enter a 6-digit verification code'
        return
      }

      try {
        isLoading.value = true

        // Use real auth manager for verification
        const result = await authStore.confirmRegistration(email.value, verificationCode.value)

        if (result.success) {
          statusMessage.value =
            result.message || 'Account verified successfully! Redirecting to login...'
          statusType.value = 'success'

          // Redirect to login after a short delay
          setTimeout(() => {
            router.push('/auth/login')
          }, 2000)
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

    // Resend verification code
    const resendCode = async () => {
      if (resendCooldown.value > 0) return

      try {
        isLoading.value = true

        // Use real auth manager for resend
        const result = await authStore.resendConfirmationCode(email.value)

        if (result.success) {
          statusMessage.value = result.message || 'Verification code resent successfully'
          statusType.value = 'success'

          // Start cooldown timer
          resendCooldown.value = 60
          resendTimer = setInterval(() => {
            resendCooldown.value--
            if (resendCooldown.value <= 0 && resendTimer) {
              clearInterval(resendTimer)
              resendTimer = null
            }
          }, 1000)
        } else {
          statusMessage.value = result.error || 'Failed to resend code. Please try again.'
          statusType.value = 'error'
        }
      } catch (error) {
        console.error('Resend failed:', error)
        statusMessage.value = 'Failed to resend code. Please try again.'
        statusType.value = 'error'
      } finally {
        isLoading.value = false
      }
    }

    // Go back to registration
    const backToRegister = () => {
      currentStep.value = 'register'
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

    // Cleanup timer on unmount
    onUnmounted(() => {
      if (resendTimer) {
        clearInterval(resendTimer)
      }
    })

    return {
      currentStep,
      email,
      password,
      fullName,
      verificationCode,
      isLoading,
      resendCooldown,
      emailError,
      passwordError,
      codeError,
      statusMessage,
      statusType,
      handleRegister,
      handleVerification,
      resendCode,
      backToRegister,
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

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}
</style>
