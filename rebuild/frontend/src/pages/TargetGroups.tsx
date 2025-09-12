import React from 'react';
import TargetGroupsManagement from '../components/TargetGroupsManagement';

const TargetGroups: React.FC = () => {

  return (
    <div className="dense-dashboard">
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
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

          
          /* Content area */
          .content {
            height: calc(100vh - 100px);
            overflow: hidden;
          }
          
          /* Button styles matching other pages */
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 6px;
            border: 1px solid transparent;
            border-radius: 4px;
            background: transparent;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
          }
          .btn-success {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
          .btn-success:hover {
            background: var(--success-green-dark);
            border-color: var(--success-green-dark);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Target Groups</h1>
        </div>
      </div>
      
      <div className="content">
        <TargetGroupsManagement />
      </div>
    </div>
  );
};

export default TargetGroups;