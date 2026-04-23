import React, { useState } from 'react'
import './Network.css'
import { useNetworkSuppliers, useNetworkStats, useNetworkAlerts, useAddSupplier, useRemoveSupplier, useMarkAlertRead } from '../hooks/useQueries'
import { useToast } from '../context/ToastContext'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'

function Network() {
  const { showToast } = useToast()
  const [showAddModal, setShowAddModal] = useState(false)
  const [newSupplier, setNewSupplier] = useState({ ruc: '', name: '', alert_threshold: 10 })
  const [activeTab, setActiveTab] = useState('suppliers')

  const { data: suppliersData, isLoading: suppliersLoading } = useNetworkSuppliers()
  const { data: stats } = useNetworkStats()
  const { data: alertsData } = useNetworkAlerts()
  const addSupplier = useAddSupplier()
  const removeSupplier = useRemoveSupplier()
  const markAlertRead = useMarkAlertRead()

  const suppliers = suppliersData || []
  const alerts = alertsData || []

  const handleAddSupplier = async (e) => {
    e.preventDefault()
    try {
      await addSupplier.mutateAsync(newSupplier)
      showToast('Proveedor agregado exitosamente', 'success')
      setShowAddModal(false)
      setNewSupplier({ ruc: '', name: '', alert_threshold: 10 })
    } catch (error) {
      showToast(error?.response?.data?.detail || 'Error agregando proveedor', 'error')
    }
  }

  const handleRemoveSupplier = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este proveedor de tu red?')) return
    try {
      await removeSupplier.mutateAsync(id)
      showToast('Proveedor eliminado', 'success')
    } catch (error) {
      showToast('Error eliminando proveedor', 'error')
    }
  }

  const handleMarkAlertRead = async (alertId) => {
    try {
      await markAlertRead.mutateAsync(alertId)
    } catch (error) {
      showToast('Error marcando alerta', 'error')
    }
  }

  const getRiskColor = (level) => {
    const colors = { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' }
    return colors[level] || '#6b7280'
  }

  const getRiskLabel = (level) => {
    const labels = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico' }
    return labels[level] || level
  }

  const isLoading = suppliersLoading || addSupplier.isPending || removeSupplier.isPending

  return (
    <div className="network-page">
      <div className="network-header">
        <h1>Mi Red de Proveedores</h1>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
          + Agregar Proveedor
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_suppliers}</div>
            <div className="stat-label">Proveedores</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.avg_network_score?.toFixed(1) || 'N/A'}</div>
            <div className="stat-label">Score Promedio</div>
          </div>
          <div className="stat-card alert-card">
            <div className="stat-value">{stats.total_alerts}</div>
            <div className="stat-label">Alertas Activas</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.suppliers_at_risk || 0}</div>
            <div className="stat-label">En Riesgo</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'suppliers' ? 'active' : ''}`}
          onClick={() => setActiveTab('suppliers')}
        >
          Proveedores ({suppliers.length})
        </button>
        <button 
          className={`tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Alertas ({alerts.filter(a => !a.read).length} nuevas)
        </button>
      </div>

      {/* Suppliers Tab */}
      {activeTab === 'suppliers' && (
        <div className="suppliers-list">
          {suppliers.length === 0 ? (
            <div className="empty-state">
              <p>No tienes proveedores en tu red</p>
              <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
                Agregar tu primer proveedor
              </button>
            </div>
          ) : (
            suppliers.map(supplier => (
              <div key={supplier.id} className="supplier-card">
                <div className="supplier-info">
                  <h3>{supplier.supplier_name || 'Sin nombre'}</h3>
                  <p className="ruc">RUC: {supplier.supplier_ruc}</p>
                  <p className="added">Agregado: {new Date(supplier.created_at).toLocaleDateString()}</p>
                </div>
                <div className="supplier-metrics">
                  <div className="metric">
                    <span className="label">Score:</span>
                    <span className="value" style={{ color: getRiskColor(supplier.current_risk_level) }}>
                      {supplier.current_score || 'N/A'}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Riesgo:</span>
                    <span className="badge" style={{ backgroundColor: getRiskColor(supplier.current_risk_level) }}>
                      {getRiskLabel(supplier.current_risk_level)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Umbral:</span>
                    <span className="value">{supplier.alert_threshold}%</span>
                  </div>
                </div>
                <div className="supplier-actions">
                  <button className="btn btn-sm" onClick={() => window.open(`/compare?ruc=${supplier.supplier_ruc}`, '_blank')}>
                    Ver detalle
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleRemoveSupplier(supplier.id)}>
                    Eliminar
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="alerts-list">
          {alerts.length === 0 ? (
            <div className="empty-state">
              <p>No hay alertas en tu red</p>
            </div>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} className={`alert-card ${alert.read ? 'read' : 'unread'}`}>
                <div className="alert-header">
                  <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
                  <span className="alert-date">{new Date(alert.created_at).toLocaleString()}</span>
                </div>
                <h4>{alert.title}</h4>
                <p>{alert.message}</p>
                <div className="alert-meta">
                  <span>Proveedor: {alert.supplier_ruc}</span>
                  <span>Tipo: {alert.alert_type}</span>
                </div>
                {!alert.read && (
                  <button className="btn btn-sm" onClick={() => handleMarkAlertRead(alert.id)}>
                    Marcar como leída
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Add Supplier Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Agregar Proveedor"
        size="medium"
      >
        <form onSubmit={handleAddSupplier}>
          <div className="form-group">
            <label>RUC del proveedor</label>
            <input 
              type="text" 
              maxLength="11"
              value={newSupplier.ruc}
              onChange={e => setNewSupplier({...newSupplier, ruc: e.target.value})}
              placeholder="20100190797"
              required
            />
          </div>
          <div className="form-group">
            <label>Nombre (opcional)</label>
            <input 
              type="text"
              value={newSupplier.name}
              onChange={e => setNewSupplier({...newSupplier, name: e.target.value})}
              placeholder="Nombre del proveedor"
            />
          </div>
          <div className="form-group">
            <label>Umbral de alerta (% de cambio)</label>
            <input 
              type="number"
              min="1"
              max="50"
              value={newSupplier.alert_threshold}
              onChange={e => setNewSupplier({...newSupplier, alert_threshold: parseInt(e.target.value)})}
            />
            <small>Notificar cuando el score cambie más de este porcentaje</small>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setShowAddModal(false)}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={addSupplier.isPending}>
              {addSupplier.isPending ? 'Agregando...' : 'Agregar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Network
