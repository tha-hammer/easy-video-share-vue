// Authentication module using AWS Amplify
import { Amplify } from 'aws-amplify'
import {
  signUp,
  signIn,
  signOut,
  getCurrentUser,
  fetchAuthSession,
  confirmSignUp,
  resendSignUpCode,
  fetchUserAttributes,
  resetPassword,
  confirmResetPassword,
} from 'aws-amplify/auth'
import { COGNITO_CONFIG } from '../config/config'

// Configure Amplify exactly like the working vanilla JS app
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: COGNITO_CONFIG.userPoolId,
      userPoolClientId: COGNITO_CONFIG.userPoolClientId,
    },
  },
})

console.log('Amplify configured with:', {
  userPoolId: COGNITO_CONFIG.userPoolId,
  userPoolClientId: COGNITO_CONFIG.userPoolClientId,
  region: COGNITO_CONFIG.region,
})

// Types
interface User {
  userId: string
  username: string
  email: string
  groups: string[]
  isAdmin: boolean
}

interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  idToken: string | null
  isAdmin: boolean
}

// Auth state management
class AuthManager {
  private currentUser: User | null = null
  private isAuthenticated = false
  private accessToken: string | null = null
  private idToken: string | null = null
  private isAdmin = false
  private listeners: ((state: AuthState) => void)[] = []
  private pendingPasswordlessUsername: string | null = null

  // Subscribe to auth state changes
  subscribe(callback: (state: AuthState) => void) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((l) => l !== callback)
    }
  }

  // Notify all listeners of auth state change
  private notify() {
    this.listeners.forEach((callback) =>
      callback({
        isAuthenticated: this.isAuthenticated,
        user: this.currentUser,
        token: this.accessToken,
        idToken: this.idToken,
        isAdmin: this.isAdmin,
      }),
    )
  }

  // Check if user is in admin group
  private async checkAdminStatus(): Promise<boolean> {
    try {
      if (!this.idToken) {
        return false
      }

      // Decode JWT token to check groups
      const tokenPayload = this.parseJwt(this.idToken)
      const groups = tokenPayload['cognito:groups'] || []

      this.isAdmin = groups.includes('admin')
      console.log('Admin status:', this.isAdmin, 'Groups:', groups)

      return this.isAdmin
    } catch (error) {
      console.error('Error checking admin status:', error)
      this.isAdmin = false
      return false
    }
  }

  // Helper function to decode JWT token
  private parseJwt(token: string): Record<string, any> {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split('')
          .map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
          })
          .join(''),
      )

      return JSON.parse(jsonPayload)
    } catch (error) {
      console.error('Error parsing JWT token:', error)
      return {}
    }
  }

  // Initialize auth state on page load
  async initialize(): Promise<boolean> {
    try {
      const user = await getCurrentUser()
      const session = await fetchAuthSession()

      this.currentUser = {
        userId: user.userId,
        username: user.username,
        email: user.signInDetails?.loginId || '',
        groups: [],
        isAdmin: false,
      }
      this.isAuthenticated = true

      // Store both access token and ID token
      this.accessToken = session.tokens?.accessToken?.toString() || null
      this.idToken = session.tokens?.idToken?.toString() || null

      // Check admin status
      await this.checkAdminStatus()

      // Update user with admin status
      if (this.currentUser) {
        this.currentUser.isAdmin = this.isAdmin
      }

      console.log('User authenticated:', user.username)
      console.log('Is Admin:', this.isAdmin)

      this.notify()
      return true
    } catch (error) {
      console.log('No authenticated user')
      this.currentUser = null
      this.isAuthenticated = false
      this.accessToken = null
      this.idToken = null
      this.isAdmin = false
      this.notify()
      return false
    }
  }

  // Login
  async login(email: string, password: string) {
    try {
      const username = email.replace(/[@.]/g, '_').toLowerCase()

      const result = await signIn({
        username: username,
        password: password,
      })

      if (result.isSignedIn) {
        await this.initialize() // Refresh auth state
        return {
          success: true,
          message: 'Login successful!',
        }
      } else {
        return {
          success: false,
          error: 'Login incomplete. Please check your credentials.',
        }
      }
    } catch (error: any) {
      console.error('Login error:', error)
      return {
        success: false,
        error: error.message,
      }
    }
  }

  // Logout
  async logout() {
    try {
      await signOut()
      this.currentUser = null
      this.isAuthenticated = false
      this.accessToken = null
      this.idToken = null
      this.isAdmin = false
      this.notify()

      return {
        success: true,
        message: 'Logged out successfully',
      }
    } catch (error: any) {
      console.error('Logout error:', error)
      return {
        success: false,
        error: error.message,
      }
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    return this.currentUser
  }

  // Check if authenticated
  isUserAuthenticated(): boolean {
    return this.isAuthenticated
  }

  // Get access token
  async getAccessToken(): Promise<string | null> {
    try {
      console.log('🔑 AuthManager: Fetching auth session...')
      const session = await fetchAuthSession()
      console.log('🔑 AuthManager: Session retrieved:', {
        hasTokens: !!session.tokens,
        hasAccessToken: !!session.tokens?.accessToken,
        hasIdToken: !!session.tokens?.idToken,
      })

      // For API Gateway with Cognito authorizer, we need the ID token (not access token!)
      const idToken = session.tokens?.idToken?.toString() || null
      const accessToken = session.tokens?.accessToken?.toString() || null

      console.log('🔑 AuthManager: Token debugging:', {
        hasIdToken: !!idToken,
        hasAccessToken: !!accessToken,
        idTokenStart: idToken ? idToken.substring(0, 20) + '...' : 'None',
        accessTokenStart: accessToken ? accessToken.substring(0, 20) + '...' : 'None',
      })

      // Use ID token for API Gateway authentication (same as vanilla app)
      const tokenToUse = idToken || accessToken
      console.log('🔑 AuthManager: Using token type:', idToken ? 'ID Token' : 'Access Token')
      console.log('🔑 AuthManager: Token result:', !!tokenToUse, 'Length:', tokenToUse?.length || 0)

      if (tokenToUse) {
        console.log('🔑 AuthManager: Token start:', tokenToUse.substring(0, 50))

        // Debug: Parse token to show token_use claim
        try {
          const payload = JSON.parse(atob(tokenToUse.split('.')[1]))
          console.log('🔑 AuthManager: Token payload token_use:', payload.token_use)
          console.log('🔑 AuthManager: Token payload aud:', payload.aud)
        } catch (e) {
          console.log('🔑 AuthManager: Could not parse token payload')
        }
      }

      return tokenToUse
    } catch (error) {
      console.error('❌ AuthManager: Error getting access token:', error)
      return null
    }
  }

  // Start passwordless login (magic link)
  async startPasswordlessLogin(email: string) {
    try {
      // Generate the same username from email
      const username = email.replace(/[@.]/g, '_').toLowerCase()

      console.log('Starting passwordless login for:', username)

      // Use native Cognito forgot password flow for passwordless authentication
      // This sends a verification code to the user's email
      const result = await resetPassword({
        username: username,
      })

      console.log('Passwordless login result:', result)

      if (result.nextStep?.resetPasswordStep === 'CONFIRM_RESET_PASSWORD_WITH_CODE') {
        // Store the username for the confirmation step
        this.pendingPasswordlessUsername = username

        return {
          success: true,
          message: 'Verification code sent to your email. Use this code to sign in.',
          challengeType: 'EMAIL_CODE',
        }
      }

      return {
        success: false,
        error: 'Unexpected response from authentication service',
      }
    } catch (error: any) {
      console.error('Passwordless login error:', error)

      // Provide user-friendly error messages
      let errorMessage = error.message
      if (error.message.includes('UserNotFoundException')) {
        errorMessage =
          'No account found with this email. Please register first or use password login.'
      } else if (error.message.includes('NotAuthorizedException')) {
        errorMessage = 'Account not verified. Please check your email for verification code first.'
      } else if (error.message.includes('LimitExceededException')) {
        errorMessage = 'Too many requests. Please wait a moment before trying again.'
      }

      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  // Confirm passwordless login with verification code
  async confirmPasswordlessLogin(confirmationCode: string, newPassword: string | null = null) {
    try {
      if (!this.pendingPasswordlessUsername) {
        throw new Error('No pending passwordless login session')
      }

      console.log('Confirming passwordless login with code')

      // Generate a random password for the reset (user won't need to remember this)
      const tempPassword = newPassword || this.generateSecurePassword()

      // First, confirm the password reset with the code
      await confirmResetPassword({
        username: this.pendingPasswordlessUsername,
        confirmationCode: confirmationCode,
        newPassword: tempPassword,
      })

      console.log('Password reset confirmed')

      // Now sign in with the new temporary password
      const signInResult = await signIn({
        username: this.pendingPasswordlessUsername,
        password: tempPassword,
      })

      console.log('Sign in result:', signInResult)

      if (signInResult.isSignedIn) {
        // Initialize auth state properly
        await this.initialize()

        // Clear the pending username
        this.pendingPasswordlessUsername = null

        console.log('Passwordless login successful')

        return {
          success: true,
          message: 'Passwordless login successful!',
          user: this.currentUser,
        }
      }

      return {
        success: false,
        error: 'Failed to complete passwordless login',
      }
    } catch (error: any) {
      console.error('Passwordless confirmation error:', error)

      // Provide user-friendly error messages
      let errorMessage = error.message
      if (error.message.includes('CodeMismatchException')) {
        errorMessage = 'Invalid verification code. Please try again.'
      } else if (error.message.includes('ExpiredCodeException')) {
        errorMessage = 'Verification code has expired. Please request a new code.'
      } else if (error.message.includes('InvalidPasswordException')) {
        errorMessage = 'There was an issue with the password reset. Please try again.'
      }

      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  // Helper method to generate a secure random password
  private generateSecurePassword(): string {
    const length = 16
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    let password = ''

    // Ensure we have at least one of each required character type
    password += 'A' // uppercase
    password += 'a' // lowercase
    password += '1' // number
    password += '!' // symbol

    // Fill the rest randomly
    for (let i = 4; i < length; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length))
    }

    // Shuffle the password
    return password
      .split('')
      .sort(() => Math.random() - 0.5)
      .join('')
  }
}

// Export singleton instance
export const authManager = new AuthManager()
