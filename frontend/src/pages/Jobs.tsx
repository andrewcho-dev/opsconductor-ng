import React, { useState, useEffect } from 'react';
import { jobApi, targetApi } from '../services/api';
import { Job, JobCreate, Target } from '../types';

const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<JobCreate>({
    name: '',
    version: 1,
    definition: {
      name: '',
      version: 1,
      parameters: {},
      steps: []
    },
    is_active: true
  });

  useEffect(() => {
    fetchJobs();
    fetchTargets();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await jobApi.list();
      setJobs(response.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      setJobs([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to fetch targets:', error);
      setTargets([]); // Set empty array on error
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await jobApi.create(formData);
      setShowCreateModal(false);
      setFormData({
        name: '',
        version: 1,
        definition: {
          name: '',
          version: 1,
          parameters: {},
          steps: []
        },
        is_active: true
      });
      fetchJobs();
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job. Please check the job definition.');
    }
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
      const run = await jobApi.run(id, {});
      alert(`Job queued for execution! Run ID: ${run.id}`);
    } catch (error) {
      console.error('Failed to run job:', error);
      alert('Failed to run job.');
    }
  };

  const addStep = () => {
    const newStep = {
      type: 'winrm.exec',
      shell: 'powershell',
      target: '',
      command: '',
      timeoutSec: 60
    };
    
    setFormData({
      ...formData,
      definition: {
        ...formData.definition,
        steps: [...formData.definition.steps, newStep]
      }
    });
  };

  const removeStep = (index: number) => {
    const newSteps = formData.definition.steps.filter((_: any, i: number) => i !== index);
    setFormData({
      ...formData,
      definition: {
        ...formData.definition,
        steps: newSteps
      }
    });
  };

  const updateStep = (index: number, field: string, value: any) => {
    const newSteps = [...formData.definition.steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setFormData({
      ...formData,
      definition: {
        ...formData.definition,
        steps: newSteps
      }
    });
  };

  if (loading) return <div>Loading jobs...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Jobs</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Create Job
        </button>
      </div>

      <div className="card">
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

      {/* Create Job Modal */}
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
          <div className="card" style={{ width: '800px', margin: '20px', maxHeight: '90vh', overflow: 'auto' }}>
            <h3>Create New Job</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => {
                    const name = e.target.value;
                    setFormData({
                      ...formData,
                      name,
                      definition: { ...formData.definition, name }
                    });
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label>Version:</label>
                <input
                  type="number"
                  value={formData.version}
                  onChange={(e) => {
                    const version = parseInt(e.target.value);
                    setFormData({
                      ...formData,
                      version,
                      definition: { ...formData.definition, version }
                    });
                  }}
                  min={1}
                  required
                />
              </div>

              <div className="form-group">
                <label>Job Steps:</label>
                {formData.definition.steps.map((step: any, index: number) => (
                  <div key={index} style={{ 
                    border: '1px solid #ddd', 
                    padding: '10px', 
                    margin: '10px 0',
                    borderRadius: '4px' 
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h5>Step {index + 1}</h5>
                      <button 
                        type="button"
                        className="btn btn-danger"
                        onClick={() => removeStep(index)}
                        style={{ fontSize: '12px' }}
                      >
                        Remove
                      </button>
                    </div>
                    
                    <div className="form-group">
                      <label>Type:</label>
                      <select
                        value={step.type}
                        onChange={(e) => updateStep(index, 'type', e.target.value)}
                      >
                        <option value="winrm.exec">WinRM Execute</option>
                        <option value="winrm.copy">WinRM Copy</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Target:</label>
                      <select
                        value={step.target}
                        onChange={(e) => updateStep(index, 'target', e.target.value)}
                        required
                      >
                        <option value="">Select target...</option>
                        {(targets || []).map(target => (
                          <option key={target.id} value={target.name}>
                            {target.name} ({target.hostname})
                          </option>
                        ))}
                      </select>
                    </div>

                    {step.type === 'winrm.exec' && (
                      <>
                        <div className="form-group">
                          <label>Shell:</label>
                          <select
                            value={step.shell}
                            onChange={(e) => updateStep(index, 'shell', e.target.value)}
                          >
                            <option value="powershell">PowerShell</option>
                            <option value="cmd">Command Prompt</option>
                          </select>
                        </div>

                        <div className="form-group">
                          <label>Command:</label>
                          <textarea
                            value={step.command}
                            onChange={(e) => updateStep(index, 'command', e.target.value)}
                            rows={3}
                            placeholder="Enter PowerShell or CMD command"
                            required
                          />
                        </div>
                      </>
                    )}

                    <div className="form-group">
                      <label>Timeout (seconds):</label>
                      <input
                        type="number"
                        value={step.timeoutSec}
                        onChange={(e) => updateStep(index, 'timeoutSec', parseInt(e.target.value))}
                        min={1}
                      />
                    </div>
                  </div>
                ))}
                
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={addStep}
                >
                  Add Step
                </button>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Job</button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Jobs;