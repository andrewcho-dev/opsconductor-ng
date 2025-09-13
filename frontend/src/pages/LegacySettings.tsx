import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import SMTPSettingsComponent from '../components/SMTPSettings';

import { Lightbulb } from 'lucide-react';

const LegacySettings: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
          <p className="mt-2 text-sm text-gray-600">
            Configure system-wide settings and email server configuration.
          </p>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {user?.role === 'admin' ? (
            <>

              
              {/* SMTP Settings */}
              <SMTPSettingsComponent />
            </>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
              <h3 className="font-medium">Access Restricted</h3>
              <p className="mt-1">Only administrators can access system settings.</p>
            </div>
          )}
        </div>

        {/* Help Section */}
        {user?.role === 'admin' && (
          <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-4">
              <Lightbulb size={20} className="inline mr-2" />Administrator Help
            </h3>
            <div className="space-y-3 text-sm text-blue-700">

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
      </div>
    </div>
  );
};

export default LegacySettings;