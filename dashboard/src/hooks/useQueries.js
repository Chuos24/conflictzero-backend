import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api, { authAPI, verificationAPI, compareAPI, inviteAPI, complianceAPI, companyAPI, networkApi } from '../services/api'

// Auth hooks
export const useAuthMe = () => {
  return useQuery({
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
  return useQuery({
    queryKey: ['verifications', 'history'],
    queryFn: async () => {
      const { data } = await verificationAPI.history()
      return data
    },
  })
}

export const useVerifyRuc = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (ruc) => {
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

  return useMutation({
    mutationFn: async (rucs) => {
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
  return useQuery({
    queryKey: ['compare', 'history'],
    queryFn: async () => {
      const { data } = await compareAPI.history()
      return data
    },
  })
}

// Invite hooks
export const useInvites = () => {
  return useQuery({
    queryKey: ['invites', 'list'],
    queryFn: async () => {
      const { data } = await inviteAPI.list()
      return data
    },
  })
}

export const useInviteStats = () => {
  return useQuery({
    queryKey: ['invites', 'stats'],
    queryFn: async () => {
      const { data } = await inviteAPI.stats()
      return data
    },
  })
}

export const useCreateInvite = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (inviteData) => {
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
  return useQuery({
    queryKey: ['compliance', 'status'],
    queryFn: async () => {
      const { data } = await complianceAPI.status()
      return data
    },
  })
}

export const useComplianceObligations = () => {
  return useQuery({
    queryKey: ['compliance', 'obligations'],
    queryFn: async () => {
      const { data } = await complianceAPI.obligations()
      return data
    },
  })
}

export const useComplianceNetwork = () => {
  return useQuery({
    queryKey: ['compliance', 'network'],
    queryFn: async () => {
      const { data } = await complianceAPI.network()
      return data
    },
  })
}

// Company hooks
export const useCompanyProfile = () => {
  return useQuery({
    queryKey: ['company', 'profile'],
    queryFn: async () => {
      const { data } = await companyAPI.profile()
      return data
    },
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (profileData) => {
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
  return useQuery({
    queryKey: ['company', 'apiKeys'],
    queryFn: async () => {
      const { data } = await companyAPI.apiKeys()
      return data
    },
  })
}

// Network hooks (Mi Red)
export const useNetworkSuppliers = () => {
  return useQuery({
    queryKey: ['network', 'suppliers'],
    queryFn: async () => {
      const { data } = await networkApi.getSuppliers()
      return data
    },
  })
}

export const useNetworkStats = () => {
  return useQuery({
    queryKey: ['network', 'stats'],
    queryFn: async () => {
      const { data } = await networkApi.getStats()
      return data
    },
  })
}

export const useNetworkAlerts = () => {
  return useQuery({
    queryKey: ['network', 'alerts'],
    queryFn: async () => {
      const { data } = await networkApi.getAlerts()
      return data
    },
  })
}

export const useAddSupplier = () => {
  const queryClient = useQueryClient()

  return useMutation({
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

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await networkApi.removeSupplier(id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export const useMarkAlertRead = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await networkApi.markAlertRead(id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network', 'alerts'] })
    },
  })
}

// Dashboard stats hook
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/dashboard/stats')
      return data
    },
    staleTime: 1000 * 60 * 2, // 2 minutos
  })
}
