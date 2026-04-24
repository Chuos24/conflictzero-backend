import { useState } from 'react'
import api from '../services/api'
import { downloadFile } from '../utils/helpers'

export interface UseExportReturn {
  exporting: boolean
  error: string | null
  exportToCSV: (endpoint: string, filename: string) => Promise<boolean>
  exportVerifications: () => Promise<boolean>
  exportToPDF: (elementId: string, filename: string) => Promise<boolean>
}

export function useExport(): UseExportReturn {
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const exportToCSV = async (endpoint: string, filename: string): Promise<boolean> => {
    setExporting(true)
    setError(null)
    
    try {
      const response = await api.get(endpoint, {
        responseType: 'blob'
      })
      
      downloadFile(response.data as Blob, filename)
      return true
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al exportar'
      setError(message)
      return false
    } finally {
      setExporting(false)
    }
  }

  const exportVerifications = async (): Promise<boolean> => {
    const date = new Date().toISOString().split('T')[0]
    return exportToCSV(
      '/dashboard/export/csv',
      `verificaciones_${date}.csv`
    )
  }

  const exportToPDF = async (elementId: string, filename: string): Promise<boolean> => {
    setExporting(true)
    setError(null)
    
    try {
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al generar PDF'
      setError(message)
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
