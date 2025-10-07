import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  // Add headers to prevent Chrome caching issues
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
})

export interface SessionData {
  session_token: string
  expires_at: string
  custom_text?: string
  photo_shape?: 'square' | 'circle'
  pdf_size?: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'
  template_id?: string
  background_id?: string
  font_id?: string
  photo_url?: string
  waveform_url?: string
  audio_duration?: number
  // File information for display
  photo_filename?: string
  photo_size?: number
  audio_filename?: string
  audio_size?: number
}

export interface SessionUpdateData {
  custom_text?: string
  photo_shape?: 'square' | 'circle'
  pdf_size?: 'A4' | 'A4_Landscape' | 'Letter' | 'Letter_Landscape' | 'A3' | 'A3_Landscape'
  template_id?: string
  background_id?: string
  font_id?: string
}

export interface UploadResponse {
  status: 'success' | 'error'
  message?: string
  photo_url?: string
  duration?: number
  waveform_processing?: 'started' | 'completed'
}

export interface ProcessingStatus {
  photo_ready: boolean
  audio_ready: boolean
  waveform_ready: boolean
  preview_ready: boolean
}

export interface PaymentIntentResponse {
  client_secret: string
  amount: number
  order_id: string
}

export interface DownloadResponse {
  download_url: string
  expires_at: string
  email_sent: boolean
}

// Session Management
export const createSession = async (): Promise<SessionData> => {
  const response = await api.post('/session')
  return response.data
}

export const getSession = async (token: string): Promise<SessionData> => {
  const response = await api.get(`/session/${token}`)
  return response.data
}

export const updateSession = async (token: string, data: SessionUpdateData): Promise<void> => {
  console.log('🌐 API updateSession called with token:', token, 'data:', data)
  const response = await api.put(`/session/${token}`, data)
  console.log('🌐 API updateSession response:', response.status, response.data)
}

// File Uploads
export const uploadPhoto = async (token: string, file: File): Promise<UploadResponse> => {
  // Validate file before upload to catch Chrome-specific issues early
  if (!file || file.size === 0) {
    throw new Error('Invalid file: File is empty or corrupted')
  }

  // Create a fresh FormData instance to avoid Chrome caching issues
  const formData = new FormData()

  // Ensure file is properly appended with explicit filename
  formData.append('photo', file, file.name)

  // Add a timestamp to prevent caching
  formData.append('timestamp', Date.now().toString())

  const response = await api.post(`/session/${token}/photo`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      // Force Chrome to not cache the request
      'Cache-Control': 'no-cache',
      'X-Requested-With': 'XMLHttpRequest'
    },
    onUploadProgress: (progressEvent) => {
      const progress = progressEvent.total
        ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
        : 0
      // You can emit this progress to a callback if needed
      console.log(`Photo upload progress: ${progress}%`)
    },
    // Ensure request is not cached
    params: {
      _t: Date.now()
    }
  })

  return response.data
}

export const uploadAudio = async (token: string, file: File): Promise<UploadResponse> => {
  // Validate file before upload to catch Chrome-specific issues early
  if (!file || file.size === 0) {
    throw new Error('Invalid file: File is empty or corrupted')
  }

  // Create a fresh FormData instance to avoid Chrome caching issues
  const formData = new FormData()

  // Ensure file is properly appended with explicit filename
  formData.append('audio', file, file.name)

  // Add a timestamp to prevent caching
  formData.append('timestamp', Date.now().toString())

  const response = await api.post(`/session/${token}/audio`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      // Force Chrome to not cache the request
      'Cache-Control': 'no-cache',
      'X-Requested-With': 'XMLHttpRequest'
    },
    onUploadProgress: (progressEvent) => {
      const progress = progressEvent.total
        ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
        : 0
      console.log(`Audio upload progress: ${progress}%`)
    },
    // Ensure request is not cached
    params: {
      _t: Date.now()
    }
  })

  return response.data
}

// File Removal
export const removePhoto = async (token: string): Promise<{ status: string; message: string }> => {
  const response = await api.delete(`/session/${token}/photo`)
  return response.data
}

export const removeAudio = async (token: string): Promise<{ status: string; message: string }> => {
  const response = await api.delete(`/session/${token}/audio`)
  return response.data
}

// Processing Status
export const getProcessingStatus = async (token: string): Promise<ProcessingStatus> => {
  const response = await api.get(`/session/${token}/status`)
  return response.data
}

// Preview
export const getPreviewUrl = async (token: string): Promise<{ preview_url: string; expires_at: string }> => {
  const response = await api.get(`/session/${token}/preview`)
  return response.data
}

// Payment
export const createPaymentIntent = async (
  token: string,
  email: string,
  tier: 'standard' | 'premium' = 'standard'
): Promise<PaymentIntentResponse> => {
  const response = await api.post(`/session/${token}/payment`, { email, tier })
  return response.data
}

export const completeOrder = async (
  orderId: string,
  paymentIntentId: string,
  sessionToken: string
): Promise<DownloadResponse> => {
  const response = await api.post(`/orders/${orderId}/complete`, {
    payment_intent_id: paymentIntentId,
    session_token: sessionToken
  })
  return response.data
}

export default api
