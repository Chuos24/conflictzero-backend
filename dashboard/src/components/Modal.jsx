import React, { useEffect, useRef } from 'react'
import './Modal.css'

/**
 * Reusable Modal Component
 * 
 * @param {boolean} isOpen - Whether modal is visible
 * @param {Function} onClose - Callback when modal is closed
 * @param {string} title - Modal title
 * @param {React.ReactNode} children - Modal content
 * @param {string} size - Modal size: 'small', 'medium', 'large', 'fullscreen'
 * @param {boolean} showCloseButton - Whether to show close button
 * @param {boolean} closeOnOverlay - Whether to close on overlay click
 * @param {boolean} closeOnEscape - Whether to close on Escape key
 */
function Modal({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'medium',
  showCloseButton = true,
  closeOnOverlay = true,
  closeOnEscape = true
}) {
  const modalRef = useRef(null)
  
  useEffect(() => {
    const handleEscape = (e) => {
      if (closeOnEscape && e.key === 'Escape') {
        onClose()
      }
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, closeOnEscape, onClose])
  
  const handleOverlayClick = (e) => {
    if (closeOnOverlay && e.target === e.currentTarget) {
      onClose()
    }
  }
  
  if (!isOpen) return null
  
  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div 
        className={`modal modal--${size}`} 
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal__header">
          {title && (
            <h2 id="modal-title" className="modal__title">
              {title}
            </h2>
          )}
          {showCloseButton && (
            <button 
              className="modal__close-btn"
              onClick={onClose}
              aria-label="Cerrar"
            >
              ×
            </button>
          )}
        </div>
        <div className="modal__body">
          {children}
        </div>
      </div>
    </div>
  )
}

export default Modal
