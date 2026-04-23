import React from 'react';
import './Skeleton.css';

/**
 * Skeleton - Componente de placeholder para estados de carga
 * 
 * Referencia: Material Design Skeleton Screens
 * https://material.io/design/communication/launch-screen.html#skeleton-screen
 */

export const Skeleton = ({ 
  variant = 'text', 
  width, 
  height, 
  className = '',
  count = 1,
  circle = false,
  ...props 
}) => {
  const style = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;
  if (circle) style.borderRadius = '50%';

  const elements = [];
  for (let i = 0; i < count; i++) {
    elements.push(
      <span
        key={i}
        className={`cz-skeleton cz-skeleton--${variant} ${className}`}
        style={style}
        {...props}
      >
        &zwnj;
      </span>
    );
  }

  return <>{elements}</>;
};

/**
 * SkeletonCard - Esqueleto de tarjeta para loading states
 */
export const SkeletonCard = ({ lines = 3, hasImage = false }) => (
  <div className="cz-skeleton-card">
    {hasImage && <Skeleton variant="rect" width="100%" height={160} className="cz-skeleton-card__image" />}
    <div className="cz-skeleton-card__content">
      <Skeleton variant="text" width="60%" height={24} />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} variant="text" width={`${Math.random() * 40 + 40}%`} />
      ))}
    </div>
  </div>
);

/**
 * SkeletonTable - Esqueleto de tabla para loading states
 */
export const SkeletonTable = ({ rows = 5, columns = 4 }) => (
  <div className="cz-skeleton-table">
    <div className="cz-skeleton-table__header">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} variant="text" width={`${80 + Math.random() * 20}%`} height={20} />
      ))}
    </div>
    <div className="cz-skeleton-table__body">
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={rowIdx} className="cz-skeleton-table__row">
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton key={colIdx} variant="text" width={`${60 + Math.random() * 40}%`} />
          ))}
        </div>
      ))}
    </div>
  </div>
);

/**
 * SkeletonProfile - Esqueleto de perfil para loading states
 */
export const SkeletonProfile = () => (
  <div className="cz-skeleton-profile">
    <div className="cz-skeleton-profile__header">
      <Skeleton variant="circle" width={80} height={80} />
      <div className="cz-skeleton-profile__info">
        <Skeleton variant="text" width={200} height={28} />
        <Skeleton variant="text" width={150} />
        <Skeleton variant="text" width={100} />
      </div>
    </div>
    <div className="cz-skeleton-profile__stats">
      <SkeletonCard lines={2} />
      <SkeletonCard lines={2} />
      <SkeletonCard lines={2} />
    </div>
  </div>
);

export default Skeleton;
