import { useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCompare, useCompareHistory } from '../hooks/useQueries'
import { compareSchema } from '../lib/validations'
import Skeleton from '../components/Skeleton'
import type { z } from 'zod'
import type { Comparison } from '../types'
import './Compare.css'

type CompareFormData = z.infer<typeof compareSchema>

function Compare(): JSX.Element {
  const [results, setResults] = useState<Comparison | null>(null)
  const [error, setError] = useState<string>('')

  const compareMutation = useCompare()
  const { data: historyData, isLoading: historyLoading } = useCompareHistory()

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
  } = useForm<CompareFormData>({
    resolver: zodResolver(compareSchema),
    defaultValues: {
      rucs: ['', ''],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'rucs' as 'rucs',
  })

  const onSubmit = async (data: CompareFormData): Promise<void> => {
    setError('')
    setResults(null)

    try {
      const result = await compareMutation.mutateAsync(data.rucs)
      setResults(result)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al comparar empresas'
      setFormError('root', { message: msg })
      setError(msg)
    }
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'warning'
    if (score >= 40) return 'danger'
    return 'critical'
  }

  const getRiskLabel = (level: string): string => {
    const labels: Record<string, string> = {
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
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="ruc-inputs">
              {fields.map((field, index) => (
                <div key={field.id} className="ruc-field">
                  <input
                    type="text"
                    placeholder={`RUC ${index + 1}`}
                    maxLength={11}
                    {...register(`rucs.${index}`)}
                    className={errors.rucs?.[index] ? 'invalid' : ''}
                  />
                  {fields.length > 2 && (
                    <button
                      type="button"
                      className="remove-btn"
                      onClick={() => remove(index)}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>

            {errors.rucs && !Array.isArray(errors.rucs) && (
              <div className="error-message">{errors.rucs.message}</div>
            )}

            {fields.length < 10 && (
              <button
                type="button"
                className="add-ruc-btn"
                onClick={() => append('')}
              >
                + Agregar RUC
              </button>
            )}

            {errors.root && <div className="error-message">{errors.root.message}</div>}
            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              className="compare-btn"
              disabled={compareMutation.isPending}
            >
              {compareMutation.isPending ? 'Comparando...' : 'Comparar Empresas'}
            </button>
          </form>
        </div>

        {results && (
          <div className="results-card">
            <h2>Resultados de la Comparación</h2>

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

            {results.recommendation && (
              <div className="recommendation-box">
                <h4>💡 Recomendación</h4>
                <p>{results.recommendation}</p>
              </div>
            )}

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

        {/* Historial de comparaciones */}
        <div className="history-card">
          <h2>Historial de Comparaciones</h2>
          {historyLoading ? (
            <Skeleton variant="rect" height={200} />
          ) : historyData?.items && historyData.items.length > 0 ? (
            <div className="history-list">
              {historyData.items.map((item) => (
                <div key={item.id} className="history-item">
                  <span className="history-rucs">
                    {item.rucs?.join(', ') || 'N/A'}
                  </span>
                  <span className="history-date">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No hay comparaciones recientes</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Compare
