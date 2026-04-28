import { useState, useEffect, FormEvent } from 'react'
import { useAuth } from '../context/AuthContext'
import './Invites.css'

interface InviteItem {
  id: string
  email: string
  company_name: string
  status: string
  created_at: string
}

interface InviteStatsData {
  total_sent: number
  accepted: number
  pending: number
  conversion_rate: number
}

interface InviteFormData {
  email: string
  company_name: string
  message: string
}

function Invites(): JSX.Element {
  const { user } = useAuth()
  const [invites, setInvites] = useState<InviteItem[]>([])
  const [stats, setStats] = useState<InviteStatsData>({
    total_sent: 0,
    accepted: 0,
    pending: 0,
    conversion_rate: 0
  })
  const [loading, setLoading] = useState<boolean>(true)
  const [showForm, setShowForm] = useState<boolean>(false)
  const [formData, setFormData] = useState<InviteFormData>({
    email: '',
    company_name: '',
    message: ''
  })
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')

  useEffect(() => {
    fetchInvites()
    fetchStats()
  }, [])

  const fetchInvites = async (): Promise<void> => {
    try {
      const response = await fetch('/api/v2/invites', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cz_token')}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setInvites(data.invites || [])
      }
    } catch (err) {
      console.error('Error fetching invites:', err)
    }
  }

  const fetchStats = async (): Promise<void> => {
    try {
      const response = await fetch('/api/v2/invites/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cz_token')}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Error fetching stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      const response = await fetch('/api/v2/invites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('cz_token')}`
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setSuccess('Invitación enviada exitosamente')
        setFormData({ email: '', company_name: '', message: '' })
        setShowForm(false)
        fetchInvites()
        fetchStats()
      } else {
        const data = await response.json()
        setError(data.detail || 'Error al enviar invitación')
      }
    } catch (err) {
      setError('Error de conexión')
    }
  }

  const handleResend = async (inviteId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/v2/invites/${inviteId}/resend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('cz_token')}`
        }
      })

      if (response.ok) {
        setSuccess('Invitación reenviada')
        fetchInvites()
      }
    } catch (err) {
      setError('Error al reenviar')
    }
  }

  const getStatusBadge = (status: string): JSX.Element => {
    const statusConfig: Record<string, { class: string; label: string }> = {
      pending: { class: 'status-pending', label: 'Pendiente' },
      accepted: { class: 'status-accepted', label: 'Aceptada' },
      expired: { class: 'status-expired', label: 'Expirada' }
    }
    const config = statusConfig[status] || statusConfig.pending
    return <span className={`status-badge ${config.class}`}>{config.label}</span>
  }

  if (loading) {
    return <div className="loading">Cargando...</div>
  }

  return (
    <div className="invites-page">
      <div className="page-header">
        <h1>Sistema de Invitaciones</h1>
        <p>Invita a otras constructoras y expande tu red de confianza</p>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon">📧</div>
          <div className="stat-info">
            <span className="stat-value">{stats.total_sent}</span>
            <span className="stat-label">Invitaciones Enviadas</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-info">
            <span className="stat-value">{stats.accepted}</span>
            <span className="stat-label">Aceptadas</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-info">
            <span className="stat-value">{stats.pending}</span>
            <span className="stat-label">Pendientes</span>
          </div>
        </div>
        <div className="stat-card highlight">
          <div className="stat-icon">📈</div>
          <div className="stat-info">
            <span className="stat-value">{stats.conversion_rate}%</span>
            <span className="stat-label">Tasa de Conversión</span>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="invites-actions">
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nueva Invitación'}
        </button>
      </div>

      {showForm && (
        <div className="invite-form-card">
          <h3>Nueva Invitación</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="contacto@empresa.com"
                  required
                />
              </div>
              <div className="form-group">
                <label>Nombre de la Empresa</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  placeholder="Constructora Ejemplo S.A.C."
                  required
                />
              </div>
            </div>
            <div className="form-group">
              <label>Mensaje Personalizado (opcional)</label>
              <textarea
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                placeholder="Hola, te invito a unirte a Conflict Zero..."
                rows={3}
              />
            </div>
            <button type="submit" className="btn btn-primary">
              Enviar Invitación
            </button>
          </form>
        </div>
      )}

      <div className="invites-list-card">
        <h3>Historial de Invitaciones</h3>
        {invites.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No has enviado invitaciones aún</p>
            <span>Invita a tus socios comerciales a unirse</span>
          </div>
        ) : (
          <table className="invites-table">
            <thead>
              <tr>
                <th>Empresa</th>
                <th>Email</th>
                <th>Estado</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {invites.map((invite) => (
                <tr key={invite.id}>
                  <td>{invite.company_name}</td>
                  <td>{invite.email}</td>
                  <td>{getStatusBadge(invite.status)}</td>
                  <td>{new Date(invite.created_at).toLocaleDateString('es-PE')}</td>
                  <td>
                    {invite.status === 'pending' && (
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleResend(invite.id)}
                      >
                        Reenviar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {user?.plan_tier === 'founder' && (
        <div className="founder-notice">
          <div className="notice-icon">⭐</div>
          <div className="notice-content">
            <h4>Programa Founder Activo</h4>
            <p>Como Founder, tienes la obligación contractual de invitar a tus subcontratistas. Cada invitación cuenta para tu red de confianza.</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Invites
