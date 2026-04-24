/**
 * Utility functions for Conflict Zero Dashboard
 */

interface FormatDateOptions {
  year?: 'numeric' | '2-digit';
  month?: 'numeric' | '2-digit' | 'short' | 'long' | 'narrow';
  day?: 'numeric' | '2-digit';
  hour?: 'numeric' | '2-digit';
  minute?: 'numeric' | '2-digit';
  second?: 'numeric' | '2-digit';
}

/**
 * Format date to localized string
 */
export function formatDate(date: string | Date | null | undefined, options: FormatDateOptions = {}): string {
  if (!date) return 'N/A';

  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Fecha inválida';

  const defaultOptions: FormatDateOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };

  return d.toLocaleDateString('es-PE', defaultOptions as Intl.DateTimeFormatOptions);
}

/**
 * Format datetime to localized string
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';

  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Fecha inválida';

  return d.toLocaleString('es-PE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format number with locale
 */
export function formatNumber(num: number | null | undefined, decimals = 0): string {
  if (num === null || num === undefined) return 'N/A';

  return Number(num).toLocaleString('es-PE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * Format currency in PEN
 */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return 'N/A';

  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency: 'PEN'
  }).format(amount);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string | null | undefined, maxLength = 50): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;

  return text.substring(0, maxLength) + '...';
}

/**
 * Get risk level color
 */
export function getRiskColor(score: number): string {
  if (score >= 80) return '#4caf50'; // Green - Low risk
  if (score >= 60) return '#ff9800'; // Orange - Medium risk
  if (score >= 40) return '#f44336'; // Red - High risk
  return '#8b0000'; // Dark red - Critical
}

/**
 * Get risk level label
 */
export function getRiskLabel(score: number): string {
  if (score >= 80) return 'Bajo Riesgo';
  if (score >= 60) return 'Riesgo Medio';
  if (score >= 40) return 'Alto Riesgo';
  return 'Riesgo Crítico';
}

/**
 * Get status badge class
 */
export function getStatusClass(status: string | null | undefined): string {
  const statusMap: Record<string, string> = {
    'completed': 'status-success',
    'pending': 'status-pending',
    'processing': 'status-processing',
    'error': 'status-error',
    'failed': 'status-error',
    'accepted': 'status-success',
    'rejected': 'status-error',
    'active': 'status-success',
    'inactive': 'status-inactive',
    'revoked': 'status-error'
  };

  return statusMap[status?.toLowerCase() ?? ''] || 'status-default';
}

/**
 * Validate RUC format
 */
export function isValidRUC(ruc: string | null | undefined): boolean {
  if (!ruc) return false;

  // RUC must be 11 digits
  if (!/^\d{11}$/.test(ruc)) return false;

  // Check if starts with valid digits (10, 15, 16, 17, 20)
  const firstTwo = parseInt(ruc.substring(0, 2));
  const validPrefixes = [10, 15, 16, 17, 20];

  return validPrefixes.includes(firstTwo);
}

/**
 * Generate UUID v4
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c: string) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => void>(
  func: T,
  wait = 300
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: unknown[]) => void>(
  func: T,
  limit = 300
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  return function(this: unknown, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Deep clone object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Download file from blob
 */
export function downloadFile(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
}

/**
 * Parse query params from URL
 */
export function parseQueryParams(): Record<string, string> {
  const params = new URLSearchParams(window.location.search);
  const result: Record<string, string> = {};

  for (const [key, value] of params.entries()) {
    result[key] = value;
  }

  return result;
}

/**
 * Build query string from object
 */
export function buildQueryString(params: Record<string, unknown>): string {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      queryParams.append(key, String(value));
    }
  });

  return queryParams.toString();
}

/**
 * LocalStorage helpers with JSON support
 */
export const storage = {
  get<T>(key: string, defaultValue: T | null = null): T | null {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) as T : defaultValue;
    } catch (e) {
      return defaultValue;
    }
  },

  set<T>(key: string, value: T): boolean {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  },

  remove(key: string): boolean {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      return false;
    }
  },

  clear(): boolean {
    try {
      localStorage.clear();
      return true;
    } catch (e) {
      return false;
    }
  }
};

/**
 * Calculate time ago
 */
export function timeAgo(date: string | Date): string {
  const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);

  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + ' años atrás';

  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + ' meses atrás';

  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + ' días atrás';

  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + ' horas atrás';

  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + ' minutos atrás';

  return 'hace unos segundos';
}
