import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { userApi, targetApi, jobApi, jobRunApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ServiceHealthMonitor from '../components/ServiceHealthMonitor';
import AIChat from '../components/AIChat';
import AIMonitor from '../components/AIMonitor';
import { Users, Target, Settings, Play, RefreshCw, Activity } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { isLoading: authLoading, isAuthenticated } = useAuth();
  const [stats, setStats] = useState({
    users: 0,
    targets: 0,
    jobs: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showAIMonitor, setShowAIMonitor] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [serviceHealthLastUpdate, setServiceHealthLastUpdate] = useState<Date | null>(null);

  const handleRefreshServices = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const fetchStats = async () => {
    try {
      const requests = [
        userApi.list(0, 1),
        targetApi.list(0, 1),
        jobApi.list(0, 1),
        jobRunApi.list(0, 1)
      ];

      const [
        usersRes,
        targetsRes,
        jobsRes,
        runsRes
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
      // Log failures for debugging but keep dashboard rendering
      if (usersRes.status === 'rejected') console.warn('Users stats failed:', usersRes.reason);
      if (targetsRes.status === 'rejected') console.warn('Targets stats failed:', targetsRes.reason);
      if (jobsRes.status === 'rejected') console.warn('Jobs stats failed:', jobsRes.reason);
      if (runsRes.status === 'rejected') console.warn('Runs stats failed:', runsRes.reason);

      setStats({
        users: getTotal(usersRes),
        targets: getTotal(targetsRes),
        jobs: getTotal(jobsRes),
        recentRuns: getTotal(runsRes)
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
    <div className="dense-dashboard" style={{ 
      height: 'calc(100vh - 45px)', 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Ultra-compact header with inline stats */}
      <div className="dashboard-header" style={{ flexShrink: 0 }}>
        <div className="header-left">
          <h1>Dashboard</h1>
        </div>
        <div className="header-right">
          <div className="inline-stats">
            <Link to="/users" className="stat">
              <Users size={14} />
              <span className="count">{stats.users}</span>
              <span className="label">Users</span>
            </Link>
            <Link to="/targets" className="stat">
              <Target size={14} />
              <span className="count">{stats.targets}</span>
              <span className="label">Targets</span>
            </Link>
            <Link to="/jobs" className="stat">
              <Settings size={14} />
              <span className="count">{stats.jobs}</span>
              <span className="label">Jobs</span>
            </Link>
            <Link to="/monitoring" className="stat">
              <Play size={14} />
              <span className="count">{stats.recentRuns}</span>
              <span className="label">Runs</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs for switching between AI Chat and AI Monitor */}
      <div className="dashboard-tabs" style={{ 
        display: 'flex', 
        gap: '1rem', 
        padding: '0.5rem 1rem',
        borderBottom: '1px solid var(--neutral-200)',
        flexShrink: 0
      }}>
        <button
          onClick={() => setShowAIMonitor(false)}
          className={`btn btn-sm ${!showAIMonitor ? 'btn-primary' : 'btn-secondary'}`}
          style={{ minWidth: '120px' }}
        >
          AI Assistant
        </button>
        <button
          onClick={() => setShowAIMonitor(true)}
          className={`btn btn-sm ${showAIMonitor ? 'btn-primary' : 'btn-secondary'}`}
          style={{ minWidth: '120px' }}
        >
          <Activity size={14} style={{ marginRight: '4px' }} />
          AI Monitor
        </button>
      </div>

      {/* Main content area - scrollable */}
      <div style={{ 
        flex: 1,
        display: 'flex',
        gap: '12px',
        padding: '12px',
        minHeight: 0,
        overflow: 'auto'
      }}>
        {/* Service Health Monitor - Fixed width */}
        <div className="dashboard-section service-health-section" style={{ 
          width: '280px',
          flexShrink: 0,
          maxHeight: '100%'
        }}>
          <div className="section-header" style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center' 
          }}>
            <span>Service Health</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {serviceHealthLastUpdate && (
                <span style={{ fontSize: '10px', color: 'var(--neutral-500)' }}>
                  {serviceHealthLastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              <button
                onClick={handleRefreshServices}
                style={{ 
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  color: 'var(--neutral-600)'
                }}
                title="Refresh service health"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          </div>
          <div className="compact-content" style={{ 
            padding: '4px 8px'
          }}>
            <ServiceHealthMonitor 
              refreshTrigger={refreshTrigger} 
              onLastUpdateChange={setServiceHealthLastUpdate}
            />
          </div>
        </div>

        {/* AI Interface - Takes remaining space */}
        <div style={{ 
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0
        }}>
          {showAIMonitor ? (
            <AIMonitor />
          ) : (
            <AIChat />
          )}
        </div>
      </div>

      <style jsx>{`
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 20px;
          background: white;
          border-bottom: 1px solid var(--neutral-200);
        }

        .dashboard-header h1 {
          font-size: 20px;
          font-weight: 600;
          color: var(--neutral-800);
          margin: 0;
        }

        .inline-stats {
          display: flex;
          gap: 20px;
        }

        .stat {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: var(--neutral-50);
          border-radius: 6px;
          text-decoration: none;
          transition: all 0.2s;
        }

        .stat:hover {
          background: var(--primary-blue-light);
          transform: translateY(-1px);
        }

        .stat .count {
          font-size: 18px;
          font-weight: 600;
          color: var(--neutral-800);
        }

        .stat .label {
          font-size: 12px;
          color: var(--neutral-600);
        }

        .dashboard-section {
          background: white;
          border: 1px solid var(--neutral-200);
          border-radius: 8px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .section-header {
          padding: 10px 12px;
          background: var(--neutral-50);
          border-bottom: 1px solid var(--neutral-200);
          font-size: 13px;
          font-weight: 600;
          color: var(--neutral-700);
        }

        .compact-content {
          flex: 1;
          overflow: auto;
        }

        .dashboard-tabs {
          background: white;
        }

        .btn {
          padding: 6px 12px;
          border: 1px solid var(--neutral-300);
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          transition: all 0.2s;
          display: inline-flex;
          align-items: center;
        }

        .btn-primary {
          background: var(--primary-blue);
          color: white;
          border-color: var(--primary-blue);
        }

        .btn-secondary {
          background: white;
          color: var(--neutral-700);
          border-color: var(--neutral-300);
        }

        .btn-secondary:hover {
          background: var(--neutral-50);
        }

        .loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          background: rgba(255, 255, 255, 0.9);
          z-index: 9999;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid var(--neutral-200);
          border-top-color: var(--primary-blue);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .service-health-section {
          min-height: 200px;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;