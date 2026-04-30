import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api, {
  authAPI,
  verificationAPI,
  compareAPI,
  inviteAPI,
  complianceAPI,
  companyAPI,
  networkApi,
} from '../services/api'
import type {
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
} from '../types'

// Auth hooks
export const useAuthMe = () => {
  return useQuery<User>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const { data } = await authAPI.me()
      return data
    },
    staleTime: 1000 * 60 * 10,
  })
}

// Verification hooks
export const useVerifications = () => {
  return useQuery<PaginatedResponse<VerificationRequest>>({
    queryKey: ['verifications', 'history'],
    queryFn: async () => {
      const { data } = await verificationAPI.history()
      return data
    },
  })
}

export const useVerifyRuc = () => {
  const queryClient = useQueryClient()

  return useMutation<VerificationResult, Error, string>({
    mutationFn: async (ruc: string) => {
      const { data } = await verificationAPI.verify(ruc)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verifications'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// Compare hooks
export const useCompare = () => {
  const queryClient = useQueryClient()

  return useMutation<Comparison, Error, string[]>({
    mutationFn: async (rucs: string[]) => {
      const { data } = await compareAPI.compare(rucs)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compare', 'history'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export const useCompareHistory = () => {
  return useQuery<PaginatedResponse<Comparison>>({
    queryKey: ['compare', 'history'],
    queryFn: async () => {
      const { data } = await compareAPI.history()
      return data
    },
  })
}

// Invite hooks
export const useInvites = () => {
  return useQuery<PaginatedResponse<Invite>>({
    queryKey: ['invites', 'list'],
    queryFn: async () => {
      const { data } = await inviteAPI.list()
      return data
    },
  })
}

export const useInviteStats = () => {
  return useQuery<InviteStats>({
    queryKey: ['invites', 'stats'],
    queryFn: async () => {
      const { data } = await inviteAPI.stats()
      return data
    },
  })
}

export const useCreateInvite = () => {
  const queryClient = useQueryClient()

  return useMutation<Invite, Error, InviteCreate>({
    mutationFn: async (inviteData: InviteCreate) => {
      const { data } = await inviteAPI.create(inviteData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invites'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// Compliance hooks
export const useComplianceStatus = () => {
  return useQuery<ComplianceStatus>({
    queryKey: ['compliance', 'status'],
    queryFn: async () => {
      const { data } = await complianceAPI.status()
      return data
    },
  })
}

export const useComplianceObligations = () => {
  return useQuery<PaginatedResponse<ComplianceObligation>>({
    queryKey: ['compliance', 'obligations'],
    queryFn: async () => {
      const { data } = await complianceAPI.obligations()
      return data
    },
  })
}

export const useComplianceNetwork = () => {
  return useQuery<NetworkStats>({
    queryKey: ['compliance', 'network'],
    queryFn: async () => {
      const { data } = await complianceAPI.network()
      return data
    },
  })
}

// Company hooks
export const useCompanyProfile = () => {
  return useQuery<Company>({
    queryKey: ['company', 'profile'],
    queryFn: async () => {
      const { data } = await companyAPI.profile()
      return data
    },
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()

  return useMutation<Company, Error, CompanyUpdate>({
    mutationFn: async (profileData: CompanyUpdate) => {
      const { data } = await companyAPI.update(profileData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', 'profile'] })
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}

export const useApiKeys = () => {
  return useQuery<ApiKey[]>({
    queryKey: ['company', 'apiKeys'],
    queryFn: async () => {
      const { data } = await companyAPI.apiKeys()
      return data
    },
  })
}

// Network hooks (Mi Red)
export const useNetworkSuppliers = () => {
  return useQuery<PaginatedResponse<NetworkSupplier>>({
    queryKey: ['network', 'suppliers'],
    queryFn: async () => {
      const { data } = await networkApi.getSuppliers()
      return data
    },
  })
}

export const useNetworkStats = () => {
  return useQuery<NetworkStats>({
    queryKey: ['network', 'stats'],
    queryFn: async () => {
      const { data } = await networkApi.getStats()
      return data
    },
  })
}

export const useNetworkAlerts = () => {
  return useQuery<PaginatedResponse<NetworkAlert>>({
    queryKey: ['network', 'alerts'],
    queryFn: async () => {
      const { data } = await networkApi.getAlerts()
      return data
    },
  })
}

export const useAddSupplier = () => {
  const queryClient = useQueryClient()

  return useMutation<NetworkSupplier, Error, { ruc: string; notes?: string; tags?: string[] }>({
    mutationFn: async (supplierData) => {
      const { data } = await networkApi.addSupplier(supplierData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export const useRemoveSupplier = () => {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: async (id: string) => {
      await networkApi.removeSupplier(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export const useMarkAlertRead = () => {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: async (id: string) => {
      await networkApi.markAlertRead(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network', 'alerts'] })
    },
  })
}

// Dashboard stats hook
export const useDashboardStats = () => {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/dashboard/stats')
      return data
    },
    staleTime: 1000 * 60 * 2, // 2 minutos
  })
}

// ───────────────────────────────────────────────
// Monitoring hooks (Fase 2)
// ───────────────────────────────────────────────

export interface MonitoringStats {
  total_snapshots: number
  total_changes_detected: number
  pending_alerts: number
  critical_changes: number
  warning_changes: number
  last_run: {
    id: number | null
    status: string | null
    completed_at: string | null
  }
}

export interface MonitoringAlert {
  id: number
  change_id: number
  company_id: number
  title: string
  message: string
  channel: string
  severity: string
  status: string
  created_at: string
  sent_at: string | null
  read_at: string | null
}

export interface MonitoringChange {
  id: number
  company_id: number
  change_type: string
  description: string
  severity: string
  previous_value: string | null
  new_value: string | null
  alert_sent: boolean
  created_at: string
}

export interface MonitoringRule {
  id: number
  company_id: number | null
  rule_type: string
  conditions: Record<string, unknown>
  notify_email: boolean
  notify_dashboard: boolean
  notify_webhook: boolean
  webhook_url: string | null
  frequency: string
  is_active: boolean
  created_at: string
}

export const useMonitoringStats = () => {
  return useQuery<MonitoringStats>({
    queryKey: ['monitoring', 'stats'],
    queryFn: async () => {
      const { data } = await api.get('/api/v2/monitoring/stats')
      return data
    },
    staleTime: 1000 * 60 * 2,
  })
}

export const useMonitoringAlerts = (status?: string) => {
  return useQuery<MonitoringAlert[]>({
    queryKey: ['monitoring', 'alerts', status],
    queryFn: async () => {
      const params = status && status !== 'all' ? { status } : {}
      const { data } = await api.get('/api/v2/monitoring/alerts', { params })
      return data
    },
    staleTime: 1000 * 60,
  })
}

export const useMonitoringChanges = (severity?: string) => {
  return useQuery<MonitoringChange[]>({
    queryKey: ['monitoring', 'changes', severity],
    queryFn: async () => {
      const params = severity ? { severity } : {}
      const { data } = await api.get('/api/v2/monitoring/changes', { params })
      return data
    },
    staleTime: 1000 * 60,
  })
}

export const useMonitoringRules = () => {
  return useQuery<MonitoringRule[]>({
    queryKey: ['monitoring', 'rules'],
    queryFn: async () => {
      const { data } = await api.get('/api/v2/monitoring/rules')
      return data
    },
  })
}

export const useMarkMonitoringAlertRead = () => {
  const queryClient = useQueryClient()

  return useMutation<void, Error, number>({
    mutationFn: async (alertId: number) => {
      await api.post(`/api/v2/monitoring/alerts/${alertId}/read`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'alerts'] })
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'stats'] })
    },
  })
}

export const useDismissMonitoringAlert = () => {
  const queryClient = useQueryClient()

  return useMutation<void, Error, number>({
    mutationFn: async (alertId: number) => {
      await api.post(`/api/v2/monitoring/alerts/${alertId}/dismiss`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'alerts'] })
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'stats'] })
    },
  })
}

// ───────────────────────────────────────────────
// ML Scoring hooks (Fase 2)
// ───────────────────────────────────────────────

export interface MLScore {
  ruc: string
  ml_score: number
  risk_level: string
  features: {
    verification_frequency: number
    score_volatility: number
    sanction_history: number
    debt_trend: number
    compliance_consistency: number
  }
  explanation: string[]
  lookback_days: number
  calculated_at: string
  model_version: string
}

export interface MLAnomalies {
  ruc: string
  anomalies: {
    type: string
    severity: string
    description: string
    detected_at?: string
    count?: number
    previous?: number
    current?: number
  }[]
  anomaly_count: number
  has_anomalies: boolean
  days_analyzed: number
  analyzed_at: string
}

export interface MLBenchmark {
  ruc: string
  individual_score: number
  sector: string | null
  sector_average: number | null
  sector_median: number | null
  percentile: number | null
  comparison: string
}

export const useMLScore = (ruc: string | null, lookbackDays: number = 90) => {
  return useQuery<MLScore>({
    queryKey: ['ml', 'score', ruc, lookbackDays],
    queryFn: async () => {
      const { data } = await api.get(`/api/v2/ml/score/${ruc}`, {
        params: { lookback_days: lookbackDays }
      })
      return data
    },
    enabled: !!ruc && ruc.length === 11,
    staleTime: 1000 * 60 * 5, // 5 minutos
  })
}

export const useMLAnomalies = (ruc: string | null, days: number = 30) => {
  return useQuery<MLAnomalies>({
    queryKey: ['ml', 'anomalies', ruc, days],
    queryFn: async () => {
      const { data } = await api.get(`/api/v2/ml/score/${ruc}/anomalies`, {
        params: { days }
      })
      return data
    },
    enabled: !!ruc && ruc.length === 11,
    staleTime: 1000 * 60 * 5,
  })
}

export const useMLBenchmark = (ruc: string | null, sector?: string) => {
  return useQuery<MLBenchmark>({
    queryKey: ['ml', 'benchmark', ruc, sector],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (sector) params.sector = sector
      const { data } = await api.get(`/api/v2/ml/score/${ruc}/benchmark`, { params })
      return data
    },
    enabled: !!ruc && ruc.length === 11,
    staleTime: 1000 * 60 * 10,
  })
}
