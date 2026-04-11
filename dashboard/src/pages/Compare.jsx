import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import './Compare.css'

function Compare() {
  const [rucs, setRucs] = useState(['', ''])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const addRucField = () => {
    if (rucs.length < 10) {
      setRucs([...rucs, ''])
    }
  }

  const removeRucField = (index) => {
    if (rucs.length > 2) {
      const newRucs = rucs.filter((_, i) => i !== index)
      setRucs(newRucs)
    }
  }

  const updateRuc = (index, value) => {
    const newRucs = [...rucs]
    newRucs[index] = value.replace(/\D/g, '').slice(0, 11)
    setRucs(newRucs)
  }

  const handleCompare = async (e) => {
    e.preventDefault()
    
    // Validar que todos los RUCs tengan 11 dígitos
    const validRucs = rucs.filter(r => r.length === 11)
    if (validRucs.length < 2) {
      setError('Se necesitan al menos 2 RUCs válidos de 11 dígitos')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/compare/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ rucs: validRucs })
      })

      const data = await response.json()

      if (response.ok) {
        setResults(data)
      } else {
        setError(data.detail || 'Error al comparar empresas')
      }
    } catch (err) {
      setError('Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'warning'
    if (score >= 40) return 'danger'
    return 'critical'
  }

  const getRiskLabel = (level) => {
    const labels = {
      'low': 'Bajo',
      'medium': 'Medio',
      'high': 'Alto',
      'critical': 'Crítico'
    }
    return labels[level] || level
  }

  return (
    <div className="compare-page">
      <header className="page-header">
        <h1>Comparar Empresas</h1>
        <p className="subtitle">
          Compara hasta 10 empresas simultáneamente
        </p>
      </header>

      <div className="compare-container">
        <div className="input-card">
          <h2>Ingresar RUCs</h2>
          <form onSubmit={handleCompare}>
            <div className="ruc-inputs">
              {rucs.map((ruc, index) => (
                <div key={index} className="ruc-field">
                  <input
                    type="text"
                    value={ruc}
                    onChange={(e) => updateRuc(index, e.target.value)}
                    placeholder={`RUC ${index + 1}`}
                    className={ruc.length === 11 ? 'valid' : ruc.length > 0 ? 'invalid' : ''}
                  />
                  {rucs.length > 2 && (
                    <button
                      type="button"
                      className="remove-btn"
                      onClick={() => removeRucField(index)}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>

            {rucs.length < 10 && (
              <button
                type="button"
                className="add-ruc-btn"
                onClick={addRucField}
              >
                + Agregar RUC
              </button>
            )}

            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              className="compare-btn"
              disabled={loading || rucs.filter(r => r.length === 11).length < 2}
            >
              {loading ? 'Comparando...' : 'Comparar Empresas'}
            </button>
          </form>
        </div>

        {results && (
          <div className="results-card">
            <h2>Resultados de la Comparación</h2>
            
            {/* Tabla de comparación */}
            <div className="comparison-table-wrapper">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Empresa</th>
                    <th>RUC</th>
                    <th>Score</th>
                    <th>Riesgo</th>
                    <th>SUNAT</th>
                    <th>OSCE</th>
                    <th>TCE</th>
                  </tr>
                </thead>
                <tbody>
                  {results.companies?.map((company) => (
                    <tr key={company.ruc}>
                      <td className="company-name">{company.name}</td>
                      <td className="ruc-cell">{company.ruc}</td>
                      <td>
                        <span className={`score-badge ${getScoreColor(company.score)}`}>
                          {company.score}
                        </span>
                      </td>
                      <td>
                        <span className={`risk-badge ${company.risk_level}`}>
                          {getRiskLabel(company.risk_level)}
                        </span>
                      </td>
                      <td>
                        {company.sunat_status === 'ACTIVO' ? (
                          <span className="status-good">✓</span>
                        ) : (
                          <span className="status-bad">✗</span>
                        )}
                      </td>
                      <td>
                        {company.osce_sanctions === 0 ? (
                          <span className="status-good">0</span>
                        ) : (
                          <span className="status-bad">{company.osce_sanctions}</span>
                        )}
                      </td>
                      <td>
                        {company.tce_sanctions === 0 ? (
                          <span className="status-good">0</span>
                        ) : (
                          <span className="status-bad">{company.tce_sanctions}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Análisis comparativo */}
            <div className="analysis-section">
              <h3>Análisis Comparativo</h3>
              <div className="analysis-grid">
                <div className="analysis-card best">
                  <h4>🏆 Mejor Opción</h4>
                  <p className="company-name">{results.analysis?.best?.name}</p>
                  <p className="score">Score: {results.analysis?.best?.score}/100</p>
                </div>
                <div className="analysis-card worst">
                  <h4>⚠️ Mayor Riesgo</h4>
                  <p className="company-name">{results.analysis?.worst?.name}</p>
                  <p className="score">Score: {results.analysis?.worst?.score}/100</p>
                </div>
                <div className="analysis-card avg">
                  <h4>📊 Promedio</h4>
                  <p className="score">{results.analysis?.average_score}/100</p>
                  <p className="count">{results.companies?.length} empresas</p>
                </div>
              </div>
            </div>

            {/* Recomendación */}
            {results.recommendation && (
              <div className="recommendation-box">
                <h4>💡 Recomendación</h4>
                <p>{results.recommendation}</p>
              </div>
            )}

            {/* Exportar */}
            <div className="export-actions">
              <button className="export-btn pdf">
                📄 Exportar PDF
              </button>
              <button className="export-btn excel">
    📊 Exportar Excel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Compare