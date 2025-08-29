import React, { useState, useEffect } from 'react';
import { discoveryApi } from '../services/api';
import {
  DiscoveryJob,
  DiscoveredTarget,
  DiscoveryJobCreate,
  DiscoveryConfig
} from '../types';

const Discovery: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'targets' | 'create'>('jobs');
  const [jobs, setJobs] = useState<DiscoveryJob[]>([]);
  const [targets, setTargets] = useState<DiscoveredTarget[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalTargets, setTotalTargets] = useState(0);
  const [pageSize] = useState(50); // Show 50 targets per page
  
  // Edit states
  const [editingJob, setEditingJob] = useState<DiscoveryJob | null>(null);
  const [editingTarget, setEditingTarget] = useState<DiscoveredTarget | null>(null);
  const [showEditJobModal, setShowEditJobModal] = useState(false);
  const [showEditTargetModal, setShowEditTargetModal] = useState(false);

  // Form state for creating new discovery job
  const [newJob, setNewJob] = useState<DiscoveryJobCreate>({
    name: '',
    discovery_type: 'network_scan',
    config: {
      cidr_ranges: [''],
      scan_intensity: 'standard',
      os_detection: true,
      service_detection: true,
      connection_testing: false,
      timeout: 300
    }
  });

  useEffect(() => {
    if (activeTab === 'jobs') {
      loadJobs();
    } else if (activeTab === 'targets') {
      setCurrentPage(1); // Reset to first page when switching to targets tab
      loadTargets(1);
    }
  }, [activeTab]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await discoveryApi.listJobs();
      setJobs(response.jobs || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load discovery jobs');
    } finally {
      setLoading(false);
    }
  };

  const loadTargets = async (page: number = currentPage) => {
    try {
      setLoading(true);
      const skip = (page - 1) * pageSize;
      const response = await discoveryApi.listTargets(skip, pageSize);
      setTargets(response.targets || []);
      setTotalTargets(response.total || 0);
      setCurrentPage(page);
    } catch (err: any) {
      setError(err.message || 'Failed to load discovered targets');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      
      // Filter out empty CIDR ranges
      const config: DiscoveryConfig = {
        ...newJob.config,
        cidr_ranges: newJob.config.cidr_ranges?.filter(range => range.trim() !== '') || []
      };

      await discoveryApi.createJob({
        ...newJob,
        config
      });

      // Reset form
      setNewJob({
        name: '',
        discovery_type: 'network_scan',
        config: {
          cidr_ranges: [''],
          scan_intensity: 'standard',
          os_detection: true,
          service_detection: true,
          connection_testing: false,
          timeout: 300
        }
      });

      // Switch to jobs tab and reload
      setActiveTab('jobs');
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to create discovery job');
    } finally {
      setLoading(false);
    }
  };

  const handleImportTargets = async () => {
    if (selectedTargets.length === 0) {
      setError('Please select targets to import');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const result = await discoveryApi.importTargets({
        target_ids: selectedTargets,
        import_options: {
          auto_assign_credentials: false,
          add_tags: ['discovered']
        }
      });

      alert(`Successfully imported ${result.imported} targets to registered targets. ${result.failed} failed.`);
      setSelectedTargets([]);
      await loadTargets();
    } catch (err: any) {
      setError(err.message || 'Failed to import targets');
    } finally {
      setLoading(false);
    }
  };

  const handleIgnoreTargets = async () => {
    if (selectedTargets.length === 0) {
      setError('Please select targets to ignore');
      return;
    }

    if (!window.confirm(`Are you sure you want to ignore ${selectedTargets.length} targets? This will permanently remove them from the discovered targets list.`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      await discoveryApi.ignoreTargets(selectedTargets);
      alert(`Removed ${selectedTargets.length} ignored targets from the list`);
      setSelectedTargets([]);
      await loadTargets();
    } catch (err: any) {
      setError(err.message || 'Failed to ignore targets');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTargets = async () => {
    if (selectedTargets.length === 0) {
      setError('Please select targets to delete');
      return;
    }

    if (!window.confirm(`Are you sure you want to permanently delete ${selectedTargets.length} targets? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const result = await discoveryApi.bulkDeleteTargets(selectedTargets);
      alert(`Successfully deleted ${result.deleted} targets.`);
      setSelectedTargets([]);
      await loadTargets();
    } catch (err: any) {
      setError(err.message || 'Failed to delete targets');
    } finally {
      setLoading(false);
    }
  };

  const addCidrRange = () => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        cidr_ranges: [...(prev.config.cidr_ranges || []), '']
      }
    }));
  };

  const updateCidrRange = (index: number, value: string) => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        cidr_ranges: prev.config.cidr_ranges?.map((range, i) => i === index ? value : range) || []
      }
    }));
  };

  const removeCidrRange = (index: number) => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        cidr_ranges: prev.config.cidr_ranges?.filter((_, i) => i !== index) || []
      }
    }));
  };

  const getStatusBadge = (status: string) => {
    const statusColors = {
      pending: 'badge-warning',
      running: 'badge-info',
      completed: 'badge-success',
      failed: 'badge-danger'
    };
    return statusColors[status as keyof typeof statusColors] || 'badge-secondary';
  };

  const getDuplicateStatusBadge = (status: string) => {
    const statusColors = {
      unique: 'badge-success',
      duplicate: 'badge-warning',
      similar: 'badge-info'
    };
    return statusColors[status as keyof typeof statusColors] || 'badge-secondary';
  };

  // CRUD Handlers
  const handleEditJob = (job: DiscoveryJob) => {
    setEditingJob(job);
    setShowEditJobModal(true);
  };

  const handleDeleteJob = async (jobId: number) => {
    if (!window.confirm('Are you sure you want to delete this discovery job? This will also delete all discovered targets from this job.')) {
      return;
    }

    try {
      setLoading(true);
      await discoveryApi.deleteJob(jobId);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to delete discovery job');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateJob = async (jobData: Partial<DiscoveryJobCreate>) => {
    if (!editingJob) return;

    try {
      setLoading(true);
      await discoveryApi.updateJob(editingJob.id, jobData);
      setShowEditJobModal(false);
      setEditingJob(null);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to update discovery job');
    } finally {
      setLoading(false);
    }
  };

  const handleEditTarget = (target: DiscoveredTarget) => {
    setEditingTarget(target);
    setShowEditTargetModal(true);
  };

  const handleDeleteTarget = async (targetId: number) => {
    if (!window.confirm('Are you sure you want to delete this discovered target?')) {
      return;
    }

    try {
      setLoading(true);
      await discoveryApi.deleteTarget(targetId);
      await loadTargets();
    } catch (err: any) {
      setError(err.message || 'Failed to delete discovered target');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTarget = async (targetData: Partial<DiscoveredTarget>) => {
    if (!editingTarget) return;

    try {
      setLoading(true);
      await discoveryApi.updateTarget(editingTarget.id, targetData);
      setShowEditTargetModal(false);
      setEditingTarget(null);
      await loadTargets();
    } catch (err: any) {
      setError(err.message || 'Failed to update discovered target');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="discovery-page">
      <div className="page-header">
        <h1>Target Discovery</h1>
        <p>Automatically discover Windows machines and other targets on your network</p>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
          <button 
            type="button" 
            className="btn-close" 
            onClick={() => setError(null)}
          ></button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="nav nav-tabs mb-4">
        <button
          className={`nav-link ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Discovery Jobs
        </button>
        <button
          className={`nav-link ${activeTab === 'targets' ? 'active' : ''}`}
          onClick={() => setActiveTab('targets')}
        >
          Discovered Targets
        </button>
        <button
          className={`nav-link ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          Create Discovery Job
        </button>
      </div>

      {/* Discovery Jobs Tab */}
      {activeTab === 'jobs' && (
        <div className="tab-content">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3>Discovery Jobs</h3>
            <button 
              className="btn btn-primary"
              onClick={() => setActiveTab('create')}
            >
              New Discovery Job
            </button>
          </div>

          {loading ? (
            <div className="text-center">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Duration</th>
                    <th>Results</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center text-muted">
                        No discovery jobs found. Create your first discovery job to get started.
                      </td>
                    </tr>
                  ) : (
                    jobs.map(job => (
                      <tr key={job.id}>
                        <td>
                          <strong>{job.name}</strong>
                        </td>
                        <td>
                          <span className="badge badge-secondary">
                            {job.discovery_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${getStatusBadge(job.status)}`}>
                            {job.status}
                          </span>
                        </td>
                        <td>{new Date(job.created_at).toLocaleString()}</td>
                        <td>
                          {job.started_at && job.completed_at ? (
                            `${Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
                          ) : job.started_at ? (
                            'Running...'
                          ) : (
                            '-'
                          )}
                        </td>
                        <td>
                          {job.results_summary ? (
                            <div className="small">
                              <div>Hosts: {job.results_summary.total_hosts || 0}</div>
                              <div>Windows: {job.results_summary.windows_hosts || 0}</div>
                              <div>Linux: {job.results_summary.linux_hosts || 0}</div>
                            </div>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td>
                          <div className="btn-group btn-group-sm">
                            {(job.status === 'pending' || job.status === 'failed') && (
                              <button
                                className="btn btn-outline-primary"
                                onClick={() => handleEditJob(job)}
                                title="Edit Job"
                              >
                                Edit
                              </button>
                            )}
                            <button
                              className="btn btn-outline-danger"
                              onClick={() => handleDeleteJob(job.id)}
                              title="Delete Job"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Discovered Targets Tab */}
      {activeTab === 'targets' && (
        <div className="tab-content">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3>Discovered Targets</h3>
            <div>
              {selectedTargets.length > 0 && (
                <div className="btn-group">
                  <button 
                    className="btn btn-success"
                    onClick={handleImportTargets}
                    disabled={loading}
                    title="Import selected targets to registered targets and remove from this list"
                  >
                    Import ({selectedTargets.length})
                  </button>
                  <button 
                    className="btn btn-secondary"
                    onClick={handleIgnoreTargets}
                    disabled={loading}
                    title="Remove selected targets from this list permanently"
                  >
                    Ignore ({selectedTargets.length})
                  </button>
                  <button 
                    className="btn btn-danger"
                    onClick={handleDeleteTargets}
                    disabled={loading}
                    title="Permanently delete selected targets"
                  >
                    Delete ({selectedTargets.length})
                  </button>
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="text-center">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTargets(targets.filter(t => t.import_status === 'pending').map(t => t.id));
                          } else {
                            setSelectedTargets([]);
                          }
                        }}
                        checked={selectedTargets.length > 0 && selectedTargets.length === targets.filter(t => t.import_status === 'pending').length}
                      />
                    </th>
                    <th>IP Address</th>
                    <th>Hostname</th>
                    <th>OS</th>
                    <th>Services</th>
                    <th>Status</th>
                    <th>Discovered</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {targets.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center text-muted">
                        No discovered targets found. Run a discovery job to find targets.
                      </td>
                    </tr>
                  ) : (
                    targets.map(target => (
                      <tr key={target.id}>
                        <td>
                          {target.import_status === 'pending' && (
                            <input
                              type="checkbox"
                              checked={selectedTargets.includes(target.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedTargets(prev => [...prev, target.id]);
                                } else {
                                  setSelectedTargets(prev => prev.filter(id => id !== target.id));
                                }
                              }}
                            />
                          )}
                        </td>
                        <td>
                          <strong>{target.ip_address}</strong>
                        </td>
                        <td>{target.hostname || '-'}</td>
                        <td>
                          {target.os_type && (
                            <div>
                              <div>{target.os_type}</div>
                              {target.os_version && (
                                <small className="text-muted">{target.os_version}</small>
                              )}
                            </div>
                          )}
                        </td>
                        <td>
                          {target.services.length > 0 ? (
                            <div className="small">
                              {target.services.map((service, idx) => (
                                <span key={idx} className="badge badge-info me-1 mb-1">
                                  {service.protocol}:{service.port}
                                  {service.is_secure && ' (SSL)'}
                                </span>
                              ))}
                            </div>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td>
                          <div>
                            <span className={`badge ${getDuplicateStatusBadge(target.duplicate_status)} me-1`}>
                              {target.duplicate_status}
                            </span>
                            <span className={`badge ${target.import_status === 'pending' ? 'badge-warning' : target.import_status === 'imported' ? 'badge-success' : 'badge-secondary'}`}>
                              {target.import_status}
                            </span>
                          </div>
                        </td>
                        <td>{new Date(target.discovered_at).toLocaleString()}</td>
                        <td>
                          <div className="btn-group btn-group-sm">
                            <button
                              className="btn btn-outline-primary"
                              onClick={() => handleEditTarget(target)}
                              title="Edit Target"
                            >
                              Edit
                            </button>
                            <button
                              className="btn btn-outline-danger"
                              onClick={() => handleDeleteTarget(target.id)}
                              title="Delete Target"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination Controls */}
          {totalTargets > pageSize && (
            <div className="d-flex justify-content-between align-items-center mt-3">
              <div className="text-muted">
                Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalTargets)} of {totalTargets} targets
              </div>
              <nav>
                <ul className="pagination pagination-sm mb-0">
                  <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                    <button 
                      className="page-link" 
                      onClick={() => loadTargets(currentPage - 1)}
                      disabled={currentPage === 1 || loading}
                    >
                      Previous
                    </button>
                  </li>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.ceil(totalTargets / pageSize) }, (_, i) => i + 1)
                    .filter(page => {
                      // Show first page, last page, current page, and 2 pages around current
                      const totalPages = Math.ceil(totalTargets / pageSize);
                      return page === 1 || page === totalPages || 
                             (page >= currentPage - 2 && page <= currentPage + 2);
                    })
                    .map((page, index, array) => {
                      // Add ellipsis if there's a gap
                      const showEllipsis = index > 0 && page - array[index - 1] > 1;
                      return (
                        <React.Fragment key={page}>
                          {showEllipsis && (
                            <li className="page-item disabled">
                              <span className="page-link">...</span>
                            </li>
                          )}
                          <li className={`page-item ${currentPage === page ? 'active' : ''}`}>
                            <button 
                              className="page-link" 
                              onClick={() => loadTargets(page)}
                              disabled={loading}
                            >
                              {page}
                            </button>
                          </li>
                        </React.Fragment>
                      );
                    })}
                  
                  <li className={`page-item ${currentPage === Math.ceil(totalTargets / pageSize) ? 'disabled' : ''}`}>
                    <button 
                      className="page-link" 
                      onClick={() => loadTargets(currentPage + 1)}
                      disabled={currentPage === Math.ceil(totalTargets / pageSize) || loading}
                    >
                      Next
                    </button>
                  </li>
                </ul>
              </nav>
            </div>
          )}
        </div>
      )}

      {/* Create Discovery Job Tab */}
      {activeTab === 'create' && (
        <div className="tab-content">
          <h3>Create Discovery Job</h3>
          <form onSubmit={handleCreateJob} className="row g-3">
            <div className="col-md-6">
              <label htmlFor="jobName" className="form-label">Job Name</label>
              <input
                type="text"
                className="form-control"
                id="jobName"
                value={newJob.name}
                onChange={(e) => setNewJob(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>

            <div className="col-md-6">
              <label htmlFor="discoveryType" className="form-label">Discovery Type</label>
              <select
                className="form-select"
                id="discoveryType"
                value={newJob.discovery_type}
                onChange={(e) => setNewJob(prev => ({ ...prev, discovery_type: e.target.value as any }))}
              >
                <option value="network_scan">Network Scan</option>
                <option value="ad_query" disabled>Active Directory Query (Coming Soon)</option>
                <option value="cloud_api" disabled>Cloud API Discovery (Coming Soon)</option>
              </select>
            </div>

            <div className="col-12">
              <label className="form-label">Network Ranges (CIDR)</label>
              {newJob.config.cidr_ranges?.map((range, index) => (
                <div key={index} className="input-group mb-2">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g., 192.168.1.0/24"
                    value={range}
                    onChange={(e) => updateCidrRange(index, e.target.value)}
                  />
                  <button
                    type="button"
                    className="btn btn-outline-danger"
                    onClick={() => removeCidrRange(index)}
                    disabled={newJob.config.cidr_ranges?.length === 1}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="btn btn-outline-primary btn-sm"
                onClick={addCidrRange}
              >
                Add Network Range
              </button>
            </div>

            <div className="col-md-4">
              <label htmlFor="scanIntensity" className="form-label">Scan Intensity</label>
              <select
                className="form-select"
                id="scanIntensity"
                value={newJob.config.scan_intensity}
                onChange={(e) => setNewJob(prev => ({
                  ...prev,
                  config: { ...prev.config, scan_intensity: e.target.value as any }
                }))}
              >
                <option value="light">Light - Ports: 22, 3389, 5985</option>
                <option value="standard">Standard - Ports: 22, 80, 135, 443, 3389, 5985, 5986</option>
                <option value="deep">Deep - Ports: 22, 80, 135, 139, 443, 445, 3389, 5985, 5986, 8080</option>
              </select>
              <div className="form-text">
                <small>
                  <strong>Current scan:</strong> 22 (SSH), 3389 (RDP), 5985 (WinRM HTTP), 5986 (WinRM HTTPS)
                </small>
              </div>
            </div>

            <div className="col-md-4">
              <label htmlFor="timeout" className="form-label">Timeout (seconds)</label>
              <input
                type="number"
                className="form-control"
                id="timeout"
                min="60"
                max="3600"
                value={newJob.config.timeout}
                onChange={(e) => setNewJob(prev => ({
                  ...prev,
                  config: { ...prev.config, timeout: parseInt(e.target.value) }
                }))}
              />
            </div>

            <div className="col-md-4">
              <label className="form-label">Options</label>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="osDetection"
                  checked={newJob.config.os_detection}
                  onChange={(e) => setNewJob(prev => ({
                    ...prev,
                    config: { ...prev.config, os_detection: e.target.checked }
                  }))}
                />
                <label className="form-check-label" htmlFor="osDetection">
                  OS Detection
                </label>
              </div>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="serviceDetection"
                  checked={newJob.config.service_detection}
                  onChange={(e) => setNewJob(prev => ({
                    ...prev,
                    config: { ...prev.config, service_detection: e.target.checked }
                  }))}
                />
                <label className="form-check-label" htmlFor="serviceDetection">
                  Service Detection
                </label>
              </div>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="connectionTesting"
                  checked={newJob.config.connection_testing}
                  onChange={(e) => setNewJob(prev => ({
                    ...prev,
                    config: { ...prev.config, connection_testing: e.target.checked }
                  }))}
                />
                <label className="form-check-label" htmlFor="connectionTesting">
                  Connection Testing
                </label>
              </div>
            </div>

            <div className="col-12">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Discovery Job'}
              </button>
              <button
                type="button"
                className="btn btn-secondary ms-2"
                onClick={() => setActiveTab('jobs')}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Job Modal */}
      {showEditJobModal && editingJob && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Edit Discovery Job</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowEditJobModal(false);
                    setEditingJob(null);
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target as HTMLFormElement);
                  const name = formData.get('name') as string;
                  const config = editingJob.config;
                  handleUpdateJob({ name, config });
                }}>
                  <div className="mb-3">
                    <label htmlFor="editJobName" className="form-label">Job Name</label>
                    <input
                      type="text"
                      className="form-control"
                      id="editJobName"
                      name="name"
                      defaultValue={editingJob.name}
                      required
                    />
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setShowEditJobModal(false);
                        setEditingJob(null);
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Updating...' : 'Update Job'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Target Modal */}
      {showEditTargetModal && editingTarget && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Edit Discovered Target</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowEditTargetModal(false);
                    setEditingTarget(null);
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target as HTMLFormElement);
                  const hostname = formData.get('hostname') as string;
                  const os_type = formData.get('os_type') as string;
                  const os_version = formData.get('os_version') as string;
                  const import_status = formData.get('import_status') as 'pending' | 'imported' | 'ignored' | 'duplicate_skipped';
                  handleUpdateTarget({ hostname, os_type, os_version, import_status });
                }}>
                  <div className="mb-3">
                    <label htmlFor="editHostname" className="form-label">Hostname</label>
                    <input
                      type="text"
                      className="form-control"
                      id="editHostname"
                      name="hostname"
                      defaultValue={editingTarget.hostname || ''}
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="editOsType" className="form-label">OS Type</label>
                    <select
                      className="form-select"
                      id="editOsType"
                      name="os_type"
                      defaultValue={editingTarget.os_type || ''}
                    >
                      <option value="">Unknown</option>
                      <option value="windows">Windows</option>
                      <option value="linux">Linux</option>
                      <option value="unix">Unix</option>
                      <option value="macos">macOS</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label htmlFor="editOsVersion" className="form-label">OS Version</label>
                    <input
                      type="text"
                      className="form-control"
                      id="editOsVersion"
                      name="os_version"
                      defaultValue={editingTarget.os_version || ''}
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="editImportStatus" className="form-label">Import Status</label>
                    <select
                      className="form-select"
                      id="editImportStatus"
                      name="import_status"
                      defaultValue={editingTarget.import_status}
                    >
                      <option value="pending">Pending</option>
                      <option value="imported">Imported</option>
                      <option value="ignored">Ignored</option>
                      <option value="duplicate_skipped">Duplicate Skipped</option>
                    </select>
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setShowEditTargetModal(false);
                        setEditingTarget(null);
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Updating...' : 'Update Target'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal backdrop */}
      {(showEditJobModal || showEditTargetModal) && (
        <div className="modal-backdrop show"></div>
      )}
    </div>
  );
};

export default Discovery;