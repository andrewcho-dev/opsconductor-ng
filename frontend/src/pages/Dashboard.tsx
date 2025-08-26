import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { userApi, credentialApi, targetApi, jobApi, jobRunApi, schedulerApi } from '../services/api';
import ServiceHealthMonitor from '../components/ServiceHealthMonitor';
import SystemMetrics from '../components/SystemMetrics';
import RecentActivity from '../components/RecentActivity';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    users: 0,
    credentials: 0,
    targets: 0,
    jobs: 0,
    recentRuns: 0,
    schedules: 0,
    schedulerRunning: false
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [users, credentials, targets, jobs, runs, schedules, schedulerStatus] = await Promise.all([
          userApi.list(0, 1),
          credentialApi.list(0, 1),
          targetApi.list(0, 1),
          jobApi.list(0, 1),
          jobRunApi.list(0, 1),
          schedulerApi.list(0, 1),
          schedulerApi.getStatus()
        ]);

        setStats({
          users: users.total,
          credentials: credentials.total,
          targets: targets.total,
          jobs: jobs.total,
          recentRuns: runs.total,
          schedules: schedules.total,
          schedulerRunning: schedulerStatus.scheduler_running
        });
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      
      {/* Service Health Monitoring */}
      <div style={{ marginBottom: '30px' }}>
        <ServiceHealthMonitor />
      </div>

      {/* Stats Overview */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '20px',
        marginBottom: '30px'
      }}>
        <Link to="/users" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#007bff' }}>{stats.users}</h3>
            <p>Users</p>
          </div>
        </Link>

        <Link to="/credentials" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#28a745' }}>{stats.credentials}</h3>
            <p>Credentials</p>
          </div>
        </Link>

        <Link to="/targets" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#ffc107' }}>{stats.targets}</h3>
            <p>Targets</p>
          </div>
        </Link>

        <Link to="/jobs" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#dc3545' }}>{stats.jobs}</h3>
            <p>Jobs</p>
          </div>
        </Link>

        <Link to="/schedules" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#17a2b8' }}>{stats.schedules}</h3>
            <p>Schedules</p>
            <div style={{ 
              fontSize: '12px', 
              marginTop: '5px',
              color: stats.schedulerRunning ? '#28a745' : '#dc3545'
            }}>
              Scheduler: {stats.schedulerRunning ? 'Running' : 'Stopped'}
            </div>
          </div>
        </Link>

        <Link to="/runs" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer' }}>
            <h3 style={{ color: '#6f42c1' }}>{stats.recentRuns}</h3>
            <p>Job Runs</p>
          </div>
        </Link>
      </div>

      {/* System Metrics and Recent Activity */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '20px',
        marginBottom: '30px'
      }}>
        <SystemMetrics />
        <RecentActivity />
      </div>

      <div className="card">
        <h2>Quick Actions</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Link to="/users" className="btn btn-primary">Manage Users</Link>
          <Link to="/credentials" className="btn btn-primary">Add Credentials</Link>
          <Link to="/targets" className="btn btn-primary">Add Targets</Link>
          <Link to="/jobs" className="btn btn-primary">Create Job</Link>
          <Link to="/schedules" className="btn btn-primary">Schedule Jobs</Link>
          <Link to="/runs" className="btn btn-secondary">View Job History</Link>
        </div>
      </div>

      <div className="card">
        <h2>System Information</h2>
        <p><strong>Status:</strong> <span style={{ color: '#28a745' }}>Online</span></p>
        <p><strong>Version:</strong> 1.0.0</p>
        <p><strong>Backend:</strong> Python FastAPI</p>
        <p><strong>Frontend:</strong> React TypeScript</p>
        <p><strong>Database:</strong> PostgreSQL</p>
        <p><strong>Executor:</strong> Python pywinrm</p>
      </div>
    </div>
  );
};

export default Dashboard;