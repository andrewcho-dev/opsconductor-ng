import React from 'react';

interface PageHeaderProps {
  title: string;
  children?: React.ReactNode;
}

/**
 * Standardized page header component
 * Used across all pages for consistent layout
 */
const PageHeader: React.FC<PageHeaderProps> = ({ title, children }) => {
  return (
    <div className="page-header">
      <div className="page-header-left">
        <h1>{title}</h1>
      </div>
      <div className="page-header-right">
        {children}
      </div>
    </div>
  );
};

export default PageHeader;