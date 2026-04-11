/**
 * Utility functions for Conflict Zero Dashboard
 */

/**
 * Format date to localized string
 */
export function formatDate(date, options = {}) {
  if (!date) return 'N/A'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return 'Fecha inválida'
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  }
  
  return d.toLocaleDateString('es-PE', defaultOptions)
}

/**
 * Format datetime to localized string
 */
export function formatDateTime(date) {
  if (!date) return 'N/A'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return 'Fecha inválida'
  
  return d.toLocaleString('es-PE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Format number with locale
 */
export function formatNumber(num, decimals = 0) {
  if (num === null || num === undefined) return 'N/A'
  
  return Number(num).toLocaleString('es-PE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format currency in PEN
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return 'N/A'
  
  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency: 'PEN'
  }).format(amount)
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, maxLength = 50) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  
  return text.substring(0, maxLength) + '...'
}

/**
 * Get risk level color
 */
export function getRiskColor(score) {
  if (score >= 80) return '#4caf50' // Green - Low risk
  if (score >= 60) return '#ff9800' // Orange - Medium risk
  if (score >= 40) return '#f44336' // Red - High risk
  return '#8b0000' // Dark red - Critical
}

/**
 * Get risk level label
 */
export function getRiskLabel(score) {
  if (score >= 80) return 'Bajo Riesgo'
  if (score >= 60) return 'Riesgo Medio'
  if (score >= 40) return 'Alto Riesgo'
  return 'Riesgo Crítico'
}

/**
 * Get status badge class
 */
export function getStatusClass(status) {
  const statusMap = {
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
  }
  
  return statusMap[status?.toLowerCase()] || 'status-default'
}

/**
 * Validate RUC format
 */
export function isValidRUC(ruc) {
  if (!ruc) return false
  
  // RUC must be 11 digits
  if (!/^\d{11}$/.test(ruc)) return false
  
  // Check if starts with valid digits (10, 15, 16, 17, 20)
  const firstTwo = parseInt(ruc.substring(0, 2))
  const validPrefixes = [10, 15, 16, 17, 20]
  
  return validPrefixes.includes(firstTwo)
}

/**
 * Generate UUID v4
 */
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * Debounce function
 */
export function debounce(func, wait = 300) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Throttle function
 */
export function throttle(func, limit = 300) {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Deep clone object
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Download file from blob
 */
export function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy:', err)
    return false
  }
}

/**
 * Parse query params from URL
 */
export function parseQueryParams() {
  const params = new URLSearchParams(window.location.search)
  const result = {}
  
  for (const [key, value] of params.entries()) {
    result[key] = value
  }
  
  return result
}

/**
 * Build query string from object
 */
export function buildQueryString(params) {
  const queryParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      queryParams.append(key, value)
    }
  })
  
  return queryParams.toString()
}

/**
 * LocalStorage helpers with JSON support
 */
export const storage = {
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (e) {
      return defaultValue
    }
  },
  
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
      return true
    } catch (e) {
      return false
    }
  },
  
  remove(key) {
    try {
      localStorage.removeItem(key)
      return true
    } catch (e) {
      return false
    }
  },
  
  clear() {
    try {
      localStorage.clear()
      return true
    } catch (e) {
      return false
    }
  }
}

/**
 * Calculate time ago
 */
export function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000)
  
  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + ' años atrás'
  
  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + ' meses atrás'
  
  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + ' días atrás'
  
  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + ' horas atrás'
  
  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + ' minutos atrás'
  
  return 'hace unos segundos'
}
