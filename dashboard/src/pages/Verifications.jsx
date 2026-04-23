import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../context/AuthContext'
import { useVerifications, useVerifyRuc } from '../hooks/useQueries'
import { verifyRucSchema } from '../lib/validations'
import LoadingSpinner from '../components/LoadingSpinner'
import './Verifications.css'

function Verifications() {
  const { user } = useAuth()
  const { data: historyData, isLoading: historyLoading } = useVerifications()
  const verifyMutation = useVerifyRuc()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    resolver: zodResolver(verifyRucSchema),
    defaultValues: { ruc: '' },
  })

  const [results, setResults] = React.useState(null)

  const onSubmit = async (data) => {
    try {
      const result = await verifyMutation.mutateAsync(data.ruc)
      setResults({
        ...result,
        ruc: data.ruc,
        company_name: result.target_company_name,
      })
      reset()
    } catch (err) {
      // Error handled by mutation
    }
  }

  const history = historyData?.items || []
  const loading = verifyMutation.isPending
  const error = verifyMutation.error?.response?.data?.detail || errors.ruc?.message

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
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="search-box">
              <input
                type="text"
                placeholder="Ingresa el RUC (11 dígitos)"
                maxLength={11}
                className="ruc-input"
                {...register('ruc')}
                aria-invalid={errors.ruc ? 'true' : 'false'}
              />
              <button
                type="submit"
                className="verify-btn"
                disabled={loading}
              >
                {loading ? 'Verificando...' : 'Verificar'}
              </button>
            </div>
            {error && <div className="error-text">{error}</div>}
            {errors.ruc && <div className="error-text">{errors.ruc.message}</div>}
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