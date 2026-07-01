/*
 * Conflict Zero - Countries Admin Page
 * Fase 3 Enterprise - Multi-country configuration
 */

import { useState } from 'react';

import { useToast } from '../context/ToastContext';
import {
  SUPPORTED_COUNTRIES,
  getCountryByCode,
  getDefaultCountry,
  formatCurrency,
  validateDocumentFormat,
  getDocumentPlaceholder,
} from '../utils/countries';
import './Countries.css';

interface CountrySettings {
  code: string;
  enabled: boolean;
  defaultDocument: string;
  apiKeys: Record<string, string>;
}

function Countries(): JSX.Element {
  const { success, error } = useToast();
  const [activeCountry, setActiveCountry] = useState<string>(getDefaultCountry().code);
  const [settings, setSettings] = useState<Record<string, CountrySettings>>({
    PE: { code: 'PE', enabled: true, defaultDocument: '', apiKeys: {} },
    CL: { code: 'CL', enabled: false, defaultDocument: '', apiKeys: {} },
    CO: { code: 'CO', enabled: false, defaultDocument: '', apiKeys: {} },
    MX: { code: 'MX', enabled: false, defaultDocument: '', apiKeys: {} },
    ES: { code: 'ES', enabled: false, defaultDocument: '', apiKeys: {} },
  });
  const [testDocument, setTestDocument] = useState('');
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message?: string;
  } | null>(null);

  const country = getCountryByCode(activeCountry) || getDefaultCountry();

  const handleToggleCountry = (code: string) => {
    setSettings((prev: Record<string, CountrySettings>) => ({
      ...prev,
      [code]: { ...prev[code], enabled: !prev[code].enabled },
    }));
    success(`País ${code} ${settings[code]?.enabled ? 'desactivado' : 'activado'}`);
  };

  const handleTestDocument = () => {
    const result = validateDocumentFormat(activeCountry, testDocument);
    setValidationResult(result);
    if (result.valid) {
      success('Documento válido');
    } else {
      error(result.message || 'Documento inválido');
    }
  };

  const handleSave = () => {
    success('Configuración guardada');
  };

  return (
    <div className="countries-page">
      <div className="page-header">
        <h1>🌍 Multi-País</h1>
        <p className="subtitle">Configuración de países y validación de documentos</p>
      </div>

      <div className="countries-grid">
        <div className="countries-sidebar">
          <h3>Países Soportados</h3>
          <div className="country-list">
            {SUPPORTED_COUNTRIES.map(c => (
              <button
                key={c.code}
                className={`country-item ${activeCountry === c.code ? 'active' : ''} ${settings[c.code]?.enabled ? 'enabled' : 'disabled'}`}
                onClick={() => setActiveCountry(c.code)}
              >
                <span className="country-flag">{c.flag}</span>
                <span className="country-name">{c.name}</span>
                <span className={`status-badge ${settings[c.code]?.enabled ? 'on' : 'off'}`}>
                  {settings[c.code]?.enabled ? 'ON' : 'OFF'}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="countries-detail">
          <div className="detail-header">
            <span className="detail-flag">{country.flag}</span>
            <h2>{country.name}</h2>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={settings[activeCountry]?.enabled}
                onChange={() => handleToggleCountry(activeCountry)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div className="detail-cards">
            <div className="info-card">
              <h4>Moneda</h4>
              <p className="big">{country.currencySymbol}</p>
              <p className="muted">{country.currency}</p>
              <p className="sample">Ej: {formatCurrency(1000, country.code)}</p>
            </div>

            <div className="info-card">
              <h4>Documento</h4>
              <p className="big">{country.documentLabel}</p>
              <p className="muted">{country.documentExample}</p>
            </div>

            <div className="info-card">
              <h4>Impuesto</h4>
              <p className="big">{(country.vatRate * 100).toFixed(0)}%</p>
              <p className="muted">{country.vatLabel}</p>
            </div>

            <div className="info-card">
              <h4>Teléfono</h4>
              <p className="big">{country.phonePrefix}</p>
              <p className="muted">{country.timezone}</p>
            </div>
          </div>

          <div className="validation-section">
            <h3>🧪 Validador de Documentos</h3>
            <p>
              Prueba la validación de {country.documentLabel} para {country.name}
            </p>
            <div className="validation-input">
              <input
                type="text"
                value={testDocument}
                onChange={e => setTestDocument(e.target.value)}
                placeholder={getDocumentPlaceholder(activeCountry)}
                className={validationResult ? (validationResult.valid ? 'valid' : 'invalid') : ''}
              />
              <button onClick={handleTestDocument} className="btn-primary">
                Validar
              </button>
            </div>
            {validationResult && (
              <div className={`validation-result ${validationResult.valid ? 'success' : 'error'}`}>
                {validationResult.valid ? '✅' : '❌'}{' '}
                {validationResult.message || (validationResult.valid ? 'Válido' : 'Inválido')}
              </div>
            )}
          </div>

          <div className="detail-section">
            <h3>🔗 Fuentes de Verificación</h3>
            <div className="sources-grid">
              {activeCountry === 'PE' && (
                <>
                  <div className="source-item">
                    <span>☀️</span> SUNAT
                  </div>
                  <div className="source-item">
                    <span>📋</span> OSCE
                  </div>
                  <div className="source-item">
                    <span>⚖️</span> TCE
                  </div>
                  <div className="source-item">
                    <span>🛡️</span> INDECOPI
                  </div>
                </>
              )}
              {activeCountry === 'CL' && (
                <>
                  <div className="source-item">
                    <span>🏛️</span> SII
                  </div>
                  <div className="source-item">
                    <span>🛒</span> ChileCompra
                  </div>
                  <div className="source-item">
                    <span>⚖️</span> TDLC
                  </div>
                </>
              )}
              {activeCountry === 'CO' && (
                <>
                  <div className="source-item">
                    <span>🏛️</span> DIAN
                  </div>
                  <div className="source-item">
                    <span>🛒</span> SECOP
                  </div>
                  <div className="source-item">
                    <span>🛡️</span> SIC
                  </div>
                </>
              )}
              {activeCountry === 'MX' && (
                <>
                  <div className="source-item">
                    <span>🏛️</span> SAT
                  </div>
                  <div className="source-item">
                    <span>🛒</span> CompraNet
                  </div>
                  <div className="source-item">
                    <span>🛡️</span> COFECE
                  </div>
                </>
              )}
              {activeCountry === 'ES' && (
                <>
                  <div className="source-item">
                    <span>🏛️</span> AEAT
                  </div>
                  <div className="source-item">
                    <span>📜</span> BOE
                  </div>
                  <div className="source-item">
                    <span>🛡️</span> CNMC
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="detail-section">
            <h3>⚖️ Marco Legal</h3>
            <p className="legal-text">
              {activeCountry === 'PE' && 'Ley N° 29733 - Protección de Datos Personales'}
              {activeCountry === 'CL' && 'Ley N° 19.628 - Protección de la Vida Privada'}
              {activeCountry === 'CO' && 'Ley 1581 de 2012 - Protección de Datos Personales'}
              {activeCountry === 'MX' &&
                'Ley Federal de Protección de Datos Personales en Posesión de los Particulares'}
              {activeCountry === 'ES' &&
                'RGPD (Reglamento General de Protección de Datos) + LOPDGDD'}
            </p>
          </div>

          <div className="actions">
            <button onClick={handleSave} className="btn-primary">
              💾 Guardar Configuración
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Countries;
