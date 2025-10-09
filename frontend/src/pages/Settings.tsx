import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Settings as SettingsIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { isAdmin } from '../utils/permissions';
import SMTPSettingsComponent from '../components/SMTPSettings';

type SettingSection = 'communication' | 'system' | 'security' | 'notifications';

interface SettingSectionItem {
  id: SettingSection;
  name: string;
  description: string;
}

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [selectedSection, setSelectedSection] = useState<SettingSection>('communication');

  const settingSections: SettingSectionItem[] = [
    {
      id: 'communication',
      name: 'Communication',
      description: 'Email, Slack, Teams, and webhook settings'
    },
    {
      id: 'system',
      name: 'System',
      description: 'General application configuration'
    },
    {
      id: 'security',
      name: 'Security',
      description: 'Authentication and access control'
    },
    {
      id: 'notifications',
      name: 'Notifications',
      description: 'Alert and notification preferences'
    }
  ];

  // Only allow admin users
  if (!isAdmin(user)) {
    return (
      <div className="dense-dashboard">
        <div className="dashboard-header">
          <div className="header-left">
            <h1>Settings</h1>
          </div>
          <div className="header-stats">
            <Link to="/ai-chat" className="stat-pill">
              <MessageSquare size={14} />
              <span>AI Assistant</span>
            </Link>
          </div>
        </div>
        <div className="dashboard-grid">
          <div className="dashboard-section" style={{ gridColumn: '1 / 4' }}>
            <div style={{
              backgroundColor: 'var(--warning-orange-light)',
              border: '1px solid var(--warning-orange)',
              borderRadius: 'var(--border-radius)',
              padding: 'var(--space-4)',
              margin: 'var(--space-4)'
            }}>
              <h3 style={{ fontWeight: 600, marginBottom: 'var(--space-2)', color: 'var(--warning-orange)' }}>
                Access Restricted
              </h3>
              <p style={{ margin: 0, color: 'var(--neutral-700)' }}>
                Only administrators can access system settings.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const renderSectionContent = () => {
    switch (selectedSection) {
      case 'communication':
        return (
          <div style={{ padding: 'var(--space-4)' }}>
            <SMTPSettingsComponent />
            
            {/* Placeholder for future communication settings */}
            <div style={{
              marginTop: 'var(--space-6)',
              padding: 'var(--space-4)',
              backgroundColor: 'var(--neutral-50)',
              border: '1px solid var(--neutral-200)',
              borderRadius: 'var(--border-radius)'
            }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                Additional Communication Services
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--neutral-600)', margin: 0 }}>
                Slack, Microsoft Teams, and Webhook configurations will be available here soon.
              </p>
            </div>
          </div>
        );
      
      case 'system':
        return (
          <div style={{ padding: 'var(--space-4)' }}>
            <div style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--neutral-50)',
              border: '1px solid var(--neutral-200)',
              borderRadius: 'var(--border-radius)'
            }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                System Configuration
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--neutral-600)', margin: 0 }}>
                General system settings will be available here soon.
              </p>
            </div>
          </div>
        );
      
      case 'security':
        return (
          <div style={{ padding: 'var(--space-4)' }}>
            <div style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--neutral-50)',
              border: '1px solid var(--neutral-200)',
              borderRadius: 'var(--border-radius)'
            }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                Security Settings
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--neutral-600)', margin: 0 }}>
                Authentication and security settings will be available here soon.
              </p>
            </div>
          </div>
        );
      
      case 'notifications':
        return (
          <div style={{ padding: 'var(--space-4)' }}>
            <div style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--neutral-50)',
              border: '1px solid var(--neutral-200)',
              borderRadius: 'var(--border-radius)'
            }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                Notification Preferences
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--neutral-600)', margin: 0 }}>
                Notification settings will be available here soon.
              </p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="dense-dashboard">
      <style>
        {`
          .dashboard-grid {
            height: calc(100vh - 110px);
          }
          .dashboard-section {
            height: 100%;
          }
          .settings-list-section {
            grid-column: 1;
            height: 100%;
            overflow: hidden;
            display: flex;
            flex-direction: column;
          }
          .settings-detail-section {
            grid-column: 2 / 4;
            height: 100%;
            overflow-y: auto;
          }
          .settings-list {
            flex: 1;
            overflow-y: auto;
            padding: var(--space-2);
          }
          .setting-item {
            padding: var(--space-3);
            margin-bottom: var(--space-2);
            border-radius: var(--border-radius);
            cursor: pointer;
            transition: background-color 0.15s ease;
            border: 1px solid transparent;
          }
          .setting-item:hover:not(.selected) {
            background: var(--neutral-50);
          }
          .setting-item.selected {
            background: var(--primary-blue-light);
            border-color: var(--primary-blue);
            border-left: 3px solid var(--primary-blue);
          }
          .setting-item-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--neutral-800);
            margin-bottom: 4px;
          }
          .setting-item-description {
            font-size: 11px;
            color: var(--neutral-600);
            line-height: 1.4;
          }
        `}
      </style>

      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Settings</h1>
        </div>
        <div className="header-stats">
          <Link to="/settings" className="stat-pill">
            <SettingsIcon size={14} />
            <span>System Configuration</span>
          </Link>
          <Link to="/ai-chat" className="stat-pill">
            <MessageSquare size={14} />
            <span>AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Settings Sections List */}
        <div className="dashboard-section settings-list-section">
          <div className="section-header">
            Setting Categories
          </div>
          <div className="settings-list">
            {settingSections.map((section) => (
              <div
                key={section.id}
                className={`setting-item ${selectedSection === section.id ? 'selected' : ''}`}
                onClick={() => setSelectedSection(section.id)}
              >
                <div className="setting-item-name">{section.name}</div>
                <div className="setting-item-description">{section.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Columns 2-3: Settings Detail Panel */}
        <div className="dashboard-section settings-detail-section">
          <div className="section-header">
            {settingSections.find(s => s.id === selectedSection)?.name} Settings
          </div>
          {renderSectionContent()}
        </div>
      </div>
    </div>
  );
};

export default Settings;