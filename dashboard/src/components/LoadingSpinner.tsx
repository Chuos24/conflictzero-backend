import React from 'react'
import './LoadingSpinner.css'

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'
  text?: string
}

function LoadingSpinner({ size = 'medium', text = 'Cargando...' }: LoadingSpinnerProps): JSX.Element {
  const sizeClass = `spinner-${size}`
  
  return (
    <div className="loading-spinner-container">
      <div className={`loading-spinner ${sizeClass}`}></div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  )
}

export default LoadingSpinner