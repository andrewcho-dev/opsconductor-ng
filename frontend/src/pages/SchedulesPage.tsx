import React from 'react';
import { Calendar, Clock, AlertCircle } from 'lucide-react';

const SchedulesPage: React.FC = () => {
  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">
                <Calendar className="me-2" size={24} />
                Workflow Schedules
              </h1>
              <p className="text-muted mb-0">Manage automated workflow execution schedules</p>
            </div>
          </div>

          {/* Coming Soon Notice */}
          <div className="card">
            <div className="card-body text-center py-5">
              <div className="mb-4">
                <Clock size={64} className="text-primary mb-3" />
              </div>
              <h3 className="mb-3">Scheduling Feature Coming Soon</h3>
              <p className="text-muted mb-4">
                The workflow scheduling feature is currently under development. 
                This will allow you to automate workflow execution based on cron schedules.
              </p>
              
              <div className="alert alert-info d-inline-block text-start" role="alert">
                <AlertCircle size={20} className="me-2" />
                <strong>Planned Features:</strong>
                <ul className="mb-0 mt-2">
                  <li>Create and manage cron-based schedules</li>
                  <li>Link schedules to automation workflows</li>
                  <li>Monitor schedule execution history</li>
                  <li>Enable/disable schedules on demand</li>
                  <li>Timezone support for global operations</li>
                </ul>
              </div>
              
              <div className="mt-4">
                <p className="text-muted small">
                  For now, you can execute workflows manually through the AI Assistant or Assets page.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchedulesPage;