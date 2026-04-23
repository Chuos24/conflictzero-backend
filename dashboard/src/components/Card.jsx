import React from 'react'
import './Card.css'

/**
 * Reusable Card Component
 * 
 * @param {React.ReactNode} children - Card content
 * @param {string} title - Card title
 * @param {React.ReactNode} icon - Card icon
 * @param {React.ReactNode} action - Action button/link
 * @param {string} className - Additional CSS classes
 * @param {boolean} hoverable - Enable hover effect
 * @param {Function} onClick - Click handler
 */
function Card({ 
  children, 
  title = null, 
  icon = null,
  action = null,
  className = '',
  hoverable = false,
  onClick = null
}) {
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
