/**
 * Conflict Zero - SDK JavaScript/TypeScript Oficial
 * ================================================
 * SDK para integrar la API de Conflict Zero en aplicaciones JS/TS.
 *
 * Uso:
 *   import { ConflictZeroClient } from 'conflictzero';
 *
 *   const client = new ConflictZeroClient({ apiKey: 'tu_api_key' });
 *   const company = await client.verifyRUC('20100012345');
 */

export class ConflictZeroError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.name = 'ConflictZeroError';
    this.statusCode = statusCode;
  }
}

export class AuthenticationError extends ConflictZeroError {
  constructor(message = 'API key inválida o expirada') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends ConflictZeroError {
  constructor(message = 'Rate limit excedido') {
    super(message, 429);
    this.name = 'RateLimitError';
  }
}

export class NotFoundError extends ConflictZeroError {
  constructor(message = 'Recurso no encontrado') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends ConflictZeroError {
  constructor(message = 'Error de validación') {
    super(message, 422);
    this.name = 'ValidationError';
  }
}

export class ConflictZeroClient {
  /**
   * Cliente oficial de Conflict Zero para JavaScript/TypeScript.
   *
   * @param {Object} config
   * @param {string} config.apiKey - Tu API key de Conflict Zero
   * @param {string} [config.baseURL='https://api.conflictzero.com'] - URL base de la API
   * @param {number} [config.timeout=30000] - Timeout en milisegundos
   */
  constructor({ apiKey, baseURL = 'https://api.conflictzero.com', timeout = 30000 }) {
    this.apiKey = apiKey;
    this.baseURL = baseURL.replace(/\/$/, '');
    this.timeout = timeout;
  }

  async _request(method, endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'User-Agent': 'ConflictZero-SDK-JS/1.0.0'
        },
        signal: controller.signal,
        ...options
      });

      clearTimeout(timeoutId);

      if (response.status === 401) {
        throw new AuthenticationError();
      } else if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || '60';
        throw new RateLimitError(`Rate limit excedido. Reintenta en ${retryAfter}s`);
      } else if (response.status === 404) {
        throw new NotFoundError();
      } else if (response.status === 422) {
        const body = await response.text();
        throw new ValidationError(`Error de validación: ${body}`);
      } else if (response.status >= 500) {
        throw new ConflictZeroError(`Error del servidor: ${response.status}`, response.status);
      }

      if (!response.ok) {
        throw new ConflictZeroError(`HTTP ${response.status}`, response.status);
      }

      const data = await response.json();
      return { success: true, data, statusCode: response.status };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new ConflictZeroError('Request timeout', 408);
      }
      throw error;
    }
  }

  // ============================================================
  // VERIFICACIÓN
  // ============================================================

  /** Verifica un RUC peruano */
  async verifyRUC(ruc) {
    return this._request('GET', `/api/v2/verify/${ruc}`);
  }

  /** Verifica múltiples RUCs en una sola petición */
  async verifyBulk(rucs) {
    return this._request('POST', '/api/v2/verify/bulk', {
      body: JSON.stringify({ rucs })
    });
  }

  /** Obtiene detalles completos de una empresa */
  async getCompanyDetails(ruc) {
    return this._request('GET', `/api/v2/company/${ruc}`);
  }

  // ============================================================
  // COMPARACIÓN
  // ============================================================

  /** Compara hasta 10 empresas */
  async compareCompanies(rucs) {
    return this._request('POST', '/api/v2/compare', {
      body: JSON.stringify({ rucs })
    });
  }

  // ============================================================
  // SCORING
  // ============================================================

  /** Obtiene el score de riesgo de un proveedor */
  async getRiskScore(ruc) {
    return this._request('GET', `/api/v2/score/${ruc}`);
  }

  /** Obtiene el certificado de compliance */
  async getComplianceCertificate(ruc) {
    return this._request('GET', `/api/v2/certificate/${ruc}`);
  }

  // ============================================================
  // RED DE PROVEEDORES
  // ============================================================

  /** Obtiene la red de proveedores del usuario */
  async getNetwork() {
    return this._request('GET', '/api/v2/network');
  }

  /** Agrega un proveedor a la red */
  async addToNetwork(ruc, name, tags = []) {
    return this._request('POST', '/api/v2/network', {
      body: JSON.stringify({ ruc, name, tags })
    });
  }

  /** Elimina un proveedor de la red */
  async removeFromNetwork(companyId) {
    return this._request('DELETE', `/api/v2/network/${companyId}`);
  }

  // ============================================================
  // MONITOREO
  // ============================================================

  /** Obtiene alertas de monitoreo */
  async getMonitoringAlerts(status) {
    const params = status ? `?status=${status}` : '';
    return this._request('GET', `/api/v2/monitoring/alerts${params}`);
  }

  /** Obtiene cambios detectados */
  async getMonitoringChanges(severity) {
    const params = severity ? `?severity=${severity}` : '';
    return this._request('GET', `/api/v2/monitoring/changes${params}`);
  }

  /** Crea un snapshot manual de un proveedor */
  async createSnapshot(companyId) {
    return this._request('POST', `/api/v2/monitoring/snapshots/${companyId}`);
  }

  /** Ejecuta monitoreo manual */
  async runMonitoring() {
    return this._request('POST', '/api/v2/monitoring/run');
  }

  /** Obtiene estadísticas de monitoreo */
  async getMonitoringStats() {
    return this._request('GET', '/api/v2/monitoring/stats');
  }

  // ============================================================
  // WEBHOOKS
  // ============================================================

  /** Registra un webhook para recibir eventos */
  async registerWebhook(url, events, secret) {
    const payload = { url, events };
    if (secret) payload.secret = secret;
    return this._request('POST', '/api/v2/webhooks', {
      body: JSON.stringify(payload)
    });
  }

  /** Lista webhooks registrados */
  async listWebhooks() {
    return this._request('GET', '/api/v2/webhooks');
  }

  /** Elimina un webhook */
  async deleteWebhook(webhookId) {
    return this._request('DELETE', `/api/v2/webhooks/${webhookId}`);
  }

  // ============================================================
  // ADMIN
  // ============================================================

  /** Obtiene estadísticas del dashboard (solo admin) */
  async getDashboardStats() {
    return this._request('GET', '/api/v2/admin/dashboard');
  }

  /** Obtiene usuarios recientes (solo admin) */
  async getRecentUsers(limit = 50) {
    return this._request('GET', `/api/v2/admin/users?limit=${limit}`);
  }

  // ============================================================
  // UTILIDADES
  // ============================================================

  /** Verifica el estado de la API */
  async healthCheck() {
    return this._request('GET', '/api/v2/health');
  }
}

export default ConflictZeroClient;
