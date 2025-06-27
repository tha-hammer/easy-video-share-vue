import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authManager } from '@/core/auth/authManager'

// Types based on our Terraform schema
interface User {
  userId: string // Cognito sub
  username: string // Cognito username
  email: string // User email
  groups: string[] // ['admin'] or ['user']
  isAdmin: boolean // Computed from groups
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(true)

  const initialize = async () => {
    try {
      isLoading.value = true
      console.log('Initializing auth with real authManager...')

      const isAuth = await authManager.initialize()

      if (isAuth) {
        const currentUser = authManager.getCurrentUser()
        if (currentUser) {
          user.value = currentUser
          isAuthenticated.value = true
          console.log('✅ Auth initialized successfully with real user:')
          console.log('- User ID:', user.value.userId)
          console.log('- Email:', user.value.email)
          console.log('- Is Admin:', user.value.isAdmin)
        }
      } else {
        user.value = null
        isAuthenticated.value = false
        console.log('❌ No authenticated user found')
      }

      return isAuth
    } catch (error) {
      console.error('Auth initialization failed:', error)
      user.value = null
      isAuthenticated.value = false
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const login = async (email: string, password: string) => {
    try {
      isLoading.value = true
      console.log('Attempting real login for:', email)

      const result = await authManager.login(email, password)

      if (result.success) {
        // Refresh auth state
        await initialize()
      }

      return result
    } catch (error) {
      console.error('Login failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed',
      }
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      const result = await authManager.logout()

      user.value = null
      isAuthenticated.value = false

      return result
    } catch (error) {
      console.error('Logout failed:', error)
      return {
        success: false,
        error: 'Logout failed',
      }
    }
  }

  // Passwordless authentication methods
  const startPasswordlessLogin = async (email: string) => {
    try {
      isLoading.value = true
      return await authManager.startPasswordlessLogin(email)
    } catch (error) {
      console.error('Passwordless login failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to start passwordless login',
      }
    } finally {
      isLoading.value = false
    }
  }

  const confirmPasswordlessLogin = async (confirmationCode: string) => {
    try {
      isLoading.value = true

      const result = await authManager.confirmPasswordlessLogin(confirmationCode)

      if (result.success && result.user) {
        user.value = result.user
        isAuthenticated.value = true
      }

      return result
    } catch (error) {
      console.error('Passwordless confirmation failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to confirm passwordless login',
      }
    } finally {
      isLoading.value = false
    }
  }

  const register = async (email: string, password: string, fullName?: string) => {
    try {
      isLoading.value = true
      console.log('Attempting registration for:', email)

      const result = await authManager.register(email, password, fullName)
      return result
    } catch (error) {
      console.error('Registration failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Registration failed',
      }
    } finally {
      isLoading.value = false
    }
  }

  const confirmRegistration = async (email: string, confirmationCode: string) => {
    try {
      isLoading.value = true

      const result = await authManager.confirmRegistration(email, confirmationCode)

      if (result.success) {
        // Registration is complete, but user still needs to login
        // No need to update auth state yet
      }

      return result
    } catch (error) {
      console.error('Registration confirmation failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Verification failed',
      }
    } finally {
      isLoading.value = false
    }
  }

  const resendConfirmationCode = async (email: string) => {
    try {
      isLoading.value = true
      return await authManager.resendConfirmationCode(email)
    } catch (error) {
      console.error('Resend failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to resend code',
      }
    } finally {
      isLoading.value = false
    }
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    initialize,
    login,
    logout,
    startPasswordlessLogin,
    confirmPasswordlessLogin,
    register,
    confirmRegistration,
    resendConfirmationCode,
  }
})
