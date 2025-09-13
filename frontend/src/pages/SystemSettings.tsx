import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import SMTPSettingsComponent from '../components/SMTPSettings';


import { 
  Settings, 
  Mail, 
 
 
  ChevronRight,
  AlertCircle
} from 'lucide-react';

const SystemSettings: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract section from URL path
  const pathParts = location.pathname.split('/');
  const currentSection = pathParts[2] || 'overview';
  
  const sections = [
    {
      id: 'overview',
      name: 'Overview',
      icon: <Settings size={16} />,
      description: 'System settings overview and navigation',
      component: null
    },

    {
      id: 'smtp',
      name: 'SMTP Configuration',
      icon: <Mail size={16} />,
      description: 'Configure email server settings for system emails',
      component: SMTPSettingsComponent,
      adminOnly: true
    },


  ];

  const visibleSections = sections.filter(section => !section.adminOnly || user?.role === 'admin');

  const handleSectionChange = (sectionId: string) => {
    navigate(`/settings/${sectionId}`);
  };

  const currentSectionData = sections.find(s => s.id === currentSection) || sections[0];
  const CurrentComponent = currentSectionData.component;

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - 2/3, 1/3 format for settings */
          .dense-dashboard {
            padding: 8px 12px;
            max-width: 100%;
            font-size: 13px;
          }
          .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .header-left h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            color: var(--neutral-800);
          }
          .header-subtitle {
            font-size: 12px;
            color: var(--neutral-600);
            margin: 2px 0 0 0;
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          
          /* Settings navigation */
          .settings-nav {
            padding: 0;
          }
          .nav-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid var(--neutral-100);
            cursor: pointer;
            transition: all 0.15s;
            font-size: 13px;
          }
          .nav-item:hover {
            background: var(--neutral-50);
          }
          .nav-item.active {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
            color: var(--primary-blue);
          }
          .nav-item.disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .nav-item.disabled:hover {
            background: white;
          }
          .nav-icon {
            margin-right: 8px;
            flex-shrink: 0;
          }
          .nav-content {
            flex: 1;
          }
          .nav-title {
            font-weight: 500;
            margin-bottom: 2px;
          }
          .nav-description {
            font-size: 11px;
            color: var(--neutral-500);
            line-height: 1.3;
          }
          .nav-chevron {
            margin-left: auto;
            color: var(--neutral-400);
          }
          
          /* Settings content area */
          .settings-content {
            padding: 12px;
          }
          .content-header {
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .content-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--neutral-800);
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .content-description {
            font-size: 12px;
            color: var(--neutral-600);
            margin: 0;
          }
          
          /* Overview section */
          .overview-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
          }
          .overview-card {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 12px;
          }
          .overview-card h3 {
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
            margin: 0 0 8px 0;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .overview-card p {
            font-size: 12px;
            color: var(--neutral-600);
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          .overview-card .card-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
          }
          .btn-card {
            padding: 4px 8px;
            font-size: 11px;
            border: 1px solid var(--primary-blue);
            background: white;
            color: var(--primary-blue);
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.15s;
          }
          .btn-card:hover {
            background: var(--primary-blue);
            color: white;
          }
          .btn-card:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          /* Access denied styling */
          .access-denied {
            background: var(--warning-yellow-light);
            border: 1px solid var(--warning-yellow);
            color: var(--warning-yellow-dark);
            padding: 12px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
          }
          
          /* Admin badge */
          .admin-badge {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 9px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 6px;
          }
          
          /* Component wrapper */
          .component-wrapper {
            flex: 1;
            overflow: auto;
          }
          
          /* Override component styles to fit our layout */
          .component-wrapper .min-h-screen {
            min-height: auto !important;
          }
          .component-wrapper .py-8 {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
          }
          .component-wrapper .max-w-7xl {
            max-width: none !important;
          }
          .component-wrapper .mx-auto {
            margin-left: 0 !important;
            margin-right: 0 !important;
          }
          .component-wrapper .px-4,
          .component-wrapper .sm\\:px-6,
          .component-wrapper .lg\\:px-8 {
            padding-left: 0 !important;
            padding-right: 0 !important;
          }
          
          /* Hide component headers since we have our own */
          .component-wrapper h1:first-child,
          .component-wrapper .mb-8:first-child h1,
          .component-wrapper > div > h1:first-child {
            display: none;
          }
          .component-wrapper .mb-8:first-child p,
          .component-wrapper > div > p:first-of-type {
            display: none;
          }
          .component-wrapper .mb-8:first-child,
          .component-wrapper > div:first-child {
            margin-bottom: 0 !important;
          }
          
          /* Override Tailwind classes that might interfere */
          .component-wrapper .bg-gray-50 {
            background: white !important;
          }
          .component-wrapper .py-8 {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>System Settings</h1>
          <p className="header-subtitle">Configure system-wide settings and preferences</p>
        </div>
      </div>

      {/* 2/3, 1/3 dashboard grid */}
      <div className="dashboard-grid">
        {/* Left 2/3: Settings Content */}
        <div className="dashboard-section">
          <div className="section-header">
            {currentSectionData.name}
          </div>
          <div className="compact-content">
            <div className="settings-content">
              <div className="content-header">
                <h2 className="content-title">
                  {currentSectionData.icon}
                  {currentSectionData.name}
                  {currentSectionData.adminOnly && <span className="admin-badge">Admin Only</span>}
                </h2>
                <p className="content-description">{currentSectionData.description}</p>
              </div>

              {/* Check admin access for admin-only sections */}
              {currentSectionData.adminOnly && user?.role !== 'admin' ? (
                <div className="access-denied">
                  <AlertCircle size={16} />
                  <div>
                    <strong>Access Restricted</strong><br />
                    Only administrators can access this section.
                  </div>
                </div>
              ) : currentSection === 'overview' ? (
                /* Overview Section */
                <div className="overview-grid">


                  <div className="overview-card">
                    <h3>
                      <Mail size={16} />
                      SMTP Configuration
                      <span className="admin-badge">Admin</span>
                    </h3>
                    <p>
                      Configure the email server settings that will be used for all system emails. 
                      Test the configuration to ensure emails are delivered properly.
                    </p>
                    <div className="card-actions">
                      <button 
                        className="btn-card"
                        onClick={() => handleSectionChange('smtp')}
                        disabled={user?.role !== 'admin'}
                      >
                        Configure SMTP
                      </button>
                    </div>
                  </div>




                </div>
              ) : CurrentComponent ? (
                /* Render the selected component */
                <div className="component-wrapper">
                  <CurrentComponent />
                </div>
              ) : (
                <div className="access-denied">
                  <AlertCircle size={16} />
                  <div>Section not found or not available.</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right 1/3: Navigation or Future Use */}
        <div className="dashboard-section">
          <div className="section-header">
            Additional Information
          </div>
          <div className="compact-content">
            <div style={{ padding: '12px', color: 'var(--neutral-500)', fontSize: '12px', textAlign: 'center' }}>
              <p>This space is reserved for field details or future enhancements.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;