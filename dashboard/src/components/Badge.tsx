import React from 'react'
import './Badge.css'

export interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default'
  size?: 'small' | 'medium' | 'large'
  children: React.ReactNode
  pulse?: boolean
  className?: string
}

function Badge({ 
  variant = 'default', 
  size = 'medium', 
  children, 
  pulse = false,
  className = ''
}: BadgeProps): JSX.Element {
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