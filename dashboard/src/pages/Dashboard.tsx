import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useDashboardStats, useMLScore } from '../hooks/useQueries'
import LoadingSpinner from '../components/LoadingSpinner'
import Badge from '../components/Badge'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import './Dashboard.css'

interface ChartDataPoint {
  month: string
  count: number
  score: number
}

interface ComplianceDistributionItem {
  name: string
  value: number
  color: string
}

interface RiskFactorItem {
  factor: string
  count: number
}

interface DefaultChartData {
  verificationsByMonth: ChartDataPoint[]
  complianceDistribution: ComplianceDistributionItem[]
  topRiskFactors: RiskFactorItem[]
}

interface ActivityItem {
  title: string
  status: string
  date: string
  ruc?: string
}

// Mock chart data (server-side rendering fallback)
const defaultChartData: DefaultChartData = {
  verificationsByMonth: [
    { month: 'Ene', count: 12, score: 78 },
    { month: 'Feb', count: 18, score: 82 },
    { month: 'Mar', count: 25, score: 85 },
    { month: 'Abr', count: 32, score: 88 }
  ],
  complianceDistribution: [
    { name: 'Compliant', value: 75, color: '#4caf50' },
    { name: 'Warning', value: 15, color: '#ff9800' },
    { name: 'Critical', value: 10, color: '#f44336' }
  ],
  topRiskFactors: [
    { factor: 'OSCE Sanciones', count: 5 },
    { factor: 'TCE Sanciones', count: 3 },
    { factor: 'Deuda Tributaria', count: 2 },
    { factor: 'Indecopi', count: 1 }
  ]
}

function Dashboard(): JSX.Element {
  const { user } = useAuth()
  const { data: stats, isLoading } = useDashboardStats()

  // Tomar el RUC de la última verificación para mostrar ML Score
  const lastRuc = (stats?.recent_activity?.[0] as ActivityItem & { ruc?: string })?.ruc || null
  const { data: mlScore } = useMLScore(lastRuc, 90)

  // Use server data when available, fallback to mock
  const chartData: DefaultChartData = stats?.chart_data || defaultChartData
  const recentActivity: ActivityItem[] = stats?.recent_activity || []

  if (isLoading) {
    return (
      <div className="dashboard-loading">
        <LoadingSpinner size="large" text="Cargando dashboard..." />
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Bienvenido, {user?.company_name}</h1>
          <p className="dashboard-subtitle">
            {user?.plan_tier === 'founder'
              ? 'Programa Founder - Acceso completo'
              : `Plan ${user?.plan_tier || 'Bronze'}`}
          </p>
        </div>
        <div className="dashboard-actions">
          <Link to="/compare" className="btn-primary">
            Comparar Empresas
          </Link>
          <Link to="/verifications" className="btn-secondary">
            Nueva Verificación
          </Link>
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">✓</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.verifications_count || 0}</span>
            <span className="stat-label">Verificaciones</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⚖️</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.comparisons_count || 0}</span>
            <span className="stat-label">Comparaciones</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📧</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.invites_sent || 0}</span>
            <span className="stat-label">Invitaciones Enviadas</span>
          </div>
        </div>

        <div className="stat-card highlight">
          <div className="stat-icon">🛡️</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.compliance_score || 85}%</span>
            <span className="stat-label">Score Compliance</span>
          </div>
        </div>
      </div>

      {/* ML Score Summary */}
      {lastRuc && mlScore && (
        <div className="ml-score-summary">
          <div className="ml-summary-header">
            <h3>ML Score de Riesgo Predictivo</h3>
            <Badge variant="default" size="small">v{mlScore.model_version}</Badge>
          </div>
          <div className="ml-summary-content">
            <div className="ml-summary-item">
              <span className="ml-summary-ruc">{lastRuc}</span>
              <div className="ml-summary-score">
                <span
                  className="ml-score-value"
                  style={{
                    color: mlScore.risk_level === 'low' ? '#22c55e' :
                           mlScore.risk_level === 'moderate' ? '#eab308' :
                           mlScore.risk_level === 'high' ? '#f97316' : '#ef4444'
                  }}
                >
                  {mlScore.ml_score}
                </span>
                <span className="ml-score-label">/100</span>
              </div>
              <Badge
                variant={
                  mlScore.risk_level === 'low' ? 'success' :
                  mlScore.risk_level === 'moderate' ? 'warning' :
                  mlScore.risk_level === 'high' ? 'error' : 'error'
                }
                size="small"
              >
                {mlScore.risk_level === 'low' ? 'Bajo Riesgo' :
                 mlScore.risk_level === 'moderate' ? 'Riesgo Moderado' :
                 mlScore.risk_level === 'high' ? 'Alto Riesgo' : 'Riesgo Crítico'}
              </Badge>
            </div>
            {mlScore.explanation?.[0] && (
              <p className="ml-summary-insight">{mlScore.explanation[0]}</p>
            )}
            <Link to="/verifications" className="ml-summary-link">
              Ver análisis completo →
            </Link>
          </div>
        </div>
      )}

      {/* Charts Section */}
      {chartData && (
        <div className="charts-grid">
          <div className="chart-card">
            <h3>Tendencia de Verificaciones</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={chartData.verificationsByMonth}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d4af37" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#d4af37" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="month" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#d4af37' }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#d4af37"
                  fillOpacity={1}
                  fill="url(#colorCount)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Distribución de Compliance</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={chartData.complianceDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {chartData.complianceDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card wide">
            <h3>Factores de Riesgo Principales</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData.topRiskFactors} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" stroke="#888" />
                <YAxis dataKey="factor" type="category" stroke="#888" width={120} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#d4af37' }}
                />
                <Bar dataKey="count" fill="#d4af37" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>Verificaciones Recientes</h3>
          {recentActivity.length > 0 ? (
            <div className="activity-list">
              {recentActivity.slice(0, 5).map((activity, idx) => (
                <div key={idx} className="activity-item">
                  <div className={`activity-status status-${activity.status}`}></div>
                  <div className="activity-info">
                    <span className="activity-title">{activity.title}</span>
                    <span className="activity-date">{activity.date}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No hay verificaciones recientes</p>
              <Link to="/verifications" className="link-action">
                Realizar primera verificación
              </Link>
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <h3>Estado de Compliance</h3>
          <div className="compliance-summary">
            <div className="compliance-item">
              <span className="compliance-name">SUNAT</span>
              <span className="compliance-status ok">✓ Al día</span>
            </div>
            <div className="compliance-item">
              <span className="compliance-name">OSCE</span>
              <span className="compliance-status ok">✓ Al día</span>
            </div>
            <div className="compliance-item">
              <span className="compliance-name">TCE</span>
              <span className="compliance-status warning">⚠ Pendiente</span>
            </div>
            <div className="compliance-item">
              <span className="compliance-name">INDECOPI</span>
              <span className="compliance-status ok">✓ Al día</span>
            </div>
          </div>
          <Link to="/compliance" className="card-action">
            Ver detalles completos →
          </Link>
        </div>

        <div className="dashboard-card wide">
          <h3>Red de Invitaciones</h3>
          <div className="invites-progress">
            <div className="progress-header">
              <span>Progreso hacia el siguiente tier</span>
              <span>{stats?.invites_accepted || 0}/10 invitaciones</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min((stats?.invites_accepted || 0) / 10 * 100, 100)}%` }}
              ></div>
            </div>
            <p className="progress-hint">
              Invita a 10 empresas y desbloquea el tier Silver con descuentos exclusivos.
            </p>
          </div>
          <div className="invites-actions">
            <Link to="/invites" className="btn-outline">
              Enviar Invitaciones
            </Link>
            <Link to="/invites" className="link-action">
              Ver estadísticas →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
