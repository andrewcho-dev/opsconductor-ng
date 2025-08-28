import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import NotificationPreferences from '../components/NotificationPreferences';
import NotificationHistory from '../components/NotificationHistory';

const Notifications: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'preferences' | 'history'>('preferences');

  const tabs = [
    {
      id: 'preferences' as const,
      name: 'My Preferences',
      icon: '🔔',
      description: 'Configure your personal notification settings'
    },
    {
      id: 'history' as const,
      name: 'Notification History',
      icon: '📋',
      description: 'View and manage notification history and worker status',
      adminOnly: true
    }
  ];

  const visibleTabs = tabs.filter(tab => !tab.adminOnly || user?.role === 'admin');

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your notification preferences and view notification history.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {visibleTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Description */}
          <div className="mt-4">
            {visibleTabs.map((tab) => (
              activeTab === tab.id && (
                <p key={tab.id} className="text-sm text-gray-600">
                  {tab.description}
                </p>
              )
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'preferences' && (
            <NotificationPreferences />
          )}

          {activeTab === 'history' && user?.role === 'admin' && (
            <NotificationHistory />
          )}

          {activeTab === 'history' && user?.role !== 'admin' && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
              Access denied. Only administrators can view notification history.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Notifications;