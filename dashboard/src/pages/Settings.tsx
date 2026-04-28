import { useState, FormEvent } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
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

      {activeTab === 'notifications' && (
        <div className="settings-card">
          <h2>Notificaciones</h2>
          <p className="coming-soon">Próximamente disponible</p>
        </div>
      )}
    </div>
  )
}
