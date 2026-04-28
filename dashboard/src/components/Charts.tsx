import { useEffect, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import './Charts.css'

// Colores del tema
const COLORS = ['#d4af37', '#c0c0c0', '#cd7f32', '#1a1a1a', '#8b0000']

export interface VerificationTrendsData {
  date: string
  verifications: number
  comparisons: number
}

export interface RiskDistributionData {
  name: string
  value: number
  color?: string
}

export interface SanctionsByEntityData {
  entity: string
  sanciones: number
}

export interface ComplianceHistoryData {
  month: string
  score: number
}

export interface VerificationTrendsProps {
  data?: VerificationTrendsData[]
}

/**
 * Gráfico de verificaciones por tiempo
 */
export function VerificationTrends({ data = [] }: VerificationTrendsProps): JSX.Element {
  const [chartData, setChartData] = useState<VerificationTrendsData[]>([])

  useEffect(() => {
    if (data.length === 0) {
      const sample = [
        { date: 'Ene', verifications: 12, comparisons: 3 },
        { date: 'Feb', verifications: 18, comparisons: 5 },
        { date: 'Mar', verifications: 25, comparisons: 8 },
        { date: 'Abr', verifications: 22, comparisons: 6 },
        { date: 'May', verifications: 30, comparisons: 10 },
        { date: 'Jun', verifications: 35, comparisons: 12 },
      ]
      setChartData(sample)
    } else {
      setChartData(data)
    }
  }, [data])

  return (
    <div className="chart-container">
      <h4 className="chart-title">Tendencia de Verificaciones</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="date" stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #d4af37' }}
            labelStyle={{ color: '#d4af37' }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="verifications" 
            name="Verificaciones" 
            stroke="#d4af37" 
            strokeWidth={2}
          />
          <Line 
            type="monotone" 
            dataKey="comparisons" 
            name="Comparaciones" 
            stroke="#c0c0c0" 
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export interface RiskDistributionProps {
  data?: RiskDistributionData[]
}

/**
 * Gráfico de distribución de riesgo
 */
export function RiskDistribution({ data = [] }: RiskDistributionProps): JSX.Element {
  const [chartData, setChartData] = useState<RiskDistributionData[]>([])

  useEffect(() => {
    if (data.length === 0) {
      setChartData([
        { name: 'Bajo Riesgo', value: 45, color: '#22c55e' },
        { name: 'Riesgo Medio', value: 30, color: '#eab308' },
        { name: 'Alto Riesgo', value: 18, color: '#f97316' },
        { name: 'Crítico', value: 7, color: '#ef4444' },
      ])
    } else {
      setChartData(data)
    }
  }, [data])

  return (
    <div className="chart-container">
      <h4 className="chart-title">Distribución de Riesgo</h4>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #d4af37' }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export interface SanctionsByEntityProps {
  data?: SanctionsByEntityData[]
}

/**
 * Gráfico de sanciones por entidad
 */
export function SanctionsByEntity({ data = [] }: SanctionsByEntityProps): JSX.Element {
  const [chartData, setChartData] = useState<SanctionsByEntityData[]>([])

  useEffect(() => {
    if (data.length === 0) {
      setChartData([
        { entity: 'SUNAT', sanciones: 2 },
        { entity: 'OSCE', sanciones: 5 },
        { entity: 'TCE', sanciones: 1 },
        { entity: 'INDECOPI', sanciones: 3 },
      ])
    } else {
      setChartData(data)
    }
  }, [data])

  return (
    <div className="chart-container">
      <h4 className="chart-title">Sanciones por Entidad</h4>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="entity" stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #d4af37' }}
            labelStyle={{ color: '#d4af37' }}
          />
          <Bar dataKey="sanciones" fill="#d4af37" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export interface ComplianceHistoryProps {
  data?: ComplianceHistoryData[]
}

/**
 * Gráfico de compliance score histórico
 */
export function ComplianceHistory({ data = [] }: ComplianceHistoryProps): JSX.Element {
  const [chartData, setChartData] = useState<ComplianceHistoryData[]>([])

  useEffect(() => {
    if (data.length === 0) {
      setChartData([
        { month: 'Ene', score: 72 },
        { month: 'Feb', score: 78 },
        { month: 'Mar', score: 75 },
        { month: 'Abr', score: 82 },
        { month: 'May', score: 85 },
        { month: 'Jun', score: 88 },
      ])
    } else {
      setChartData(data)
    }
  }, [data])

  return (
    <div className="chart-container">
      <h4 className="chart-title">Evolución del Compliance Score</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="month" stroke="#888" />
          <YAxis domain={[0, 100]} stroke="#888" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #d4af37' }}
            labelStyle={{ color: '#d4af37' }}
            formatter={(value: number) => [`${value}%`, 'Score']}
          />
          <Line 
            type="monotone" 
            dataKey="score" 
            stroke="#d4af37" 
            strokeWidth={3}
            dot={{ fill: '#d4af37', r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export interface StatsDashboardProps {
  verificationData?: VerificationTrendsData[]
  riskData?: RiskDistributionData[]
  sanctionsData?: SanctionsByEntityData[]
  complianceData?: ComplianceHistoryData[]
}

/**
 * Dashboard de estadísticas con múltiples gráficos
 */
export function StatsDashboard({ verificationData, riskData, sanctionsData, complianceData }: StatsDashboardProps): JSX.Element {
  return (
    <div className="stats-dashboard">
      <div className="charts-grid">
        <div className="chart-card">
          <VerificationTrends data={verificationData} />
        </div>
        <div className="chart-card">
          <RiskDistribution data={riskData} />
        </div>
        <div className="chart-card">
          <SanctionsByEntity data={sanctionsData} />
        </div>
        <div className="chart-card wide">
          <ComplianceHistory data={complianceData} />
        </div>
      </div>
    </div>
  )
}

export default StatsDashboard
