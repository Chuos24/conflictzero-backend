import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import './Verifications.css'

function Verifications() {
  const { user } = useAuth()
  const [ruc, setRuc] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')

  // Cargar historial al montar
  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('cz_token')
      const response = await fetch('/api/v1/verify/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setHistory(data.items || [])
      }
    } catch (err) {
      console.error('Error cargando historial:', err)
    }
  }

  const handleVerify = async (e) => {
    e.preventDefault()
    if (ruc.length !== 11) {
      setError('El RUC debe tener 11 dígitos')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)

    try {
      const token = localStorage.getItem('cz_token')
      const response = await fetch('/api/v1/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ruc })
      })

      const data = await response.json()

      if (response.ok) {
        setResults({
          ...data,
          ruc: ruc,
          company_name: data.target_company_name
        })
        fetchHistory() // Actualizar historial
      } else {
        setError(data.detail || 'Error al verificar')
      }
    } catch (err) {
      setError('Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'low': return 'success'
      case 'medium': return 'warning'
      case 'high': return 'danger'
      case 'critical': return 'critical'
      default: return 'neutral'
    }
  }

  const getRiskLabel = (level) => {
    switch (level) {
      case 'low': return 'Bajo'
      case 'medium': return 'Medio'
      case 'high': return 'Alto'
      case 'critical': return 'Crítico'
      default: return 'Desconocido'
    }
  }

  return (
    <div className="verifications-page">
      <header className="page-header">
        <h1>Verificaciones</h1>
        <p className="subtitle">
          Consulta el riesgo de empresas en tiempo real
        </p>
      </header>

      <div className="verifications-grid">
        {/* Formulario de búsqueda */}
        <div className="verify-card">
          <h2>Nueva Verificación</h2>
          <form onSubmit={handleVerify}>
            <div className="search-box">
              <input
                type="text"
                value={ruc}
                onChange={(e) => setRuc(e.target.value.replace(/\D/g, ''))}
                placeholder="Ingresa el RUC (11 dígitos)"
                maxLength={11}
                className="ruc-input"
              />
              <button
                type="submit"
                className="verify-btn"
                disabled={loading || ruc.length !== 11}
              >
                {loading ? 'Verificando...' : 'Verificar'}
              </button>
            </div>
            {error && <div className="error-text">{error}</div>}
          </form>

          {/* Resultados */}
          {results && (
            <div className={`results-card ${getRiskColor(results.risk_level)}`}>
              <div className="result-header">
                <h3>{results.company_name}</h3>
                <span className={`risk-badge ${getRiskColor(results.risk_level)}`}>
                  {getRiskLabel(results.risk_level)}
                </span>
              </div>
              <div className="result-score">
                <div className="score-circle">
                  <span className="score-value">{results.score}</span>
                  <span className="score-label">/100</span>
                </div>
                <div className="score-legend">
                  {results.score >= 80 ? '✅ Excelente' :
                   results.score >= 60 ? '⚠️ Regular' :
                   results.score >= 40 ? '❌ Riesgoso' : '🚨 Crítico'}
                </div>
              </div>
              <div className="result-details">
                <div className="detail-row">
                  <span>RUC:</span>
                  <span>{results.ruc}</span>
                </div>
                {results.sunat_tax_status && (
                  <div className="detail-row">
                    <span>Estado SUNAT:</span>
                    <span>{results.sunat_tax_status}</span>
                  </div>
                )}
                {results.osce_sanctions_count > 0 && (
                  <div className="detail-row warning">
                    <span>Sanciones OSCE:</span>
                    <span>{results.osce_sanctions_count}</span>
                  </div>
                )}
                {results.tce_sanctions_count > 0 && (
                  <div className="detail-row warning">
                    <span>Sanciones TCE:</span>
                    <span>{results.tce_sanctions_count}</span>
                  </div>
                )}
              </div>
              {results.certificate_url && (
                <a
                  href={results.certificate_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="certificate-link"
                >
                  📄 Descargar Certificado
                </a>
              )}
            </div>
          )}
        </div>

        {/* Historial */}
        <div className="history-card">
          <h2>Historial de Verificaciones</h2>
          {history.length === 0 ? (
            <div className="empty-state">
              <p>No hay verificaciones recientes</p>
            </div>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <div key={item.id} className="history-item">
                  <div className="history-info">
                    <span className="history-name">{item.target_company_name || 'Empresa desconocida'}</span>
                    <span className="history-ruc">{item.target_ruc_hash}</span>
                  </div>
                  <div className="history-meta">
                    <span className={`risk-dot ${getRiskColor(item.risk_level)}`}></span>
                    <span className="history-score">{item.score}/100</span>
                    <span className="history-date">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Uso del plan */}
      <div className="usage-card">
        <h3>Uso del Plan</h3>
        <div className="usage-bar">
          <div
            className="usage-fill"
            style={{
              width: `${(user?.used_queries_this_month / user?.max_monthly_queries) * 100}%`
            }}
          ></div>
        </div>
        <p className="usage-text">
          {user?.used_queries_this_month || 0} / {user?.max_monthly_queries || 1000} consultas este mes
        </p>
      </div>
    </div>
  )
}

export default Verifications