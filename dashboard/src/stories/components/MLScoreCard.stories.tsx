// @ts-nocheck
import MLScoreCard from '../components/MLScoreCard'

/**
 * MLScoreCard - Componente de score de riesgo con Machine Learning
 *
 * Referencia: Stripe Radar risk scores
 * https://stripe.com/docs/radar
 */
export default {
  title: 'Components/MLScoreCard',
  component: MLScoreCard,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Tarjeta de score de riesgo basado en ML con gauge visual, anomalías detectadas y features del modelo.',
      },
    },
  },
}

const mockScoreLow = {
  ml_score: 15,
  risk_level: 'low',
  model_version: '1.2.0',
  lookback_days: 90,
  features: {
    verification_frequency: 85,
    score_volatility: 12,
    sanction_history: 0,
    debt_trend: 10,
    compliance_consistency: 95,
  },
  explanation: [
    'Historial de verificaciones consistente y frecuente',
    'Baja volatilidad en scores históricos',
    'Sin sanciones registradas en OSCE/TCE',
    'Tendencia de deuda estable y manejable',
  ],
  calculated_at: new Date().toISOString(),
  ruc: '20100100123',
}

const mockScoreModerate = {
  ml_score: 45,
  risk_level: 'moderate',
  model_version: '1.2.0',
  lookback_days: 90,
  features: {
    verification_frequency: 50,
    score_volatility: 45,
    sanction_history: 15,
    debt_trend: 40,
    compliance_consistency: 60,
  },
  explanation: [
    'Verificaciones irregulares en los últimos 90 días',
    'Volatilidad moderada en comportamiento de score',
    'Una sanción menor registrada hace 6 meses',
    'Tendencia de deuda ligeramente creciente',
  ],
  calculated_at: new Date().toISOString(),
  ruc: '20100100456',
}

const mockScoreHigh = {
  ml_score: 78,
  risk_level: 'high',
  model_version: '1.2.0',
  lookback_days: 90,
  features: {
    verification_frequency: 20,
    score_volatility: 75,
    sanction_history: 60,
    debt_trend: 70,
    compliance_consistency: 30,
  },
  explanation: [
    'Muy pocas verificaciones en el período analizado',
    'Alta volatilidad en scores históricos',
    'Múltiples sanciones activas en OSCE/TCE',
    'Tendencia de deuda significativamente creciente',
  ],
  calculated_at: new Date().toISOString(),
  ruc: '20100100789',
}

const mockScoreCritical = {
  ml_score: 95,
  risk_level: 'critical',
  model_version: '1.2.0',
  lookback_days: 90,
  features: {
    verification_frequency: 5,
    score_volatility: 92,
    sanction_history: 95,
    debt_trend: 88,
    compliance_consistency: 10,
  },
  explanation: [
    'Casi sin verificaciones - comportamiento sospechoso',
    'Extrema volatilidad en scores históricos',
    'Sanciones severas y recientes registradas',
    'Tendencia de deuda crítica y creciente',
    'Compliance inconsistente con múltiples incumplimientos',
  ],
  calculated_at: new Date().toISOString(),
  ruc: '20100100999',
}

export const LowRisk = {
  args: {
    ruc: '20100100123',
  },
  parameters: {
    mockData: mockScoreLow,
  },
}

export const ModerateRisk = {
  args: {
    ruc: '20100100456',
  },
  parameters: {
    mockData: mockScoreModerate,
  },
}

export const HighRisk = {
  args: {
    ruc: '20100100789',
  },
  parameters: {
    mockData: mockScoreHigh,
  },
}

export const CriticalRisk = {
  args: {
    ruc: '20100100999',
  },
  parameters: {
    mockData: mockScoreCritical,
  },
}

export const Loading = {
  args: {
    ruc: null,
  },
}
