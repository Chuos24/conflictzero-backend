import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginResponse,
  RegisterData,
  User,
  VerificationRequest,
  VerificationResult,
  Comparison,
  Invite,
  InviteCreate,
  InviteStats,
  ComplianceStatus,
  ComplianceObligation,
  Company,
  CompanyUpdate,
  ApiKey,
  NetworkSupplier,
  NetworkAlert,
  NetworkStats,
  DashboardStats,
  PaginatedResponse,
  PaymentOrder,
  CulqiToken,
  FounderApplication,
  FounderApplicationCreate,
  PublicProfile,
  Webhook,
  WebhookDelivery,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000
});

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('cz_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cz_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/api/v1/auth/login', { email, password }),
  register: (data: RegisterData) =>
    api.post<LoginResponse>('/api/v1/auth/register', data),
  me: () => api.get<User>('/api/v1/auth/me'),
  refresh: () => api.post<LoginResponse>('/api/v1/auth/refresh')
};

// Verifications API
export const verificationAPI = {
  verify: (ruc: string) =>
    api.post<VerificationResult>('/api/v1/verify', { ruc }),
  history: () =>
    api.get<PaginatedResponse<VerificationRequest>>('/api/v1/verifications/history'),
  getById: (id: string) =>
    api.get<VerificationRequest>(`/api/v1/verifications/${id}`),
  certificate: (id: string) =>
    api.get<Blob>(`/api/v1/verifications/${id}/certificate`, { responseType: 'blob' })
};

// Compare API
export const compareAPI = {
  compare: (rucs: string[]) =>
    api.post<Comparison>('/api/v1/compare', { rucs }),
  history: () =>
    api.get<PaginatedResponse<Comparison>>('/api/v1/compare/history')
};

// Invites API
export const inviteAPI = {
  list: () => api.get<PaginatedResponse<Invite>>('/api/v2/invites'),
  create: (data: InviteCreate) => api.post<Invite>('/api/v2/invites', data),
  stats: () => api.get<InviteStats>('/api/v2/invites/stats'),
  resend: (id: string) => api.post<void>(`/api/v2/invites/${id}/resend`)
};

// Compliance API
export const complianceAPI = {
  status: () => api.get<ComplianceStatus>('/api/v2/founder/compliance'),
  obligations: () =>
    api.get<PaginatedResponse<ComplianceObligation>>('/api/v2/founder/obligations'),
  network: () => api.get<NetworkStats>('/api/v2/founder/network')
};

// Company API
export const companyAPI = {
  profile: () => api.get<Company>('/api/v1/company/profile'),
  update: (data: CompanyUpdate) =>
    api.patch<Company>('/api/v1/company/profile', data),
  publicProfile: () => api.get<PublicProfile>('/api/v1/company/public-profile'),
  apiKeys: () => api.get<ApiKey[]>('/api/v1/company/api-keys'),
  createApiKey: (name: string) =>
    api.post<ApiKey>('/api/v1/company/api-keys', { name }),
  revokeApiKey: (id: string) => api.delete<void>(`/api/v1/company/api-keys/${id}`)
};

// Network API (Mi Red - Supplier Network)
export const networkApi = {
  // Suppliers
  getSuppliers: () =>
    api.get<PaginatedResponse<NetworkSupplier>>('/api/v2/network/'),
  addSupplier: (data: { ruc: string; notes?: string; tags?: string[] }) =>
    api.post<NetworkSupplier>('/api/v2/network/add', data),
  getSupplier: (id: string) =>
    api.get<NetworkSupplier>(`/api/v2/network/${id}`),
  updateSupplier: (id: string, data: { notes?: string; tags?: string[]; status?: string }) =>
    api.patch<NetworkSupplier>(`/api/v2/network/${id}`, data),
  removeSupplier: (id: string) =>
    api.delete<void>(`/api/v2/network/${id}`),

  // Alerts
  getAlerts: () =>
    api.get<PaginatedResponse<NetworkAlert>>('/api/v2/network/alerts'),
  markAlertRead: (id: string) =>
    api.patch<void>(`/api/v2/network/alerts/${id}/read`),
  markAllAlertsRead: () =>
    api.post<void>('/api/v2/network/alerts/mark-all-read'),

  // Stats
  getStats: () => api.get<NetworkStats>('/api/v2/network/stats/dashboard')
};

// Dashboard API
export const dashboardAPI = {
  stats: () => api.get<DashboardStats>('/api/v1/dashboard/stats')
};

// Founder Applications API
export const founderAPI = {
  apply: (data: FounderApplicationCreate) =>
    api.post<FounderApplication>('/api/v1/founder/apply', data),
  myApplication: () =>
    api.get<FounderApplication>('/api/v1/founder/my-application')
};

// Payments API
export const paymentAPI = {
  createOrder: (plan: string) =>
    api.post<PaymentOrder>('/api/v1/payments/create-order', { plan }),
  process: (data: { token: CulqiToken; order_id: string }) =>
    api.post<PaymentOrder>('/api/v1/payments/process', data),
  history: () => api.get<PaymentOrder[]>('/api/v1/payments/history')
};

// Webhooks API
export const webhookAPI = {
  list: () => api.get<Webhook[]>('/api/v1/webhooks/list'),
  create: (data: { url: string; events: string[]; secret?: string }) =>
    api.post<Webhook>('/api/v1/webhooks/register', data),
  delete: (id: string) => api.delete<void>(`/api/v1/webhooks/${id}`),
  test: (id: string) => api.post<void>(`/api/v1/webhooks/${id}/test`),
  deliveries: (id: string) =>
    api.get<WebhookDelivery[]>(`/api/v1/webhooks/${id}/deliveries`)
};

export default api;
