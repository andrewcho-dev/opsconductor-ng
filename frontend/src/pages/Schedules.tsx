import React, { useState, useEffect } from 'react';
import { schedulerApi, jobApi } from '../services/api';
import { Schedule, ScheduleCreate, Job, SchedulerStatus } from '../types';

const Schedules: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save schedule');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      try {
        await schedulerApi.delete(id);
        await fetchData();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete schedule');
      }
    }
  };

  const handleEdit = (schedule: Schedule) => {
    setEditingSchedule(schedule);
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
    setShowCreateForm(false);
  };

  const handleSchedulerToggle = async () => {
    try {
      if (schedulerStatus?.scheduler_running) {
        await schedulerApi.stop();
      } else {
        await schedulerApi.start();
      }
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle scheduler');
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

  if (loading) return <div className="loading">Loading schedules...</div>;

  return (
    <div className="schedules-page">
      <div className="page-header">
        <h1>Job Schedules</h1>
        <div className="header-actions">
          {schedulerStatus && (
            <div className="scheduler-status">
              <span className={`status-indicator ${schedulerStatus.scheduler_running ? 'running' : 'stopped'}`}>
                {schedulerStatus.scheduler_running ? 'Running' : 'Stopped'}
              </span>
              <button
                onClick={handleSchedulerToggle}
                className={`btn ${schedulerStatus.scheduler_running ? 'btn-danger' : 'btn-success'}`}
              >
                {schedulerStatus.scheduler_running ? 'Stop Scheduler' : 'Start Scheduler'}
              </button>
            </div>
          )}
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn btn-primary"
          >
            Create Schedule
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="alert-close">×</button>
        </div>
      )}

      {schedulerStatus && (
        <div className="scheduler-info">
          <div className="info-card">
            <h3>Scheduler Status</h3>
            <div className="status-grid">
              <div>
                <strong>Status:</strong> {schedulerStatus.scheduler_running ? 'Running' : 'Stopped'}
              </div>
              <div>
                <strong>Active Schedules:</strong> {schedulerStatus.active_schedules}
              </div>
              <div>
                <strong>Next Execution:</strong> {formatDateTime(schedulerStatus.next_execution)}
              </div>
              <div>
                <strong>Last Check:</strong> {formatDateTime(schedulerStatus.last_check)}
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>{editingSchedule ? 'Edit Schedule' : 'Create Schedule'}</h2>
              <button onClick={resetForm} className="modal-close">×</button>
            </div>
            <form onSubmit={handleSubmit} className="modal-body">
              <div className="form-group">
                <label htmlFor="job_id">Job:</label>
                <select
                  id="job_id"
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
                <label htmlFor="cron">Cron Expression:</label>
                <input
                  type="text"
                  id="cron"
                  value={formData.cron}
                  onChange={(e) => setFormData({ ...formData, cron: e.target.value })}
                  placeholder="* * * * *"
                  required
                />
                <div className="cron-presets">
                  <label>Quick presets:</label>
                  <div className="preset-buttons">
                    {cronPresets.map((preset, index) => (
                      <button
                        key={index}
                        type="button"
                        onClick={() => setFormData({ ...formData, cron: preset.value })}
                        className="btn btn-sm btn-secondary"
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="timezone">Timezone:</label>
                <select
                  id="timezone"
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

              <div className="modal-actions">
                <button type="button" onClick={resetForm} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingSchedule ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="schedules-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Job</th>
              <th>Cron Expression</th>
              <th>Timezone</th>
              <th>Next Run</th>
              <th>Last Run</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {schedules.length === 0 ? (
              <tr>
                <td colSpan={9} className="no-data">No schedules found</td>
              </tr>
            ) : (
              schedules.map(schedule => (
                <tr key={schedule.id}>
                  <td>{schedule.id}</td>
                  <td>{getJobName(schedule.job_id)}</td>
                  <td><code>{schedule.cron}</code></td>
                  <td>{schedule.timezone}</td>
                  <td>{formatDateTime(schedule.next_run_at)}</td>
                  <td>{formatDateTime(schedule.last_run_at)}</td>
                  <td>
                    <span className={`status-badge ${schedule.is_active ? 'active' : 'inactive'}`}>
                      {schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{formatDateTime(schedule.created_at)}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        onClick={() => handleEdit(schedule)}
                        className="btn btn-sm btn-secondary"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(schedule.id)}
                        className="btn btn-sm btn-danger"
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
    </div>
  );
};

export default Schedules;