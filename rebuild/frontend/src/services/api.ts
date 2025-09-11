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

// Base API configuration
// Explicitly construct the API URL to ensure HTTPS and correct port
// Service port mapping for development
const SERVICE_PORTS = {
  auth: 3001,
  users: 3002,
  credentials: 3004,
  targets: 3005,
  jobs: 3006,
  executor: 3007,

  notifications: 3009,
  discovery: 3010,
  stepLibraries: 3011
};

export const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Always use the current window location for API calls
  // This ensures the frontend uses the same host/port that the user is accessing
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = window.location.port;
  
  // For development, force HTTP protocol to avoid certificate issues
  const apiProtocol = (hostname === 'localhost' || hostname === '127.0.0.1') ? 'http:' : protocol;
  
  // Build the base URL
  if (port && 
      !((apiProtocol === 'https:' && port === '443') || 
        (apiProtocol === 'http:' && port === '80'))) {
    return `${apiProtocol}//${hostname}:${port}`;
  }
  
  return `${apiProtocol}//${hostname}`;
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
    
    // Add session token if available (simple session-based auth)
    const sessionToken = localStorage.getItem('session_token');
    if (sessionToken) {
      config.headers.Authorization = `Bearer ${sessionToken}`;
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
  localStorage.setItem('session_token', token);
};

export const clearTokens = () => {
  localStorage.removeItem('session_token');
  localStorage.removeItem('user');
};

export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('session_token');
};

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/v1/auth/login', credentials);
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

// Credential API
export const credentialApi = {
  getAll: async (skip = 0, limit = 100): Promise<CredentialListResponse> => {
    const response: AxiosResponse<CredentialListResponse> = await api.get('/api/v1/credentials', {
      params: { skip, limit }
    });
    return response.data;
  },

  list: async (skip = 0, limit = 100): Promise<CredentialListResponse> => {
    const response: AxiosResponse<CredentialListResponse> = await api.get('/api/v1/credentials', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.get(`/api/v1/credentials/${id}`);
    return response.data;
  },

  getDecrypted: async (id: number): Promise<CredentialDecrypted> => {
    const response: AxiosResponse<CredentialDecrypted> = await api.get(`/api/v1/credentials/${id}/decrypt`);
    return response.data;
  },

  create: async (credData: CredentialCreate): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.post('/api/v1/credentials', credData);
    return response.data;
  },

  update: async (id: number, credData: Partial<CredentialCreate>): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.put(`/api/v1/credentials/${id}`, credData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/credentials/${id}`);
  },

  rotate: async (id: number, newCredentialData: Record<string, any>): Promise<void> => {
    await api.post(`/api/v1/credentials/${id}/rotate`, newCredentialData);
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



// Job API
export const jobApi = {
  list: async (skip = 0, limit = 100, activeOnly = true): Promise<JobListResponse> => {
    const response: AxiosResponse<JobListResponse> = await api.get('/api/v1/jobs', {
      params: { skip, limit, active_only: activeOnly }
    });
    return response.data;
  },

  get: async (id: number): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.get(`/api/v1/jobs/${id}`);
    return response.data;
  },

  create: async (jobData: JobCreate): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.post('/api/v1/jobs', jobData);
    return response.data;
  },

  update: async (id: number, jobData: Partial<JobCreate>): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.put(`/api/v1/jobs/${id}`, jobData);
    return response.data;
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
    const response: AxiosResponse<JobRunListResponse> = await api.get('/api/v1/executions', {
      params: { skip, limit, job_id: jobId }
    });
    return response.data;
  },

  get: async (id: number): Promise<JobRun> => {
    const response: AxiosResponse<JobRun> = await api.get(`/api/v1/executions/${id}`);
    return response.data;
  },

  getSteps: async (id: number): Promise<JobRunStep[]> => {
    const response: AxiosResponse<JobRunStep[]> = await api.get(`/api/v1/executions/${id}/steps`);
    return response.data;
  }
};



// Health Monitoring API
export const healthApi = {
  checkService: async (service: string): Promise<{ status: string; service: string; responseTime?: number; error?: string }> => {
    // Get service status from centralized health endpoint
    try {
      const allServices = await healthApi.checkAllServices();
      return allServices[service] || { 
        status: 'unknown', 
        service, 
        error: 'Service not found in health check' 
      };
    } catch (error) {
      return { 
        status: 'unhealthy', 
        service, 
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  checkAllServices: async (): Promise<Record<string, any>> => {
    const startTime = Date.now();
    try {
      // Get health status from centralized API gateway endpoint
      const response = await api.get('/health', {
        timeout: 10000 // 10 second timeout
      });
      const responseTime = Date.now() - startTime;
      
      const results: Record<string, any> = {};
      
      // Process the health checks from the API gateway
      if (response.data && response.data.checks) {
        response.data.checks.forEach((check: any) => {
          results[check.name] = {
            status: check.status,
            service: check.name,
            responseTime: check.response_time_ms || responseTime,
            details: check.details
          };
        });
      }
      
      return results;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        'api-gateway': {
          status: 'unhealthy',
          service: 'api-gateway',
          responseTime,
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      };
    }
  },

  getSystemStats: async (): Promise<any> => {
    try {
      // Get execution status for queue statistics
      const executorResponse = await api.get('/api/v1/executions/status');
      return executorResponse.data;
    } catch (error) {
      return { error: 'Failed to fetch system stats' };
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
    const response = await api.get('/api/v1/notifications/smtp/settings');
    return response.data;
  },

  updateSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    const response = await api.post('/api/v1/notifications/smtp/settings', settings);
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
    const response: AxiosResponse<DiscoveryJobListResponse> = await api.get('/api/v1/discovery/jobs', {
      params: { skip, limit }
    });
    return response.data;
  },

  getJob: async (id: number): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.get(`/api/v1/discovery/jobs/${id}`);
    return response.data;
  },

  createJob: async (jobData: DiscoveryJobCreate): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.post('/api/v1/discovery/jobs', jobData);
    return response.data;
  },

  updateJob: async (id: number, jobData: Partial<DiscoveryJobCreate>): Promise<DiscoveryJob> => {
    const response: AxiosResponse<DiscoveryJob> = await api.put(`/api/v1/discovery/jobs/${id}`, jobData);
    return response.data;
  },

  deleteJob: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovery/jobs/${id}`);
  },

  runJob: async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post(`/api/v1/discovery/jobs/${id}/run`);
    return response.data;
  },

  cancelJob: async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post(`/api/v1/discovery/jobs/${id}/cancel`);
    return response.data;
  },

  // Discovered Targets
  listTargets: async (skip = 0, limit = 100, jobId?: number, status?: string): Promise<DiscoveredTargetListResponse> => {
    const response: AxiosResponse<DiscoveredTargetListResponse> = await api.get('/api/v1/discovery/targets', {
      params: { skip, limit, job_id: jobId, status }
    });
    return response.data;
  },

  getTarget: async (id: number): Promise<DiscoveredTarget> => {
    const response: AxiosResponse<DiscoveredTarget> = await api.get(`/api/v1/discovery/targets/${id}`);
    return response.data;
  },

  updateTarget: async (id: number, targetData: Partial<DiscoveredTarget>): Promise<DiscoveredTarget> => {
    const response: AxiosResponse<DiscoveredTarget> = await api.put(`/api/v1/discovery/targets/${id}`, targetData);
    return response.data;
  },

  deleteTarget: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovery/targets/${id}`);
  },

  importTargets: async (importRequest: TargetImportRequest): Promise<{ imported: number; failed: number; details: any[] }> => {
    const response = await api.post('/api/v1/discovery/import-targets', importRequest);
    return response.data;
  },

  ignoreTargets: async (targetIds: number[]): Promise<{ ignored: number }> => {
    const response = await api.post('/api/v1/discovery/targets/ignore', { target_ids: targetIds });
    return response.data;
  },

  bulkDeleteTargets: async (targetIds: number[]): Promise<{ deleted: number }> => {
    const response = await api.delete('/api/v1/discovery/targets/bulk', { 
      data: { target_ids: targetIds }
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
    const response = await api.get('/api/v1/executions/celery/status');
    return response.data;
  },

  getMetrics: async (): Promise<any> => {
    const response = await api.get('/api/v1/executions/celery/metrics');
    return response.data;
  },

  getQueues: async (): Promise<any> => {
    const response = await api.get('/api/v1/executions/celery/queues');
    return response.data;
  }
};

export default api;