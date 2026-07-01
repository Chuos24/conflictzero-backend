import { useState, useEffect } from 'react';

import { useToast } from '../context/ToastContext';
import api from '../services/api';
import type { AuditReport, AuditReportType, AuditSchedule } from '../types';
import './AuditReports.css';

const REPORT_TYPE_LABELS: Record<AuditReportType, string> = {
  compliance: 'Compliance',
  security: 'Seguridad',
  data_processing: 'Procesamiento de Datos',
  network_changes: 'Cambios en Red',
};

const REPORT_TYPE_ICONS: Record<AuditReportType, string> = {
  compliance: '🛡️',
  security: '🔒',
  data_processing: '📊',
  network_changes: '🌐',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  generated: 'Generado',
  signed: 'Firmado',
  archived: 'Archivado',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'status-pending',
  generated: 'status-success',
  signed: 'status-primary',
  archived: 'status-muted',
};

export default function AuditReports(): JSX.Element {
  const { success, error: showError } = useToast();
  const [reports, setReports] = useState<AuditReport[]>([]);
  const [schedule, setSchedule] = useState<AuditSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<AuditReportType | null>(null);
  const [selectedType, setSelectedType] = useState<AuditReportType>('compliance');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (): Promise<void> => {
    try {
      setLoading(true);
      const [reportsRes, scheduleRes] = await Promise.all([
        api.get('/api/v2/audit/reports').catch(() => ({ data: { reports: [] } })),
        api.get('/api/v2/audit/schedule').catch(() => ({ data: { schedule: [] } })),
      ]);
      setReports(reportsRes.data.reports || []);
      setSchedule(scheduleRes.data.schedule || []);
    } catch (err) {
      showError('Error al cargar reportes de auditoría');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (): Promise<void> => {
    try {
      setGenerating(selectedType);
      const endpoint = `/api/v2/audit/reports/${selectedType.replace('_', '-')}`;
      const res = await api.post(endpoint, null, {
        params: {
          start_date: new Date(dateRange.start).toISOString(),
          end_date: new Date(dateRange.end).toISOString(),
        },
      });
      success(`Reporte ${REPORT_TYPE_LABELS[selectedType]} generado exitosamente`);
      setReports(prev => [
        {
          id: res.data.report_id,
          report_number: res.data.report_id,
          report_type: selectedType,
          status: 'generated',
          period_start: dateRange.start,
          period_end: dateRange.end,
          generated_at: new Date().toISOString(),
          ...res.data,
        },
        ...prev,
      ]);
    } catch (err) {
      showError('Error al generar reporte');
      console.error(err);
    } finally {
      setGenerating(null);
    }
  };

  const handleSignReport = async (reportNumber: string): Promise<void> => {
    try {
      await api.post(`/api/v2/audit/reports/${reportNumber}/sign`);
      success('Reporte firmado exitosamente');
      setReports(prev =>
        prev.map(r => (r.report_number === reportNumber ? { ...r, status: 'signed' } : r))
      );
    } catch (err) {
      showError('Error al firmar reporte');
      console.error(err);
    }
  };

  const handleDownloadPDF = async (report: AuditReport): Promise<void> => {
    try {
      const response = await api.get(`/api/v2/audit/reports/${report.report_number}/pdf`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit-report-${report.report_number}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      success('PDF descargado exitosamente');
    } catch (err) {
      showError('Error al descargar el PDF');
      console.error(err);
    }
  };

  const handleDownloadJSON = (report: AuditReport): void => {
    if (report.json_url) {
      window.open(report.json_url, '_blank');
    } else {
      // Generate JSON from data
      const dataStr = JSON.stringify(report.data || {}, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit-report-${report.report_number}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    }
  };

  if (loading) {
    return <div className="audit-loading">Cargando...</div>;
  }

  return (
    <div className="audit-container">
      <h1>Auditoría y Reportes</h1>
      <p className="audit-subtitle">
        Genera y gestiona reportes de auditoría para compliance, seguridad y procesamiento de datos.
      </p>

      {/* Generate Report Section */}
      <div className="generate-section">
        <h2>Generar Nuevo Reporte</h2>
        <div className="generate-form">
          <div className="form-row">
            <div className="form-group">
              <label>Tipo de Reporte</label>
              <select
                value={selectedType}
                onChange={e => setSelectedType(e.target.value as AuditReportType)}
                className="form-select"
              >
                {Object.entries(REPORT_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Fecha Inicio</label>
              <input
                type="date"
                value={dateRange.start}
                onChange={e => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Fecha Fin</label>
              <input
                type="date"
                value={dateRange.end}
                onChange={e => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="form-input"
              />
            </div>
          </div>
          <button
            className="btn-primary"
            onClick={handleGenerateReport}
            disabled={generating !== null}
          >
            {generating ? 'Generando...' : `Generar Reporte ${REPORT_TYPE_LABELS[selectedType]}`}
          </button>
        </div>
      </div>

      {/* Schedule */}
      {schedule.length > 0 && (
        <div className="schedule-section">
          <h2>Calendario de Auditorías Programadas</h2>
          <div className="schedule-grid">
            {schedule.map(item => (
              <div key={item.report_type} className="schedule-card">
                <div className="schedule-icon">
                  {REPORT_TYPE_ICONS[item.report_type as AuditReportType]}
                </div>
                <div className="schedule-info">
                  <h4>{REPORT_TYPE_LABELS[item.report_type as AuditReportType]}</h4>
                  <p className="schedule-freq">Frecuencia: {item.frequency}</p>
                  <p className="schedule-next">
                    Próximo: {new Date(item.next_scheduled).toLocaleDateString()}
                  </p>
                </div>
                <div className={`schedule-status ${item.is_active ? 'active' : 'inactive'}`}>
                  {item.is_active ? 'Activo' : 'Inactivo'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reports List */}
      <div className="reports-section">
        <h2>Reportes Generados</h2>
        {reports.length === 0 ? (
          <div className="empty-state">
            <p>No has generado ningún reporte de auditoría.</p>
          </div>
        ) : (
          <div className="reports-table-wrapper">
            <table className="reports-table">
              <thead>
                <tr>
                  <th>Número</th>
                  <th>Tipo</th>
                  <th>Estado</th>
                  <th>Período</th>
                  <th>Generado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(report => (
                  <tr key={report.id}>
                    <td className="mono">{report.report_number}</td>
                    <td>
                      <span className="report-type">
                        {REPORT_TYPE_ICONS[report.report_type]}{' '}
                        {REPORT_TYPE_LABELS[report.report_type]}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${STATUS_COLORS[report.status] || ''}`}>
                        {STATUS_LABELS[report.status] || report.status}
                      </span>
                    </td>
                    <td>
                      {new Date(report.period_start).toLocaleDateString()} -{' '}
                      {new Date(report.period_end).toLocaleDateString()}
                    </td>
                    <td>
                      {report.generated_at
                        ? new Date(report.generated_at).toLocaleDateString()
                        : '-'}
                    </td>
                    <td>
                      <div className="action-buttons">
                        {report.status !== 'signed' && (
                          <button
                            className="btn-icon"
                            title="Firmar reporte"
                            onClick={() => handleSignReport(report.report_number)}
                          >
                            ✍️
                          </button>
                        )}
                        <button
                          className="btn-icon"
                          title="Descargar JSON"
                          onClick={() => handleDownloadJSON(report)}
                        >
                          📄
                        </button>
                        {report.pdf_url && (
                          <button
                            className="btn-icon"
                            title="Descargar PDF"
                            onClick={() => handleDownloadPDF(report)}
                          >
                            📑
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
