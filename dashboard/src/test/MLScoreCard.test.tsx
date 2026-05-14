import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MLScoreCard from '../components/MLScoreCard'
import * as useQueriesModule from '../hooks/useQueries'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, enabled: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('MLScoreCard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders loading state', () => {
    vi.spyOn(useQueriesModule, 'useMLScore').mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isPending: false,
      isError: false,
      isSuccess: false,
      status: 'pending',
      fetchStatus: 'fetching',
    } as any)
    vi.spyOn(useQueriesModule, 'useMLAnomalies').mockReturnValue({
      data: undefined,
    } as any)

    render(<MLScoreCard ruc="20123456789" />, { wrapper: createWrapper() })
    expect(screen.getByText(/Calculando ML Score/)).toBeInTheDocument()
  })

  it('renders error state', () => {
    vi.spyOn(useQueriesModule, 'useMLScore').mockReturnValue({
      data: undefined,
      isLoading: false,
      error: { message: 'Network error' },
      isPending: false,
      isError: true,
      isSuccess: false,
      status: 'error',
      fetchStatus: 'idle',
    } as any)
    vi.spyOn(useQueriesModule, 'useMLAnomalies').mockReturnValue({
      data: undefined,
    } as any)

    render(<MLScoreCard ruc="20123456789" />, { wrapper: createWrapper() })
    expect(screen.getByText(/Error calculando ML Score/)).toBeInTheDocument()
    expect(screen.getByText(/Network error/)).toBeInTheDocument()
  })

  it('renders null when no ruc', () => {
    const { container } = render(<MLScoreCard ruc={null} />, { wrapper: createWrapper() })
    expect(container.firstChild).toBeNull()
  })

  it('renders score data', () => {
    const mockScore = {
      ruc: '20123456789',
      ml_score: 78,
      risk_level: 'low',
      features: {
        verification_frequency: 80,
        score_volatility: 20,
        sanction_history: 0,
        debt_trend: 10,
        compliance_consistency: 90,
      },
      explanation: ['Buena consistencia de compliance', 'Sin sanciones detectadas'],
      lookback_days: 90,
      calculated_at: '2026-05-13T10:00:00Z',
      model_version: 'v1.5',
    }

    vi.spyOn(useQueriesModule, 'useMLScore').mockReturnValue({
      data: mockScore,
      isLoading: false,
      error: null,
      isPending: false,
      isError: false,
      isSuccess: true,
      status: 'success',
      fetchStatus: 'idle',
    } as any)
    vi.spyOn(useQueriesModule, 'useMLAnomalies').mockReturnValue({
      data: { has_anomalies: false, anomaly_count: 0, anomalies: [] },
    } as any)

    render(<MLScoreCard ruc="20123456789" />, { wrapper: createWrapper() })
    expect(screen.getByText('ML Score de Riesgo')).toBeInTheDocument()
    expect(screen.getByText('78')).toBeInTheDocument()
    expect(screen.getByText(/Bajo Riesgo/)).toBeInTheDocument()
  })

  it('renders anomalies when present', () => {
    const mockScore = {
      ruc: '20123456789',
      ml_score: 45,
      risk_level: 'high',
      features: {
        verification_frequency: 30,
        score_volatility: 70,
        sanction_history: 50,
        debt_trend: 60,
        compliance_consistency: 40,
      },
      explanation: ['Score bajo detectado'],
      lookback_days: 90,
      calculated_at: '2026-05-13T10:00:00Z',
      model_version: 'v1.5',
    }

    const anomalies = {
      has_anomalies: true,
      anomaly_count: 2,
      anomalies: [
        { severity: 'critical', description: 'Sanción reciente detectada' },
        { severity: 'high', description: 'Incremento de deuda' }
      ]
    }

    vi.spyOn(useQueriesModule, 'useMLScore').mockReturnValue({
      data: mockScore,
      isLoading: false,
      error: null,
      isPending: false,
      isError: false,
      isSuccess: true,
      status: 'success',
      fetchStatus: 'idle',
    } as any)
    vi.spyOn(useQueriesModule, 'useMLAnomalies').mockReturnValue({
      data: anomalies,
    } as any)

    render(<MLScoreCard ruc="20123456789" />, { wrapper: createWrapper() })
    expect(screen.getByText(/Anomalías Detectadas/)).toBeInTheDocument()
    expect(screen.getByText('Sanción reciente detectada')).toBeInTheDocument()
    expect(screen.getByText('Incremento de deuda')).toBeInTheDocument()
  })
})
