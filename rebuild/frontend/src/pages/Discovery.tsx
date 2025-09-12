import React, { useState, useEffect } from 'react';
import { discoveryApi } from '../services/api';
import {
  DiscoveryJob,
  DiscoveredTarget,
  DiscoveryJobCreate,
  DiscoveryConfig,
  DiscoveryService
} from '../types';
import { Check, X, Plus, Trash2, Play, Square, Edit3 } from 'lucide-react';

// Default services organized by categories
const DEFAULT_SERVICES: DiscoveryService[] = [
  // Remote Access
  { name: 'SSH', port: 22, protocol: 'tcp', category: 'Remote Access', enabled: false },
  { name: 'Telnet', port: 23, protocol: 'tcp', category: 'Remote Access', enabled: false },
  { name: 'RDP', port: 3389, protocol: 'tcp', category: 'Remote Access', enabled: false },
  { name: 'VNC', port: 5900, protocol: 'tcp', category: 'Remote Access', enabled: false },
  
  // Windows Management
  { name: 'WinRM HTTP', port: 5985, protocol: 'tcp', category: 'Windows Management', enabled: false },
  { name: 'WinRM HTTPS', port: 5986, protocol: 'tcp', category: 'Windows Management', enabled: false },
  { name: 'WMI', port: 135, protocol: 'tcp', category: 'Windows Management', enabled: false },
  { name: 'NetBIOS', port: 139, protocol: 'tcp', category: 'Windows Management', enabled: false },
  { name: 'SMB', port: 445, protocol: 'tcp', category: 'Windows Management', enabled: false },
  
  // Web Services
  { name: 'HTTP', port: 80, protocol: 'tcp', category: 'Web Services', enabled: false },
  { name: 'HTTPS', port: 443, protocol: 'tcp', category: 'Web Services', enabled: false },
  { name: 'HTTP Alt', port: 8080, protocol: 'tcp', category: 'Web Services', enabled: false },
  { name: 'HTTPS Alt', port: 8443, protocol: 'tcp', category: 'Web Services', enabled: false },
  
  // Database Services
  { name: 'MySQL', port: 3306, protocol: 'tcp', category: 'Database Services', enabled: false },
  { name: 'PostgreSQL', port: 5432, protocol: 'tcp', category: 'Database Services', enabled: false },
  { name: 'SQL Server', port: 1433, protocol: 'tcp', category: 'Database Services', enabled: false },
  { name: 'Oracle', port: 1521, protocol: 'tcp', category: 'Database Services', enabled: false },
  { name: 'MongoDB', port: 27017, protocol: 'tcp', category: 'Database Services', enabled: false },
  { name: 'Redis', port: 6379, protocol: 'tcp', category: 'Database Services', enabled: false },
  
  // Email Services
  { name: 'SMTP', port: 25, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'SMTP SSL', port: 465, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'SMTP TLS', port: 587, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'POP3', port: 110, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'POP3S', port: 995, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'IMAP', port: 143, protocol: 'tcp', category: 'Email Services', enabled: false },
  { name: 'IMAPS', port: 993, protocol: 'tcp', category: 'Email Services', enabled: false },
  
  // File Services
  { name: 'FTP', port: 21, protocol: 'tcp', category: 'File Services', enabled: false },
  { name: 'FTPS', port: 990, protocol: 'tcp', category: 'File Services', enabled: false },
  { name: 'SFTP', port: 22, protocol: 'tcp', category: 'File Services', enabled: false },
  { name: 'NFS', port: 2049, protocol: 'tcp', category: 'File Services', enabled: false },
  
  // Network Services
  { name: 'DNS', port: 53, protocol: 'tcp', category: 'Network Services', enabled: false },
  { name: 'DHCP', port: 67, protocol: 'udp', category: 'Network Services', enabled: false },
  { name: 'SNMP', port: 161, protocol: 'udp', category: 'Network Services', enabled: false },
  { name: 'LDAP', port: 389, protocol: 'tcp', category: 'Network Services', enabled: false },
  { name: 'LDAPS', port: 636, protocol: 'tcp', category: 'Network Services', enabled: false },
];

const Discovery: React.FC = () => {
  const [jobs, setJobs] = useState<DiscoveryJob[]>([]);
  const [targets, setTargets] = useState<DiscoveredTarget[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [selectedJob, setSelectedJob] = useState<DiscoveryJob | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<DiscoveredTarget | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingJob, setEditingJob] = useState<DiscoveryJob | null>(null);
  const [saving, setSaving] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalTargets, setTotalTargets] = useState(0);
  const [pageSize] = useState(50);
  
  // Network range validation states
  const [validationResults, setValidationResults] = useState<{[key: number]: any}>({});
  
  // Progress tracking state
  const [jobProgress, setJobProgress] = useState<{[key: number]: any}>({});
  
  // Task ID tracking for direct Celery status
  const [jobTaskIds, setJobTaskIds] = useState<{[key: number]: string}>({});
  
  // Form state for creating new discovery job
  const [newJob, setNewJob] = useState<DiscoveryJobCreate>({
    name: '',
    discovery_type: 'network_scan',
    config: {
      cidr_ranges: [''],
      services: [...DEFAULT_SERVICES],
      os_detection: true,
      timeout: 300
    }
  });

  useEffect(() => {
    loadJobs();
    // Don't load targets initially - wait for job selection
  }, []);



  // Load targets when selected job changes
  useEffect(() => {
    if (selectedJob) {
      loadTargets(1, selectedJob.id);
    } else {
      setTargets([]);
      setTotalTargets(0);
    }
  }, [selectedJob]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await discoveryApi.listJobs();
      setJobs(response.discovery_jobs || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load discovery jobs');
    } finally {
      setLoading(false);
    }
  };

  const loadTargets = async (page: number = currentPage, jobId?: number) => {
    try {
      setLoading(true);
      const skip = (page - 1) * pageSize;
      // Only load targets if a job is selected
      if (jobId || selectedJob) {
        const response = await discoveryApi.listTargets(skip, pageSize, jobId || selectedJob?.id);
        setTargets(response.targets || []);
        setTotalTargets(response.total || 0);
      } else {
        // No job selected, show empty list
        setTargets([]);
        setTotalTargets(0);
      }
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
      setSaving(true);
      setError(null);
      
      const enabledServices = newJob.config.services?.filter(s => s.enabled) || [];
      if (enabledServices.length === 0) {
        setError('Please select at least one service to scan for.');
        setSaving(false);
        return;
      }
      
      const config: DiscoveryConfig = {
        ...newJob.config,
        cidr_ranges: newJob.config.cidr_ranges?.filter(range => range.trim() !== '') || [],
        services: enabledServices
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
          services: [...DEFAULT_SERVICES],
          os_detection: true,
          timeout: 300
        }
      });

      setShowCreateForm(false);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to create discovery job');
    } finally {
      setSaving(false);
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
      if (selectedJob) {
        await loadTargets(currentPage, selectedJob.id);
      }
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

    if (!window.confirm(`Are you sure you want to ignore ${selectedTargets.length} targets?`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      await discoveryApi.ignoreTargets(selectedTargets);
      alert(`Removed ${selectedTargets.length} ignored targets from the list`);
      setSelectedTargets([]);
      if (selectedJob) {
        await loadTargets(currentPage, selectedJob.id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to ignore targets');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: number) => {
    if (!window.confirm('Are you sure you want to delete this discovery job? This will also delete all discovered targets associated with this job.')) {
      return;
    }

    try {
      setLoading(true);
      await discoveryApi.deleteJob(jobId);
      await loadJobs();
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
        setSelectedTarget(null);
        setSelectedTargets([]);
        // Targets will be cleared by the useEffect when selectedJob becomes null
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete discovery job');
    } finally {
      setLoading(false);
    }
  };

  const handleRunJob = async (jobId: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await discoveryApi.runJob(jobId);
      
      // Immediate feedback - job has been sent
      if (result.task_id) {
        // Store the task_id for status tracking
        setJobTaskIds(prev => ({ ...prev, [jobId]: result.task_id! }));
        // Set initial status to "running" for immediate UI feedback
        setJobProgress(prev => ({ ...prev, [jobId]: { status: 'running', message: 'Job started...' } }));
        
        // Start polling immediately for this job
        pollJobStatus(jobId, result.task_id);
      }
      
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to run discovery job');
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (jobId: number, taskId: string) => {
    try {
      const progress = await discoveryApi.getJobProgress(jobId, taskId);
      setJobProgress(prev => ({ ...prev, [jobId]: progress }));
      
      // If job is still running, poll again in 3 seconds
      if (progress.status !== 'completed' && progress.status !== 'failed' && progress.status !== 'SUCCESS') {
        setTimeout(() => pollJobStatus(jobId, taskId), 3000);
      } else {
        // Job finished, remove from tracking and refresh
        setJobTaskIds(prev => {
          const updated = { ...prev };
          delete updated[jobId];
          return updated;
        });
        loadJobs();
        if (selectedJob && selectedJob.id === jobId) {
          loadTargets(currentPage, jobId);
        }
      }
    } catch (error) {
      console.error(`Failed to get progress for job ${jobId}:`, error);
      // On error, stop tracking this job
      setJobTaskIds(prev => {
        const updated = { ...prev };
        delete updated[jobId];
        return updated;
      });
    }
  };

  const handleCancelJob = async (jobId: number) => {
    if (!window.confirm('Are you sure you want to cancel this running job?')) {
      return;
    }

    try {
      setLoading(true);
      await discoveryApi.cancelJob(jobId);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to cancel discovery job');
    } finally {
      setLoading(false);
    }
  };

  const handleEditJob = (job: DiscoveryJob) => {
    setEditingJob(job);
    setNewJob({
      name: job.name,
      discovery_type: job.scan_type,
      config: {
        cidr_ranges: job.configuration?.cidr_ranges || [''],
        services: job.configuration?.services || [...DEFAULT_SERVICES],
        os_detection: job.configuration?.os_detection ?? true,
        timeout: job.configuration?.timeout || 300
      }
    });
    setShowEditForm(true);
    setShowCreateForm(false);
  };

  const handleUpdateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingJob) return;

    try {
      setSaving(true);
      setError(null);
      
      const enabledServices = newJob.config.services?.filter(s => s.enabled) || [];
      if (enabledServices.length === 0) {
        setError('Please select at least one service to scan for.');
        setSaving(false);
        return;
      }
      
      const config: DiscoveryConfig = {
        ...newJob.config,
        cidr_ranges: newJob.config.cidr_ranges?.filter(range => range.trim() !== '') || [],
        services: enabledServices
      };

      await discoveryApi.updateJob(editingJob.id, {
        name: newJob.name,
        config
      });

      // Reset form
      setNewJob({
        name: '',
        discovery_type: 'network_scan',
        config: {
          cidr_ranges: [''],
          services: [...DEFAULT_SERVICES],
          os_detection: true,
          timeout: 300
        }
      });

      setShowEditForm(false);
      setEditingJob(null);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to update discovery job');
    } finally {
      setSaving(false);
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

  const validateNetworkRange = async (range: string, index: number) => {
    if (!range.trim()) {
      return;
    }

    try {
      setLoading(true);
      const response = await discoveryApi.validateNetworkRanges({ ranges: [range] });
      
      setValidationResults(prev => ({
        ...prev,
        [index]: response.results[0]
      }));
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate network range');
    } finally {
      setLoading(false);
    }
  };

  const updateServiceEnabled = (serviceName: string, enabled: boolean) => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        services: prev.config.services?.map(service => 
          service.name === serviceName ? { ...service, enabled } : service
        ) || []
      }
    }));
  };

  const updateServicePort = (serviceName: string, port: number) => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        services: prev.config.services?.map(service => 
          service.name === serviceName ? { ...service, port } : service
        ) || []
      }
    }));
  };

  const toggleCategoryServices = (category: string, enabled: boolean) => {
    setNewJob(prev => ({
      ...prev,
      config: {
        ...prev.config,
        services: prev.config.services?.map(service => 
          service.category === category ? { ...service, enabled } : service
        ) || []
      }
    }));
  };

  const getServicesByCategory = () => {
    const categories: { [key: string]: DiscoveryService[] } = {};
    newJob.config.services?.forEach(service => {
      if (!categories[service.category]) {
        categories[service.category] = [];
      }
      categories[service.category].push(service);
    });
    return categories;
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
        return 'status-badge-warning';
      case 'running':
        return 'status-badge-info';
      case 'completed':
        return 'status-badge-success';
      case 'failed':
        return 'status-badge-danger';
      default:
        return 'status-badge-neutral';
    }
  };

  const getDuplicateStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'unique':
        return 'status-badge-success';
      case 'duplicate':
        return 'status-badge-warning';
      case 'similar':
        return 'status-badge-info';
      default:
        return 'status-badge-neutral';
    }
  };

  if (loading && jobs.length === 0 && targets.length === 0) {
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
          /* Dashboard-style layout - EXACT MATCH */
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
            grid-template-columns: 1fr 1fr 1fr;
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
          
          /* Jobs table styles */
          .jobs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .jobs-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .jobs-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .jobs-table tr:hover {
            background: var(--neutral-50);
          }
          .jobs-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .jobs-table tr {
            cursor: pointer;
          }
          
          /* Targets table styles */
          .targets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .targets-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .targets-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .targets-table tr:hover {
            background: var(--neutral-50);
          }
          .targets-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .targets-table tr {
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
          .form-textarea {
            min-height: 60px;
            resize: vertical;
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
          
          .service-badge {
            display: inline-block;
            background: var(--neutral-100);
            color: var(--neutral-700);
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            margin: 1px;
          }
          
          .checkbox-input {
            width: 14px;
            height: 14px;
            margin: 0;
          }
          
          .network-range-item {
            display: flex;
            gap: 4px;
            margin-bottom: 6px;
            align-items: center;
          }
          .network-range-item input {
            flex: 1;
          }
          .network-range-item button {
            padding: 4px 8px;
            font-size: 10px;
            border: 1px solid var(--neutral-300);
            background: white;
            border-radius: 3px;
            cursor: pointer;
          }
          .network-range-item button:hover {
            background: var(--neutral-50);
          }
          
          .service-category {
            margin-bottom: 12px;
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
          }
          .service-category-header {
            background: var(--neutral-50);
            padding: 6px 8px;
            font-weight: 600;
            font-size: 11px;
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .service-category-content {
            padding: 6px 8px;
          }
          .service-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
            font-size: 11px;
          }
          .service-item input[type="checkbox"] {
            width: 12px;
            height: 12px;
          }
          .service-item input[type="number"] {
            width: 60px;
            padding: 2px 4px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 11px;
          }
          
          .alert {
            background: var(--danger-red-light);
            color: var(--danger-red);
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 12px;
          }
          
          .bulk-actions {
            padding: 8px;
            background: var(--neutral-50);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
          }
          .bulk-actions button {
            padding: 4px 8px;
            font-size: 11px;
            border: 1px solid var(--neutral-300);
            background: white;
            border-radius: 3px;
            cursor: pointer;
          }
          .bulk-actions button:hover {
            background: var(--neutral-100);
          }
          .bulk-actions button.btn-success {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
          .bulk-actions button.btn-danger {
            background: var(--danger-red);
            color: white;
            border-color: var(--danger-red);
          }
        `}
      </style>
      
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Target Discovery</h1>
          <p className="header-subtitle">Automatically discover Windows machines and other targets on your network</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-icon btn-success"
            onClick={() => {
              setShowCreateForm(true);
              setShowEditForm(false);
              setEditingJob(null);
            }}
            title="Create new discovery job"
            disabled={showCreateForm || showEditForm}
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

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Discovery Jobs */}
        <div className="dashboard-section">
          <div className="section-header">
            Discovery Jobs ({jobs.length})
            <button 
              className="btn-icon btn-success"
              onClick={() => {
                setShowCreateForm(true);
                setShowEditForm(false);
                setEditingJob(null);
              }}
              title="Create new job"
              disabled={showCreateForm || showEditForm}
            >
              <Plus size={14} />
            </button>
          </div>
          <div className="compact-content">
            {jobs.length === 0 ? (
              <div className="empty-state">
                <h3>No discovery jobs</h3>
                <p>Create your first discovery job to get started.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={() => {
                    setShowCreateForm(true);
                    setShowEditForm(false);
                    setEditingJob(null);
                  }}
                  title="Create first job"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="jobs-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Results</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr 
                        key={job.id} 
                        className={selectedJob?.id === job.id ? 'selected' : ''}
                        onClick={() => setSelectedJob(job)}
                      >
                        <td style={{ fontWeight: '500' }}>{job.name}</td>
                        <td>
                          {jobTaskIds[job.id] && jobProgress[job.id] ? (
                            <div style={{ minWidth: '120px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                                <span className={`status-badge ${getStatusBadge(jobProgress[job.id].status)}`} style={{ fontSize: '10px' }}>
                                  {jobProgress[job.id].status}
                                </span>
                                <span style={{ fontSize: '10px', color: 'var(--neutral-600)' }}>
                                  {jobProgress[job.id].progress}%
                                </span>
                              </div>
                              <div style={{ 
                                width: '100%', 
                                height: '4px', 
                                backgroundColor: 'var(--neutral-200)', 
                                borderRadius: '2px',
                                overflow: 'hidden',
                                marginBottom: '2px'
                              }}>
                                <div style={{ 
                                  width: `${jobProgress[job.id].progress}%`, 
                                  height: '100%', 
                                  backgroundColor: 'var(--primary-blue)',
                                  transition: 'width 0.3s ease'
                                }} />
                              </div>
                              <div style={{ fontSize: '9px', color: 'var(--neutral-500)', lineHeight: '1.2' }}>
                                {jobProgress[job.id].phase === 'scanning' && jobProgress[job.id].current_target ? (
                                  `Scanning ${jobProgress[job.id].current_target}`
                                ) : (
                                  jobProgress[job.id].message || 'Running...'
                                )}
                              </div>
                              {jobProgress[job.id].targets_found > 0 && (
                                <div style={{ fontSize: '9px', color: 'var(--success-600)' }}>
                                  Found: {jobProgress[job.id].targets_found}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className={`status-badge ${getStatusBadge(jobProgress[job.id]?.status || job.status)}`}>
                              {jobProgress[job.id]?.status || job.status}
                            </span>
                          )}
                        </td>
                        <td>
                          {job.results && Object.keys(job.results).length > 0 ? (
                            <div style={{ fontSize: '10px' }}>
                              <div>Hosts: {job.results.total_hosts || 0}</div>
                              <div>Win: {job.results.windows_hosts || 0}</div>
                            </div>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            {/* Run/Cancel button - conditional based on status */}
                            {jobTaskIds[job.id] ? (
                              <button
                                className="btn-icon btn-ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCancelJob(job.id);
                                }}
                                title="Cancel job"
                              >
                                <Square size={14} />
                              </button>
                            ) : (
                              <button
                                className="btn-icon btn-success"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRunJob(job.id);
                                }}
                                title="Run job"
                                disabled={jobTaskIds[job.id] !== undefined}
                              >
                                <Play size={14} />
                              </button>
                            )}
                            
                            {/* Edit button - always available */}
                            <button
                              className="btn-icon btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditJob(job);
                              }}
                              title="Edit job"
                              disabled={jobTaskIds[job.id] !== undefined}
                            >
                              <Edit3 size={14} />
                            </button>
                            
                            {/* Delete button - always available */}
                            <button
                              className="btn-icon btn-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteJob(job.id);
                              }}
                              title="Delete job"
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

        {/* Column 2: Discovered Targets */}
        <div className="dashboard-section">
          <div className="section-header">
            Discovered Targets ({targets.length})
            {selectedJob && (
              <div style={{ fontSize: '12px', fontWeight: 'normal', color: '#666', marginTop: '4px' }}>
                From job: {selectedJob.name}
              </div>
            )}
          </div>
          {selectedTargets.length > 0 && (
            <div className="bulk-actions">
              <button 
                className="btn-success"
                onClick={handleImportTargets}
                disabled={loading}
              >
                Import ({selectedTargets.length})
              </button>
              <button 
                onClick={handleIgnoreTargets}
                disabled={loading}
              >
                Ignore ({selectedTargets.length})
              </button>
            </div>
          )}
          <div className="compact-content">
            {targets.length === 0 ? (
              <div className="empty-state">
                {!selectedJob ? (
                  <>
                    <h3>No discovery job selected</h3>
                    <p>Select a discovery job from the left panel to view its discovered targets.</p>
                  </>
                ) : (
                  <>
                    <h3>No discovered targets</h3>
                    <p>This discovery job hasn't found any targets yet. Run the job to discover targets.</p>
                  </>
                )}
              </div>
            ) : (
              <div className="table-container">
                <table className="targets-table">
                  <thead>
                    <tr>
                      <th>
                        <input
                          type="checkbox"
                          className="checkbox-input"
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
                    </tr>
                  </thead>
                  <tbody>
                    {targets.map((target) => (
                      <tr 
                        key={target.id} 
                        className={selectedTarget?.id === target.id ? 'selected' : ''}
                        onClick={() => setSelectedTarget(target)}
                      >
                        <td>
                          {target.import_status === 'pending' && (
                            <input
                              type="checkbox"
                              className="checkbox-input"
                              checked={selectedTargets.includes(target.id)}
                              onChange={(e) => {
                                e.stopPropagation();
                                if (e.target.checked) {
                                  setSelectedTargets(prev => [...prev, target.id]);
                                } else {
                                  setSelectedTargets(prev => prev.filter(id => id !== target.id));
                                }
                              }}
                            />
                          )}
                        </td>
                        <td style={{ fontWeight: '500' }}>{target.ip_address}</td>
                        <td>{target.hostname || '-'}</td>
                        <td>
                          {target.os_type && (
                            <div>
                              <div>{target.os_type}</div>
                              {target.os_version && (
                                <div style={{ fontSize: '10px', color: 'var(--neutral-500)' }}>{target.os_version}</div>
                              )}
                            </div>
                          )}
                        </td>
                        <td>
                          {target.services.length > 0 ? (
                            <div>
                              {target.services.slice(0, 3).map((service, idx) => (
                                <span key={idx} className="service-badge">
                                  {service.protocol}:{service.port}
                                </span>
                              ))}
                              {target.services.length > 3 && (
                                <span className="service-badge">+{target.services.length - 3}</span>
                              )}
                            </div>
                          ) : (
                            '-'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Details/Create Panel */}
        <div className="dashboard-section">
          <div className="section-header">
            {showCreateForm ? 'Create Discovery Job' : showEditForm ? 'Edit Discovery Job' : selectedJob ? 'Job Details' : selectedTarget ? 'Target Details' : 'Select Item'}
            {(showCreateForm || showEditForm) && (
              <button 
                className="btn-icon btn-ghost"
                onClick={() => {
                  setShowCreateForm(false);
                  setShowEditForm(false);
                  setEditingJob(null);
                }}
                title="Cancel"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <div className="compact-content">
            {showCreateForm || showEditForm ? (
              <div className="create-form">
                <form onSubmit={showEditForm ? handleUpdateJob : handleCreateJob}>
                  <div className="form-group">
                    <label className="form-label">Job Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newJob.name}
                      onChange={(e) => setNewJob(prev => ({ ...prev, name: e.target.value }))}
                      required
                      placeholder="Enter job name"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Network Ranges</label>
                    <div style={{ fontSize: '10px', color: 'var(--neutral-600)', marginBottom: '6px' }}>
                      CIDR: 192.168.1.0/24, Range: 192.168.1.100-120, IPs: 192.168.1.20,192.168.1.22
                    </div>
                    {newJob.config.cidr_ranges?.map((range, index) => {
                      const validation = validationResults[index];
                      return (
                        <div key={index} className="network-range-item">
                          <input
                            type="text"
                            className="form-input"
                            placeholder="e.g., 192.168.1.0/24"
                            value={range}
                            onChange={(e) => {
                              updateCidrRange(index, e.target.value);
                              if (validationResults[index]) {
                                setValidationResults(prev => {
                                  const newResults = { ...prev };
                                  delete newResults[index];
                                  return newResults;
                                });
                              }
                            }}
                            style={{
                              borderColor: validation ? (validation.valid ? 'var(--success-green)' : 'var(--danger-red)') : 'var(--neutral-300)'
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => validateNetworkRange(range, index)}
                            disabled={!range.trim()}
                            title="Validate"
                          >
                            ✓
                          </button>
                          <button
                            type="button"
                            onClick={() => removeCidrRange(index)}
                            disabled={newJob.config.cidr_ranges?.length === 1}
                            title="Remove"
                          >
                            ×
                          </button>
                        </div>
                      );
                    })}
                    <button
                      type="button"
                      onClick={addCidrRange}
                      style={{ fontSize: '11px', padding: '4px 8px', border: '1px solid var(--neutral-300)', background: 'white', borderRadius: '3px', cursor: 'pointer' }}
                    >
                      Add Range
                    </button>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Services to Scan</label>
                    <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                      {Object.entries(getServicesByCategory()).map(([category, services]) => {
                        const enabledCount = services.filter(s => s.enabled).length;
                        const totalCount = services.length;
                        
                        return (
                          <div key={category} className="service-category">
                            <div className="service-category-header">
                              <span>{category}</span>
                              <label style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <input
                                  type="checkbox"
                                  checked={enabledCount === totalCount}
                                  onChange={(e) => toggleCategoryServices(category, e.target.checked)}
                                />
                                All ({enabledCount}/{totalCount})
                              </label>
                            </div>
                            <div className="service-category-content">
                              {services.map(service => (
                                <div key={service.name} className="service-item">
                                  <input
                                    type="checkbox"
                                    checked={service.enabled}
                                    onChange={(e) => updateServiceEnabled(service.name, e.target.checked)}
                                  />
                                  <span style={{ flex: 1 }}>{service.name}</span>
                                  <input
                                    type="number"
                                    value={service.port}
                                    onChange={(e) => updateServicePort(service.name, parseInt(e.target.value) || service.port)}
                                    min="1"
                                    max="65535"
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Timeout (seconds)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={newJob.config.timeout}
                      onChange={(e) => setNewJob(prev => ({
                        ...prev,
                        config: { ...prev.config, timeout: parseInt(e.target.value) || 300 }
                      }))}
                      min="30"
                      max="3600"
                    />
                  </div>

                  <div className="action-buttons">
                    <button 
                      type="button"
                      onClick={() => {
                        setShowCreateForm(false);
                        setShowEditForm(false);
                        setEditingJob(null);
                      }}
                      style={{ padding: '6px 12px', border: '1px solid var(--neutral-300)', background: 'white', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit"
                      className="btn-primary"
                      disabled={saving}
                    >
                      {saving ? (showEditForm ? 'Updating...' : 'Creating...') : (showEditForm ? 'Update Job' : 'Create Job')}
                    </button>
                  </div>
                </form>
              </div>
            ) : selectedJob ? (
              <div className="details-panel">
                <h3>{selectedJob.name}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${getStatusBadge(selectedJob.status)}`}>
                      {selectedJob.status}
                    </span>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Target Range</div>
                  <div className="detail-value">{selectedJob.target_range}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Scan Type</div>
                  <div className="detail-value">{selectedJob.scan_type}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Created</div>
                  <div className="detail-value">{new Date(selectedJob.created_at).toLocaleString()}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Duration</div>
                  <div className="detail-value">
                    {selectedJob.started_at && selectedJob.completed_at ? (
                      `${Math.round((new Date(selectedJob.completed_at).getTime() - new Date(selectedJob.started_at).getTime()) / 1000)}s`
                    ) : selectedJob.started_at ? (
                      'Running...'
                    ) : (
                      '-'
                    )}
                  </div>
                </div>

                {selectedJob.status === 'running' && jobProgress[selectedJob.id] && (
                  <>
                    <div className="detail-group">
                      <div className="detail-label">Progress</div>
                      <div className="detail-value">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <div style={{ 
                            flex: 1,
                            height: '8px', 
                            backgroundColor: 'var(--neutral-200)', 
                            borderRadius: '4px',
                            overflow: 'hidden'
                          }}>
                            <div style={{ 
                              width: `${jobProgress[selectedJob.id].progress}%`, 
                              height: '100%', 
                              backgroundColor: 'var(--primary-blue)',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                          <span style={{ fontSize: '12px', fontWeight: '500' }}>
                            {jobProgress[selectedJob.id].progress}%
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--neutral-600)' }}>
                          {jobProgress[selectedJob.id].message}
                        </div>
                      </div>
                    </div>

                    {jobProgress[selectedJob.id].phase === 'scanning' && (
                      <>
                        <div className="detail-group">
                          <div className="detail-label">Targets Scanned</div>
                          <div className="detail-value">
                            {jobProgress[selectedJob.id].targets_scanned || 0} / {jobProgress[selectedJob.id].total_targets || 0}
                          </div>
                        </div>

                        <div className="detail-group">
                          <div className="detail-label">Targets Found</div>
                          <div className="detail-value" style={{ color: 'var(--success-600)', fontWeight: '500' }}>
                            {jobProgress[selectedJob.id].targets_found || 0}
                          </div>
                        </div>

                        {jobProgress[selectedJob.id].current_target && (
                          <div className="detail-group">
                            <div className="detail-label">Current Target</div>
                            <div className="detail-value" style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                              {jobProgress[selectedJob.id].current_target}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </>
                )}

                {selectedJob.results && Object.keys(selectedJob.results).length > 0 && (
                  <>
                    <div className="detail-group">
                      <div className="detail-label">Total Hosts</div>
                      <div className="detail-value">{selectedJob.results.total_hosts || 0}</div>
                    </div>

                    <div className="detail-group">
                      <div className="detail-label">Windows Hosts</div>
                      <div className="detail-value">{selectedJob.results.windows_hosts || 0}</div>
                    </div>

                    <div className="detail-group">
                      <div className="detail-label">Linux Hosts</div>
                      <div className="detail-value">{selectedJob.results.linux_hosts || 0}</div>
                    </div>
                  </>
                )}

                <div className="action-buttons">
                  {selectedJob.status === 'running' ? (
                    <button 
                      className="btn-icon btn-ghost"
                      onClick={() => handleCancelJob(selectedJob.id)}
                      title="Cancel job"
                    >
                      <Square size={16} />
                    </button>
                  ) : selectedJob.status === 'pending' || selectedJob.status === 'failed' ? (
                    <>
                      <button 
                        className="btn-icon btn-success"
                        onClick={() => handleRunJob(selectedJob.id)}
                        title="Run job"
                      >
                        <Play size={16} />
                      </button>
                      <button 
                        className="btn-icon btn-ghost"
                        onClick={() => handleEditJob(selectedJob)}
                        title="Edit job"
                      >
                        <Edit3 size={16} />
                      </button>
                      <button 
                        className="btn-icon btn-danger"
                        onClick={() => handleDeleteJob(selectedJob.id)}
                        title="Delete job"
                      >
                        <Trash2 size={16} />
                      </button>
                    </>
                  ) : (
                    <button 
                      className="btn-icon btn-danger"
                      onClick={() => handleDeleteJob(selectedJob.id)}
                      title="Delete job"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>
            ) : selectedTarget ? (
              <div className="details-panel">
                <h3>{selectedTarget.ip_address}</h3>
                
                <div className="detail-group">
                  <div className="detail-label">IP Address</div>
                  <div className="detail-value">{selectedTarget.ip_address}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Hostname</div>
                  <div className="detail-value">{selectedTarget.hostname || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">OS Type</div>
                  <div className="detail-value">{selectedTarget.os_type || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">OS Version</div>
                  <div className="detail-value">{selectedTarget.os_version || '-'}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Import Status</div>
                  <div className="detail-value">
                    <span className={`status-badge ${getDuplicateStatusBadge(selectedTarget.import_status)}`}>
                      {selectedTarget.import_status}
                    </span>
                  </div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Discovered</div>
                  <div className="detail-value">{new Date(selectedTarget.discovered_at).toLocaleString()}</div>
                </div>

                <div className="detail-group">
                  <div className="detail-label">Services ({selectedTarget.services.length})</div>
                  <div className="detail-value">
                    {selectedTarget.services.length > 0 ? (
                      <div>
                        {selectedTarget.services.map((service, idx) => (
                          <div key={idx} style={{ fontSize: '11px', marginBottom: '2px' }}>
                            {service.protocol}:{service.port}
                            {service.is_secure && ' (SSL)'}
                          </div>
                        ))}
                      </div>
                    ) : (
                      'None detected'
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Select a discovery job or target to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Discovery;