import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const res = await axios.post('/api/auth/refresh/', { refresh })
          localStorage.setItem('access_token', res.data.access)
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const authAPI = {
  login: (data) => api.post('/auth/login/', data),
  register: (data) => api.post('/auth/register/', data),
  profile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
}

// Documents
export const documentsAPI = {
  list: (params) => api.get('/documents/', { params }),
  get: (id) => api.get(`/documents/${id}/`),
  upload: (formData, onProgress) => api.post('/documents/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  }),
  delete: (id) => api.delete(`/documents/${id}/`),
}

// Analysis
export const analysisAPI = {
  start: (data) => api.post('/analysis/start/', data),
  list: () => api.get('/analysis/'),
  get: (id) => api.get(`/analysis/${id}/`),
  status: (id) => api.get(`/analysis/${id}/status/`),
}

// Reports
export const reportsAPI = {
  downloadPDF: (analysisId) => api.get(`/reports/${analysisId}/pdf/`, { responseType: 'blob' }),
}

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats/'),
  history: () => api.get('/dashboard/history/'),
  distribution: () => api.get('/dashboard/distribution/'),
}

export default api
