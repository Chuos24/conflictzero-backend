import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import api from '../services/api'
import type { GDPRRequest, GDPRRequestType, DataRetentionPolicy } from '../types'
import './Privacy.css'

const REQUEST_TYPE_LABELS: Record<GDPRRequestType, string> = {
  access: 'Derecho de Acceso',
  rectification: 'Derecho de Rectificación',
  erasure: 'Derecho al Olvido',
  portability: 'Derecho a la Portabilidad',
  objection: 'Derecho de Oposición',
  restriction: 'Derecho a la Limitación'
}

const REQUEST_TYPE_DESCRIPTIONS: Record<GDPRRequestType, string> = {
  access: 'Solicitar una copia de todos los datos personales que tenemos sobre ti.',
  rectification: 'Corregir datos personales inexactos o incompletos.',
  erasure: 'Solicitar la eliminación de tus datos personales (sujeto a restricciones legales).',
  portability: 'Recibir tus datos en un formato estructurado y transferirlos a otro servicio.',
  objection: 'Oponerte al procesamiento de tus datos para fines específicos.',
  restriction: 'Solicitar la limitación del procesamiento de tus datos.'
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  in_review: 'En Revisión',
  fulfilled: 'Cumplida',
  rejected: 'Rechazada',
  partially_fulfilled: 'Parcialmente Cumplida'
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'status-pending',
  in_review: 'status-review',
  fulfilled: 'status-success',
  rejected: 'status-danger',
  partially_fulfilled: 'status-warning'
}

export default function Privacy(): JSX.Element {
  const { user } = useAuth()
  const { success, error: showError } = useToast()
  const [requests, setRequests] = useState<GDPRRequest[]>([])
  const [policies, setPolicies] = useState<DataRetentionPolicy[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedType, setSelectedType] = useState<GDPRRequestType>('access')
  const [description, setDescription] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async (): Promise<void> => {
    try {
      setLoading(true)
      const [requestsRes, policiesRes] = await Promise.all([
        api.get('/api/v2/audit/gdpr/requests').catch(() => ({ data: { requests: [] } })),
        api.get('/api/v2/audit/gdpr/policies').catch(() => ({ data: { policies: [] } }))
      ])
      setRequests(requestsRes.data.requests || [])
      setPolicies(policiesRes.data.policies || [])
    } catch (err) {
      showError('Error al cargar datos de privacidad')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitRequest = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!selectedType) return

    try {
      setSubmitting(true)
      const res = await api.post(`/api/v2/audit/gdpr/requests?request_type=${selectedType}&description=${encodeURIComponent(description)}`)
      success('Solicitud creada exitosamente')
      setRequests(prev => [res.data.request, ...prev])
      setShowForm(false)
      setDescription('')
    } catch (err) {
      showError('Error al crear la solicitud')
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleExportData = async (): Promise<void> => {
    try {
      const res = await api.get('/api/v2/audit/gdpr/export', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `gdpr-export-${user?.id || 'user'}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      success('Datos exportados exitosamente')
    } catch (err) {
      showError('Error al exportar datos')
      console.error(err)
    }
  }

  const handleRequestErasure = async (): Promise<void> => {
    if (!window.confirm('¿Estás seguro de solicitar el borrado de tus datos? Esta acción iniciará un proceso de validación legal.')) {
      return
    }
    try {
      const res = await api.delete('/api/v2/audit/gdpr/erase')
      if (res.data.status === 'rejected') {
        showError(`Solicitud rechazada: ${res.data.reasons?.join(', ')}`)
      } else {
        success('Solicitud de borrado enviada. Será procesada en un máximo de 30 días.')
      }
    } catch (err) {
      showError('Error al solicitar borrado')
      console.error(err)
    }
  }

  if (loading) return <div className="privacy-loading">Cargando...</div>

  return (
    <div className="privacy-container">
      <h1>Privacidad y Protección de Datos</h1>
      <p className="privacy-subtitle">
        Gestiona tus derechos sobre datos personales conforme al GDPR y la Ley 29733 de Perú.
      </p>

      {/* Actions */}
      <div className="privacy-actions">
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancelar' : 'Nueva Solicitud'}
        </button>
        <button className="btn-secondary" onClick={handleExportData}>
          📥 Exportar Mis Datos
        </button>
        <button className="btn-danger" onClick={handleRequestErasure}>
          🗑️ Solicitar Borrado
        </button>
      </div>

      {/* Request Form */}
      {showForm && (
        <form className="request-form" onSubmit={handleSubmitRequest}>
          <h3>Nueva Solicitud GDPR</h3>
          <div className="form-group">
            <label>Tipo de Solicitud</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as GDPRRequestType)}
              className="form-select"
            >
              {Object.entries(REQUEST_TYPE_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
            <p className="form-help">{REQUEST_TYPE_DESCRIPTIONS[selectedType]}</p>
          </div>
          <div className="form-group">
            <label>Descripción (opcional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe los detalles de tu solicitud..."
              rows={3}
              className="form-textarea"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Enviando...' : 'Enviar Solicitud'}
            </button>
          </div>
        </form>
      )}

      {/* Requests List */}
      <div className="requests-section">
        <h2>Mis Solicitudes</h2>
        {requests.length === 0 ? (
          <div className="empty-state">
            <p>No has realizado ninguna solicitud de privacidad.</p>
          </div>
        ) : (
          <div className="requests-table-wrapper">
            <table className="requests-table">
              <thead>
                <tr>
                  <th>Número</th>
                  <th>Tipo</th>
                  <th>Estado</th>
                  <th>Solicitada</th>
                  <th>Vencimiento</th>
                  <th>Días Restantes</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id} className={req.is_overdue ? 'overdue' : ''}>
                    <td className="mono">{req.request_number}</td>
                    <td>{REQUEST_TYPE_LABELS[req.request_type] || req.request_type}</td>
                    <td>
                      <span className={`status-badge ${STATUS_COLORS[req.status] || ''}`}>
                        {STATUS_LABELS[req.status] || req.status}
                      </span>
                    </td>
                    <td>{new Date(req.requested_at).toLocaleDateString()}</td>
                    <td>{new Date(req.due_at).toLocaleDateString()}</td>
                    <td>
                      {req.is_overdue ? (
                        <span className="text-danger">Vencida</span>
                      ) : (
                        <span className="text-muted">{req.days_remaining ?? '-'} días</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Data Retention Policies */}
      {policies.length > 0 && (
        <div className="policies-section">
          <h2>Políticas de Retención de Datos</h2>
          <div className="policies-grid">
            {policies.map((policy) => (
              <div key={policy.data_type} className="policy-card">
                <h4>{policy.description}</h4>
                <div className="policy-meta">
                  <span className="policy-retention">
                    ⏱️ {Math.floor(policy.retention_days / 365)} años
                  </span>
                  <span className="policy-basis">
                    📋 {policy.legal_basis}
                  </span>
                </div>
                <div className="policy-tags">
                  {policy.allow_anonymization && (
                    <span className="tag tag-anon">Anonimizable</span>
                  )}
                  {policy.requires_manual_approval && (
                    <span className="tag tag-manual">Requiere Aprobación</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
