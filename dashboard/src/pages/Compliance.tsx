import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import './Compliance.css'

interface ComplianceData {
  status: string
  description: string
  contractual_obligation?: boolean
  contractual_signed_at?: string
  founder_expires_at?: string
}

interface ObligationsData {
  invites_sent: number
  invites_converted: number
  conversion_rate: number
  estimated_commission: number
  required_invites: number
}

interface NetworkInvite {
  id: string
  email: string
  status: string
  created_at: string
}

interface NetworkData {
  total_invited: number
  total_paid: number
  network_depth: number
  recent_invites?: NetworkInvite[]
}

export default function Compliance(): JSX.Element {
  const { user } = useAuth()
  const [compliance, setCompliance] = useState<ComplianceData | null>(null)
  const [obligations, setObligations] = useState<ObligationsData | null>(null)
  const [network, setNetwork] = useState<NetworkData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    fetchComplianceData()
  }, [])

  const fetchComplianceData = async (): Promise<void> => {
    try {
      setLoading(true)
      const [complianceRes, obligationsRes, networkRes] = await Promise.all([
        api.get('/api/v2/founder/compliance'),
        api.get('/api/v2/founder/obligations'),
        api.get('/api/v2/founder/network')
      ])

      setCompliance(complianceRes.data)
      setObligations(obligationsRes.data)
      setNetwork(networkRes.data)
    } catch (err) {
      setError('Error al cargar datos de compliance')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'cumpliendo': 'success',
      'en_riesgo': 'warning',
      'riesgo_inminente': 'danger',
      'sin_obligacion': 'neutral'
    }
    return colors[status] || 'neutral'
  }

  if (loading) return <div className="compliance-loading">Cargando...</div>
  if (error) return <div className="compliance-error">{error}</div>

  return (
    <div className="compliance-container">
      <h1>Compliance de Founder</h1>

      {!user?.is_founder && (
        <div className="not-founder-alert">
          <p>No eres parte del programa Founder. Aplica para acceder a beneficios exclusivos.</p>
          <button className="btn-primary">Aplicar a Founder</button>
        </div>
      )}

      {compliance && (
        <div className="compliance-status-card">
          <h2>Estado de Cumplimiento</h2>
          <div className={`status-badge ${getStatusColor(compliance.status)}`}>
            {compliance.status}
          </div>
          <p className="status-description">{compliance.description}</p>

          {compliance.contractual_obligation && (
            <div className="obligation-details">
              <h3>Obligación Contractual</h3>
              <p>Firmada: {compliance.contractual_signed_at ? new Date(compliance.contractual_signed_at).toLocaleDateString() : 'N/A'}</p>
              <p>Expira: {compliance.founder_expires_at ? new Date(compliance.founder_expires_at).toLocaleDateString() : 'N/A'}</p>
            </div>
          )}
        </div>
      )}

      {obligations && (
        <div className="obligations-card">
          <h2>Obligaciones Mensuales</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-value">{obligations.invites_sent}</span>
              <span className="metric-label">Invitaciones Enviadas</span>
            </div>
            <div className="metric">
              <span className="metric-value">{obligations.invites_converted}</span>
              <span className="metric-label">Convertidas</span>
            </div>
            <div className="metric">
              <span className="metric-value">{obligations.conversion_rate}%</span>
              <span className="metric-label">Tasa de Conversión</span>
            </div>
            <div className="metric">
              <span className="metric-value">S/{obligations.estimated_commission}</span>
              <span className="metric-label">Comisión Estimada</span>
            </div>
          </div>

          {obligations.required_invites > 0 && (
            <div className="progress-section">
              <p>Progreso hacia meta mensual</p>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min((obligations.invites_converted / obligations.required_invites) * 100, 100)}%` }}
                />
              </div>
              <p className="progress-text">
                {obligations.invites_converted} de {obligations.required_invites} invitados convertidos
              </p>
            </div>
          )}
        </div>
      )}

      {network && (
        <div className="network-card">
          <h2>Tu Red de Invitados</h2>
          <div className="network-stats">
            <div className="stat">
              <span className="stat-value">{network.total_invited}</span>
              <span className="stat-label">Total Invitados</span>
            </div>
            <div className="stat">
              <span className="stat-value">{network.total_paid}</span>
              <span className="stat-label">Convertidos a Pagado</span>
            </div>
            <div className="stat">
              <span className="stat-value">{network.network_depth}</span>
              <span className="stat-label">Profundidad de Red</span>
            </div>
          </div>

          {network.recent_invites && network.recent_invites.length > 0 && (
            <div className="recent-invites">
              <h3>Invitaciones Recientes</h3>
              <table className="invites-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {network.recent_invites.map(invite => (
                    <tr key={invite.id}>
                      <td>{invite.email}</td>
                      <td>
                        <span className={`status-tag ${invite.status}`}>
                          {invite.status}
                        </span>
                      </td>
                      <td>{new Date(invite.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
