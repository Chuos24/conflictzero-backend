import { VerificationTrends, RiskDistribution, SanctionsByEntity, ComplianceHistory, StatsDashboard } from '../components/Charts'

export default {
  title: 'Components/Charts',
  component: StatsDashboard,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Componentes de visualización de datos usando Recharts. Incluyen gráficos de líneas, barras, pie y dashboards completos.',
      },
    },
  },
}

export const VerificationTrendsDefault = {
  render: () => <VerificationTrends />,
  name: 'Tendencia de Verificaciones',
  parameters: {
    docs: {
      description: {
        story: 'Gráfico de líneas mostrando verificaciones y comparaciones mensuales.',
      },
    },
  },
}

export const VerificationTrendsCustom = {
  render: () => (
    <VerificationTrends
      data={[
        { date: 'Jul', verifications: 42, comparisons: 15 },
        { date: 'Ago', verifications: 38, comparisons: 12 },
        { date: 'Sep', verifications: 55, comparisons: 20 },
        { date: 'Oct', verifications: 48, comparisons: 18 },
      ]}
    />
  ),
  name: 'Tendencia - Datos Custom',
}

export const RiskDistributionDefault = {
  render: () => <RiskDistribution />,
  name: 'Distribución de Riesgo',
  parameters: {
    docs: {
      description: {
        story: 'Gráfico de donut mostrando distribución por niveles de riesgo.',
      },
    },
  },
}

export const RiskDistributionCustom = {
  render: () => (
    <RiskDistribution
      data={[
        { name: 'Bajo Riesgo', value: 60, color: '#22c55e' },
        { name: 'Riesgo Medio', value: 25, color: '#eab308' },
        { name: 'Alto Riesgo', value: 15, color: '#ef4444' },
      ]}
    />
  ),
  name: 'Riesgo - Datos Custom',
}

export const SanctionsByEntityDefault = {
  render: () => <SanctionsByEntity />,
  name: 'Sanciones por Entidad',
}

export const SanctionsByEntityCustom = {
  render: () => (
    <SanctionsByEntity
      data={[
        { entity: 'SUNAT', sanciones: 5 },
        { entity: 'OSCE', sanciones: 12 },
        { entity: 'TCE', sanciones: 3 },
        { entity: 'INDECOPI', sanciones: 8 },
        { entity: 'SBS', sanciones: 1 },
      ]}
    />
  ),
  name: 'Sanciones - Datos Custom',
}

export const ComplianceHistoryDefault = {
  render: () => <ComplianceHistory />,
  name: 'Historial de Compliance',
}

export const StatsDashboardDefault = {
  render: () => <StatsDashboard />,
  name: 'Dashboard Completo',
  parameters: {
    layout: 'fullscreen',
  },
}

export const StatsDashboardCustom = {
  render: () => (
    <StatsDashboard
      verificationData={[
        { date: 'Q1', verifications: 100, comparisons: 30 },
        { date: 'Q2', verifications: 150, comparisons: 45 },
        { date: 'Q3', verifications: 200, comparisons: 60 },
      ]}
      riskData={[
        { name: 'Bajo', value: 70, color: '#22c55e' },
        { name: 'Medio', value: 20, color: '#eab308' },
        { name: 'Alto', value: 10, color: '#ef4444' },
      ]}
      sanctionsData={[
        { entity: 'SUNAT', sanciones: 8 },
        { entity: 'OSCE', sanciones: 15 },
      ]}
      complianceData={[
        { month: 'Q1', score: 75 },
        { month: 'Q2', score: 82 },
        { month: 'Q3', score: 90 },
      ]}
    />
  ),
  name: 'Dashboard - Datos Custom',
  parameters: {
    layout: 'fullscreen',
  },
}
