import { useState, FormEvent, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { webhookAPI } from '../services/api'
import api from '../services/api'
import type { Webhook, WebhookDelivery } from '../types'
import './Settings.css'

interface PasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

interface ApiKeyResponse {
  api_key: string
  prefix?: string
}

const WEBHOOK_EVENTS = [
  { value: 'verification.completed', label: 'Verificación completada' },
  { value: 'score.updated', label: 'Score actualizado' },
  { value: 'supplier.changed', label: 'Proveedor cambió' },
  { value: 'alert.created', label: 'Nueva alerta' },
  { value: 'invite.registered', label: 'Invitado registrado' },
]

export default function Settings(): JSX.Element {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<string>('password')
  const [loading, setLoading] = useState<boolean>(false)
  const [message, setMessage] = useState<string>('')

  const [passwordData, setPasswordData] = useState<PasswordData>({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  const [apiKey, setApiKey] = useState<ApiKeyResponse | null>(null)
  const [showApiKey, setShowApiKey] = useState<boolean>(false)

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

  const handleRegenerateApiKey = async (): Promise<void> => {
    if (!confirm('¿Estás seguro? La API key anterior dejará de funcionar.')) return

    setLoading(true)
    try {
      const response = await api.post('/api/v1/auth/regenerate-api-key')
      setApiKey(response.data)
      setShowApiKey(true)
      setMessage('API key generada. Guárdala ahora, no se mostrará de nuevo.')
    } catch (err: unknown) {
      setMessage('Error al generar API key')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string): void => {
    navigator.clipboard.writeText(text)
    setMessage('Copiado al portapapeles')
  }

  const typedUser = user as { api_key_prefix?: string } | null

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
          <h2>API Key</h2>
          <p className="description">
            Usa esta API key para acceder a nuestra API programáticamente.
          </p>

          {typedUser?.api_key_prefix && (
            <div className="current-key">
              <p>API Key actual: <code>{typedUser.api_key_prefix}...</code></p>
            </div>
          )}

          {showApiKey && apiKey && (
            <div className="api-key-display">
              <code className="key-value">{apiKey.api_key}</code>
              <button
                className="btn-copy"
                onClick={() => copyToClipboard(apiKey.api_key)}
              >
                Copiar
              </button>
            </div>
          )}

          <button
            className="btn-warning"
            onClick={handleRegenerateApiKey}
            disabled={loading}
          >
            {loading ? 'Generando...' : 'Generar Nueva API Key'}
          </button>

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
