import axios, { AxiosInstance, AxiosError, AxiosResponse, CancelTokenSource } from 'axios'

// API base configuration with fallback to same-origin
const getBaseUrl = (): string => {
  // Try VITE_API_BASE_URL first, then fallback to current origin
  const envUrl = import.meta.env?.VITE_API_BASE_URL
  const fallbackUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8001'
  
  return (envUrl || fallbackUrl).replace(/\/$/, '')
}

const BASE_URL = getBaseUrl()
// Don't add /api here since axios will handle the path prefix correctly
const API_BASE_URL = BASE_URL
const DEFAULT_TIMEOUT = 30000 // 30 seconds for regular requests
const GENERATION_TIMEOUT = 45000 // 45 seconds for generation requests

// Active request tracking for cancellation
const activeRequests = new Map<string, CancelTokenSource>()

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check function
export const checkAPIHealth = async (): Promise<{ status: 'healthy' | 'degraded' | 'unhealthy', data?: any }> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 5000 })
    if (response.status === 200 && response.data) {
      // Use the actual status from the API response
      const apiStatus = response.data.status || 'healthy'
      return { 
        status: apiStatus === 'healthy' ? 'healthy' : 'degraded',
        data: response.data 
      }
    }
    return { status: 'degraded' }
  } catch (error) {
    console.warn('Health check failed:', error)
    return { status: 'unhealthy' }
  }
}

// Create generation request with extended timeout and cancellation
export const createGenerationRequest = (url: string, data: any, requestId: string) => {
  // Cancel any existing request with same ID
  if (activeRequests.has(requestId)) {
    activeRequests.get(requestId)?.cancel('New request initiated')
    activeRequests.delete(requestId)
  }

  // Create new cancel token
  const source = axios.CancelToken.source()
  activeRequests.set(requestId, source)

  return apiClient.request({
    method: 'POST',
    url,
    data,
    timeout: GENERATION_TIMEOUT,
    cancelToken: source.token,
    onUploadProgress: (progressEvent) => {
      console.log(`Upload progress: ${Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))}%`)
    }
  }).finally(() => {
    // Clean up on completion
    activeRequests.delete(requestId)
  })
}

// Cancel active request
export const cancelRequest = (requestId: string) => {
  const source = activeRequests.get(requestId)
  if (source) {
    source.cancel('Request canceled by user')
    activeRequests.delete(requestId)
    return true
  }
  return false
}

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    console.log(`📍 Base URL: ${API_BASE_URL}`)
    return config
  },
  (error) => {
    console.error('🚨 Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error: any) => {
    // Cancel request if user navigated away
    if (axios.isCancel(error)) {
      throw new Error('Запрос отменен')
    }

    console.error('🚨 API Error:', error.response?.status, error.message)
    
    // Handle common error scenarios  
    if (error.code === 'ECONNABORTED') {
      throw new Error('Время ожидания истекло. Попробуйте еще раз.')
    }
    
    if (!error.response) {
      throw new Error('Нет соединения с сервером. Проверьте подключение к интернету.')
    }
    
    const status = error.response.status
    const message = error.response.data?.message || error.message
    
    switch (status) {
      case 400:
        throw new Error(`Некорректный запрос: ${message}`)
      case 401:
        throw new Error('Необходима авторизация')
      case 403:
        throw new Error('Доступ запрещен')
      case 404:
        throw new Error('Ресурс не найден')
      case 422:
        throw new Error(`Ошибка валидации: ${message}`)
      case 500:
        throw new Error('Внутренняя ошибка сервера. Попробуйте позже.')
      case 503:
        throw new Error('Сервис временно недоступен. Попробуйте позже.')
      default:
        throw new Error(`Ошибка сервера (${status}): ${message}`)
    }
  }
)

export { apiClient as api }
export default apiClient