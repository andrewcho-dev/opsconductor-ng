import React from 'react';
import AIChat from '../components/AIChat';
import SystemBadges from '../components/SystemBadges';

const AIChatPage: React.FC = () => {
  return (
    <div className="dense-dashboard">
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>AI Assistant</h1>
          <p className="header-subtitle">Ask me to run automation tasks, check system status, or get help with OpsConductor.</p>
        </div>
        <div className="header-right">
          <SystemBadges />
        </div>
      </div>

      <AIChat />
    </div>
  );
};

export default AIChatPage;