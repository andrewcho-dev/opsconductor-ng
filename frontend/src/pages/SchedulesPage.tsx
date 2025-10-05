import React from 'react';
import { Calendar, Clock, AlertCircle, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';

const SchedulesPage: React.FC = () => {
  return (
    <PageContainer>
      <PageHeader title="Workflow Schedules">
        <Link to="/ai-chat" className="stat-pill">
          <MessageSquare size={14} />
          <span>AI Assistant</span>
        </Link>
      </PageHeader>

      {/* Coming Soon Notice */}
      <div className="card">
        <div className="card-body text-center py-5">
          <div className="mb-4">
            <Clock size={64} style={{ color: 'var(--primary-blue)', marginBottom: '16px' }} />
          </div>
          <h3 className="mb-3">Scheduling Feature Coming Soon</h3>
          <p className="text-muted mb-4">
            The workflow scheduling feature is currently under development. 
            This will allow you to automate workflow execution based on cron schedules.
          </p>
          
          <div style={{ 
            display: 'inline-block', 
            textAlign: 'left',
            backgroundColor: 'var(--primary-blue-light)',
            border: '1px solid var(--primary-blue)',
            borderRadius: 'var(--border-radius)',
            padding: 'var(--space-4)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <AlertCircle size={20} style={{ color: 'var(--primary-blue)' }} />
              <strong style={{ color: 'var(--primary-blue-dark)' }}>Planned Features:</strong>
            </div>
            <ul style={{ marginBottom: 0, paddingLeft: '24px', color: 'var(--neutral-700)' }}>
              <li>Create and manage cron-based schedules</li>
              <li>Link schedules to automation workflows</li>
              <li>Monitor schedule execution history</li>
              <li>Enable/disable schedules on demand</li>
              <li>Timezone support for global operations</li>
            </ul>
          </div>
          
          <div style={{ marginTop: 'var(--space-6)' }}>
            <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
              For now, you can execute workflows manually through the AI Assistant or Assets page.
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default SchedulesPage;