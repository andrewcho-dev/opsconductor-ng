import React, { useEffect, useState } from 'react';
import { Target, Calendar, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { assetApi, scheduleApi } from '../services/api';

interface SystemStats {
  assets: number;
  schedules: number;
  recentRuns: number;
}

const SystemBadges: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SystemStats>({
    assets: 0,
    schedules: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [assetsResponse, schedulesResponse] = await Promise.all([
          assetApi.list(),
          scheduleApi.list(0, 1000) // Get all schedules
        ]);

        const getTotal = (response: any) => {
          if (response?.meta?.total_items !== undefined) return response.meta.total_items;
          if (response?.data?.total !== undefined) return response.data.total;
          if (response?.total !== undefined) return response.total;
          if (Array.isArray(response?.data)) return response.data.length;
          if (Array.isArray(response)) return response.length;
          return 0;
        };

        setStats({
          assets: getTotal(assetsResponse),
          schedules: getTotal(schedulesResponse),
          recentRuns: 0, // No runs data available
        });
      } catch (error) {
        console.error('Failed to fetch system badges stats:', error);
        setStats({
          assets: 0,
          schedules: 0,
          recentRuns: 0,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const badges = [
    {
      title: 'Assets',
      value: stats.assets,
      icon: Target,
      color: 'var(--success-green)',
      onClick: () => navigate('/assets')
    },
    {
      title: 'Schedules',
      value: stats.schedules,
      icon: Calendar,
      color: 'var(--warning-orange)',
      onClick: () => navigate('/schedules')
    },
    {
      title: 'Runs',
      value: stats.recentRuns,
      icon: Play,
      color: 'var(--secondary-gray)',
      onClick: () => navigate('/history/job-runs')
    }
  ];

  if (loading) {
    return (
      <div className="system-badges">
        {[1, 2, 3].map((i) => (
          <div key={i} className="system-badge badge-loading"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="system-badges">
      {badges.map((badge) => {
        const IconComponent = badge.icon;
        return (
          <div 
            key={badge.title} 
            className="system-badge clickable" 
            title={`${badge.title} - Click to view`}
            onClick={badge.onClick}
            style={{ cursor: 'pointer' }}
          >
            <IconComponent 
              className="badge-icon" 
              style={{ color: badge.color }}
            />
            <span className="badge-value">{badge.value}</span>
          </div>
        );
      })}
    </div>
  );
};

export default SystemBadges;