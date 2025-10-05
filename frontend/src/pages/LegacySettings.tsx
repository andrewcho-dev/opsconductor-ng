import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import SMTPSettingsComponent from '../components/SMTPSettings';
import { isAdmin } from '../utils/permissions';
import { Lightbulb, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';

const LegacySettings: React.FC = () => {
  const { user } = useAuth();

  return (
    <PageContainer>
      <PageHeader title="System Settings">
        <Link to="/ai-chat" className="stat-pill">
          <MessageSquare size={14} />
          <span>AI Assistant</span>
        </Link>
      </PageHeader>

      {/* Content */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {isAdmin(user) ? (
          <>
            {/* SMTP Settings */}
            <SMTPSettingsComponent />
          </>
        ) : (
          <div style={{
            backgroundColor: 'var(--warning-orange-light)',
            border: '1px solid var(--warning-orange)',
            borderRadius: 'var(--border-radius)',
            padding: 'var(--space-4)'
          }}>
            <h3 style={{ fontWeight: 600, marginBottom: 'var(--space-2)', color: 'var(--warning-orange)' }}>
              Access Restricted
            </h3>
            <p style={{ margin: 0, color: 'var(--neutral-700)' }}>
              Only administrators can access system settings.
            </p>
          </div>
        )}
      </div>

      {/* Help Section */}
      {isAdmin(user) && (
        <div style={{
          marginTop: 'var(--space-8)',
          backgroundColor: 'var(--primary-blue-light)',
          border: '1px solid var(--primary-blue)',
          borderRadius: 'var(--border-radius)',
          padding: 'var(--space-6)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 600,
            color: 'var(--primary-blue-dark)',
            marginBottom: 'var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)'
          }}>
            <Lightbulb size={20} />
            Administrator Help
          </h3>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--neutral-700)'
          }}>
            <div>
              <strong>SMTP Settings:</strong> Configure the email server settings that will be used for all 
              system emails. Make sure to test the configuration after making changes.
            </div>
            <div>
              <strong>Security:</strong> Use app passwords for Gmail and other providers that support 2FA. 
              Always use TLS encryption for secure email transmission.
            </div>
            <div>
              <strong>Testing:</strong> Use the test functionality to verify your SMTP configuration before 
              saving. This helps ensure emails will be delivered properly.
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
};

export default LegacySettings;