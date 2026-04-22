import { useState } from 'react'
import api from '../services/api'
import { downloadFile } from '../utils/helpers'

export function useExport() {
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState(null)

  const exportToCSV = async (endpoint, filename) => {
    setExporting(true)
    setError(null)
    
    try {
      const response = await api.get(endpoint, {
        responseType: 'blob'
      })
      
      downloadFile(response.data, filename)
      return true
    } catch (err) {
      setError(err.message || 'Error al exportar')
      return false
    } finally {
      setExporting(false)
    }
  }

  const exportVerifications = async () => {
    const date = new Date().toISOString().split('T')[0]
    return exportToCSV(
      '/dashboard/export/csv',
      `verificaciones_${date}.csv`
    )
  }

  const exportToPDF = async (elementId, filename) => {
    setExporting(true)
    setError(null)
    
    try {
      // Dynamically import html2pdf only when needed
      const html2pdf = (await import('html2pdf.js')).default
      
      const element = document.getElementById(elementId)
      if (!element) {
        throw new Error('Elemento no encontrado')
      }

      const opt = {
        margin: 10,
        filename: filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      }

      await html2pdf().set(opt).from(element).save()
      return true
    } catch (err) {
      setError(err.message || 'Error al generar PDF')
      return false
    } finally {
      setExporting(false)
    }
  }

  return {
    exporting,
    error,
    exportToCSV,
    exportVerifications,
    exportToPDF
  }
}
