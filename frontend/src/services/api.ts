import axios from 'axios'
import type { SignInData, SignUpData, OTPData, AuthResponse, User } from '../types/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/signin'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  // Sign up
  signUp: async (data: SignUpData): Promise<AuthResponse> => {
    const response = await api.post('/api/signup', data)
    return response.data
  },

  // Sign in
  signIn: async (data: SignInData): Promise<AuthResponse> => {
    const response = await api.post('/api/signin', data)
    return response.data
  },

  // Verify OTP
  verifyOTP: async (data: OTPData): Promise<AuthResponse> => {
    const response = await api.post('/api/verify-otp', data)
    return response.data
  },

  // Resend OTP
  resendOTP: async (email: string): Promise<AuthResponse> => {
    const response = await api.post('/api/resend-otp', { email })
    return response.data
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/api/me')
    return response.data
  },

  // Google OAuth
  googleAuth: () => {
    window.location.href = `${API_BASE_URL}/api/auth/google`
  },

  // Logout
  logout: async (): Promise<void> => {
    await api.post('/api/logout')
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
}

export default api
