import React from 'react';

type BadgeVariant = 'primary' | 'success' | 'warning' | 'danger' | 'neutral';
type StatusType = 'active' | 'inactive' | 'succeeded' | 'failed' | 'running' | 'pending' | 'queued' | 'maintenance' | 'decommissioned' | 'online' | 'offline';

interface StatusBadgeProps {
  status?: StatusType;
  variant?: BadgeVariant;
  children?: React.ReactNode;
  showDot?: boolean;
}

/**
 * Standardized status badge component
 * Automatically maps status types to appropriate colors
 */
const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  variant, 
  children, 
  showDot = false 
}) => {
  // Auto-determine variant from status if not explicitly provided
  const getVariant = (): BadgeVariant => {
    if (variant) return variant;
    
    if (!status) return 'neutral';
    
    switch (status) {
      case 'active':
      case 'succeeded':
      case 'online':
        return 'success';
      case 'inactive':
      case 'failed':
      case 'offline':
        return 'danger';
      case 'running':
      case 'pending':
        return 'primary';
      case 'queued':
      case 'maintenance':
        return 'warning';
      case 'decommissioned':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  const getDotClass = (): string => {
    const v = getVariant();
    switch (v) {
      case 'success':
        return 'active';
      case 'danger':
        return 'inactive';
      case 'warning':
        return 'warning';
      default:
        return '';
    }
  };

  const badgeVariant = getVariant();
  const displayText = children || (status ? status.charAt(0).toUpperCase() + status.slice(1) : '');

  return (
    <span className={`badge badge-${badgeVariant}`}>
      {showDot && <span className={`status-dot ${getDotClass()}`} />}
      {displayText}
    </span>
  );
};

export default StatusBadge;