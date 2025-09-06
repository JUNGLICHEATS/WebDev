import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { Mail, ArrowLeft, Brain } from 'lucide-react'

export default function OTPVerification() {
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [isResending, setIsResending] = useState(false)
  
  const { verifyOTP, resendOTP } = useAuth()
  const { addToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    // Get email from navigation state or URL params
    const stateEmail = location.state?.email
    const urlParams = new URLSearchParams(location.search)
    const paramEmail = urlParams.get('email')
    
    if (stateEmail) {
      setEmail(stateEmail)
    } else if (paramEmail) {
      setEmail(paramEmail)
    } else {
      // If no email, redirect to sign up
      navigate('/signup')
    }
  }, [location, navigate])

  useEffect(() => {
    // Start resend cooldown timer
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return // Prevent multiple characters
    
    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const newOtp = [...otp]
    
    for (let i = 0; i < pastedData.length && i < 6; i++) {
      newOtp[i] = pastedData[i]
    }
    
    setOtp(newOtp)
    
    // Focus the next empty input or the last input
    const nextEmptyIndex = newOtp.findIndex((digit, index) => !digit && index < 6)
    const focusIndex = nextEmptyIndex === -1 ? 5 : nextEmptyIndex
    inputRefs.current[focusIndex]?.focus()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const otpString = otp.join('')
    if (otpString.length !== 6) {
      addToast({
        type: 'error',
        title: 'Invalid OTP',
        message: 'Please enter all 6 digits of the verification code.',
      })
      return
    }

    setIsLoading(true)

    try {
      await verifyOTP({
        email,
        otp: otpString
      })

      addToast({
        type: 'success',
        title: 'Email Verified!',
        message: 'Your account has been successfully verified.',
      })
      
      navigate('/dashboard')
    } catch (error: any) {
      addToast({
        type: 'error',
        title: 'Verification Failed',
        message: error.message || 'Invalid or expired verification code.',
      })
      
      // Clear OTP on error
      setOtp(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return

    setIsResending(true)

    try {
      await resendOTP(email)
      setResendCooldown(60) // 60 seconds cooldown
      addToast({
        type: 'success',
        title: 'Code Sent!',
        message: 'A new verification code has been sent to your email.',
      })
    } catch (error: any) {
      addToast({
        type: 'error',
        title: 'Resend Failed',
        message: error.message || 'Failed to resend verification code.',
      })
    } finally {
      setIsResending(false)
    }
  }

  return (
    <div className="card max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-full flex items-center justify-center">
            <Brain className="w-8 h-8 text-white" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Verify Your Email</h2>
        <p className="text-gray-600">We've sent a verification code to your email address</p>
      </div>

      <div className="text-center mb-6">
        <div className="flex items-center justify-center mb-2">
          <Mail className="w-5 h-5 text-primary-600 mr-2" />
          <span className="text-sm text-gray-600">Code sent to:</span>
        </div>
        <p className="font-medium text-gray-900">{email}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-4 text-center">
            Enter the 6-digit code
          </label>
          <div className="flex justify-center space-x-3">
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                pattern="[0-9]"
                maxLength={1}
                className="w-12 h-12 text-center text-xl font-bold border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                value={digit}
                onChange={(e) => handleOtpChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                autoComplete="one-time-code"
              />
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || otp.join('').length !== 6}
          className="btn-primary w-full py-3 text-base"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Verifying...
            </div>
          ) : (
            'Verify Code'
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 mb-4">
          Didn't receive the code?
        </p>
        <button
          onClick={handleResend}
          disabled={resendCooldown > 0 || isResending}
          className="text-primary-600 hover:text-primary-500 font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isResending ? (
            'Sending...'
          ) : resendCooldown > 0 ? (
            `Resend in ${resendCooldown}s`
          ) : (
            'Resend Code'
          )}
        </button>
      </div>

      <div className="mt-8 space-y-3 text-sm text-gray-500">
        <div className="flex items-center justify-center">
          <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></div>
          <span>Check your spam folder if you don't see the email</span>
        </div>
        <div className="flex items-center justify-center">
          <div className="w-2 h-2 bg-red-400 rounded-full mr-2"></div>
          <span>Code expires in 10 minutes</span>
        </div>
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={() => navigate('/signup')}
          className="text-sm text-gray-600 hover:text-gray-800 flex items-center justify-center"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Sign Up
        </button>
      </div>
    </div>
  )
}
