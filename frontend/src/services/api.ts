import axios, { AxiosResponse } from 'axios';
import {
  User, UserCreate, UserUpdate, UserListResponse,
  Credential, CredentialCreate, CredentialListResponse, CredentialDecrypted,
  Target, TargetCreate, TargetListResponse, WinRMTestResult, SSHTestResult,
  Job, JobCreate, JobListResponse,
  JobRun, JobRunListResponse, JobRunStep,
  Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListResponse, SchedulerStatus,
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
  scheduler: 3008,
  notifications: 3009,
  discovery: 3010,
  stepLibraries: 3011
};

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

// Token management  
let refreshToken: string | null = localStorage.getItem('refresh_token');

// Request interceptor to add auth token and set dynamic baseURL
api.interceptors.request.use(
  (config) => {
    // Set dynamic baseURL for each request
    config.baseURL = getApiBaseUrl();
    
    // Always get fresh token from localStorage
    const currentToken = localStorage.getItem('access_token');
    console.log('API Request Interceptor:', { 
      baseURL: config.baseURL,
      url: config.url, 
      hasToken: !!currentToken,
      tokenPreview: currentToken ? currentToken.substring(0, 20) + '...' : null
    });
    if (currentToken) {
      config.headers.Authorization = `Bearer ${currentToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle both 401 (Unauthorized) and 403 (Forbidden) errors
    if ((error.response?.status === 401 || error.response?.status === 403) && !originalRequest._retry) {
      originalRequest._retry = true;
      console.log(`Auth error (${error.response?.status}), attempting token refresh`);

      const currentRefreshToken = localStorage.getItem('refresh_token');
      if (currentRefreshToken) {
        try {
          console.log('Refreshing token with refresh_token');
          const response = await axios.post(`${getApiBaseUrl()}/refresh`, {
            refresh_token: currentRefreshToken
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          console.log('Token refresh successful, updating tokens');
          
          setTokens(access_token, newRefreshToken);
          
          // Update user data in AuthContext
          try {
            const userResponse = await axios.get(`${getApiBaseUrl()}/verify`, {
              headers: { Authorization: `Bearer ${access_token}` }
            });
            if (userResponse.data?.user) {
              localStorage.setItem('user', JSON.stringify(userResponse.data.user));
            }
          } catch (userError) {
            console.error('Failed to refresh user data:', userError);
          }
          
          // Retry the original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          // Refresh failed, redirect to login
          clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        console.log('No refresh token found, redirecting to login');
        // No refresh token, redirect to login
        clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Token management functions
export const setTokens = (access: string, refresh: string) => {
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};

export const clearTokens = () => {
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
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

  refresh: async (): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    });
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

// Scheduler API
export const schedulerApi = {
  // Schedule management
  list: async (skip = 0, limit = 100): Promise<ScheduleListResponse> => {
    const response: AxiosResponse<ScheduleListResponse> = await api.get('/api/v1/schedules', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.get(`/api/v1/schedules/${id}`);
    return response.data;
  },

  create: async (schedule: ScheduleCreate): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.post('/api/v1/schedules', schedule);
    return response.data;
  },

  update: async (id: number, schedule: ScheduleUpdate): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.put(`/api/v1/schedules/${id}`, schedule);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/schedules/${id}`);
  },

  // Scheduler control
  getStatus: async (): Promise<SchedulerStatus> => {
    const response: AxiosResponse<SchedulerStatus> = await api.get('/api/v1/scheduler/status');
    return response.data;
  },

  start: async (): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post('/api/v1/scheduler/start');
    return response.data;
  },

  stop: async (): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post('/api/v1/scheduler/stop');
    return response.data;
  }
};

// Health Monitoring API
export const healthApi = {
  checkService: async (service: string): Promise<{ status: string; service: string; responseTime?: number; error?: string }> => {
    const startTime = Date.now();
    try {
      // Map service names to their health endpoints
      const serviceMap: Record<string, string> = {
        'auth': '/api/v1/auth/health',
        'users': '/api/v1/users/health', 
        'credentials': '/api/v1/credentials/health',
        'targets': '/api/v1/targets/health',
        'jobs': '/api/v1/jobs/health',
        'executor': '/api/v1/executor/health',
        'scheduler': '/api/v1/scheduler/health',
        'notification': '/api/v1/notification/health',
        'discovery': '/api/v1/discovery/health',
        'step-libraries': '/api/v1/step-libraries/health'
      };
      
      const endpoint = serviceMap[service] || `/api/v1/${service}/health`;
      const response = await api.get(endpoint, {
        timeout: 5000 // 5 second timeout
      });
      const responseTime = Date.now() - startTime;
      return { ...response.data, responseTime };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      return { 
        status: 'unhealthy', 
        service, 
        responseTime,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  checkAllServices: async (): Promise<Record<string, any>> => {
    const services = ['auth', 'users', 'credentials', 'targets', 'jobs', 'executor', 'scheduler', 'notification', 'discovery', 'step-libraries'];
    const results: Record<string, any> = {};
    
    const checks = services.map(async (service) => {
      const result = await healthApi.checkService(service);
      results[service] = result;
    });
    
    await Promise.allSettled(checks);
    return results;
  },

  getSystemStats: async (): Promise<any> => {
    try {
      // Get executor status for queue statistics
      const executorResponse = await api.get('/api/v1/executor/status');
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
    const response = await api.get('/api/v1/notification/channels');
    return response.data;
  },

  // SMTP settings (admin only)
  getSMTPSettings: async (): Promise<SMTPSettingsResponse> => {
    const response = await api.get('/api/v1/notification/smtp/settings');
    return response.data;
  },

  updateSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    const response = await api.post('/api/v1/notification/smtp/settings', settings);
    return response.data;
  },

  testSMTPSettings: async (testRequest: SMTPTestRequest): Promise<SMTPTestResponse> => {
    const response = await api.post('/api/v1/notification/smtp/test', testRequest);
    return response.data;
  }
};

// Discovery API
export const discoveryApi = {
  // Discovery Jobs
  listJobs: async (skip = 0, limit = 100): Promise<DiscoveryJobListResponse> => {
    const response: AxiosResponse<DiscoveryJobListResponse> = await api.get('/api/v1/discovery/discovery-jobs', {
      params: { skip, limit }
    });
    return response.data;
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

  runJob: async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post(`/api/v1/discovery/discovery-jobs/${id}/run`);
    return response.data;
  },

  cancelJob: async (id: number): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post(`/api/v1/discovery/discovery-jobs/${id}/cancel`);
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

export default api;