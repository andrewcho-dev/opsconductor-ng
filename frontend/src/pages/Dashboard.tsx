import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { userApi, credentialApi, targetApi, jobApi, jobRunApi, schedulerApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ServiceHealthMonitor from '../components/ServiceHealthMonitor';
import SystemMetrics from '../components/SystemMetrics';
import RecentActivity from '../components/RecentActivity';
import { Users, Shield, Target, Settings, Play, Calendar, Search, CheckCircle, Circle, Plus } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { isLoading: authLoading, isAuthenticated } = useAuth();
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

  const fetchStats = async () => {
    try {
      const requests = [
        userApi.list(0, 1),
        credentialApi.list(0, 1),
        targetApi.list(0, 1),
        jobApi.list(0, 1),
        jobRunApi.list(0, 1),
        schedulerApi.list(0, 1),
        schedulerApi.getStatus()
      ];

      const [
        usersRes,
        credentialsRes,
        targetsRes,
        jobsRes,
        runsRes,
        schedulesRes,
        schedulerStatusRes
      ] = await Promise.allSettled(requests);

      const getTotal = (res: any) => {
        if (res.status !== 'fulfilled') return 0;
        // Handle new API response format with meta.total_items
        if (res.value?.meta?.total_items !== undefined) {
          return res.value.meta.total_items;
        }
        // Handle old API response format with total
        return res.value?.total ?? 0;
      };
      const getSchedulerRunning = (res: any) => (res.status === 'fulfilled' ? !!res.value?.scheduler_running : false);

      // Log failures for debugging but keep dashboard rendering
      if (usersRes.status === 'rejected') console.warn('Users stats failed:', usersRes.reason);
      if (credentialsRes.status === 'rejected') console.warn('Credentials stats failed:', credentialsRes.reason);
      if (targetsRes.status === 'rejected') console.warn('Targets stats failed:', targetsRes.reason);
      if (jobsRes.status === 'rejected') console.warn('Jobs stats failed:', jobsRes.reason);
      if (runsRes.status === 'rejected') console.warn('Runs stats failed:', runsRes.reason);
      if (schedulesRes.status === 'rejected') console.warn('Schedules stats failed:', schedulesRes.reason);
      if (schedulerStatusRes.status === 'rejected') console.warn('Scheduler status failed:', schedulerStatusRes.reason);

      setStats({
        users: getTotal(usersRes),
        credentials: getTotal(credentialsRes),
        targets: getTotal(targetsRes),
        jobs: getTotal(jobsRes),
        recentRuns: getTotal(runsRes),
        schedules: getTotal(schedulesRes),
        schedulerRunning: getSchedulerRunning(schedulerStatusRes)
      });
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      fetchStats();
    }
  }, [isAuthenticated, authLoading]);

  if (authLoading || loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      {/* Ultra-compact header with inline stats */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Dashboard</h1>
          <span className={`scheduler-status ${stats.schedulerRunning ? 'running' : 'stopped'}`}>
            Scheduler {stats.schedulerRunning ? <CheckCircle size={12} className="inline" /> : <Circle size={12} className="inline" />}
          </span>
        </div>
        <div className="header-stats">
          <Link to="/user-management" className="stat-pill"><Users size={14} /> {stats.users}</Link>
          <Link to="/credential-management" className="stat-pill"><Shield size={14} /> {stats.credentials}</Link>
          <Link to="/targets-management" className="stat-pill"><Target size={14} /> {stats.targets}</Link>
          <Link to="/job-management" className="stat-pill"><Settings size={14} /> {stats.jobs}</Link>
          <Link to="/job-runs" className="stat-pill"><Play size={14} /> {stats.recentRuns}</Link>
          <Link to="/schedule-management" className="stat-pill"><Calendar size={14} /> {stats.schedules}</Link>
        </div>
      </div>

      {/* Ultra-dense 3-column layout */}
      <div className="dashboard-grid">
        {/* Column 1: Service Health - Compact */}
        <div className="dashboard-section">
          <div className="section-header">Service Health</div>
          <div className="compact-content">
            <ServiceHealthMonitor />
          </div>
        </div>

        {/* Column 2: System Metrics - Compact */}
        <div className="dashboard-section">
          <div className="section-header">System Metrics</div>
          <div className="compact-content">
            <SystemMetrics />
          </div>
        </div>

        {/* Column 3: Recent Activity + Quick Actions */}
        <div className="dashboard-section">
          <div className="section-header">Recent Activity</div>
          <div className="compact-content">
            <RecentActivity />
          </div>
          
          {/* Inline Quick Actions */}
          <div className="quick-actions">
            <Link to="/job-management/create" className="action-btn primary"><Plus size={14} /> Job</Link>
            <Link to="/targets-management/create" className="action-btn"><Plus size={14} /> Target</Link>
            <Link to="/credential-management/create" className="action-btn"><Plus size={14} /> Cred</Link>
            <Link to="/discovery" className="action-btn"><Search size={14} /> Discover</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;