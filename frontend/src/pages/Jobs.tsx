import React, { useState, useEffect } from 'react';
import { Job } from '../types';
import { jobApi } from '../services/api';
import VisualJobBuilder from '../components/VisualJobBuilder';

const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  // Always use visual builder - traditional editor removed
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await jobApi.list();
      setJobs(response.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setEditingJob(null);
  };

  const handleEdit = (job: Job) => {
    setEditingJob(job);
    setShowCreateModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await jobApi.delete(id);
        fetchJobs();
      } catch (error) {
        console.error('Failed to delete job:', error);
      }
    }
  };

  const handleRunJob = async (id: number) => {
    try {
      await jobApi.run(id);
      alert('Job started successfully!');
    } catch (error) {
      console.error('Failed to run job:', error);
      alert('Failed to run job. Please try again.');
    }
  };

  if (loading) return <div>Loading jobs...</div>;

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Jobs</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Create New Job
        </button>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Version</th>
              <th>Steps</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(jobs || []).map(job => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>{job.name}</td>
                <td>{job.version}</td>
                <td>{job.definition.steps?.length || 0}</td>
                <td>
                  <span className={`status ${job.is_active ? 'status-succeeded' : 'status-failed'}`}>
                    {job.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(job.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleRunJob(job.id)}
                      disabled={!job.is_active}
                      style={{ fontSize: '12px' }}
                    >
                      Run
                    </button>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => handleEdit(job)}
                      style={{ fontSize: '12px' }}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(job.id)}
                      style={{ fontSize: '12px' }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Job Modal - Visual Builder Only */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          overflow: 'auto'
        }}>
          <div className="card" style={{ width: '95vw', height: '90vh', margin: '20px', overflow: 'hidden' }}>
            <div style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>🎨 {editingJob ? 'Edit Job' : 'Create New Job'}</h3>
                <button 
                  onClick={() => setShowCreateModal(false)}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    fontSize: '24px', 
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ×
                </button>
              </div>
              
              <div style={{ flex: 1 }}>
                <VisualJobBuilder
                  editingJob={editingJob}
                  onJobCreate={async (jobData) => {
                    try {
                      if (editingJob) {
                        await jobApi.update(editingJob.id, jobData);
                      } else {
                        await jobApi.create(jobData);
                      }
                      setShowCreateModal(false);
                      resetForm();
                      fetchJobs();
                    } catch (error) {
                      console.error(`Failed to ${editingJob ? 'update' : 'create'} job:`, error);
                      alert(`Failed to ${editingJob ? 'update' : 'create'} job. Please try again.`);
                    }
                  }}
                  onCancel={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Jobs;