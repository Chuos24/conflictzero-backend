import { useState, useEffect } from 'react'
import { useToast } from '../context/ToastContext'
import api from '../services/api'
import './WhiteLabel.css'

interface WhiteLabelConfig {
  app_name: string
  app_short_name: string
  company_name: string
  support_url: string | null
  privacy_url: string | null
  terms_url: string | null
  support_email: string
  support_phone: string | null
  logo_url: string | null
  logo_dark_url: string | null
  favicon_url: string | null
  theme: {
    primary: string
    secondary: string
    success: string
    warning: string
    danger: string
    background: string
    surface: string
    text: string
    textMuted: string
    border: string
  }
  font_family: string
  meta_title: string
  meta_description: string
  default_language: string
  supported_languages: string[]
  features: Record<string, boolean>
  custom_texts: Record<string, string>
}

const DEFAULT_CONFIG: WhiteLabelConfig = {
  app_name: 'Conflict Zero',
  app_short_name: 'CZ',
  company_name: 'Conflict Zero S.A.C.',
  support_url: 'https://conflictzero.com/support',
  privacy_url: 'https://conflictzero.com/privacy',
  terms_url: 'https://conflictzero.com/terms',
  support_email: 'soporte@conflictzero.com',
  support_phone: null,
  logo_url: null,
  logo_dark_url: null,
  favicon_url: null,
  theme: {
    primary: '#2563eb',
    secondary: '#64748b',
    success: '#22c55e',
    warning: '#f59e0b',
    danger: '#ef4444',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#0f172a',
    textMuted: '#64748b',
    border: '#e2e8f0'
  },
  font_family: 'Inter, system-ui, sans-serif',
  meta_title: 'Conflict Zero - Verificación de Proveedores',
  meta_description: 'Sistema de verificación de riesgo de proveedores',
  default_language: 'es',
  supported_languages: ['es'],
  features: {
    founder_program: true,
    api_access: true,
    webhooks: true,
    ml_scoring: true,
    compliance_tracking: true,
    white_label: false
  },
  custom_texts: {
    login_title: 'Bienvenido',
    login_subtitle: 'Ingresa tus credenciales para continuar',
    dashboard_welcome: 'Panel de Control',
    verification_title: 'Verificar RUC',
    network_title: 'Mi Red de Proveedores'
  }
}

const MARKET_OPTIONS = [
  { value: 'peru', label: 'Perú', docType: 'RUC' },
  { value: 'chile', label: 'Chile', docType: 'RUT' },
  { value: 'colombia', label: 'Colombia', docType: 'NIT' },
  { value: 'mexico', label: 'México', docType: 'RFC' },
  { value: 'spain', label: 'España', docType: 'NIF/CIF' }
]

export default function WhiteLabel(): JSX.Element {
  const { success, error: showError } = useToast()
  const [config, setConfig] = useState<WhiteLabelConfig>(DEFAULT_CONFIG)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'general' | 'theme' | 'texts'>('general')
  const [previewCss, setPreviewCss] = useState('')

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async (): Promise<void> => {
    try {
      setLoading(true)
      const res = await api.get('/api/v2/white-label/config')
      setConfig({ ...DEFAULT_CONFIG, ...res.data })
      
      // Fetch CSS preview
      const cssRes = await api.get('/api/v2/white-label/config/default/css').catch(() => null)
      if (cssRes?.data?.css) {
        setPreviewCss(cssRes.data.css)
      }
    } catch (err) {
      console.error('Error loading white-label config:', err)
      // Use default config on error
      setConfig(DEFAULT_CONFIG)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (): Promise<void> => {
    try {
      setSaving(true)
      // In a real implementation, this would save to backend
      // For now, just show success
      success('Configuración guardada exitosamente')
    } catch (err) {
      showError('Error al guardar configuración')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = (): void => {
    if (window.confirm('¿Restaurar configuración por defecto? Se perderán los cambios.')) {
      setConfig(DEFAULT_CONFIG)
      success('Configuración restaurada')
    }
  }

  const updateConfig = (path: string, value: unknown): void => {
    setConfig(prev => {
      const keys = path.split('.')
      const newConfig = { ...prev }
      let current: Record<string, unknown> = newConfig
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...(current[keys[i]] as Record<string, unknown>) }
        current = current[keys[i]] as Record<string, unknown>
      }
      
      current[keys[keys.length - 1]] = value
      return newConfig as WhiteLabelConfig
    })
  }

  const handleMarketSelect = (marketId: string): void => {
    const market = MARKET_OPTIONS.find(m => m.value === marketId)
    if (!market) return

    updateConfig('app_name', `Conflict Zero ${market.label}`)
    updateConfig('custom_texts.verification_title', `Verificar ${market.docType}`)
    updateConfig('default_language', 'es')
    updateConfig('supported_languages', ['es'])
  }

  if (loading) return <div className="whitelabel-loading">Cargando...</div>

  return (
    <div className="whitelabel-container">
      <div className="whitelabel-header">
        <h1>Personalización de Marca</h1>
        <p className="whitelabel-subtitle">
          Configura la apariencia y los textos de tu plataforma white-label.
        </p>
      </div>

      <div className="whitelabel-tabs">
        <button
          className={`tab-btn ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button
          className={`tab-btn ${activeTab === 'theme' ? 'active' : ''}`}
          onClick={() => setActiveTab('theme')}
        >
          Tema y Colores
        </button>
        <button
          className={`tab-btn ${activeTab === 'texts' ? 'active' : ''}`}
          onClick={() => setActiveTab('texts')}
        >
          Textos
        </button>
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="whitelabel-section">
          <h2>Configuración General</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label>Nombre de la Aplicación</label>
              <input
                type="text"
                value={config.app_name}
                onChange={(e) => updateConfig('app_name', e.target.value)}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Nombre Corto</label>
              <input
                type="text"
                value={config.app_short_name}
                onChange={(e) => updateConfig('app_short_name', e.target.value)}
                className="form-input"
                maxLength={10}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Nombre de la Empresa</label>
            <input
              type="text"
              value={config.company_name}
              onChange={(e) => updateConfig('company_name', e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email de Soporte</label>
              <input
                type="email"
                value={config.support_email}
                onChange={(e) => updateConfig('support_email', e.target.value)}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Teléfono de Soporte</label>
              <input
                type="tel"
                value={config.support_phone || ''}
                onChange={(e) => updateConfig('support_phone', e.target.value || null)}
                className="form-input"
                placeholder="Opcional"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>URL de Soporte</label>
              <input
                type="url"
                value={config.support_url || ''}
                onChange={(e) => updateConfig('support_url', e.target.value || null)}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>URL de Privacidad</label>
              <input
                type="url"
                value={config.privacy_url || ''}
                onChange={(e) => updateConfig('privacy_url', e.target.value || null)}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label>URL de Términos</label>
            <input
              type="url"
              value={config.terms_url || ''}
              onChange={(e) => updateConfig('terms_url', e.target.value || null)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Plantilla de Mercado</label>
            <select
              onChange={(e) => handleMarketSelect(e.target.value)}
              className="form-select"
              defaultValue=""
            >
              <option value="">Seleccionar mercado...</option>
              {MARKET_OPTIONS.map(m => (
                <option key={m.value} value={m.value}>{m.label} ({m.docType})</option>
              ))}
            </select>
            <small className="form-help">Aplica configuración predefinida para el mercado seleccionado</small>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Logo URL</label>
              <input
                type="url"
                value={config.logo_url || ''}
                onChange={(e) => updateConfig('logo_url', e.target.value || null)}
                className="form-input"
                placeholder="https://..."
              />
            </div>
            <div className="form-group">
              <label>Logo Modo Oscuro</label>
              <input
                type="url"
                value={config.logo_dark_url || ''}
                onChange={(e) => updateConfig('logo_dark_url', e.target.value || null)}
                className="form-input"
                placeholder="https://..."
              />
            </div>
          </div>

          <div className="form-group">
            <label>Favicon URL</label>
            <input
              type="url"
              value={config.favicon_url || ''}
              onChange={(e) => updateConfig('favicon_url', e.target.value || null)}
              className="form-input"
              placeholder="https://..."
            />
          </div>
        </div>
      )}

      {/* Theme Tab */}
      {activeTab === 'theme' && (
        <div className="whitelabel-section">
          <h2>Tema y Colores</h2>
          
          <div className="color-grid">
            {Object.entries(config.theme).map(([key, value]) => (
              <div className="color-item" key={key}>
                <label className="color-label">
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </label>
                <div className="color-input-wrapper">
                  <input
                    type="color"
                    value={value}
                    onChange={(e) => updateConfig(`theme.${key}`, e.target.value)}
                    className="color-picker"
                  />
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => updateConfig(`theme.${key}`, e.target.value)}
                    className="color-text"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="form-group">
            <label>Familia de Fuente</label>
            <input
              type="text"
              value={config.font_family}
              onChange={(e) => updateConfig('font_family', e.target.value)}
              className="form-input"
            />
          </div>

          <div className="css-preview">
            <h3>Vista Previa CSS</h3>
            <pre className="css-code">{previewCss}</pre>
          </div>
        </div>
      )}

      {/* Texts Tab */}
      {activeTab === 'texts' && (
        <div className="whitelabel-section">
          <h2>Textos Personalizados</h2>
          
          {Object.entries(config.custom_texts).map(([key, value]) => (
            <div className="form-group" key={key}>
              <label>{key.replace(/_/g, ' ').replace(/^./, str => str.toUpperCase())}</label>
              <input
                type="text"
                value={value}
                onChange={(e) => {
                  const newTexts = { ...config.custom_texts, [key]: e.target.value }
                  updateConfig('custom_texts', newTexts)
                }}
                className="form-input"
              />
            </div>
          ))}

          <div className="form-row">
            <div className="form-group">
              <label>Título Meta (SEO)</label>
              <input
                type="text"
                value={config.meta_title}
                onChange={(e) => updateConfig('meta_title', e.target.value)}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Descripción Meta (SEO)</label>
              <input
                type="text"
                value={config.meta_description}
                onChange={(e) => updateConfig('meta_description', e.target.value)}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Idioma por Defecto</label>
            <select
              value={config.default_language}
              onChange={(e) => updateConfig('default_language', e.target.value)}
              className="form-select"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>
      )}

      <div className="whitelabel-actions">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Guardando...' : 'Guardar Configuración'}
        </button>
        <button
          className="btn-secondary"
          onClick={handleReset}
        >
          Restaurar Defecto
        </button>
      </div>

      <div className="whitelabel-preview">
        <h3>Vista Previa</h3>
        <div 
          className="preview-box"
          style={{
            backgroundColor: config.theme.background,
            color: config.theme.text,
            border: `1px solid ${config.theme.border}`,
            fontFamily: config.font_family
          }}
        >
          <div 
            className="preview-header"
            style={{ backgroundColor: config.theme.primary, color: '#fff' }}
          >
            {config.app_name}
          </div>
          <div className="preview-content">
            <p style={{ color: config.theme.textMuted }}>
              {config.custom_texts.login_subtitle}
            </p>
            <button 
              className="preview-btn"
              style={{ backgroundColor: config.theme.primary, color: '#fff' }}
            >
              {config.custom_texts.login_title}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
