import React from 'react';
import NotificationPreferences from '../components/NotificationPreferences';
import { Bell } from 'lucide-react';

const Notifications: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Bell size={24} />
            Notification Preferences
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Configure your personal notification settings including email, webhooks, Slack, and Teams.
          </p>
        </div>

        {/* Content */}
        <div className="space-y-6">
          <NotificationPreferences />
        </div>
      </div>
    </div>
  );
};

export default Notifications;