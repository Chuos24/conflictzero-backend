import { useState, FormEvent, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { webhookAPI } from '../services/api'
import api from '../services/api'
import type { Webhook, WebhookDelivery, ApiKey } from '../types'
import './Settings.css'

interface PasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

const WEBHOOK_EVENTS = [
  { value: 'verification.completed', label: 'Verificación completada' },
  { value: 'score.updated', label: 'Score actualizado' },
  { value: 'supplier.changed', label: 'Proveedor cambió' },
  { value: 'alert.created', label: 'Nueva alerta' },
  { value: 'invite.registered', label: 'Invitado registrado' },
]

export default function Settings(): JSX.Element {
  const { } = useAuth()
  const [activeTab, setActiveTab] = useState<string>('password')
  const [loading, setLoading] = useState<boolean>(false)
  const [message, setMessage] = useState<string>('')

  const [passwordData, setPasswordData] = useState<PasswordData>({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyDesc, setNewKeyDesc] = useState('')
  const [createdKey, setCreatedKey] = useState<{api_key: string; name: string} | null>(null)
  const [showCreatedKey, setShowCreatedKey] = useState(false)

  // Webhooks state
  const [webhooks, setWebhooks] = useState<Webhook[]>([])
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['verification.completed'])
  const [webhookDeliveries, setWebhookDeliveries] = useState<Record<string, WebhookDelivery[]>>({})
  const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null)

  useEffect(() => {
    if (activeTab === 'webhooks') {
      loadWebhooks()
    }
  }, [activeTab])

  const loadWebhooks = async () => {
    try {
      const response = await webhookAPI.list()
      setWebhooks(response.data)
    } catch {
      setMessage('Error al cargar webhooks')
    }
  }

  const handleCreateWebhook = async (e: FormEvent) => {
    e.preventDefault()
    if (!webhookUrl.trim()) {
      setMessage('La URL del webhook es obligatoria')
      return
    }
    setLoading(true)
    try {
      await webhookAPI.create({
        url: webhookUrl,
        events: selectedEvents,
        secret: webhookSecret || undefined
      })
      setMessage('Webhook registrado correctamente')
      setWebhookUrl('')
      setWebhookSecret('')
      setSelectedEvents(['verification.completed'])
      await loadWebhooks()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al crear webhook'
      setMessage(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteWebhook = async (id: string) => {
    if (!confirm('¿Eliminar este webhook?')) return
    setLoading(true)
    try {
      await webhookAPI.delete(id)
      setMessage('Webhook eliminado')
      await loadWebhooks()
      if (expandedWebhook === id) setExpandedWebhook(null)
    } catch {
      setMessage('Error al eliminar webhook')
    } finally {
      setLoading(false)
    }
  }

  const handleTestWebhook = async (id: string) => {
    setLoading(true)
    try {
      await webhookAPI.test(id)
      setMessage('Evento de prueba enviado')
    } catch {
      setMessage('Error al enviar prueba')
    } finally {
      setLoading(false)
    }
  }

  const toggleEvent = (event: string) => {
    setSelectedEvents(prev =>
      prev.includes(event) ? prev.filter(e => e !== event) : [...prev, event]
    )
  }

  const toggleDeliveries = async (id: string) => {
    if (expandedWebhook === id) {
      setExpandedWebhook(null)
      return
    }
    setExpandedWebhook(id)
    if (!webhookDeliveries[id]) {
      try {
        const response = await webhookAPI.deliveries(id)
        setWebhookDeliveries(prev => ({ ...prev, [id]: response.data }))
      } catch {
        setMessage('Error al cargar entregas')
      }
    }
  }

  const handlePasswordChange = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage('Las contraseñas no coinciden')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      await api.post('/api/v1/auth/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      })
      setMessage('Contraseña actualizada correctamente')
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al cambiar contraseña'
      setMessage(msg)
    } finally {
      setLoading(false)
    }
  }

  const loadApiKeys = async () => {
    try {
      const response = await api.get('/api/v1/company/api-keys')
      setApiKeys(response.data.items || [])
    } catch {
      setMessage('Error al cargar API keys')
    }
  }

  const handleCreateApiKey = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    if (!newKeyName.trim()) {
      setMessage('El nombre es obligatorio')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/v1/company/api-keys', {
        name: newKeyName,
        description: newKeyDesc || undefined
      })
      setCreatedKey(response.data)
      setShowCreatedKey(true)
      setNewKeyName('')
      setNewKeyDesc('')
      setMessage('API key creada. Guárdala ahora, no se mostrará de nuevo.')
      await loadApiKeys()
    } catch (err: unknown) {
      setMessage('Error al crear API key')
    } finally {
      setLoading(false)
    }
  }

  const handleRevokeApiKey = async (id: string): Promise<void> => {
    if (!confirm('¿Revocar esta API key? Dejará de funcionar inmediatamente.')) return

    setLoading(true)
    try {
      await api.delete(`/api/v1/company/api-keys/${id}`)
      setMessage('API key revocada')
      await loadApiKeys()
    } catch {
      setMessage('Error al revocar API key')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string): void => {
    navigator.clipboard.writeText(text)
    setMessage('Copiado al portapapeles')
  }

  useEffect(() => {
    if (activeTab === 'api') {
      loadApiKeys()
    }
  }, [activeTab])

  return (
    <div className="settings-container">
      <h1>Configuración</h1>

      <div className="settings-tabs">
        <button
          className={activeTab === 'password' ? 'active' : ''}
          onClick={() => setActiveTab('password')}
        >
          Contraseña
        </button>
        <button
          className={activeTab === 'api' ? 'active' : ''}
          onClick={() => setActiveTab('api')}
        >
          API Key
        </button>
        <button
          className={activeTab === 'webhooks' ? 'active' : ''}
          onClick={() => setActiveTab('webhooks')}
        >
          Webhooks
        </button>
        <button
          className={activeTab === 'notifications' ? 'active' : ''}
          onClick={() => setActiveTab('notifications')}
        >
          Notificaciones
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      {activeTab === 'password' && (
        <div className="settings-card">
          <h2>Cambiar Contraseña</h2>
          <form onSubmit={handlePasswordChange}>
            <div className="form-group">
              <label>Contraseña Actual</label>
              <input
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Nueva Contraseña</label>
              <input
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                minLength={8}
                required
              />
            </div>
            <div className="form-group">
              <label>Confirmar Nueva Contraseña</label>
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Actualizando...' : 'Cambiar Contraseña'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'api' && (
        <div className="settings-card">
          <h2>API Keys</h2>
          <p className="description">
            Gestiona tus API keys para acceder programáticamente a Conflict Zero.
          </p>

          {showCreatedKey && createdKey && (
            <div className="api-key-created">
              <div className="api-key-display">
                <label>API Key (solo se muestra una vez):</label>
                <code className="key-value">{createdKey.api_key}</code>
                <button
                  className="btn-copy"
                  onClick={() => copyToClipboard(createdKey.api_key)}
                >
                  Copiar
                </button>
              </div>
              <button
                className="btn-small"
                onClick={() => setShowCreatedKey(false)}
              >
                Ocultar
              </button>
            </div>
          )}

          <form onSubmit={handleCreateApiKey} className="webhook-form">
            <div className="form-group">
              <label>Nombre</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Ej: Producción, Desarrollo, Zapier"
                required
              />
            </div>
            <div className="form-group">
              <label>Descripción (opcional)</label>
              <input
                type="text"
                value={newKeyDesc}
                onChange={(e) => setNewKeyDesc(e.target.value)}
                placeholder="Para qué se usará esta key"
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Creando...' : 'Crear API Key'}
            </button>
          </form>

          <h3 className="webhooks-list-title">Tus API Keys</h3>
          {apiKeys.length === 0 ? (
            <p className="empty-state">No tienes API keys registradas.</p>
          ) : (
            <ul className="webhooks-list">
              {apiKeys.map(key => (
                <li key={key.id} className="webhook-item">
                  <div className="webhook-header">
                    <div className="webhook-info">
                      <strong>{key.name}</strong>
                      <code className="webhook-url">{key.key_prefix}...</code>
                      {key.description && (
                        <span className="webhook-events">{key.description}</span>
                      )}
                      <span className="event-tag">
                        {key.usage_count} usos
                      </span>
                      {key.last_used_at && (
                        <span className="event-tag">
                          Último uso: {new Date(key.last_used_at).toLocaleDateString()}
                        </span>
                      )}
                      {key.expires_at && (
                        <span className="event-tag">
                          Expira: {new Date(key.expires_at).toLocaleDateString()}
                        </span>
                      )}
                      {!key.is_active && (
                        <span className="status-badge failed">Revocada</span>
                      )}
                    </div>
                    <div className="webhook-actions">
                      {key.is_active && (
                        <button
                          className="btn-small btn-danger"
                          onClick={() => handleRevokeApiKey(key.id)}
                          disabled={loading}
                        >
                          Revocar
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="api-docs-link">
            <a href="/docs" target="_blank" rel="noopener noreferrer">
              Ver documentación de API →
            </a>
          </div>
        </div>
      )}

      {activeTab === 'webhooks' && (
        <div className="settings-card">
          <h2>Webhooks</h2>
          <p className="description">
            Recibe notificaciones en tiempo real cuando ocurran eventos en tu cuenta.
          </p>

          <form onSubmit={handleCreateWebhook} className="webhook-form">
            <div className="form-group">
              <label>URL del Webhook</label>
              <input
                type="url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://tuservidor.com/webhook"
                required
              />
            </div>
            <div className="form-group">
              <label>Secreto (opcional, para firma HMAC)</label>
              <input
                type="text"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
                placeholder="whsec_..."
              />
            </div>
            <div className="form-group">
              <label>Eventos</label>
              <div className="events-list">
                {WEBHOOK_EVENTS.map(ev => (
                  <label key={ev.value} className="event-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(ev.value)}
                      onChange={() => toggleEvent(ev.value)}
                    />
                    {ev.label}
                  </label>
                ))}
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Registrando...' : 'Registrar Webhook'}
            </button>
          </form>

          <h3 className="webhooks-list-title">Webhooks Activos</h3>
          {webhooks.length === 0 ? (
            <p className="empty-state">No tienes webhooks registrados.</p>
          ) : (
            <ul className="webhooks-list">
              {webhooks.map(wh => (
                <li key={wh.id} className="webhook-item">
                  <div className="webhook-header">
                    <div className="webhook-info">
                      <code className="webhook-url">{wh.url}</code>
                      <span className="webhook-events">
                        {wh.events.map(e => {
                          const label = WEBHOOK_EVENTS.find(we => we.value === e)?.label || e
                          return <span key={e} className="event-tag">{label}</span>
                        })}
                      </span>
                      {wh.secret && <span className="secret-badge">🔒 HMAC</span>}
                    </div>
                    <div className="webhook-actions">
                      <button
                        className="btn-small"
                        onClick={() => handleTestWebhook(wh.id)}
                        disabled={loading}
                      >
                        Probar
                      </button>
                      <button
                        className="btn-small btn-secondary"
                        onClick={() => toggleDeliveries(wh.id)}
                      >
                        {expandedWebhook === wh.id ? 'Ocultar' : 'Entregas'}
                      </button>
                      <button
                        className="btn-small btn-danger"
                        onClick={() => handleDeleteWebhook(wh.id)}
                        disabled={loading}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                  {expandedWebhook === wh.id && (
                    <div className="webhook-deliveries">
                      {(webhookDeliveries[wh.id] || []).length === 0 ? (
                        <p className="empty-state">Sin entregas registradas.</p>
                      ) : (
                        <table className="deliveries-table">
                          <thead>
                            <tr>
                              <th>Evento</th>
                              <th>Estado</th>
                              <th>HTTP</th>
                              <th>Fecha</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(webhookDeliveries[wh.id] || []).map(d => (
                              <tr key={d.id}>
                                <td>{d.event}</td>
                                <td>
                                  <span className={`status-badge ${d.status}`}>
                                    {d.status}
                                  </span>
                                </td>
                                <td>{d.http_status || '-'}</td>
                                <td>{new Date(d.created_at).toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {activeTab === 'notifications' && (
        <div className="settings-card">
          <h2>Notificaciones</h2>
          <p className="coming-soon">Próximamente disponible</p>
        </div>
      )}
    </div>
  )
}
