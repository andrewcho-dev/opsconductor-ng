import React from 'react';
import { Link } from 'react-router-dom';
import { LucideIcon } from 'lucide-react';

interface StatPillProps {
  icon: LucideIcon;
  label: string;
  count?: number;
  to: string;
}

/**
 * Standardized stat pill component for page headers
 * Displays a count with an icon and links to a page
 */
const StatPill: React.FC<StatPillProps> = ({ icon: Icon, label, count, to }) => {
  const displayText = count !== undefined ? `${count} ${label}` : label;
  
  return (
    <Link to={to} className="stat-pill">
      <Icon size={14} />
      <span>{displayText}</span>
    </Link>
  );
};

export default StatPill;