import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Server, 
  List, 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Loader,
  Eye,
  X
} from 'lucide-react';

interface TaskInfo {
  task_id: string;
  name: string;
  state: string;
  received?: string;
  started?: string;
  succeeded?: string;
  failed?: string;
  runtime?: number;
  retries: number;
  queue: string;
  worker?: string;
  exception?: string;
  args: any[];
  kwargs: any;
}

interface WorkerInfo {
  hostname: string;
  status: string;
  active_tasks: number;
  processed_tasks: number;
  load_avg: number[];
  last_heartbeat?: string;
  pool_processes: number;
  pool_max_concurrency: number;
}

interface QueueInfo {
  name: string;
  length: number;
  consumers: number;
  messages_ready: number;
  messages_unacknowledged: number;
}

interface MonitoringStats {
  tasks: {
    total: number;
    active: number;
    by_state: Record<string, number>;
  };
  workers: {
    total: number;
    online: number;
    offline: number;
  };
  queues: {
    total_length: number;
    by_queue: Record<string, number>;
  };
}

const JobMonitoring: React.FC = () => {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [workers, setWorkers] = useState<WorkerInfo[]>([]);
  const [queues, setQueues] = useState<QueueInfo[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskInfo | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'workers' | 'queues'>('overview');
  const [taskFilter, setTaskFilter] = useState<'all' | 'active' | 'failed' | 'success'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (autoRefresh) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [autoRefresh]);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/automation/monitoring/ws`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
        console.time('Initial data load');
        
        // No need to subscribe - the WebSocket automatically sends updates
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after 3 seconds if auto-refresh is enabled
        if (autoRefresh) {
          setTimeout(connectWebSocket, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      setIsConnected(false);
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'initial_data':
        console.timeEnd('Initial data load');
        console.log('Initial data received:', message.data);
        setStats(message.data.stats);
        setTasks(message.data.tasks || []);
        setWorkers(message.data.workers || []);
        setQueues(message.data.queues || []);
        setIsLoading(false);
        break;
        
      case 'stats_update':
        setStats(message.data);
        break;
        
      case 'tasks_update':
        setTasks(message.data || []);
        break;
        
      case 'task_update':
        setTasks(prev => {
          const updated = [...prev];
          const index = updated.findIndex(t => t.task_id === message.data.task_id);
          if (index >= 0) {
            updated[index] = message.data;
          } else {
            updated.unshift(message.data);
          }
          return updated.slice(0, 100); // Keep only latest 100 tasks
        });
        break;
        
      case 'worker_update':
        setWorkers(prev => {
          const updated = [...prev];
          const index = updated.findIndex(w => w.hostname === message.data.hostname);
          if (index >= 0) {
            updated[index] = message.data;
          } else {
            updated.push(message.data);
          }
          return updated;
        });
        break;
        
      case 'queue_update':
        setQueues(prev => {
          const updated = [...prev];
          const index = updated.findIndex(q => q.name === message.data.name);
          if (index >= 0) {
            updated[index] = message.data;
          } else {
            updated.push(message.data);
          }
          return updated;
        });
        break;
    }
  };

  const cancelTask = async (taskId: string, terminate: boolean = false) => {
    try {
      const response = await fetch(`/api/automation/monitoring/tasks/${taskId}/cancel?terminate=${terminate}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Task will be updated via WebSocket
        console.log(`Task ${taskId} cancelled`);
      } else {
        console.error('Failed to cancel task');
      }
    } catch (error) {
      console.error('Error cancelling task:', error);
    }
  };

  const retryTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/automation/monitoring/tasks/${taskId}/retry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`Task ${taskId} retried with new task ID: ${result.new_task_id}`);
      } else {
        console.error('Failed to retry task');
      }
    } catch (error) {
      console.error('Error retrying task:', error);
    }
  };

  const getTaskStatusIcon = (state: string) => {
    switch (state) {
      case 'SUCCESS':
        return <CheckCircle size={16} style={{ color: 'var(--success-green)' }} />;
      case 'FAILURE':
        return <AlertTriangle size={16} style={{ color: 'var(--danger-red)' }} />;
      case 'STARTED':
        return <Loader size={16} className="loading-spinner" />;
      case 'RETRY':
        return <RotateCcw size={16} style={{ color: 'var(--warning-orange)' }} />;
      case 'REVOKED':
        return <X size={16} style={{ color: 'var(--neutral-500)' }} />;
      default:
        return <Clock size={16} style={{ color: 'var(--neutral-500)' }} />;
    }
  };

  const getTaskStatusColor = (state: string) => {
    switch (state) {
      case 'SUCCESS':
        return 'var(--success-green)';
      case 'FAILURE':
        return 'var(--danger-red)';
      case 'STARTED':
        return 'var(--primary-blue)';
      case 'RETRY':
        return 'var(--warning-orange)';
      case 'REVOKED':
        return 'var(--neutral-500)';
      default:
        return 'var(--neutral-400)';
    }
  };

  const filteredTasks = tasks.filter(task => {
    switch (taskFilter) {
      case 'active':
        return ['SENT', 'RECEIVED', 'STARTED'].includes(task.state);
      case 'failed':
        return task.state === 'FAILURE';
      case 'success':
        return task.state === 'SUCCESS';
      default:
        return true;
    }
  });

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleTimeString();
  };



  if (isLoading) {
    return (
      <div className="dense-dashboard" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader size={32} style={{ animation: 'spin 1s linear infinite', marginBottom: '16px' }} />
          <p style={{ color: 'var(--neutral-600)' }}>Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Job Monitoring</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '16px' }}>
            <div 
              style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                backgroundColor: isConnected ? 'var(--success-green)' : 'var(--danger-red)' 
              }} 
            />
            <span style={{ fontSize: '12px', color: 'var(--neutral-600)' }}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        <div className="header-stats">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn ${autoRefresh ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '12px', padding: '4px 8px' }}
          >
            {autoRefresh ? <Pause size={12} /> : <Play size={12} />}
            {autoRefresh ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="dashboard-section">
          <div className="section-header">System Overview</div>
          <div className="compact-content">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div className="metric-card">
                <div className="metric-icon">
                  <Activity size={16} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{stats.tasks.active}</div>
                  <div className="metric-label">Active Tasks</div>
                  <div className="metric-sublabel">of {stats.tasks.total} total</div>
                </div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">
                  <Server size={16} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{stats.workers.online}</div>
                  <div className="metric-label">Worker Processes</div>
                  <div className="metric-sublabel">of {stats.workers.total} total ({stats.workers.online_nodes || 1} nodes)</div>
                </div>
              </div>
              
              <div className="metric-card">
                <div className="metric-icon">
                  <List size={16} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{stats.queues.total_length}</div>
                  <div className="metric-label">Queued Jobs</div>
                  <div className="metric-sublabel">across all queues</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="dashboard-section">
        <div className="section-header">
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['overview', 'tasks', 'workers', 'queues'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '12px', padding: '4px 12px', textTransform: 'capitalize' }}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="compact-content">
          {/* Tasks Tab */}
          {activeTab === 'tasks' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {(['all', 'active', 'failed', 'success'] as const).map(filter => (
                    <button
                      key={filter}
                      onClick={() => setTaskFilter(filter)}
                      className={`btn ${taskFilter === filter ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ fontSize: '11px', padding: '2px 8px', textTransform: 'capitalize' }}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
                <span style={{ fontSize: '12px', color: 'var(--neutral-600)' }}>
                  {filteredTasks.length} tasks
                </span>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Task ID</th>
                      <th>Name</th>
                      <th>Queue</th>
                      <th>Worker</th>
                      <th>Duration</th>
                      <th>Started</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTasks.map(task => (
                      <tr key={task.task_id}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {getTaskStatusIcon(task.state)}
                            <span 
                              className="status-badge"
                              style={{ backgroundColor: getTaskStatusColor(task.state) }}
                            >
                              {task.state}
                            </span>
                          </div>
                        </td>
                        <td>
                          <code style={{ fontSize: '11px' }}>
                            {task.task_id.substring(0, 8)}...
                          </code>
                        </td>
                        <td>{task.name}</td>
                        <td>{task.queue}</td>
                        <td>{task.worker || 'N/A'}</td>
                        <td>{formatDuration(task.runtime)}</td>
                        <td>{formatTimestamp(task.started)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button
                              onClick={() => setSelectedTask(task)}
                              className="btn btn-secondary"
                              style={{ fontSize: '10px', padding: '2px 6px' }}
                              title="View Details"
                            >
                              <Eye size={10} />
                            </button>
                            {['SENT', 'RECEIVED', 'STARTED'].includes(task.state) && (
                              <button
                                onClick={() => cancelTask(task.task_id)}
                                className="btn btn-danger"
                                style={{ fontSize: '10px', padding: '2px 6px' }}
                                title="Cancel Task"
                              >
                                <Square size={10} />
                              </button>
                            )}
                            {task.state === 'FAILURE' && (
                              <button
                                onClick={() => retryTask(task.task_id)}
                                className="btn btn-warning"
                                style={{ fontSize: '10px', padding: '2px 6px' }}
                                title="Retry Task"
                              >
                                <RotateCcw size={10} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Workers Tab */}
          {activeTab === 'workers' && (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Hostname</th>
                    <th>Active Tasks</th>
                    <th>Processed</th>
                    <th>Load Avg</th>
                    <th>Pool Size</th>
                    <th>Last Heartbeat</th>
                  </tr>
                </thead>
                <tbody>
                  {workers.map(worker => (
                    <tr key={worker.hostname}>
                      <td>
                        <span 
                          className="status-badge"
                          style={{ 
                            backgroundColor: worker.status === 'online' ? 'var(--success-green)' : 'var(--danger-red)' 
                          }}
                        >
                          {worker.status}
                        </span>
                      </td>
                      <td>{worker.hostname}</td>
                      <td>{worker.active_tasks}</td>
                      <td>{worker.processed_tasks}</td>
                      <td>{worker.load_avg.map(l => l.toFixed(2)).join(', ')}</td>
                      <td>{worker.pool_processes}/{worker.pool_max_concurrency}</td>
                      <td>{formatTimestamp(worker.last_heartbeat)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Queues Tab */}
          {activeTab === 'queues' && (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Queue Name</th>
                    <th>Length</th>
                    <th>Ready</th>
                    <th>Unacknowledged</th>
                    <th>Consumers</th>
                  </tr>
                </thead>
                <tbody>
                  {queues.map(queue => (
                    <tr key={queue.name}>
                      <td>{queue.name}</td>
                      <td>
                        <span 
                          className="status-badge"
                          style={{ 
                            backgroundColor: queue.length > 10 ? 'var(--warning-orange)' : 'var(--success-green)' 
                          }}
                        >
                          {queue.length}
                        </span>
                      </td>
                      <td>{queue.messages_ready}</td>
                      <td>{queue.messages_unacknowledged}</td>
                      <td>{queue.consumers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Overview Tab */}
          {activeTab === 'overview' && stats && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Tasks by State</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {Object.entries(stats.tasks.by_state).map(([state, count]) => (
                      <div key={state} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {getTaskStatusIcon(state)}
                          <span style={{ fontSize: '12px' }}>{state}</span>
                        </div>
                        <span className="status-badge status-badge-neutral">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Queue Lengths</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {Object.entries(stats.queues.by_queue).map(([queue, length]) => (
                      <div key={queue} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px' }}>{queue}</span>
                        <span 
                          className="status-badge"
                          style={{ 
                            backgroundColor: length > 10 ? 'var(--warning-orange)' : 'var(--success-green)' 
                          }}
                        >
                          {length}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="modal-overlay" onClick={() => setSelectedTask(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Task Details</h3>
              <button onClick={() => setSelectedTask(null)} className="btn btn-secondary">
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <h4>Basic Information</h4>
                  <div className="form-group">
                    <label>Task ID</label>
                    <code>{selectedTask.task_id}</code>
                  </div>
                  <div className="form-group">
                    <label>Name</label>
                    <span>{selectedTask.name}</span>
                  </div>
                  <div className="form-group">
                    <label>State</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {getTaskStatusIcon(selectedTask.state)}
                      <span>{selectedTask.state}</span>
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Queue</label>
                    <span>{selectedTask.queue}</span>
                  </div>
                  <div className="form-group">
                    <label>Worker</label>
                    <span>{selectedTask.worker || 'N/A'}</span>
                  </div>
                </div>
                
                <div>
                  <h4>Timing</h4>
                  <div className="form-group">
                    <label>Received</label>
                    <span>{formatTimestamp(selectedTask.received)}</span>
                  </div>
                  <div className="form-group">
                    <label>Started</label>
                    <span>{formatTimestamp(selectedTask.started)}</span>
                  </div>
                  <div className="form-group">
                    <label>Completed</label>
                    <span>{formatTimestamp(selectedTask.succeeded || selectedTask.failed)}</span>
                  </div>
                  <div className="form-group">
                    <label>Runtime</label>
                    <span>{formatDuration(selectedTask.runtime)}</span>
                  </div>
                  <div className="form-group">
                    <label>Retries</label>
                    <span>{selectedTask.retries}</span>
                  </div>
                </div>
              </div>
              
              {selectedTask.exception && (
                <div style={{ marginTop: '16px' }}>
                  <h4>Error</h4>
                  <pre style={{ 
                    backgroundColor: 'var(--neutral-100)', 
                    padding: '8px', 
                    borderRadius: '4px',
                    fontSize: '11px',
                    overflow: 'auto',
                    maxHeight: '200px'
                  }}>
                    {selectedTask.exception}
                  </pre>
                </div>
              )}
              
              <div style={{ marginTop: '16px' }}>
                <h4>Arguments</h4>
                <pre style={{ 
                  backgroundColor: 'var(--neutral-100)', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '11px',
                  overflow: 'auto',
                  maxHeight: '100px'
                }}>
                  {JSON.stringify({ args: selectedTask.args, kwargs: selectedTask.kwargs }, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobMonitoring;