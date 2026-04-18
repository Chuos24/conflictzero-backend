import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cz_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cz_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/api/v1/auth/login', { email, password }),
  register: (data) => api.post('/api/v1/auth/register', data),
  me: () => api.get('/api/v1/auth/me'),
  refresh: () => api.post('/api/v1/auth/refresh')
}

// Verifications API
export const verificationAPI = {
  verify: (ruc) => api.post('/api/v1/verify', { ruc }),
  history: () => api.get('/api/v1/verifications/history'),
  getById: (id) => api.get(`/api/v1/verifications/${id}`),
  certificate: (id) => api.get(`/api/v1/verifications/${id}/certificate`)
}

// Compare API
export const compareAPI = {
  compare: (rucs) => api.post('/api/v1/compare', { rucs }),
  history: () => api.get('/api/v1/compare/history')
}

// Invites API
export const inviteAPI = {
  list: () => api.get('/api/v2/invites'),
  create: (data) => api.post('/api/v2/invites', data),
  stats: () => api.get('/api/v2/invites/stats'),
  resend: (id) => api.post(`/api/v2/invites/${id}/resend`)
}

// Compliance API
export const complianceAPI = {
  status: () => api.get('/api/v2/founder/compliance'),
  obligations: () => api.get('/api/v2/founder/obligations'),
  network: () => api.get('/api/v2/founder/network')
}

// Company API
export const companyAPI = {
  profile: () => api.get('/api/v1/company/profile'),
  update: (data) => api.patch('/api/v1/company/profile', data),
  publicProfile: () => api.get('/api/v1/company/public-profile'),
  apiKeys: () => api.get('/api/v1/company/api-keys'),
  createApiKey: (name) => api.post('/api/v1/company/api-keys', { name }),
  revokeApiKey: (id) => api.delete(`/api/v1/company/api-keys/${id}`)
}

// Network API (Mi Red - Supplier Network)
export const networkApi = {
  // Suppliers
  getSuppliers: () => api.get('/api/v2/network/'),
  addSupplier: (data) => api.post('/api/v2/network/add', data),
  getSupplier: (id) => api.get(`/api/v2/network/${id}`),
  updateSupplier: (id, data) => api.patch(`/api/v2/network/${id}`, data),
  removeSupplier: (id) => api.delete(`/api/v2/network/${id}`),
  
  // Alerts
  getAlerts: () => api.get('/api/v2/network/alerts'),
  markAlertRead: (id) => api.patch(`/api/v2/network/alerts/${id}/read`),
  markAllAlertsRead: () => api.post('/api/v2/network/alerts/mark-all-read'),
  
  // Stats
  getStats: () => api.get('/api/v2/network/stats/dashboard')
}

export default api
