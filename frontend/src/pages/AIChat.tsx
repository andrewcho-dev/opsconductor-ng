import React from 'react';
import AIChat from '../components/AIChat';

const AIChatPage: React.FC = () => {
  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH to Users page */
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
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 110px);
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>AI Assistant</h1>
        </div>
      </div>

      {/* Full-width AI Chat */}
      <div className="dashboard-section">
        <div className="compact-content">
          <AIChat />
        </div>
      </div>
    </div>
  );
};

export default AIChatPage;