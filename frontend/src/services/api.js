import axios from 'axios'
import toast from 'react-hot-toast'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Skip token for login/register endpoints
    const publicEndpoints = ['/auth/login', '/auth/register', '/auth/refresh-token']
    const isPublicEndpoint = publicEndpoints.some(endpoint => config.url.endsWith(endpoint))
    
    if (isPublicEndpoint) {
      console.log('DEBUG: Public endpoint, skipping token check')
      return config
    }

    const token = localStorage.getItem('token')
    console.log('DEBUG: API Request interceptor - token exists:', !!token)
    console.log('DEBUG: API Request URL:', config.url)
    
    if (token) {
      // Ensure we have a clean token without quotes
      const cleanToken = token.replace(/^"|"$/g, '')
      config.headers.Authorization = `Bearer ${cleanToken}`
      console.log('DEBUG: Authorization header added:', config.headers.Authorization.substring(0, 20) + '...')
    } else {
      console.log('DEBUG: No token found in localStorage')
      // Don't redirect for public endpoints
      if (!isPublicEndpoint) {
        console.log('DEBUG: Redirecting to login - no token')
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname)
      }
    }
    
    return config
  },
  (error) => {
    console.error('DEBUG: API Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    console.log(`DEBUG: API Response [${response.status}]:`, response.config.url)
    return response
  },
  async (error) => {
    const originalRequest = error.config
    const statusCode = error.response?.status
    
    console.error('DEBUG: API Response error:', {
      url: originalRequest?.url,
      status: statusCode,
      message: error.message,
      response: error.response?.data
    })

    // Handle 401 Unauthorized
    if (statusCode === 401) {
      // If this is a retry after token refresh, don't try again
      if (originalRequest._retry) {
        console.log('DEBUG: Already retried request, logging out...')
        localStorage.removeItem('token')
        window.location.href = '/login?session_expired=true'
        return Promise.reject(error)
      }

      // Try to refresh token if this is the first 401
      try {
        console.log('DEBUG: Attempting to refresh token...')
        const response = await authAPI.refreshToken()
        const { access_token } = response.data
        
        if (access_token) {
          console.log('DEBUG: Token refreshed successfully')
          localStorage.setItem('token', access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          originalRequest._retry = true
          return api(originalRequest)
        }
      } catch (refreshError) {
        console.error('DEBUG: Token refresh failed:', refreshError)
      }

      // If we get here, token refresh failed or wasn't possible
      console.log('DEBUG: Token refresh failed or not possible, logging out')
      localStorage.removeItem('token')
      window.location.href = '/login?session_expired=true'
    }
    
    // Handle other error statuses
    if (statusCode === 403) {
      toast.error('You do not have permission to perform this action')
    } else if (statusCode === 404) {
      toast.error('The requested resource was not found')
    } else if (statusCode >= 500) {
      toast.error('A server error occurred. Please try again later.')
    }

    return Promise.reject(error)
  }
)

// Authentication API
export const authAPI = {
  login: (credentials) => {
    // Convert to URL-encoded form data for OAuth2 compatibility
    const params = new URLSearchParams()
    params.append('username', credentials.username)
    params.append('password', credentials.password)
    
    return api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
  updateProfile: (profileData) => api.put('/users/me', profileData),
}

// Users API
export const usersAPI = {
  getProfile: (userId) => api.get(`/users/${userId}`),
  listUsers: (params = {}) => api.get('/users', { params }),
  getMyStudents: () => api.get('/users/students/my-students'),
  getMyTeachers: () => api.get('/users/teachers/my-teachers'),
  getDashboardStats: () => api.get('/users/stats/dashboard'),
}

// Assignments API
export const assignmentsAPI = {
  create: (assignmentData) => api.post('/assignments/', assignmentData),
  list: (params = {}) => api.get('/assignments/', { params }),
  get: (assignmentId) => api.get(`/assignments/${assignmentId}/`),
  update: (assignmentId, data) => api.put(`/assignments/${assignmentId}/`, data),
  delete: (assignmentId) => api.delete(`/assignments/${assignmentId}/`),
  getVivaQuestions: (assignmentId) => api.get(`/assignments/${assignmentId}/viva-questions/`),
}

// Submissions API
export const submissionsAPI = {
  create: (submissionData) => api.post('/submissions/', submissionData),
  list: (params = {}) => api.get('/submissions/', { params }),
  get: (submissionId) => api.get(`/submissions/${submissionId}/`),
  update: (submissionId, data) => api.put(`/submissions/${submissionId}/`, data),
  submit: (submissionId) => api.post(`/submissions/${submissionId}/submit/`),
}

// Viva Sessions API
export const vivaAPI = {
  createSession: (sessionData) => api.post('/viva/sessions', sessionData),
  listSessions: (params = {}) => api.get('/viva/sessions', { params }),
  getSession: (sessionId) => api.get(`/viva/sessions/${sessionId}`),
  updateSession: (sessionId, data) => api.put(`/viva/sessions/${sessionId}`, data),
  startSession: (sessionId) => api.post(`/viva/sessions/${sessionId}/start`),
  respondToQuestion: (sessionId, responseData) => api.post(`/viva/sessions/${sessionId}/respond`, responseData),
  generateMockQuestions: (requestData) => api.post('/viva/mock-questions', requestData),
}

// Media API
export const mediaAPI = {
  upload: (formData) => api.post('/media/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // 1 minute for file uploads
  }),
  list: (params = {}) => api.get('/media', { params }),
  get: (fileId) => api.get(`/media/${fileId}`),
  getTranscript: (fileId) => api.get(`/media/${fileId}/transcript`),
  delete: (fileId) => api.delete(`/media/${fileId}`),
}

// Utility functions
export const apiUtils = {
  // Handle file download
  downloadFile: async (url, filename) => {
    try {
      const response = await api.get(url, { responseType: 'blob' })
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Download failed:', error)
      throw error
    }
  },

  // Format file size
  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // Format duration
  formatDuration: (seconds) => {
    if (!seconds) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  },

  // Get media URL
  getMediaUrl: (filePath) => {
    return `/media/${filePath}`
  },
}

export default api
