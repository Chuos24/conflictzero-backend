import { useState } from 'react'
import { useMLScore, useMLAnomalies } from '../hooks/useQueries'
import Badge from './Badge'
import LoadingSpinner from './LoadingSpinner'
import './MLScoreCard.css'

interface MLScoreCardProps {
  ruc: string | null
}

function MLScoreCard({ ruc }: MLScoreCardProps): JSX.Element | null {
  const [showDetails, setShowDetails] = useState(false)
  const lookbackDays = 90

  const { data: score, isLoading: scoreLoading, error: scoreError } = useMLScore(ruc, lookbackDays)
  const { data: anomalies } = useMLAnomalies(ruc, 30)

  if (!ruc) return null

  if (scoreLoading) {
    return (
      <div className="ml-score-card loading">
        <LoadingSpinner size="medium" text="Calculando ML Score..." />
      </div>
    )
  }

  if (scoreError) {
    return (
      <div className="ml-score-card error">
        <p className="error-text">Error calculando ML Score: {scoreError.message}</p>
      </div>
    )
  }

  if (!score) return null

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return '#22c55e'
      case 'moderate': return '#eab308'
      case 'high': return '#f97316'
      case 'critical': return '#ef4444'
      default: return '#888'
    }
  }

  const getRiskLabel = (level: string) => {
    switch (level) {
      case 'low': return 'Bajo Riesgo'
      case 'moderate': return 'Riesgo Moderado'
      case 'high': return 'Alto Riesgo'
      case 'critical': return 'Riesgo Crítico'
      default: return level
    }
  }

  const scoreColor = getRiskColor(score.risk_level)
  const scoreAngle = (score.ml_score / 100) * 180 - 90 // -90 to 90 degrees

  return (
    <div className="ml-score-card">
      <div className="ml-score-header">
        <h3>ML Score de Riesgo</h3>
        <Badge variant="default" size="small">v{score.model_version}</Badge>
      </div>

      <div className="ml-score-gauge">
        <div className="gauge-container">
          <div className="gauge-bg" />
          <div
            className="gauge-fill"
            style={{
              background: `conic-gradient(${scoreColor} ${score.ml_score}%, transparent 0)`,
              transform: `rotate(${scoreAngle}deg)`
            }}
          />
          <div className="gauge-center">
            <span className="gauge-score" style={{ color: scoreColor }}>
              {score.ml_score}
            </span>
            <span className="gauge-label">/ 100</span>
          </div>
        </div>
        <div className="gauge-info">
          <Badge
            variant={
              score.risk_level === 'low' ? 'success' :
              score.risk_level === 'moderate' ? 'warning' :
              score.risk_level === 'high' ? 'error' : 'error'
            }
          >
            {getRiskLabel(score.risk_level)}
          </Badge>
          <span className="gauge-meta">
            Basado en {score.lookback_days} días de historial
          </span>
        </div>
      </div>

      {/* Anomalías */}
      {anomalies && anomalies.has_anomalies && (
        <div className="ml-anomalies">
          <h4>⚠️ Anomalías Detectadas ({anomalies.anomaly_count})</h4>
          <div className="anomalies-list">
            {anomalies.anomalies.map((a, i) => (
              <div key={i} className={`anomaly-item severity-${a.severity}`}>
                <Badge
                  variant={a.severity === 'critical' ? 'error' : a.severity === 'high' ? 'warning' : 'info'}
                  size="small"
                >
                  {a.severity}
                </Badge>
                <span className="anomaly-desc">{a.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Features */}
      <div className="ml-features">
        <h4>Features del Modelo</h4>
        <div className="features-grid">
          <div className="feature-bar">
            <span className="feature-label">Frecuencia de Verificaciones</span>
            <div className="feature-track">
              <div
                className="feature-fill"
                style={{ width: `${score.features.verification_frequency}%`, background: '#2196f3' }}
              />
            </div>
            <span className="feature-value">{score.features.verification_frequency.toFixed(0)}</span>
          </div>
          <div className="feature-bar">
            <span className="feature-label">Volatilidad de Score</span>
            <div className="feature-track">
              <div
                className="feature-fill"
                style={{ width: `${score.features.score_volatility}%`, background: '#9c27b0' }}
              />
            </div>
            <span className="feature-value">{score.features.score_volatility.toFixed(0)}</span>
          </div>
          <div className="feature-bar">
            <span className="feature-label">Historial de Sanciones</span>
            <div className="feature-track">
              <div
                className="feature-fill"
                style={{ width: `${score.features.sanction_history}%`, background: '#f44336' }}
              />
            </div>
            <span className="feature-value">{score.features.sanction_history.toFixed(0)}</span>
          </div>
          <div className="feature-bar">
            <span className="feature-label">Tendencia de Deuda</span>
            <div className="feature-track">
              <div
                className="feature-fill"
                style={{ width: `${score.features.debt_trend}%`, background: '#ff9800' }}
              />
            </div>
            <span className="feature-value">{score.features.debt_trend.toFixed(0)}</span>
          </div>
          <div className="feature-bar">
            <span className="feature-label">Consistencia de Compliance</span>
            <div className="feature-track">
              <div
                className="feature-fill"
                style={{ width: `${score.features.compliance_consistency}%`, background: '#4caf50' }}
              />
            </div>
            <span className="feature-value">{score.features.compliance_consistency.toFixed(0)}</span>
          </div>
        </div>
      </div>

      {/* Explicación */}
      <div className="ml-explanation">
        <button
          className="btn-ghost toggle-details"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Ocultar' : 'Ver'} explicación del modelo
        </button>
        {showDetails && (
          <ul className="explanation-list">
            {score.explanation.map((exp, i) => (
              <li key={i}>{exp}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="ml-meta">
        <span className="meta-item">
          Calculado: {new Date(score.calculated_at).toLocaleString('es-PE')}
        </span>
        <span className="meta-item">
          RUC: {score.ruc}
        </span>
      </div>
    </div>
  )
}

export default MLScoreCard
