import React from 'react'
import './Card.css'

export interface CardProps {
  children: React.ReactNode
  title?: string
  icon?: React.ReactNode
  action?: React.ReactNode
  className?: string
  hoverable?: boolean
  onClick?: () => void
}

function Card({ 
  children, 
  title = undefined, 
  icon = undefined,
  action = undefined,
  className = '',
  hoverable = false,
  onClick = undefined
}: CardProps): JSX.Element {
  const classes = [
    'card',
    hoverable && 'card--hoverable',
    onClick && 'card--clickable',
    className
  ].filter(Boolean).join(' ')
  
  return (
    <div 
      className={classes}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {(title || icon || action) && (
        <div className="card__header">
          <div className="card__title-wrapper">
            {icon && <span className="card__icon">{icon}</span>}
            {title && <h3 className="card__title">{title}</h3>}
          </div>
          {action && <div className="card__action">{action}</div>}
        </div>
      )}
      <div className="card__body">
        {children}
      </div>
    </div>
  )
}

export default Card