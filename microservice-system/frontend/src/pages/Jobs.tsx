import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Job } from '../types';
import { jobApi } from '../services/api';
import VisualJobBuilder from '../components/VisualJobBuilder';
import { Plus, Play, Edit, Trash2 } from 'lucide-react';

const Jobs: React.FC = () => {
  const navigate = useNavigate();
  const { action, id } = useParams<{ action?: string; id?: string }>();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  const isEditing = action === 'edit' && id;
  const isCreating = action === 'create';
  const showForm = isEditing || isCreating;

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (isEditing && id) {
      const job = jobs.find(j => j.id === parseInt(id));
      if (job) {
        setEditingJob(job);
      }
    } else if (isCreating) {
      setEditingJob(null);
    }
  }, [isEditing, isCreating, id, jobs]);

  const fetchJobs = async () => {
    try {
      const response = await jobApi.list();
      setJobs(response.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (window.confirm('Delete this job? This action cannot be undone.')) {
      try {
        await jobApi.delete(jobId);
        fetchJobs();
      } catch (error) {
        console.error('Failed to delete job:', error);
      }
    }
  };

  const handleRunJob = async (jobId: number) => {
    try {
      await jobApi.run(jobId);
      alert('Job started successfully!');
    } catch (error) {
      console.error('Failed to run job:', error);
      alert('Failed to start job. Check the logs for details.');
    }
  };

  const handleJobSaved = () => {
    fetchJobs();
    navigate('/job-management');
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'enabled':
        return 'status-badge-success';
      case 'inactive':
      case 'disabled':
        return 'status-badge-neutral';
      case 'error':
        return 'status-badge-danger';
      default:
        return 'status-badge-info';
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (showForm) {
    return (
      <div className="main-content">
        <div className="page-header">
          <h1 className="page-title">
            {isEditing ? 'Edit Job' : 'Create Job'}
          </h1>
          <div className="page-actions">
            <button 
              type="button" 
              className="btn btn-ghost"
              onClick={() => navigate('/job-management')}
            >
              Cancel
            </button>
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-4)' }}>
          <VisualJobBuilder
            onJobCreate={handleJobSaved}
            onCancel={() => navigate('/job-management')}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Jobs</h1>
        <div className="page-actions">
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/job-management/create')}
          >
            <Plus size={16} className="me-2" />
            Create Job
          </button>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <h3 className="empty-state-title">No jobs found</h3>
          <p className="empty-state-description">
            Create your first job to automate tasks on your targets.
          </p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/job-management/create')}
          >
            <Plus size={16} className="me-2" />
            Create Job
          </button>
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Steps</th>
                <th>Status</th>
                <th>Created</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.id}>
                  <td className="text-neutral-500">{job.id}</td>
                  <td className="font-medium">{job.name}</td>
                  <td className="text-neutral-600">-</td>
                  <td className="text-neutral-500">
                    0 steps
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadge('active')}`}>
                      Active
                    </span>
                  </td>
                  <td className="text-neutral-500">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div className="table-actions">
                      <button 
                        className="btn-icon btn-success"
                        onClick={() => handleRunJob(job.id)}
                        title="Run job"
                      >
                        <Play size={16} />
                      </button>
                      <button 
                        className="btn-icon btn-ghost"
                        onClick={() => navigate(`/job-management/edit/${job.id}`)}
                        title="Edit job"
                      >
                        <Edit size={16} />
                      </button>
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => handleDelete(job.id)}
                        title="Delete job"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Jobs;