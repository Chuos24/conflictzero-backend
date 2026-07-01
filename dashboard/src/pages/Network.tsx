import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import './Network.css';
import type { z } from 'zod';

import {
  useNetworkSuppliers,
  useNetworkStats,
  useNetworkAlerts,
  useAddSupplier,
  useRemoveSupplier,
  useMarkAlertRead,
} from '../hooks/useQueries';
import { useToast } from '../context/ToastContext';
import Modal from '../components/Modal';
import { addSupplierSchema } from '../lib/validations';
import type { NetworkSupplier, NetworkAlert } from '../types';

type AddSupplierFormData = z.infer<typeof addSupplierSchema>;

function Network(): JSX.Element {
  const { success, error } = useToast();
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('suppliers');

  const { data: suppliersData } = useNetworkSuppliers();
  const { data: stats } = useNetworkStats();
  const { data: alertsData } = useNetworkAlerts();
  const addSupplier = useAddSupplier();
  const removeSupplier = useRemoveSupplier();
  const markAlertRead = useMarkAlertRead();

  const suppliers: NetworkSupplier[] = suppliersData?.items || [];
  const alerts: NetworkAlert[] = alertsData?.items || [];

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<AddSupplierFormData>({
    resolver: zodResolver(addSupplierSchema),
    defaultValues: {
      ruc: '',
      name: '',
      alert_threshold: 10,
    },
  });

  const onSubmit = async (data: AddSupplierFormData): Promise<void> => {
    try {
      await addSupplier.mutateAsync({
        ruc: data.ruc,
        notes: data.name || undefined,
        tags: [],
      });
      success('Proveedor agregado exitosamente');
      setShowAddModal(false);
      reset();
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Error agregando proveedor';
      setError('root', { message: errMsg });
      error(errMsg);
    }
  };

  const handleRemoveSupplier = async (id: string): Promise<void> => {
    if (!confirm('¿Estás seguro de eliminar este proveedor de tu red?')) {
      return;
    }
    try {
      await removeSupplier.mutateAsync(id);
      success('Proveedor eliminado');
    } catch (err: unknown) {
      error('Error eliminando proveedor');
    }
  };

  const handleMarkAlertRead = async (alertId: string): Promise<void> => {
    try {
      await markAlertRead.mutateAsync(alertId);
    } catch (err: unknown) {
      error('Error marcando alerta');
    }
  };

  const getRiskColor = (level: string): string => {
    const colors: Record<string, string> = {
      low: '#22c55e',
      medium: '#eab308',
      high: '#f97316',
      critical: '#ef4444',
    };
    return colors[level] || '#6b7280';
  };

  const getRiskLabel = (level: string): string => {
    const labels: Record<string, string> = {
      low: 'Bajo',
      medium: 'Medio',
      high: 'Alto',
      critical: 'Crítico',
    };
    return labels[level] || level;
  };

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
            <div className="stat-value">{stats.avg_score?.toFixed(1) || 'N/A'}</div>
            <div className="stat-label">Score Promedio</div>
          </div>
          <div className="stat-card alert-card">
            <div className="stat-value">{stats.unread_alerts || 0}</div>
            <div className="stat-label">Alertas Activas</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.high_risk_count || 0}</div>
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
          Alertas ({alerts.filter(a => a.status === 'unread').length} nuevas)
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
                  <h3>{supplier.razon_social || 'Sin nombre'}</h3>
                  <p className="ruc">RUC: {supplier.ruc}</p>
                  <p className="added">
                    Agregado: {new Date(supplier.added_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="supplier-metrics">
                  <div className="metric">
                    <span className="label">Score:</span>
                    <span className="value" style={{ color: getRiskColor(supplier.risk_level) }}>
                      {supplier.current_score || 'N/A'}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Riesgo:</span>
                    <span
                      className="badge"
                      style={{ backgroundColor: getRiskColor(supplier.risk_level) }}
                    >
                      {getRiskLabel(supplier.risk_level)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">Estado:</span>
                    <span className="value">{supplier.status}</span>
                  </div>
                </div>
                <div className="supplier-actions">
                  <button
                    className="btn btn-sm"
                    onClick={() => window.open(`/compare?ruc=${supplier.ruc}`, '_blank')}
                  >
                    Ver detalle
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleRemoveSupplier(supplier.id)}
                  >
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
              <div
                key={alert.id}
                className={`alert-card ${alert.status === 'read' ? 'read' : 'unread'}`}
              >
                <div className="alert-header">
                  <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
                  <span className="alert-date">{new Date(alert.created_at).toLocaleString()}</span>
                </div>
                <h4>{alert.supplier_name}</h4>
                <p>{alert.message}</p>
                <div className="alert-meta">
                  <span>Proveedor: {alert.supplier_id}</span>
                  <span>Tipo: {alert.type}</span>
                </div>
                {alert.status === 'unread' && (
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
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          {errors.root && (
            <div className="error-message" role="alert">
              {errors.root.message}
            </div>
          )}
          <div className="form-group">
            <label htmlFor="ruc">RUC del proveedor</label>
            <input
              type="text"
              id="ruc"
              maxLength={11}
              placeholder="20100190797"
              {...register('ruc')}
              aria-invalid={errors.ruc ? 'true' : 'false'}
            />
            {errors.ruc && (
              <span className="field-error" role="alert">
                {errors.ruc.message}
              </span>
            )}
          </div>
          <div className="form-group">
            <label htmlFor="name">Nombre (opcional)</label>
            <input type="text" id="name" placeholder="Nombre del proveedor" {...register('name')} />
            {errors.name && (
              <span className="field-error" role="alert">
                {errors.name.message}
              </span>
            )}
          </div>
          <div className="form-group">
            <label htmlFor="alert_threshold">Umbral de alerta (% de cambio)</label>
            <input
              type="number"
              id="alert_threshold"
              min={1}
              max={50}
              {...register('alert_threshold', { valueAsNumber: true })}
              aria-invalid={errors.alert_threshold ? 'true' : 'false'}
            />
            {errors.alert_threshold && (
              <span className="field-error" role="alert">
                {errors.alert_threshold.message}
              </span>
            )}
            <small>Notificar cuando el score cambie más de este porcentaje</small>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setShowAddModal(false)}>
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || addSupplier.isPending}
            >
              {addSupplier.isPending ? 'Agregando...' : 'Agregar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default Network;
