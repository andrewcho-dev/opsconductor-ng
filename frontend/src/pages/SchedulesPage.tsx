import React, { useState, useEffect } from 'react';
import { 
  Calendar, Plus, Search, Filter, Eye, Edit, Trash2, Play, 
  Pause, Clock, CheckCircle, AlertTriangle, RotateCcw
} from 'lucide-react';
import { scheduleApi, jobApi } from '../services/api';
import { Schedule, ScheduleCreate, Job } from '../types';

const SchedulesPage: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;

  useEffect(() => {
    loadSchedules();
    loadJobs();
  }, [currentPage, statusFilter]);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const response = await scheduleApi.list(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage
      );
      setSchedules(response.schedules);
      setTotalItems(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      const response = await jobApi.list(0, 1000); // Load all jobs for dropdown
      setJobs(response.jobs);
    } catch (err: any) {
      console.error('Failed to load jobs:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) return;
    
    try {
      await scheduleApi.delete(id);
      loadSchedules();
    } catch (err: any) {
      setError(err.message || 'Failed to delete schedule');
    }
  };

  const handleToggleStatus = async (schedule: Schedule) => {
    try {
      if (schedule.is_active) {
        await scheduleApi.disable(schedule.id);
      } else {
        await scheduleApi.enable(schedule.id);
      }
      loadSchedules();
    } catch (err: any) {
      setError(err.message || 'Failed to update schedule status');
    }
  };

  const handleTrigger = async (id: number) => {
    try {
      await scheduleApi.trigger(id);
      loadSchedules();
    } catch (err: any) {
      setError(err.message || 'Failed to trigger schedule');
    }
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? 'badge bg-success' : 'badge bg-secondary';
  };

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? (
      <CheckCircle className="text-success" size={16} />
    ) : (
      <Pause className="text-secondary" size={16} />
    );
  };

  const filteredSchedules = schedules.filter(schedule => {
    const matchesSearch = schedule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (schedule.description && schedule.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && schedule.is_active) ||
                         (statusFilter === 'inactive' && !schedule.is_active);
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">
                <Calendar className="me-2" size={24} />
                Workflow Schedules
              </h1>
              <p className="text-muted mb-0">Manage automated workflow execution schedules</p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={16} className="me-1" />
              Create Schedule
            </button>
          </div>

          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
              ></button>
            </div>
          )}

          {/* Filters */}
          <div className="card mb-4">
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="input-group">
                    <span className="input-group-text">
                      <Search size={16} />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search schedules..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                <div className="col-md-4">
                  <select
                    className="form-select"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                <div className="col-md-2">
                  <button
                    className="btn btn-outline-secondary w-100"
                    onClick={() => {
                      setSearchTerm('');
                      setStatusFilter('all');
                    }}
                  >
                    <Filter size={16} className="me-1" />
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Schedules Table */}
          <div className="card">
            <div className="card-body">
              {filteredSchedules.length === 0 ? (
                <div className="text-center py-5">
                  <Calendar size={48} className="text-muted mb-3" />
                  <h5 className="text-muted">No schedules found</h5>
                  <p className="text-muted">Create your first schedule to automate workflow execution.</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Name</th>
                        <th>Workflow</th>
                        <th>Schedule</th>
                        <th>Last Run</th>
                        <th>Next Run</th>
                        <th>Runs/Failures</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSchedules.map((schedule) => (
                        <tr key={schedule.id}>
                          <td>
                            <div className="d-flex align-items-center">
                              {getStatusIcon(schedule.is_active)}
                              <span className={`ms-2 ${getStatusBadge(schedule.is_active)}`}>
                                {schedule.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div>
                              <div className="fw-medium">{schedule.name}</div>
                              {schedule.description && (
                                <div className="text-muted small">{schedule.description}</div>
                              )}
                            </div>
                          </td>
                          <td>
                            <span className="badge bg-light text-dark">
                              {schedule.job_name || `Job ${schedule.job_id}`}
                            </span>
                          </td>
                          <td>
                            <code className="small">{schedule.cron_expression}</code>
                            <div className="text-muted small">{schedule.timezone}</div>
                          </td>
                          <td>
                            <span className="small text-muted">
                              {schedule.last_run ? new Date(schedule.last_run).toLocaleString() : 'Never'}
                            </span>
                          </td>
                          <td>
                            <span className="small text-muted">
                              {schedule.next_run ? new Date(schedule.next_run).toLocaleString() : '-'}
                            </span>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <span className="badge bg-success me-1">{schedule.run_count}</span>
                              {schedule.failure_count > 0 && (
                                <span className="badge bg-danger">{schedule.failure_count}</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="btn-group btn-group-sm">
                              <button
                                className="btn btn-outline-success"
                                onClick={() => handleTrigger(schedule.id)}
                                title="Trigger Now"
                                disabled={!schedule.is_active}
                              >
                                <Play size={14} />
                              </button>
                              <button
                                className={`btn ${schedule.is_active ? 'btn-outline-warning' : 'btn-outline-success'}`}
                                onClick={() => handleToggleStatus(schedule)}
                                title={schedule.is_active ? 'Disable' : 'Enable'}
                              >
                                {schedule.is_active ? <Pause size={14} /> : <RotateCcw size={14} />}
                              </button>
                              <button
                                className="btn btn-outline-secondary"
                                onClick={() => {
                                  setSelectedSchedule(schedule);
                                  setShowEditModal(true);
                                }}
                                title="Edit"
                              >
                                <Edit size={14} />
                              </button>
                              <button
                                className="btn btn-outline-danger"
                                onClick={() => handleDelete(schedule.id)}
                                title="Delete"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <nav className="mt-4">
                  <ul className="pagination justify-content-center">
                    <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </button>
                    </li>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                      <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
                        <button
                          className="page-link"
                          onClick={() => setCurrentPage(page)}
                        >
                          {page}
                        </button>
                      </li>
                    ))}
                    <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </button>
                    </li>
                  </ul>
                </nav>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Schedule Modal */}
      {showCreateModal && (
        <ScheduleModal
          jobs={jobs}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadSchedules();
          }}
        />
      )}

      {/* Edit Schedule Modal */}
      {showEditModal && selectedSchedule && (
        <ScheduleModal
          schedule={selectedSchedule}
          jobs={jobs}
          onClose={() => {
            setShowEditModal(false);
            setSelectedSchedule(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedSchedule(null);
            loadSchedules();
          }}
        />
      )}
    </div>
  );
};

// Schedule Modal Component (Create/Edit)
const ScheduleModal: React.FC<{
  schedule?: Schedule;
  jobs: Job[];
  onClose: () => void;
  onSuccess: () => void;
}> = ({ schedule, jobs, onClose, onSuccess }) => {
  const isEdit = !!schedule;
  const [formData, setFormData] = useState<ScheduleCreate>({
    name: schedule?.name || '',
    description: schedule?.description || '',
    cron_expression: schedule?.cron_expression || '0 0 * * *',
    timezone: schedule?.timezone || 'UTC',
    job_id: schedule?.job_id || (jobs.length > 0 ? jobs[0].id : 0),
    is_active: schedule?.is_active ?? true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit && schedule) {
        await scheduleApi.update(schedule.id, formData);
      } else {
        await scheduleApi.create(formData);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message || `Failed to ${isEdit ? 'update' : 'create'} schedule`);
    } finally {
      setLoading(false);
    }
  };

  const cronPresets = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Every 15 minutes', value: '*/15 * * * *' },
    { label: 'Every 30 minutes', value: '*/30 * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Every 6 hours', value: '0 */6 * * *' },
    { label: 'Every 12 hours', value: '0 */12 * * *' },
    { label: 'Daily at midnight', value: '0 0 * * *' },
    { label: 'Daily at 6 AM', value: '0 6 * * *' },
    { label: 'Weekly (Sunday)', value: '0 0 * * 0' },
    { label: 'Monthly (1st)', value: '0 0 1 * *' }
  ];

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {isEdit ? 'Edit Schedule' : 'Create Schedule'}
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div className="alert alert-danger">{error}</div>
              )}
              
              <div className="row g-3">
                <div className="col-12">
                  <label className="form-label">Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                
                <div className="col-12">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                
                <div className="col-12">
                  <label className="form-label">Workflow *</label>
                  <select
                    className="form-select"
                    value={formData.job_id}
                    onChange={(e) => setFormData({ ...formData, job_id: parseInt(e.target.value) })}
                    required
                  >
                    <option value="">Select a workflow...</option>
                    {jobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="col-md-8">
                  <label className="form-label">Cron Expression *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.cron_expression}
                    onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })}
                    placeholder="0 0 * * *"
                    required
                  />
                  <div className="form-text">
                    Format: minute hour day month day-of-week
                  </div>
                </div>
                
                <div className="col-md-4">
                  <label className="form-label">Timezone</label>
                  <select
                    className="form-select"
                    value={formData.timezone}
                    onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                  </select>
                </div>
                
                <div className="col-12">
                  <label className="form-label">Quick Presets</label>
                  <div className="d-flex flex-wrap gap-2">
                    {cronPresets.map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        className="btn btn-outline-secondary btn-sm"
                        onClick={() => setFormData({ ...formData, cron_expression: preset.value })}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="col-12">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    <label className="form-check-label">
                      Active
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    {isEdit ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  isEdit ? 'Update Schedule' : 'Create Schedule'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SchedulesPage;