import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { authAPI } from '../services/api'
import type { AuthState, User, SignInData, SignUpData, OTPData } from '../types/auth'

interface AuthContextType extends AuthState {
  signIn: (data: SignInData) => Promise<{ success: boolean; message: string; requires_otp?: boolean }>
  signUp: (data: SignUpData) => Promise<{ success: boolean; message: string }>
  verifyOTP: (data: OTPData) => Promise<{ success: boolean; message: string }>
  resendOTP: (email: string) => Promise<{ success: boolean; message: string }>
  googleAuth: () => void
  logout: () => void
}

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_TOKEN'; payload: string | null }
  | { type: 'LOGOUT' }

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_USER':
      return { 
        ...state, 
        user: action.payload, 
        isAuthenticated: !!action.payload,
        isLoading: false 
      }
    case 'SET_TOKEN':
      return { ...state, token: action.payload }
    case 'LOGOUT':
      return { 
        ...state, 
        user: null, 
        token: null, 
        isAuthenticated: false,
        isLoading: false 
      }
    default:
      return state
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')
      const userStr = localStorage.getItem('user')
      
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr)
          dispatch({ type: 'SET_TOKEN', payload: token })
          dispatch({ type: 'SET_USER', payload: user })
          
          // Verify token is still valid
          await authAPI.getCurrentUser()
        } catch (error) {
          // Token is invalid, clear storage
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          dispatch({ type: 'LOGOUT' })
        }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    }

    initAuth()
  }, [])

  const signIn = async (data: SignInData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const response = await authAPI.signIn(data)
      
      if (response.success && response.access_token) {
        localStorage.setItem('token', response.access_token)
        dispatch({ type: 'SET_TOKEN', payload: response.access_token })
        
        // Get user info
        const user = await authAPI.getCurrentUser()
        localStorage.setItem('user', JSON.stringify(user))
        dispatch({ type: 'SET_USER', payload: user })
      }
      
      return response
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Sign in failed')
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const signUp = async (data: SignUpData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const response = await authAPI.signUp(data)
      return response
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Sign up failed')
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const verifyOTP = async (data: OTPData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const response = await authAPI.verifyOTP(data)
      
      if (response.success && response.access_token) {
        localStorage.setItem('token', response.access_token)
        dispatch({ type: 'SET_TOKEN', payload: response.access_token })
        
        // Get user info
        const user = await authAPI.getCurrentUser()
        localStorage.setItem('user', JSON.stringify(user))
        dispatch({ type: 'SET_USER', payload: user })
      }
      
      return response
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'OTP verification failed')
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const resendOTP = async (email: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const response = await authAPI.resendOTP(email)
      return response
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to resend OTP')
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const googleAuth = () => {
    authAPI.googleAuth()
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      dispatch({ type: 'LOGOUT' })
    }
  }

  const value: AuthContextType = {
    ...state,
    signIn,
    signUp,
    verifyOTP,
    resendOTP,
    googleAuth,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
