import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Target, Settings, Play } from 'lucide-react';
import { userApi, targetApi, jobApi, jobRunApi } from '../services/api';

interface SystemStats {
  users: number;
  targets: number;
  jobs: number;
  recentRuns: number;
}

const SystemStats: React.FC = () => {
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
        const [usersResponse, targetsResponse, jobsResponse, runsResponse] = await Promise.all([
          userApi.list(),
          targetApi.list(),
          jobApi.list(),
          jobRunApi.list(0, 10) // Get recent 10 runs
        ]);

        setStats({
          users: usersResponse.total || usersResponse.length || 0,
          targets: targetsResponse.total || targetsResponse.length || 0,
          jobs: jobsResponse.total || jobsResponse.length || 0,
          recentRuns: runsResponse.total || runsResponse.length || 0,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
        // Set fallback stats so the dashboard still shows something
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

  const statCards = [
    {
      title: 'Users',
      value: stats.users,
      icon: Users,
      link: '/user-management',
      color: 'var(--primary-blue)'
    },
    {
      title: 'Targets',
      value: stats.targets,
      icon: Target,
      link: '/targets-management',
      color: 'var(--success-green)'
    },
    {
      title: 'Jobs',
      value: stats.jobs,
      icon: Settings,
      link: '/job-management',
      color: 'var(--warning-orange)'
    },
    {
      title: 'Recent Runs',
      value: stats.recentRuns,
      icon: Play,
      link: '/history/job-runs',
      color: 'var(--secondary-gray)'
    }
  ];

  if (loading) {
    return (
      <div className="stats-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card">
            <div className="stat-card-content">
              <div className="stat-card-icon loading-placeholder"></div>
              <div className="stat-card-details">
                <div className="stat-card-value loading-placeholder"></div>
                <div className="stat-card-title loading-placeholder"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="stats-grid">
      {statCards.map((stat) => {
        const IconComponent = stat.icon;
        return (
          <Link key={stat.title} to={stat.link} className="stat-card-link">
            <div className="stat-card">
              <div className="stat-card-content">
                <div 
                  className="stat-card-icon"
                  style={{ backgroundColor: `${stat.color}15`, color: stat.color }}
                >
                  <IconComponent size={24} />
                </div>
                <div className="stat-card-details">
                  <div className="stat-card-value">{stat.value}</div>
                  <div className="stat-card-title">{stat.title}</div>
                </div>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
};

export default SystemStats;