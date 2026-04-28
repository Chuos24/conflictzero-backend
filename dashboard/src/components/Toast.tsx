import { useEffect, useState } from 'react'
import './Toast.css'

type ToastType = 'success' | 'error' | 'warning' | 'info'

const icons: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ'
}

export interface ToastProps {
  message: string
  type: ToastType
  onClose: () => void
}

function Toast({ message, type, onClose }: ToastProps): JSX.Element {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Trigger animation
    const timer = setTimeout(() => setIsVisible(true), 10)
    return () => clearTimeout(timer)
  }, [])

  const handleClose = () => {
    setIsVisible(false)
    setTimeout(onClose, 300)
  }

  return (
    <div className={`toast toast-${type} ${isVisible ? 'visible' : ''}`}>
      <span className="toast-icon">{icons[type]}</span>
      <span className="toast-message">{message}</span>
      <button className="toast-close" onClick={handleClose}>×</button>
    </div>
  )
}

export default Toast