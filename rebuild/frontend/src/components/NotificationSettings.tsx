import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import StandardizedNotificationPreferences from './StandardizedNotificationPreferences';
import NotificationWorkerStatus from './NotificationWorkerStatus';
import { AlertCircle } from 'lucide-react';

const NotificationSettings: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="notification-settings">
      <style>
        {`
          .notification-settings {
            display: flex;
            flex-direction: column;
            gap: 16px;
          }
          
          .admin-section {
            border-top: 1px solid var(--neutral-200);
            padding-top: 16px;
            margin-top: 8px;
          }
          
          .admin-section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            padding: 8px 12px;
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
          }
          
          .admin-section-header h3 {
            margin: 0;
            font-size: 13px;
            font-weight: 600;
            color: var(--neutral-700);
          }
          
          .admin-badge {
            background: var(--primary-blue);
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          
          .access-denied {
            background: var(--warning-orange-light);
            color: var(--warning-orange-dark);
            border: 1px solid var(--warning-orange);
            border-radius: 6px;
            padding: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
          }
        `}
      </style>

      {/* User Notification Preferences */}
      <StandardizedNotificationPreferences />

      {/* Admin-only Worker Status Section */}
      <div className="admin-section">
        <div className="admin-section-header">
          <h3>Notification System Management</h3>
          <span className="admin-badge">Admin Only</span>
        </div>
        
        {user?.role === 'admin' ? (
          <NotificationWorkerStatus />
        ) : (
          <div className="access-denied">
            <AlertCircle size={16} />
            <div>
              <strong>Administrator access required</strong> to manage notification worker settings and send test notifications.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationSettings;