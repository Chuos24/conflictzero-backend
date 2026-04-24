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
