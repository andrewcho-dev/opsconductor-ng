import React, { useEffect, useState } from 'react';
import { Users, Target, Settings, Play } from 'lucide-react';
import { userApi, assetApi, jobApi, jobRunApi } from '../services/api';

interface SystemStats {
  users: number;
  targets: number;
  jobs: number;
  recentRuns: number;
}

const SystemBadges: React.FC = () => {
  const [stats, setStats] = useState<SystemStats>({
    users: 0,
    targets: 0,
    jobs: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [usersResponse, assetsResponse, jobsResponse, runsResponse] = await Promise.all([
          userApi.list(),
          assetApi.list(),
          jobApi.list(),
          jobRunApi.list(0, 10) // Get recent 10 runs
        ]);

        const getTotal = (response: any) => {
          if (response?.meta?.total_items !== undefined) return response.meta.total_items;
          if (response?.data?.total !== undefined) return response.data.total;
          if (response?.total !== undefined) return response.total;
          return 0;
        };

        setStats({
          users: getTotal(usersResponse),
          targets: getTotal(assetsResponse),
          jobs: getTotal(jobsResponse),
          recentRuns: getTotal(runsResponse),
        });
      } catch (error) {
        console.error('Failed to fetch system badges stats:', error);
        setStats({
          users: 0,
          targets: 0,
          jobs: 0,
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
      title: 'Users',
      value: stats.users,
      icon: Users,
      color: 'var(--primary-blue)'
    },
    {
      title: 'Targets',
      value: stats.targets,
      icon: Target,
      color: 'var(--success-green)'
    },
    {
      title: 'Jobs',
      value: stats.jobs,
      icon: Settings,
      color: 'var(--warning-orange)'
    },
    {
      title: 'Runs',
      value: stats.recentRuns,
      icon: Play,
      color: 'var(--secondary-gray)'
    }
  ];

  if (loading) {
    return (
      <div className="system-badges">
        {[1, 2, 3, 4].map((i) => (
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
          <div key={badge.title} className="system-badge" title={badge.title}>
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