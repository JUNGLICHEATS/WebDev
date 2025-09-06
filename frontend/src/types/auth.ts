export interface User {
  id: string
  name: string
  email: string
  is_verified: boolean
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface SignInData {
  email: string
  password: string
}

export interface SignUpData {
  name: string
  email: string
  password: string
}

export interface OTPData {
  email: string
  otp: string
}

export interface AuthResponse {
  success: boolean
  message: string
  access_token?: string
  token_type?: string
  requires_otp?: boolean
  demo_otp?: string
}
