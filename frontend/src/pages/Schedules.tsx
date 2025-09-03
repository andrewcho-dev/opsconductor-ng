import React, { useState, useEffect } from 'react';
import { schedulerApi, jobApi } from '../services/api';
import { Schedule, ScheduleCreate, Job, SchedulerStatus } from '../types';
import { X, Plus, Edit, Trash2, Play, Square, Clock, Calendar } from 'lucide-react';

const Schedules: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState<ScheduleCreate>({
    job_id: 0,
    cron: '',
    timezone: 'America/Los_Angeles',
    is_active: true
  });

  // Common cron expressions
  const cronPresets = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Every 15 minutes', value: '*/15 * * * *' },
    { label: 'Every 30 minutes', value: '*/30 * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Every day at 9 AM', value: '0 9 * * *' },
    { label: 'Every weekday at 9 AM', value: '0 9 * * 1-5' },
    { label: 'Every Sunday at 2 AM', value: '0 2 * * 0' }
  ];

  const timezones = [
    'America/Los_Angeles',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'UTC',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Shanghai'
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [schedulesData, jobsData, statusData] = await Promise.all([
        schedulerApi.list(),
        jobApi.list(),
        schedulerApi.getStatus()
      ]);
      setSchedules(schedulesData.schedules);
      setJobs(jobsData.jobs);
      setSchedulerStatus(statusData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      
      if (editingSchedule) {
        await schedulerApi.update(editingSchedule.id, {
          cron: formData.cron,
          timezone: formData.timezone,
          is_active: formData.is_active
        });
      } else {
        await schedulerApi.create(formData);
      }
      await fetchData();
      resetForm();
      setShowCreateForm(false);
    } catch (err: any) {
      setError(err.message || 'Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      try {
        await schedulerApi.delete(id);
        await fetchData();
        if (selectedSchedule?.id === id) {
          setSelectedSchedule(null);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to delete schedule');
      }
    }
  };

  const handleEdit = (schedule: Schedule) => {
    setEditingSchedule(schedule);
    setSelectedSchedule(schedule);
    setFormData({
      job_id: schedule.job_id,
      cron: schedule.cron,
      timezone: schedule.timezone,
      is_active: schedule.is_active
    });
    setShowCreateForm(true);
  };

  const resetForm = () => {
    setFormData({
      job_id: 0,
      cron: '',
      timezone: 'America/Los_Angeles',
      is_active: true
    });
    setEditingSchedule(null);
  };

  const handleSchedulerToggle = async () => {
    try {
      if (schedulerStatus?.scheduler_running) {
        await schedulerApi.stop();
      } else {
        await schedulerApi.start();
      }
      await fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle scheduler');
    }
  };

  const getJobName = (jobId: number) => {
    const job = jobs.find(j => j.id === jobId);
    return job ? job.name : `Job ${jobId}`;
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? 'status-badge-success' : 'status-badge-neutral';
  };

  const getSchedulerStatusBadge = (running: boolean) => {
    return running ? 'status-badge-success' : 'status-badge-danger';
  };

  const parseCronExpression = (cron: string) => {
    const preset = cronPresets.find(p => p.value === cron);
    return preset ? preset.label : cron;
  };

  if (loading) {
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
          /* Dashboard-style layout - 2/3, 1/3 format */
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
          .header-subtitle {
            font-size: 12px;
            color: var(--neutral-600);
            margin: 2px 0 0 0;
          }
          .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: calc(100vh - 110px);
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
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Scheduler status bar */
          .scheduler-status-bar {
            background: var(--neutral-50);
            padding: 8px 12px;
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
          }
          .scheduler-info {
            display: flex;
            gap: 16px;
            align-items: center;
          }
          .scheduler-info-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
          }
          .scheduler-info-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .scheduler-info-value {
            font-size: 12px;
            color: var(--neutral-800);
          }
          
          /* Schedules table styles */
          .schedules-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .schedules-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .schedules-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .schedules-table tr:hover {
            background: var(--neutral-50);
          }
          .schedules-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .schedules-table tr {
            cursor: pointer;
          }
          
          /* Details panel */
          .details-panel {
            padding: 8px;
          }
          .details-panel h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--neutral-800);
          }
          .detail-group {
            margin-bottom: 12px;
          }
          .detail-label {
            font-size: 10px;
            font-weight: 600;
            color: var(--neutral-500);
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .detail-value {
            font-size: 12px;
            color: var(--neutral-800);
            padding: 6px 0;
            border-bottom: 1px solid var(--neutral-100);
          }
          
          /* Create form styles */
          .create-form {
            padding: 8px;
          }
          .form-group {
            margin-bottom: 12px;
          }
          .form-label {
            font-size: 11px;
            font-weight: 600;
            color: var(--neutral-700);
            margin-bottom: 4px;
            display: block;
          }
          .form-input, .form-select, .form-textarea {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 4px;
            font-size: 12px;
            background: white;
          }
          .form-input:focus, .form-select:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }
          
          /* Button styles */
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            background: none;
            cursor: pointer;
            transition: all 0.15s;
            margin: 0 1px;
            padding: 2px;
          }
          .btn-icon:hover {
            opacity: 0.7;
          }
          .btn-icon:disabled {
            opacity: 0.3;
            cursor: not-allowed;
          }
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover:not(:disabled) {
            color: var(--danger-red);
          }
          .btn-ghost {
            color: var(--neutral-500);
          }
          .btn-ghost:hover:not(:disabled) {
            color: var(--neutral-700);
          }
          .btn-primary {
            background: var(--primary-blue);
            color: white;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
          }
          .btn-primary:hover:not(:disabled) {
            background: var(--primary-blue-dark);
          }
          .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .btn-secondary {
            background: var(--neutral-200);
            color: var(--neutral-700);
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
          }
          .btn-secondary:hover:not(:disabled) {
            background: var(--neutral-300);
          }
          
          .action-buttons {
            display: flex;
            gap: 4px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--neutral-200);
          }
          
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 150px;
            color: var(--neutral-500);
            text-align: center;
          }
          .empty-state h3 {
            margin: 0 0 6px 0;
            font-size: 14px;
            font-weight: 600;
          }
          .empty-state p {
            margin: 0 0 12px 0;
            font-size: 12px;
          }
          
          .status-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .status-badge-success {
            background: var(--success-green-light);
            color: var(--success-green);
          }
          .status-badge-danger {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          .status-badge-warning {
            background: var(--warning-yellow-light);
            color: var(--warning-yellow);
          }
          .status-badge-info {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
          }
          .status-badge-neutral {
            background: var(--neutral-200);
            color: var(--neutral-600);
          }
          
          .alert {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
          }
          
          .cron-code {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: var(--neutral-100);
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 11px;
          }
          
          .preset-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-top: 6px;
          }
          .preset-btn {
            padding: 3px 6px;
            font-size: 10px;
            border: 1px solid var(--neutral-300);
            background: white;
            border-radius: 3px;
            cursor: pointer;
          }
          .preset-btn:hover {
            background: var(--neutral-50);
          }
          
          .checkbox-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            cursor: pointer;
          }
          .checkbox-label input[type="checkbox"] {
            width: 14px;
            height: 14px;
          }
          
          .scheduler-toggle-btn {
            padding: 4px 8px;
            font-size: 11px;
            border: 1px solid;
            border-radius: 3px;
            cursor: pointer;
            font-weight: 500;
          }
          .scheduler-toggle-btn.running {
            background: var(--danger-red);
            color: white;
            border-color: var(--danger-red);
          }
          .scheduler-toggle-btn.stopped {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Schedule Management</h1>
          <p className="header-subtitle">Manage automated job scheduling and monitor scheduler status</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={() => {
              resetForm();
              setShowCreateForm(true);
            }}
            title="Create new schedule"
            disabled={showCreateForm}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {error && (
        <div className="alert">
          {error}
          <button 
            style={{ float: 'right', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>
      )}

      {/* 2/3, 1/3 dashboard grid */}
      <div className="dashboard-grid">
        {/* Left 2/3: Schedules Table */}
        <div className="dashboard-section">
          <div className="section-header">
            Job Schedules ({schedules.length})
            <button 
              className="btn-icon btn-success"
              onClick={() => {
                resetForm();
                setShowCreateForm(true);
              }}
              title="Create new schedule"
              disabled={showCreateForm}
            >
              <Plus size={14} />
            </button>
          </div>
          
          {/* Scheduler Status Bar */}
          {schedulerStatus && (
            <div className="scheduler-status-bar">
              <div className="scheduler-info">
                <div className="scheduler-info-item">
                  <div className="scheduler-info-label">Status</div>
                  <div className="scheduler-info-value">
                    <span className={`status-badge ${getSchedulerStatusBadge(schedulerStatus.scheduler_running)}`}>
                      {schedulerStatus.scheduler_running ? 'Running' : 'Stopped'}
                    </span>
                  </div>
                </div>
                <div className="scheduler-info-item">
                  <div className="scheduler-info-label">Active Schedules</div>
                  <div className="scheduler-info-value">{schedulerStatus.active_schedules}</div>
                </div>
                <div className="scheduler-info-item">
                  <div className="scheduler-info-label">Next Execution</div>
                  <div className="scheduler-info-value">{formatDateTime(schedulerStatus.next_execution)}</div>
                </div>
                <div className="scheduler-info-item">
                  <div className="scheduler-info-label">Last Check</div>
                  <div className="scheduler-info-value">{formatDateTime(schedulerStatus.last_check)}</div>
                </div>
              </div>
              <button
                onClick={handleSchedulerToggle}
                className={`scheduler-toggle-btn ${schedulerStatus.scheduler_running ? 'running' : 'stopped'}`}
              >
                {schedulerStatus.scheduler_running ? 'Stop Scheduler' : 'Start Scheduler'}
              </button>
            </div>
          )}
          
          <div className="compact-content">
            {schedules.length === 0 ? (
              <div className="empty-state">
                <h3>No schedules found</h3>
                <p>Create your first schedule to automate job execution.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={() => {
                    resetForm();
                    setShowCreateForm(true);
                  }}
                  title="Create first schedule"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="schedules-table">
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Schedule</th>
                      <th>Timezone</th>
                      <th>Next Run</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedules.map((schedule) => (
                      <tr 
                        key={schedule.id} 
                        className={selectedSchedule?.id === schedule.id ? 'selected' : ''}
                        onClick={() => setSelectedSchedule(schedule)}
                      >
                        <td>
                          <div style={{ fontWeight: '500' }}>{getJobName(schedule.job_id)}</div>
                          <div style={{ fontSize: '10px', color: 'var(--neutral-500)' }}>ID: {schedule.id}</div>
                        </td>
                        <td>
                          <div className="cron-code">{schedule.cron}</div>
                          <div style={{ fontSize: '10px', color: 'var(--neutral-500)', marginTop: '2px' }}>
                            {parseCronExpression(schedule.cron)}
                          </div>
                        </td>
                        <td style={{ fontSize: '11px' }}>{schedule.timezone}</td>
                        <td style={{ fontSize: '11px', color: 'var(--neutral-600)' }}>
                          {formatDateTime(schedule.next_run_at)}
                        </td>
                        <td>
                          <span className={`status-badge ${getStatusBadge(schedule.is_active)}`}>
                            {schedule.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '2px' }}>
                            <button 
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEdit(schedule);
                              }}
                              title="Edit schedule"
                            >
                              <Edit size={14} />
                            </button>
                            <button 
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(schedule.id);
                              }}
                              title="Delete schedule"
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
          </div>
        </div>

        {/* Right 1/3: Details/Create Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {showCreateForm ? (editingSchedule ? 'Edit Schedule' : 'Create Schedule') : selectedSchedule ? 'Schedule Details' : 'Select Schedule'}
            {showCreateForm && (
              <button 
                className="btn-icon btn-ghost"
                onClick={() => {
                  setShowCreateForm(false);
                  resetForm();
                }}
                title="Cancel"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <div className="compact-content">
            {showCreateForm ? (
              <div className="create-form">
                <form onSubmit={handleSubmit}>
                  <div className="form-group">
                    <label className="form-label">Job</label>
                    <select
                      className="form-select"
                      value={formData.job_id}
                      onChange={(e) => setFormData({ ...formData, job_id: parseInt(e.target.value) })}
                      required
                      disabled={!!editingSchedule}
                    >
                      <option value={0}>Select a job</option>
                      {jobs.map(job => (
                        <option key={job.id} value={job.id}>
                          {job.name} (ID: {job.id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Cron Expression</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.cron}
                      onChange={(e) => setFormData({ ...formData, cron: e.target.value })}
                      placeholder="* * * * *"
                      required
                    />
                    <div style={{ marginTop: '6px' }}>
                      <div style={{ fontSize: '10px', color: 'var(--neutral-600)', marginBottom: '4px' }}>
                        Quick presets:
                      </div>
                      <div className="preset-buttons">
                        {cronPresets.map((preset, index) => (
                          <button
                            key={index}
                            type="button"
                            onClick={() => setFormData({ ...formData, cron: preset.value })}
                            className="preset-btn"
                          >
                            {preset.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Timezone</label>
                    <select
                      className="form-select"
                      value={formData.timezone}
                      onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                    >
                      {timezones.map(tz => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      />
                      Active
                    </label>
                  </div>

                  <div className="action-buttons">
                    <button 
                      type="button"
                      className="btn-secondary"
                      onClick={() => {
                        setShowCreateForm(false);
                        resetForm();
                      }}
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit"
                      className="btn-primary"
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : (editingSchedule ? 'Update' : 'Create')}
                    </button>
                  </div>
                </form>
              </div>
            ) : selectedSchedule ? (
              <div className="details-panel">
                <h3>Schedule #{selectedSchedule.id}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Job</div>
                  <div className="detail-value">{getJobName(selectedSchedule.job_id)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Cron Expression</div>
                  <div className="detail-value">
                    <div className="cron-code">{selectedSchedule.cron}</div>
                    <div style={{ fontSize: '10px', color: 'var(--neutral-500)', marginTop: '4px' }}>
                      {parseCronExpression(selectedSchedule.cron)}
                    </div>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Timezone</div>
                  <div className="detail-value">{selectedSchedule.timezone}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${getStatusBadge(selectedSchedule.is_active)}`}>
                      {selectedSchedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Next Run</div>
                  <div className="detail-value">{formatDateTime(selectedSchedule.next_run_at)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Last Run</div>
                  <div className="detail-value">{formatDateTime(selectedSchedule.last_run_at)}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">{formatDateTime(selectedSchedule.created_at)}</div>
                </div>

                <div className="action-buttons">
                  <button 
                    className="btn-icon btn-ghost"
                    onClick={() => handleEdit(selectedSchedule)}
                    title="Edit schedule"
                  >
                    <Edit size={16} />
                  </button>
                  <button 
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(selectedSchedule.id)}
                    title="Delete schedule"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a schedule to view details or create a new one</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Schedules;