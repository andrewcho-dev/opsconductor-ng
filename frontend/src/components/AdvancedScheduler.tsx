import React, { useState, useEffect } from 'react';
import { schedulerApi, jobApi } from '../services/api';
import { Schedule, ScheduleCreate, Job, SchedulerStatus } from '../types';

interface MaintenanceWindow {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  days_of_week: number[];
  timezone: string;
  is_active: boolean;
}

interface JobDependency {
  id: string;
  job_id: number;
  depends_on_job_id: number;
  condition: 'success' | 'failure' | 'completion';
  timeout_minutes: number;
}

interface AdvancedScheduleCreate extends ScheduleCreate {
  maintenance_windows?: string[];
  max_concurrent_runs?: number;
  retry_policy?: {
    max_retries: number;
    retry_delay_minutes: number;
    backoff_multiplier: number;
  };
  notification_settings?: {
    on_success: boolean;
    on_failure: boolean;
    on_retry: boolean;
    recipients: string[];
  };
  execution_window?: {
    start_time: string;
    end_time: string;
    timezone: string;
  };
}

const AdvancedScheduler: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [maintenanceWindows, setMaintenanceWindows] = useState<MaintenanceWindow[]>([]);
  const [jobDependencies, setJobDependencies] = useState<JobDependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showMaintenanceForm, setShowMaintenanceForm] = useState(false);
  const [showDependencyForm, setShowDependencyForm] = useState(false);
  const [activeTab, setActiveTab] = useState<'schedules' | 'maintenance' | 'dependencies'>('schedules');

  const [formData, setFormData] = useState<AdvancedScheduleCreate>({
    job_id: 0,
    cron: '',
    timezone: 'America/Los_Angeles',
    is_active: true,
    max_concurrent_runs: 1,
    retry_policy: {
      max_retries: 3,
      retry_delay_minutes: 5,
      backoff_multiplier: 2
    },
    notification_settings: {
      on_success: false,
      on_failure: true,
      on_retry: true,
      recipients: []
    }
  });

  const [maintenanceFormData, setMaintenanceFormData] = useState<Omit<MaintenanceWindow, 'id'>>({
    name: '',
    start_time: '02:00',
    end_time: '06:00',
    days_of_week: [0], // Sunday
    timezone: 'America/Los_Angeles',
    is_active: true
  });

  const [dependencyFormData, setDependencyFormData] = useState<Omit<JobDependency, 'id'>>({
    job_id: 0,
    depends_on_job_id: 0,
    condition: 'success',
    timeout_minutes: 60
  });

  const cronPresets = [
    { label: 'Every 5 minutes', value: '*/5 * * * *', description: 'High frequency monitoring' },
    { label: 'Every 15 minutes', value: '*/15 * * * *', description: 'Regular checks' },
    { label: 'Every hour', value: '0 * * * *', description: 'Hourly tasks' },
    { label: 'Every day at 2 AM', value: '0 2 * * *', description: 'Daily maintenance' },
    { label: 'Every weekday at 9 AM', value: '0 9 * * 1-5', description: 'Business hours' },
    { label: 'Every Sunday at 3 AM', value: '0 3 * * 0', description: 'Weekly maintenance' },
    { label: 'First day of month at 1 AM', value: '0 1 1 * *', description: 'Monthly tasks' },
    { label: 'Every 6 hours', value: '0 */6 * * *', description: 'Periodic sync' }
  ];

  const timezones = [
    'America/Los_Angeles', 'America/New_York', 'America/Chicago', 'America/Denver',
    'UTC', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
    'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Mumbai', 'Australia/Sydney'
  ];

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  useEffect(() => {
    fetchData();
    // Mock data for maintenance windows and dependencies
    setMaintenanceWindows([
      {
        id: '1',
        name: 'Weekend Maintenance',
        start_time: '02:00',
        end_time: '06:00',
        days_of_week: [0, 6], // Sunday, Saturday
        timezone: 'America/Los_Angeles',
        is_active: true
      }
    ]);
    setJobDependencies([
      {
        id: '1',
        job_id: 2,
        depends_on_job_id: 1,
        condition: 'success',
        timeout_minutes: 30
      }
    ]);
  }, []);

  const fetchData = async () => {
    try {
      const [schedulesResponse, jobsResponse, statusResponse] = await Promise.all([
        schedulerApi.list(),
        jobApi.list(),
        schedulerApi.getStatus()
      ]);
      
      setSchedules(schedulesResponse.schedules || []);
      setJobs(jobsResponse.jobs || []);
      setSchedulerStatus(statusResponse);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schedulerApi.create(formData);
      setShowCreateForm(false);
      fetchData();
      resetForm();
    } catch (error) {
      console.error('Failed to create schedule:', error);
      alert('Failed to create schedule. Please try again.');
    }
  };

  const handleCreateMaintenanceWindow = async (e: React.FormEvent) => {
    e.preventDefault();
    // Mock creation - in real implementation, this would call an API
    const newWindow: MaintenanceWindow = {
      ...maintenanceFormData,
      id: Date.now().toString()
    };
    setMaintenanceWindows([...maintenanceWindows, newWindow]);
    setShowMaintenanceForm(false);
    setMaintenanceFormData({
      name: '',
      start_time: '02:00',
      end_time: '06:00',
      days_of_week: [0],
      timezone: 'America/Los_Angeles',
      is_active: true
    });
  };

  const handleCreateDependency = async (e: React.FormEvent) => {
    e.preventDefault();
    // Mock creation - in real implementation, this would call an API
    const newDependency: JobDependency = {
      ...dependencyFormData,
      id: Date.now().toString()
    };
    setJobDependencies([...jobDependencies, newDependency]);
    setShowDependencyForm(false);
    setDependencyFormData({
      job_id: 0,
      depends_on_job_id: 0,
      condition: 'success',
      timeout_minutes: 60
    });
  };

  const resetForm = () => {
    setFormData({
      job_id: 0,
      cron: '',
      timezone: 'America/Los_Angeles',
      is_active: true,
      max_concurrent_runs: 1,
      retry_policy: {
        max_retries: 3,
        retry_delay_minutes: 5,
        backoff_multiplier: 2
      },
      notification_settings: {
        on_success: false,
        on_failure: true,
        on_retry: true,
        recipients: []
      }
    });
  };

  const getJobName = (jobId: number) => {
    return jobs.find(job => job.id === jobId)?.name || `Job ${jobId}`;
  };

  const toggleMaintenanceWindow = async (windowId: string) => {
    setMaintenanceWindows(windows =>
      windows.map(window =>
        window.id === windowId
          ? { ...window, is_active: !window.is_active }
          : window
      )
    );
  };

  const deleteMaintenanceWindow = (windowId: string) => {
    if (window.confirm('Are you sure you want to delete this maintenance window?')) {
      setMaintenanceWindows(windows => windows.filter(w => w.id !== windowId));
    }
  };

  const deleteDependency = (dependencyId: string) => {
    if (window.confirm('Are you sure you want to delete this dependency?')) {
      setJobDependencies(deps => deps.filter(d => d.id !== dependencyId));
    }
  };

  if (loading) return <div>Loading advanced scheduler...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Advanced Scheduler</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          {schedulerStatus && (
            <div style={{ 
              padding: '8px 16px', 
              borderRadius: '4px', 
              backgroundColor: schedulerStatus.is_running ? '#d4edda' : '#f8d7da',
              color: schedulerStatus.is_running ? '#155724' : '#721c24',
              fontSize: '14px'
            }}>
              Scheduler: {schedulerStatus.is_running ? 'Running' : 'Stopped'}
            </div>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ marginBottom: '20px', borderBottom: '1px solid #ddd' }}>
        <div style={{ display: 'flex', gap: '0' }}>
          {[
            { key: 'schedules', label: 'Schedules', icon: '📅' },
            { key: 'maintenance', label: 'Maintenance Windows', icon: '🔧' },
            { key: 'dependencies', label: 'Job Dependencies', icon: '🔗' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                padding: '12px 20px',
                border: 'none',
                borderBottom: activeTab === tab.key ? '2px solid #007bff' : '2px solid transparent',
                backgroundColor: activeTab === tab.key ? '#f8f9fa' : 'transparent',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Schedules Tab */}
      {activeTab === 'schedules' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Job Schedules</h2>
            <button 
              className="btn btn-primary"
              onClick={() => setShowCreateForm(true)}
            >
              Create Advanced Schedule
            </button>
          </div>

          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Schedule</th>
                  <th>Timezone</th>
                  <th>Next Run</th>
                  <th>Retry Policy</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map(schedule => (
                  <tr key={schedule.id}>
                    <td>{getJobName(schedule.job_id)}</td>
                    <td>
                      <code style={{ backgroundColor: '#f8f9fa', padding: '2px 6px', borderRadius: '3px' }}>
                        {schedule.cron}
                      </code>
                    </td>
                    <td>{schedule.timezone}</td>
                    <td>{schedule.next_run ? new Date(schedule.next_run).toLocaleString() : 'N/A'}</td>
                    <td>
                      <span style={{ fontSize: '12px', color: '#666' }}>
                        Max retries: 3, Delay: 5min
                      </span>
                    </td>
                    <td>
                      <span className={`status ${schedule.is_active ? 'status-succeeded' : 'status-failed'}`}>
                        {schedule.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button className="btn btn-primary" style={{ fontSize: '12px' }}>
                          Edit
                        </button>
                        <button className="btn btn-danger" style={{ fontSize: '12px' }}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Maintenance Windows Tab */}
      {activeTab === 'maintenance' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Maintenance Windows</h2>
            <button 
              className="btn btn-primary"
              onClick={() => setShowMaintenanceForm(true)}
            >
              Create Maintenance Window
            </button>
          </div>

          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Time Window</th>
                  <th>Days</th>
                  <th>Timezone</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {maintenanceWindows.map(window => (
                  <tr key={window.id}>
                    <td><strong>{window.name}</strong></td>
                    <td>{window.start_time} - {window.end_time}</td>
                    <td>
                      {window.days_of_week.map(day => dayNames[day]).join(', ')}
                    </td>
                    <td>{window.timezone}</td>
                    <td>
                      <span className={`status ${window.is_active ? 'status-succeeded' : 'status-failed'}`}>
                        {window.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button 
                          className="btn btn-secondary"
                          onClick={() => toggleMaintenanceWindow(window.id)}
                          style={{ fontSize: '12px' }}
                        >
                          {window.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button 
                          className="btn btn-danger"
                          onClick={() => deleteMaintenanceWindow(window.id)}
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
        </div>
      )}

      {/* Job Dependencies Tab */}
      {activeTab === 'dependencies' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Job Dependencies</h2>
            <button 
              className="btn btn-primary"
              onClick={() => setShowDependencyForm(true)}
            >
              Create Dependency
            </button>
          </div>

          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Depends On</th>
                  <th>Condition</th>
                  <th>Timeout</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobDependencies.map(dependency => (
                  <tr key={dependency.id}>
                    <td>{getJobName(dependency.job_id)}</td>
                    <td>{getJobName(dependency.depends_on_job_id)}</td>
                    <td>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        backgroundColor: dependency.condition === 'success' ? '#d4edda' : 
                                       dependency.condition === 'failure' ? '#f8d7da' : '#fff3cd',
                        color: dependency.condition === 'success' ? '#155724' : 
                               dependency.condition === 'failure' ? '#721c24' : '#856404'
                      }}>
                        {dependency.condition}
                      </span>
                    </td>
                    <td>{dependency.timeout_minutes} minutes</td>
                    <td>
                      <button 
                        className="btn btn-danger"
                        onClick={() => deleteDependency(dependency.id)}
                        style={{ fontSize: '12px' }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Schedule Modal */}
      {showCreateForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '700px', maxHeight: '90vh', overflow: 'auto' }}>
            <h3>Create Advanced Schedule</h3>
            <form onSubmit={handleCreateSchedule}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Job:</label>
                  <select
                    value={formData.job_id}
                    onChange={(e) => setFormData({ ...formData, job_id: parseInt(e.target.value) })}
                    required
                  >
                    <option value={0}>Select job...</option>
                    {jobs.map(job => (
                      <option key={job.id} value={job.id}>{job.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Timezone:</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  >
                    {timezones.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Schedule (Cron Expression):</label>
                <input
                  type="text"
                  value={formData.cron}
                  onChange={(e) => setFormData({ ...formData, cron: e.target.value })}
                  placeholder="* * * * *"
                  required
                />
                <div style={{ marginTop: '10px' }}>
                  <label style={{ fontSize: '12px', color: '#666' }}>Quick presets:</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '5px', marginTop: '5px' }}>
                    {cronPresets.map(preset => (
                      <button
                        key={preset.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, cron: preset.value })}
                        style={{
                          padding: '5px 8px', fontSize: '11px', border: '1px solid #ddd',
                          borderRadius: '3px', backgroundColor: '#f8f9fa', cursor: 'pointer'
                        }}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Max Concurrent Runs:</label>
                  <input
                    type="number"
                    value={formData.max_concurrent_runs}
                    onChange={(e) => setFormData({ ...formData, max_concurrent_runs: parseInt(e.target.value) })}
                    min={1}
                    max={10}
                  />
                </div>

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      style={{ marginRight: '8px' }}
                    />
                    Active
                  </label>
                </div>
              </div>

              <div style={{ border: '1px solid #ddd', borderRadius: '4px', padding: '15px', marginBottom: '15px' }}>
                <h4 style={{ marginTop: 0 }}>Retry Policy</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  <div className="form-group">
                    <label>Max Retries:</label>
                    <input
                      type="number"
                      value={formData.retry_policy?.max_retries}
                      onChange={(e) => setFormData({
                        ...formData,
                        retry_policy: { ...formData.retry_policy!, max_retries: parseInt(e.target.value) }
                      })}
                      min={0}
                      max={10}
                    />
                  </div>
                  <div className="form-group">
                    <label>Retry Delay (min):</label>
                    <input
                      type="number"
                      value={formData.retry_policy?.retry_delay_minutes}
                      onChange={(e) => setFormData({
                        ...formData,
                        retry_policy: { ...formData.retry_policy!, retry_delay_minutes: parseInt(e.target.value) }
                      })}
                      min={1}
                    />
                  </div>
                  <div className="form-group">
                    <label>Backoff Multiplier:</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.retry_policy?.backoff_multiplier}
                      onChange={(e) => setFormData({
                        ...formData,
                        retry_policy: { ...formData.retry_policy!, backoff_multiplier: parseFloat(e.target.value) }
                      })}
                      min={1}
                      max={5}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Schedule</button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Maintenance Window Modal */}
      {showMaintenanceForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '500px' }}>
            <h3>Create Maintenance Window</h3>
            <form onSubmit={handleCreateMaintenanceWindow}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={maintenanceFormData.name}
                  onChange={(e) => setMaintenanceFormData({ ...maintenanceFormData, name: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Start Time:</label>
                  <input
                    type="time"
                    value={maintenanceFormData.start_time}
                    onChange={(e) => setMaintenanceFormData({ ...maintenanceFormData, start_time: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>End Time:</label>
                  <input
                    type="time"
                    value={maintenanceFormData.end_time}
                    onChange={(e) => setMaintenanceFormData({ ...maintenanceFormData, end_time: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Days of Week:</label>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {dayNames.map((day, index) => (
                    <label key={index} style={{ display: 'flex', alignItems: 'center' }}>
                      <input
                        type="checkbox"
                        checked={maintenanceFormData.days_of_week.includes(index)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setMaintenanceFormData({
                              ...maintenanceFormData,
                              days_of_week: [...maintenanceFormData.days_of_week, index]
                            });
                          } else {
                            setMaintenanceFormData({
                              ...maintenanceFormData,
                              days_of_week: maintenanceFormData.days_of_week.filter(d => d !== index)
                            });
                          }
                        }}
                        style={{ marginRight: '5px' }}
                      />
                      {day}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Window</button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowMaintenanceForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Dependency Modal */}
      {showDependencyForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '500px' }}>
            <h3>Create Job Dependency</h3>
            <form onSubmit={handleCreateDependency}>
              <div className="form-group">
                <label>Job:</label>
                <select
                  value={dependencyFormData.job_id}
                  onChange={(e) => setDependencyFormData({ ...dependencyFormData, job_id: parseInt(e.target.value) })}
                  required
                >
                  <option value={0}>Select job...</option>
                  {jobs.map(job => (
                    <option key={job.id} value={job.id}>{job.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Depends On Job:</label>
                <select
                  value={dependencyFormData.depends_on_job_id}
                  onChange={(e) => setDependencyFormData({ ...dependencyFormData, depends_on_job_id: parseInt(e.target.value) })}
                  required
                >
                  <option value={0}>Select dependency job...</option>
                  {jobs.filter(job => job.id !== dependencyFormData.job_id).map(job => (
                    <option key={job.id} value={job.id}>{job.name}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Condition:</label>
                  <select
                    value={dependencyFormData.condition}
                    onChange={(e) => setDependencyFormData({ ...dependencyFormData, condition: e.target.value as any })}
                  >
                    <option value="success">Success</option>
                    <option value="failure">Failure</option>
                    <option value="completion">Completion</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Timeout (minutes):</label>
                  <input
                    type="number"
                    value={dependencyFormData.timeout_minutes}
                    onChange={(e) => setDependencyFormData({ ...dependencyFormData, timeout_minutes: parseInt(e.target.value) })}
                    min={1}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">Create Dependency</button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowDependencyForm(false)}
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

export default AdvancedScheduler;