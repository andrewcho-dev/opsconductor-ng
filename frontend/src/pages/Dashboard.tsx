import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { assetApi, scheduleApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ServiceHealthMonitor from '../components/ServiceHealthMonitor';
import AIMonitor from '../components/AIMonitor';
import { Target, Calendar, RefreshCw, MessageSquare } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { isLoading: authLoading, isAuthenticated } = useAuth();
  const [stats, setStats] = useState({
    assets: 0,
    schedules: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [serviceHealthLastUpdate, setServiceHealthLastUpdate] = useState<Date | null>(null);

  const handleRefreshServices = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const fetchStats = async () => {
    try {
      const requests = [
        assetApi.list(0, 1),
        scheduleApi.list(0, 1000)
      ];

      const [
        assetsRes,
        schedulesRes
      ] = await Promise.allSettled(requests);

      const getTotal = (res: any) => {
        if (res.status !== 'fulfilled') return 0;
        // Handle new API response format with meta.total_items
        if (res.value?.meta?.total_items !== undefined) {
          return res.value.meta.total_items;
        }
        // Handle asset API response format with data.total
        if (res.value?.data?.total !== undefined) {
          return res.value.data.total;
        }
        // Handle array responses
        if (Array.isArray(res.value?.data)) {
          return res.value.data.length;
        }
        if (Array.isArray(res.value)) {
          return res.value.length;
        }
        // Handle old API response format with total
        return res.value?.total ?? 0;
      };
      // Log failures for debugging but keep dashboard rendering
      if (assetsRes.status === 'rejected') console.warn('Assets stats failed:', assetsRes.reason);
      if (schedulesRes.status === 'rejected') console.warn('Schedules stats failed:', schedulesRes.reason);

      setStats({
        assets: getTotal(assetsRes),
        schedules: getTotal(schedulesRes),
        recentRuns: 0 // No runs data available
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
          .header-stats {
            display: flex;
            gap: 12px;
            align-items: center;
          }
          .stat-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            background: var(--neutral-100);
            color: var(--neutral-700);
            padding: 4px 8px;
            border-radius: 12px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.15s ease;
            white-space: nowrap;
          }
          .stat-pill:hover {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
          }
          .full-width-section {
            margin: 0 -12px 0 -12px;
            padding: 0 12px;
            width: calc(100% + 24px);
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }

          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.15s;
            margin: 0 1px;
            padding: 2px;
            color: var(--neutral-500);
          }
          .btn-icon:hover {
            color: var(--neutral-700);
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
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Dashboard</h1>
        </div>
        <div className="header-stats">
          <Link to="/assets" className="stat-pill">
            <Target size={14} />
            <span>{stats.assets} Assets</span>
          </Link>
          <Link to="/schedules" className="stat-pill">
            <Calendar size={14} />
            <span>{stats.schedules} Schedules</span>
          </Link>
          <Link to="/ai-chat" className="stat-pill">
            <MessageSquare size={14} />
            <span>AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* Service Health Monitor - Full Screen Width */}
      <div className="full-width-section">
        <div className="dashboard-section">
          <div className="section-header">
            <span>Service Health</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {serviceHealthLastUpdate && (
                <span style={{ fontSize: '10px', color: 'var(--neutral-500)' }}>
                  {serviceHealthLastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              <button
                onClick={handleRefreshServices}
                className="btn-icon"
                title="Refresh service health"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          </div>
          <div className="compact-content" style={{ padding: '8px' }}>
            <ServiceHealthMonitor 
              refreshTrigger={refreshTrigger} 
              onLastUpdateChange={setServiceHealthLastUpdate}
            />
          </div>
        </div>
      </div>

      {/* AI Monitor - Below in normal dashboard container */}
      <div className="dashboard-section" style={{ marginTop: '12px' }}>
        <div className="section-header">
          <span>AI Monitor</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => {
                // Trigger AI Monitor refresh - we'll need to pass this down
                window.dispatchEvent(new CustomEvent('refreshAIMonitor'));
              }}
              className="btn-icon"
              title="Refresh AI Monitor"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </div>
        <div className="compact-content" style={{ padding: '8px' }}>
          <AIMonitor />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;