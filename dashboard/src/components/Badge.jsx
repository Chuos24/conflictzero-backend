import React from 'react'
import './Badge.css'

/**
 * Reusable Badge Component
 * 
 * @param {string} variant - Badge style: 'success', 'warning', 'error', 'info', 'default'
 * @param {string} size - Badge size: 'small', 'medium', 'large'
 * @param {React.ReactNode} children - Badge content
 * @param {boolean} pulse - Enable pulse animation
 * @param {string} className - Additional CSS classes
 */
function Badge({ 
  variant = 'default', 
  size = 'medium', 
  children, 
  pulse = false,
  className = ''
}) {
  const classes = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    pulse && 'badge--pulse',
    className
  ].filter(Boolean).join(' ')
  
  return (
    <span className={classes}>
      {children}
    </span>
  )
}

export default Badge
