import { useState } from 'react'
import { useMonitoringStats, useMonitoringAlerts, useMonitoringChanges, useMarkMonitoringAlertRead, useDismissMonitoringAlert } from '../hooks/useQueries'
import type { MonitoringAlert, MonitoringChange } from '../hooks/useQueries'
import LoadingSpinner from '../components/LoadingSpinner'
import Badge from '../components/Badge'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import './Monitoring.css'

function Monitoring(): JSX.Element {
  const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'changes' | 'rules'>('overview')
  const [alertFilter, setAlertFilter] = useState<string>('all')
  
  const { data: stats, isLoading: statsLoading } = useMonitoringStats()
  const { data: alerts, isLoading: alertsLoading } = useMonitoringAlerts(alertFilter !== 'all' ? alertFilter : undefined)
  const { data: changes, isLoading: changesLoading } = useMonitoringChanges()
  const markReadMutation = useMarkMonitoringAlertRead()
  const dismissMutation = useDismissMonitoringAlert()

  const isLoading = statsLoading || alertsLoading || changesLoading

  if (isLoading) {
    return (
      <div className="monitoring-loading">
        <LoadingSpinner size="large" text="Cargando monitoreo..." />
      </div>
    )
  }

  const getSeverityVariant = (severity: string): 'info' | 'warning' | 'success' | 'error' | 'default' => {
    switch (severity) {
      case 'critical': return 'error'
      case 'warning': return 'warning'
      case 'info': return 'info'
      default: return 'default'
    }
  }

  const getChangeTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'sanction_added': 'Sanción nueva',
      'representative_changed': 'Cambio de representante',
      'address_changed': 'Cambio de dirección',
      'score_dropped': 'Riesgo aumentado',
      'status_changed': 'Cambio de estado',
      'compliance_expired': 'Compliance vencido'
    }
    return labels[type] || type
  }

  return (
    <div className="monitoring">
      <header className="monitoring-header">
        <div>
          <h1>Monitoreo Continuo</h1>
          <p className="monitoring-subtitle">
            Seguimiento automático de proveedores en tu red
          </p>
        </div>
        <div className="monitoring-actions">
          <button className="btn-primary" onClick={() => alert('Ejecutar monitoreo manual')}>
            Ejecutar Ahora
          </button>
        </div>
      </header>

      {/* Stats Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📸</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_snapshots || 0}</span>
            <span className="stat-label">Snapshots</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_changes_detected || 0}</span>
            <span className="stat-label">Cambios Detectados</span>
          </div>
        </div>

        <div className="stat-card highlight">
          <div className="stat-icon">🔔</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.pending_alerts || 0}</span>
            <span className="stat-label">Alertas Pendientes</span>
          </div>
        </div>

        <div className="stat-card warning">
          <div className="stat-icon">🚨</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.critical_changes || 0}</span>
            <span className="stat-label">Críticos</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="monitoring-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Resumen
        </button>
        <button
          className={`tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Alertas {alerts && alerts.length > 0 && `(${alerts.length})`}
        </button>
        <button
          className={`tab-btn ${activeTab === 'changes' ? 'active' : ''}`}
          onClick={() => setActiveTab('changes')}
        >
          Cambios
        </button>
        <button
          className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          Reglas
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="monitoring-overview">
          <div className="charts-grid">
            <div className="chart-card wide">
              <h3>Tendencia de Cambios (30 días)</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={changes?.slice(0, 30).map((c: MonitoringChange, i: number) => ({
                  day: i + 1,
                  count: changes.filter((ch: MonitoringChange) => 
                    new Date(ch.created_at).toDateString() === new Date(c.created_at).toDateString()
                  ).length
                })) || []}>
                  <defs>
                    <linearGradient id="colorChanges" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ff9800" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#ff9800" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="day" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#ff9800' }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#ff9800" fillOpacity={1} fill="url(#colorChanges)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Severidad de Cambios</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={[
                  { name: 'Info', value: stats?.warning_changes || 0, color: '#2196f3' },
                  { name: 'Warning', value: stats?.warning_changes || 0, color: '#ff9800' },
                  { name: 'Critical', value: stats?.critical_changes || 0, color: '#f44336' }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="name" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="monitoring-card">
            <h3>Última Ejecución</h3>
            {stats?.last_run?.id ? (
              <div className="last-run-info">
                <div className="run-status">
                  <Badge variant={stats.last_run.status === 'completed' ? 'success' : 'warning'}>
                    {stats.last_run.status}
                  </Badge>
                  <span className="run-date">
                    {stats.last_run.completed_at 
                      ? new Date(stats.last_run.completed_at).toLocaleString('es-PE') 
                      : 'En progreso...'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="empty-text">Aún no se ha ejecutado el monitoreo</p>
            )}
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="monitoring-alerts">
          <div className="filter-bar">
            <select 
              value={alertFilter} 
              onChange={(e) => setAlertFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">Todas</option>
              <option value="pending">Pendientes</option>
              <option value="sent">Enviadas</option>
              <option value="read">Leídas</option>
            </select>
          </div>

          {alerts && alerts.length > 0 ? (
            <div className="alerts-list">
              {alerts.map((alertItem: MonitoringAlert) => (
                <div key={alertItem.id} className={`alert-item severity-${alertItem.severity}`}>
                  <div className="alert-header">
                    <Badge variant={getSeverityVariant(alertItem.severity)}>
                      {alertItem.severity}
                    </Badge>
                    <span className="alert-date">
                      {new Date(alertItem.created_at).toLocaleString('es-PE')}
                    </span>
                  </div>
                  <h4 className="alert-title">{alertItem.title}</h4>
                  <p className="alert-message">{alertItem.message}</p>
                  <div className="alert-actions">
                    <button className="btn-sm" onClick={() => markReadMutation.mutate(alertItem.id)} disabled={markReadMutation.isPending}>
                      Marcar leída
                    </button>
                    <button className="btn-sm btn-ghost" onClick={() => dismissMutation.mutate(alertItem.id)} disabled={dismissMutation.isPending}>
                      Descartar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No hay alertas {alertFilter !== 'all' ? `con estado "${alertFilter}"` : ''}</p>
            </div>
          )}
        </div>
      )}

      {/* Changes Tab */}
      {activeTab === 'changes' && (
        <div className="monitoring-changes">
          {changes && changes.length > 0 ? (
            <div className="changes-table-wrapper">
              <table className="changes-table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Descripción</th>
                    <th>Severidad</th>
                    <th>Fecha</th>
                    <th>Valores</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.map((change: MonitoringChange) => (
                    <tr key={change.id} className={`severity-${change.severity}`}>
                      <td>
                        <Badge variant="default" size="small">
                          {getChangeTypeLabel(change.change_type)}
                        </Badge>
                      </td>
                      <td>{change.description}</td>
                      <td>
                        <Badge variant={getSeverityVariant(change.severity)} size="small">
                          {change.severity}
                        </Badge>
                      </td>
                      <td>{new Date(change.created_at).toLocaleDateString('es-PE')}</td>
                      <td className="change-values">
                        {change.previous_value && (
                          <span className="old-value">{change.previous_value}</span>
                        )}
                        {change.previous_value && change.new_value && (
                          <span className="arrow">→</span>
                        )}
                        {change.new_value && (
                          <span className="new-value">{change.new_value}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <p>No se han detectado cambios recientes</p>
            </div>
          )}
        </div>
      )}

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="monitoring-rules">
          <div className="rules-header">
            <h3>Reglas de Monitoreo</h3>
            <button className="btn-primary" onClick={() => alert('Crear regla')}>
              + Nueva Regla
            </button>
          </div>
          
          <div className="rules-list">
            <div className="rule-card">
              <div className="rule-header">
                <h4>Monitoreo General</h4>
                <Badge variant="success">Activa</Badge>
              </div>
              <p className="rule-desc">Alertar sobre cualquier cambio en proveedores de la red</p>
              <div className="rule-config">
                <span className="config-item">📧 Email</span>
                <span className="config-item">📊 Dashboard</span>
                <span className="config-item">🕐 Diario</span>
              </div>
            </div>
            
            <div className="rule-card">
              <div className="rule-header">
                <h4>Sanciones Críticas</h4>
                <Badge variant="success">Activa</Badge>
              </div>
              <p className="rule-desc">Alerta inmediata cuando se detectan nuevas sanciones</p>
              <div className="rule-config">
                <span className="config-item">📧 Email</span>
                <span className="config-item">🚨 Inmediato</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Monitoring
