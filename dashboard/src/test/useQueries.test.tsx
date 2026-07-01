import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useAuthMe,
  useVerifications,
  useVerifyRuc,
  useCompare,
  useCompareHistory,
  useDashboardStats,
} from '../hooks/useQueries';

// Mock api module
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  authAPI: { me: vi.fn() },
  verificationAPI: { history: vi.fn(), verify: vi.fn() },
  compareAPI: { compare: vi.fn(), history: vi.fn() },
  inviteAPI: { list: vi.fn(), stats: vi.fn(), create: vi.fn() },
  complianceAPI: { status: vi.fn(), obligations: vi.fn(), network: vi.fn() },
  companyAPI: { profile: vi.fn(), update: vi.fn(), apiKeys: vi.fn() },
  networkApi: {
    getSuppliers: vi.fn(),
    getStats: vi.fn(),
    getAlerts: vi.fn(),
    addSupplier: vi.fn(),
    removeSupplier: vi.fn(),
    markAlertRead: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useQueries hooks', () => {
  it('useAuthMe should fetch user data', async () => {
    const { authAPI } = await import('../services/api');
    vi.mocked(authAPI.me).mockResolvedValueOnce({
      data: { id: 1, ruc: '20123456789', name: 'Test Corp' },
    });

    const { result } = renderHook(() => useAuthMe(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe('Test Corp');
  });

  it('useVerifications should fetch verification history', async () => {
    const { verificationAPI } = await import('../services/api');
    vi.mocked(verificationAPI.history).mockResolvedValueOnce({
      data: {
        items: [{ id: 1, ruc: '20123456789', status: 'completed' }],
        total: 1,
      },
    });

    const { result } = renderHook(() => useVerifications(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(1);
  });

  it('useVerifyRuc should verify a RUC', async () => {
    const { verificationAPI } = await import('../services/api');
    vi.mocked(verificationAPI.verify).mockResolvedValueOnce({
      data: { ruc: '20123456789', score: 85, status: 'success' },
    });

    const { result } = renderHook(() => useVerifyRuc(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync('20123456789');
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('useCompare should compare multiple RUCs', async () => {
    const { compareAPI } = await import('../services/api');
    vi.mocked(compareAPI.compare).mockResolvedValueOnce({
      data: { comparison_id: 'cmp-1', results: [] },
    });

    const { result } = renderHook(() => useCompare(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync(['20123456789', '20987654321']);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('useCompareHistory should fetch comparison history', async () => {
    const { compareAPI } = await import('../services/api');
    vi.mocked(compareAPI.history).mockResolvedValueOnce({
      data: { items: [], total: 0 },
    });

    const { result } = renderHook(() => useCompareHistory(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(0);
  });

  it('useDashboardStats should fetch stats', async () => {
    const api = (await import('../services/api')).default;
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { total_verifications: 100, compliance_score: 85 },
    });

    const { result } = renderHook(() => useDashboardStats(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_verifications).toBe(100);
  });
});
