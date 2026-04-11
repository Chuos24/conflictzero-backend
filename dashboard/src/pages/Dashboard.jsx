import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts'
import './Dashboard.css'

const COLORS = ['#d4af37', '#4caf50', '#f44336', '#2196f3', '#ff9800']

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [recentActivity, setRecentActivity] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, chartRes, activityRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/chart-data'),
        api.get('/dashboard/activity')
      ])
      setStats(statsRes.data)
      setChartData(chartRes.data)
      setRecentActivity(activityRes.data || [])
    } catch (err) {
      console.error('Error fetching dashboard:', err)
      // Use mock data if API fails
      setChartData({
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
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
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