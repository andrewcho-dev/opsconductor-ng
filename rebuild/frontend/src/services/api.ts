import axios, { AxiosResponse } from 'axios';
import {
  User, UserCreate, UserUpdate, UserListResponse,
  Credential, CredentialCreate, CredentialListResponse, CredentialDecrypted,
  Target, TargetCreate, TargetListResponse, WinRMTestResult, SSHTestResult,
  Job, JobCreate, JobListResponse,
  JobRun, JobRunListResponse, JobRunStep,

  LoginRequest, AuthResponse,
  NotificationPreferences, NotificationPreferencesResponse, NotificationChannel,
  SMTPSettings, SMTPSettingsResponse, SMTPTestRequest, SMTPTestResponse,
  DiscoveryJob, DiscoveryJobCreate, DiscoveryJobListResponse,
  DiscoveredTarget, DiscoveredTargetListResponse, TargetImportRequest,
  DiscoveryTemplate, DiscoveryTemplateCreate, DiscoveryTemplateListResponse
} from '../types';

console.log('🔥 API SERVICE LOADED AT', new Date().toISOString());

// Base API configuration
// Explicitly construct the API URL to ensure HTTPS and correct port
// Service port mapping for development (kept for reference)
// const SERVICE_PORTS = {
//   auth: 3001,
//   users: 3002,
//   credentials: 3004,
//   targets: 3005,
//   jobs: 3006,
//   executor: 3007,
//   notifications: 3009,
//   discovery: 3010,
//   stepLibraries: 3011
// };

export const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // If running on development port 3000, use nginx proxy
  if (window.location.port === '3000') {
    return 'http://localhost';
  }
  
  // Use current window location but ensure correct protocol
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  
  // Only include port if it's not the standard port for the protocol
  if (window.location.port && 
      !((protocol === 'https:' && window.location.port === '443') || 
        (protocol === 'http:' && window.location.port === '80'))) {
    return `${protocol}//${hostname}:${window.location.port}`;
  }
  
  return `${protocol}//${hostname}`;
};

export const getServiceUrl = (service: string) => {
  // Always use the nginx proxy instead of direct service ports
  return getApiBaseUrl();
};

// Create axios instance with dynamic baseURL
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to set dynamic baseURL
api.interceptors.request.use(
  (config) => {
    // Set dynamic baseURL for each request
    config.baseURL = getApiBaseUrl();
    
    // Add access token if available (simple session-based auth)
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle auth errors by redirecting to login
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('Authentication required, redirecting to login');
      clearTokens();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Simple session management functions
export const setSessionToken = (token: string) => {
  localStorage.setItem('access_token', token);
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
};

export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('access_token');
};

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await axios.post(`${getApiBaseUrl()}/api/v1/auth/login`, credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/api/v1/auth/logout');
    clearTokens();
  },

  verify: async (): Promise<{ valid: boolean; user: User }> => {
    const response = await api.get('/api/v1/auth/verify');
    return response.data;
  }
};

// User API
export const userApi = {
  list: async (skip = 0, limit = 100): Promise<UserListResponse> => {
    const response: AxiosResponse<UserListResponse> = await api.get('/api/v1/users', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<User> => {
    const response: AxiosResponse<User> = await api.get(`/api/v1/users/${id}`);
    return response.data;
  },

  create: async (userData: UserCreate): Promise<User> => {
    const response: AxiosResponse<User> = await api.post('/api/v1/users', userData);
    return response.data;
  },

  update: async (id: number, userData: UserUpdate): Promise<User> => {
    const response: AxiosResponse<User> = await api.put(`/api/v1/users/${id}`, userData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/users/${id}`);
  },

  assignRole: async (id: number, role: string): Promise<void> => {
    await api.post(`/api/v1/users/${id}/roles`, { role });
  }
};

// Roles API
export const rolesApi = {
  list: async (): Promise<AxiosResponse<{success: boolean, data: Array<{id: number, name: string, description: string}>}>> => {
    return api.get('/api/v1/available-roles');
  },

  listFull: async (): Promise<AxiosResponse<{success: boolean, data: Array<{id: number, name: string, description: string, permissions: string[], is_active: boolean, created_at: string, updated_at: string}>}>> => {
    return api.get('/api/v1/roles');
  }
};



// Target API
export const targetApi = {
  list: async (skip = 0, limit = 100): Promise<TargetListResponse> => {
    const response: AxiosResponse<TargetListResponse> = await api.get('/api/v1/targets', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.get(`/api/v1/targets/${id}`);
    return response.data;
  },

  create: async (targetData: TargetCreate): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.post('/api/v1/targets', targetData);
    return response.data;
  },

  update: async (id: number, targetData: Partial<TargetCreate>): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.put(`/api/v1/targets/${id}`, targetData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/targets/${id}`);
  },

  testWinRM: async (id: number): Promise<WinRMTestResult> => {
    const response = await api.post(`/api/v1/targets/${id}/test-winrm`);
    return response.data;
  },

  testSSH: async (id: number): Promise<SSHTestResult> => {
    const response = await api.post(`/api/v1/targets/${id}/test-ssh`);
    return response.data;
  }
};

// Target Group API
export const targetGroupApi = {
  list: async (includeCount = false): Promise<any> => {
    const response = await api.get('/api/v1/target-groups', {
      params: { include_counts: includeCount }
    });
    return response.data;
  },

  getTree: async (): Promise<any> => {
    const response = await api.get('/api/v1/target-groups-tree');
    return response.data;
  },

  get: async (id: number): Promise<any> => {
    const response = await api.get(`/api/v1/target-groups/${id}`);
    return response.data;
  },

  create: async (groupData: any): Promise<any> => {
    const response = await api.post('/api/v1/target-groups', groupData);
    return response.data;
  },

  update: async (id: number, groupData: any): Promise<any> => {
    const response = await api.put(`/api/v1/target-groups/${id}`, groupData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/target-groups/${id}`);
  },

  getTargets: async (id: number): Promise<any> => {
    const response = await api.get(`/api/v1/target-groups/${id}/targets`);
    return response.data;
  },

  addTargets: async (id: number, targetIds: number[]): Promise<any> => {
    const response = await api.post(`/api/v1/target-groups/${id}/targets`, {
      target_ids: targetIds
    });
    return response.data;
  },

  removeTarget: async (groupId: number, targetId: number): Promise<void> => {
    await api.delete(`/api/v1/target-groups/${groupId}/targets/${targetId}`);
  }
};

// Asset Service Target API (for getting all targets)
export const assetTargetApi = {
  list: async (): Promise<any> => {
    const response = await api.get('/api/v1/targets');
    return response.data;
  }
};

// Job API
export const jobApi = {
  list: async (skip = 0, limit = 100): Promise<JobListResponse> => {
    const response: AxiosResponse<JobListResponse> = await api.get('/api/v1/jobs', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Job> => {
    const response: AxiosResponse<{success: boolean, data: Job}> = await api.get(`/api/v1/jobs/${id}`);
    return response.data.data;
  },

  create: async (jobData: JobCreate): Promise<Job> => {
    const response: AxiosResponse<{success: boolean, message: string, data: Job}> = await api.post('/api/v1/jobs', jobData);
    return response.data.data;
  },

  update: async (id: number, jobData: Partial<JobCreate>): Promise<Job> => {
    const response: AxiosResponse<{success: boolean, message: string, data: Job}> = await api.put(`/api/v1/jobs/${id}`, jobData);
    return response.data.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/jobs/${id}`);
  },

  run: async (id: number, parameters: Record<string, any> = {}): Promise<JobRun> => {
    const response: AxiosResponse<JobRun> = await api.post(`/api/v1/jobs/${id}/run`, { parameters });
    return response.data;
  },

  export: async (): Promise<any> => {
    const response: AxiosResponse<any> = await api.post('/api/v1/jobs/export', {});
    return response.data;
  },

  import: async (importData: any): Promise<any> => {
    const response: AxiosResponse<any> = await api.post('/api/v1/jobs/import', importData);
    return response.data;
  }
};

// Job Run API
export const jobRunApi = {
  list: async (skip = 0, limit = 100, jobId?: number): Promise<JobRunListResponse> => {
    const response: AxiosResponse<JobRunListResponse> = await api.get('/api/v1/runs', {
      params: { skip, limit, job_id: jobId }
    });
    return response.data;
  },

  get: async (id: number): Promise<JobRun> => {
    const response: AxiosResponse<JobRun> = await api.get(`/api/v1/runs/${id}`);
    return response.data;
  },

  getSteps: async (id: number): Promise<JobRunStep[]> => {
    const response: AxiosResponse<JobRunStep[]> = await api.get(`/api/v1/runs/${id}/steps`);
    return response.data;
  }
};



// Health Monitoring API
export const healthApi = {
  checkAllServices: async (): Promise<Record<string, any>> => {
    const startTime = Date.now();
    try {
      const response = await api.get('/health', {
        timeout: 10000 // 10 second timeout for comprehensive health check
      });
      const responseTime = Date.now() - startTime;
      
      // Transform the centralized health response into the expected format
      const healthData = response.data;
      const results: Record<string, any> = {};
      
      // Add overall API Gateway status
      results['api-gateway'] = {
        status: healthData.status,
        service: 'api-gateway',
        responseTime,
        message: healthData.message
      };
      
      // Add individual service checks from the centralized response
      if (healthData.checks) {
        healthData.checks.forEach((check: any) => {
          // Map service names from the health check response
          let serviceName = check.service || check.name || 'unknown';
          
          // Normalize service names to match frontend expectations
          if (serviceName.includes('identity')) {
            results['auth'] = { ...check, service: 'auth', responseTime };
            results['users'] = { ...check, service: 'users', responseTime };
          } else if (serviceName.includes('asset')) {
            results['credentials'] = { ...check, service: 'credentials', responseTime };
            results['targets'] = { ...check, service: 'targets', responseTime };
            results['discovery'] = { ...check, service: 'discovery', responseTime };
          } else if (serviceName.includes('automation')) {
            results['jobs'] = { ...check, service: 'jobs', responseTime };
            results['executor'] = { ...check, service: 'executor', responseTime };
            results['step-libraries'] = { ...check, service: 'step-libraries', responseTime };
          } else if (serviceName.includes('communication')) {
            results['notification'] = { ...check, service: 'notification', responseTime };
          } else {
            // For database, redis, etc.
            results[serviceName.toLowerCase()] = { ...check, service: serviceName.toLowerCase(), responseTime };
          }
        });
      }
      
      // Add default status for services not explicitly reported
      const expectedServices = [
        'auth', 'users', 'credentials', 'targets', 'jobs', 'executor', 
        'notification', 'discovery', 'step-libraries', 'redis', 'postgres'
      ];
      
      expectedServices.forEach(service => {
        if (!results[service]) {
          results[service] = {
            status: 'unknown',
            service,
            responseTime,
            message: 'Service status not reported'
          };
        }
      });
      
      return results;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // Return error status for all services if health check fails
      const services = [
        'api-gateway', 'auth', 'users', 'credentials', 'targets', 'jobs', 'executor',
        'notification', 'discovery', 'step-libraries', 'redis', 'postgres'
      ];
      
      const results: Record<string, any> = {};
      services.forEach(service => {
        results[service] = {
          status: 'unhealthy',
          service,
          responseTime,
          error: errorMessage
        };
      });
      
      return results;
    }
  },

  checkService: async (service: string): Promise<{ status: string; service: string; responseTime?: number; error?: string }> => {
    // For individual service checks, use the centralized health endpoint
    // and extract the specific service status
    try {
      const allServices = await healthApi.checkAllServices();
      return allServices[service] || {
        status: 'unknown',
        service,
        error: 'Service not found in health report'
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        service,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  getSystemStats: async (): Promise<any> => {
    try {
      // Get system stats from the centralized health endpoint
      const healthResponse = await api.get('/health');
      const healthData = healthResponse.data;
      
      // Extract system statistics from health data
      const stats = {
        overall_status: healthData.status,
        services_count: healthData.checks ? healthData.checks.length : 0,
        healthy_services: healthData.checks ? healthData.checks.filter((c: any) => c.status === 'healthy').length : 0,
        unhealthy_services: healthData.checks ? healthData.checks.filter((c: any) => c.status === 'unhealthy').length : 0,
        timestamp: new Date().toISOString(),
        message: healthData.message || 'System health check completed'
      };
      
      return stats;
    } catch (error) {
      return { 
        error: 'Failed to fetch system stats',
        overall_status: 'unhealthy',
        services_count: 0,
        healthy_services: 0,
        unhealthy_services: 0,
        timestamp: new Date().toISOString()
      };
    }
  }
};

// Notification Preferences API
export const notificationApi = {
  // User notification preferences
  getUserPreferences: async (userId: number): Promise<NotificationPreferencesResponse> => {
    const response = await api.get(`/api/v1/users/${userId}/notification-preferences`);
    return response.data;
  },

  updateUserPreferences: async (userId: number, preferences: NotificationPreferences): Promise<NotificationPreferencesResponse> => {
    const response = await api.put(`/api/v1/users/${userId}/notification-preferences`, preferences);
    return response.data;
  },

  // Notification channels
  getChannels: async (): Promise<NotificationChannel[]> => {
    const response = await api.get('/api/v1/channels');
    return response.data;
  },

  // SMTP settings (admin only)
  getSMTPSettings: async (): Promise<SMTPSettingsResponse> => {
    const response = await api.get('/api/v1/notifications/smtp');
    return response.data;
  },

  updateSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    const response = await api.post('/api/v1/notifications/smtp', settings);
    return response.data;
  },

  testSMTPSettings: async (testRequest: SMTPTestRequest): Promise<SMTPTestResponse> => {
    const response = await api.post('/api/v1/notifications/smtp/test', testRequest);
    return response.data;
  }
};

// Discovery API
export const discoveryApi = {
  // Discovery Jobs
  listJobs: async (skip = 0, limit = 100): Promise<DiscoveryJobListResponse> => {
    const response: AxiosResponse<JobListResponse> = await api.get('/api/v1/jobs', {
      params: { skip, limit, job_type: 'discovery' }
    });
    
    // Transform automation jobs to discovery job format for compatibility
    const discoveryJobs = response.data.jobs?.map(job => ({
      id: job.id,
      name: job.name,
      description: job.description,
      target_range: job.workflow_definition?.inputs?.cidr_ranges?.join(', ') || 'N/A',
      scan_type: 'network_scan', // Default for discovery jobs
      status: 'pending' as const, // Will be updated by progress polling
      configuration: job.workflow_definition?.inputs || {},
      created_by: job.created_by,
      created_at: job.created_at,
      updated_at: job.updated_at,
      results: {}
    })) || [];
    
    return {
      discovery_jobs: discoveryJobs,
      total: response.data.total || 0,
      skip: response.data.skip || 0,
      limit: response.data.limit || 100
    };
  },

  getJob: async (id: number): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.get(`/api/v1/discovery/discovery-jobs/${id}`);
    return response.data;
  },

  createJob: async (jobData: DiscoveryJobCreate): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.post('/api/v1/discovery/discovery-jobs', jobData);
    return response.data;
  },

  updateJob: async (id: number, jobData: Partial<DiscoveryJobCreate>): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.put(`/api/v1/discovery/discovery-jobs/${id}`, jobData);
    return response.data;
  },

  deleteJob: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovery/discovery-jobs/${id}`);
  },

  runJob: async (id: number): Promise<{ message: string; task_id?: string; status_url?: string }> => {
    const response: AxiosResponse<{ success: boolean; message: string; data: any }> = await api.post(`/api/v1/jobs/${id}/run`);
    return {
      message: response.data.message,
      task_id: response.data.data?.task_id,
      status_url: response.data.data?.status_url
    };
  },

  cancelJob: async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post(`/api/v1/discovery/discovery-jobs/${id}/cancel`);
    return response.data;
  },

  getJobProgress: async (id: number, taskId?: string): Promise<{
    status: string;
    progress?: number;
    total?: number;
    message: string;
    phase?: string;
    targets_found?: number;
    targets_scanned?: number;
    total_targets?: number;
    current_target?: string;
    result?: any;
    ready?: boolean;
    successful?: boolean;
    failed?: boolean;
  }> => {
    if (taskId) {
      // Use direct Celery status if we have task_id
      const response = await api.get(`/api/v1/tasks/${taskId}/status`);
      const celeryData = response.data;
      
      // Transform Celery response to expected format
      return {
        status: celeryData.status === 'SUCCESS' ? 'completed' : 
                celeryData.status === 'FAILURE' ? 'failed' : 
                celeryData.status === 'PENDING' ? 'running' : celeryData.status.toLowerCase(),
        message: celeryData.result?.message || `Task ${celeryData.status}`,
        result: celeryData.result,
        ready: celeryData.ready,
        successful: celeryData.successful,
        failed: celeryData.failed,
        progress: celeryData.result?.progress || (celeryData.ready ? 100 : 0)
      };
    } else {
      // Fallback to job execution status
      const response = await api.get(`/api/v1/jobs/${id}/execution-status`);
      return {
        status: response.data.status || 'unknown',
        message: response.data.message || 'No status available',
        progress: 0
      };
    }
  },

  // Discovered Targets
  listTargets: async (skip = 0, limit = 100, jobId?: number, status?: string): Promise<DiscoveredTargetListResponse> => {
    console.log('🚀🚀🚀 CALLING NEW ENDPOINT: /api/v1/discovered-targets AT', new Date().toISOString(), '🚀🚀🚀');
    const response: AxiosResponse<DiscoveredTargetListResponse> = await api.get('/api/v1/discovered-targets', {
      params: { skip, limit, job_id: jobId, status }
    });
    return response.data;
  },

  getTarget: async (id: number): Promise<DiscoveredTarget> => {
    const response: AxiosResponse<{success: boolean, data: DiscoveredTarget}> = await api.get(`/api/v1/discovered-targets/${id}`);
    return response.data.data;
  },

  updateTarget: async (id: number, targetData: Partial<DiscoveredTarget>): Promise<DiscoveredTarget> => {
    const response: AxiosResponse<DiscoveredTarget> = await api.put(`/api/v1/discovered-targets/${id}`, targetData);
    return response.data;
  },

  deleteTarget: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovered-targets/${id}`);
  },

  importTargets: async (importRequest: TargetImportRequest): Promise<{ imported: number; failed: number; details: any[] }> => {
    const response = await api.post('/api/v1/discovery/import-targets', importRequest);
    return response.data;
  },

  ignoreTargets: async (targetIds: number[]): Promise<{ ignored: number }> => {
    const response = await api.post('/api/v1/discovered-targets/ignore', { target_ids: targetIds });
    return response.data;
  },

  bulkDeleteTargets: async (targetIds: number[]): Promise<{ deleted: number }> => {
    const response = await api.post('/api/v1/discovered-targets/bulk-delete', { 
      target_ids: targetIds
    });
    return response.data;
  },

  // Discovery Templates
  listTemplates: async (skip = 0, limit = 100): Promise<DiscoveryTemplateListResponse> => {
    const response: AxiosResponse<DiscoveryTemplateListResponse> = await api.get('/api/v1/discovery/templates', {
      params: { skip, limit }
    });
    return response.data;
  },

  getTemplate: async (id: number): Promise<DiscoveryTemplate> => {
    const response: AxiosResponse<DiscoveryTemplate> = await api.get(`/api/v1/discovery/templates/${id}`);
    return response.data;
  },

  createTemplate: async (templateData: DiscoveryTemplateCreate): Promise<DiscoveryTemplate> => {
    const response: AxiosResponse<DiscoveryTemplate> = await api.post('/api/v1/discovery/templates', templateData);
    return response.data;
  },

  updateTemplate: async (id: number, templateData: Partial<DiscoveryTemplateCreate>): Promise<DiscoveryTemplate> => {
    const response: AxiosResponse<DiscoveryTemplate> = await api.put(`/api/v1/discovery/templates/${id}`, templateData);
    return response.data;
  },

  deleteTemplate: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovery/templates/${id}`);
  },

  // Network Range Validation
  validateNetworkRanges: async (ranges: { ranges: string[] }): Promise<any> => {
    const response = await api.post('/api/v1/discovery/validate-network-ranges', ranges);
    return response.data;
  }
};

// Celery Monitoring API
export const celeryApi = {
  getStatus: async (): Promise<any> => {
    const response = await api.get('/api/v1/executor/celery/status');
    return response.data;
  },

  getMetrics: async (): Promise<any> => {
    const response = await api.get('/api/v1/executor/celery/metrics');
    return response.data;
  },

  getQueues: async (): Promise<any> => {
    const response = await api.get('/api/v1/executor/celery/queues');
    return response.data;
  }
};

export default api;