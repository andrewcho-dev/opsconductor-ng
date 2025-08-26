import axios, { AxiosResponse } from 'axios';
import {
  User, UserCreate, UserUpdate, UserListResponse,
  Credential, CredentialCreate, CredentialListResponse, CredentialDecrypted,
  Target, TargetCreate, TargetListResponse,
  Job, JobCreate, JobListResponse,
  JobRun, JobRunListResponse, JobRunStep,
  Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListResponse, SchedulerStatus,
  LoginRequest, AuthResponse
} from '../types';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let accessToken: string | null = localStorage.getItem('access_token');
let refreshToken: string | null = localStorage.getItem('refresh_token');

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
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

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/refresh`, {
            refresh_token: refreshToken
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          
          setTokens(access_token, newRefreshToken);
          
          // Retry the original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
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
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const isAuthenticated = (): boolean => {
  return !!accessToken;
};

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/login', credentials);
    return response.data;
  },

  refresh: async (): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/api/revoke-all');
    clearTokens();
  },

  verify: async (): Promise<{ valid: boolean; user: User }> => {
    const response = await api.get('/api/verify');
    return response.data;
  }
};

// User API
export const userApi = {
  list: async (skip = 0, limit = 100): Promise<UserListResponse> => {
    const response: AxiosResponse<UserListResponse> = await api.get('/users', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<User> => {
    const response: AxiosResponse<User> = await api.get(`/users/${id}`);
    return response.data;
  },

  create: async (userData: UserCreate): Promise<User> => {
    const response: AxiosResponse<User> = await api.post('/users', userData);
    return response.data;
  },

  update: async (id: number, userData: UserUpdate): Promise<User> => {
    const response: AxiosResponse<User> = await api.put(`/users/${id}`, userData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
  },

  assignRole: async (id: number, role: string): Promise<void> => {
    await api.post(`/users/${id}/roles`, { role });
  }
};

// Credential API
export const credentialApi = {
  list: async (skip = 0, limit = 100): Promise<CredentialListResponse> => {
    const response: AxiosResponse<CredentialListResponse> = await api.get('/credentials', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.get(`/credentials/${id}`);
    return response.data;
  },

  getDecrypted: async (id: number): Promise<CredentialDecrypted> => {
    const response: AxiosResponse<CredentialDecrypted> = await api.get(`/credentials/${id}/decrypt`);
    return response.data;
  },

  create: async (credData: CredentialCreate): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.post('/credentials', credData);
    return response.data;
  },

  update: async (id: number, credData: Partial<CredentialCreate>): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.put(`/credentials/${id}`, credData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/credentials/${id}`);
  },

  rotate: async (id: number, newCredentialData: Record<string, any>): Promise<void> => {
    await api.post(`/credentials/${id}/rotate`, newCredentialData);
  }
};

// Target API
export const targetApi = {
  list: async (skip = 0, limit = 100): Promise<TargetListResponse> => {
    const response: AxiosResponse<TargetListResponse> = await api.get('/targets', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.get(`/targets/${id}`);
    return response.data;
  },

  create: async (targetData: TargetCreate): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.post('/targets', targetData);
    return response.data;
  },

  update: async (id: number, targetData: Partial<TargetCreate>): Promise<Target> => {
    const response: AxiosResponse<Target> = await api.put(`/targets/${id}`, targetData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/targets/${id}`);
  },

  testWinRM: async (id: number): Promise<{ success: boolean; message: string; details?: any }> => {
    const response = await api.post(`/targets/${id}/test-winrm`);
    return response.data;
  }
};

// Job API
export const jobApi = {
  list: async (skip = 0, limit = 100, activeOnly = true): Promise<JobListResponse> => {
    const response: AxiosResponse<JobListResponse> = await api.get('/jobs', {
      params: { skip, limit, active_only: activeOnly }
    });
    return response.data;
  },

  get: async (id: number): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.get(`/jobs/${id}`);
    return response.data;
  },

  create: async (jobData: JobCreate): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.post('/jobs', jobData);
    return response.data;
  },

  update: async (id: number, jobData: Partial<JobCreate>): Promise<Job> => {
    const response: AxiosResponse<Job> = await api.put(`/jobs/${id}`, jobData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },

  run: async (id: number, parameters: Record<string, any> = {}): Promise<JobRun> => {
    const response: AxiosResponse<JobRun> = await api.post(`/jobs/${id}/run`, { parameters });
    return response.data;
  }
};

// Job Run API
export const jobRunApi = {
  list: async (skip = 0, limit = 100, jobId?: number): Promise<JobRunListResponse> => {
    const response: AxiosResponse<JobRunListResponse> = await api.get('/runs', {
      params: { skip, limit, job_id: jobId }
    });
    return response.data;
  },

  get: async (id: number): Promise<JobRun> => {
    const response: AxiosResponse<JobRun> = await api.get(`/runs/${id}`);
    return response.data;
  },

  getSteps: async (id: number): Promise<JobRunStep[]> => {
    const response: AxiosResponse<JobRunStep[]> = await api.get(`/runs/${id}/steps`);
    return response.data;
  }
};

// Scheduler API
export const schedulerApi = {
  // Schedule management
  list: async (skip = 0, limit = 100): Promise<ScheduleListResponse> => {
    const response: AxiosResponse<ScheduleListResponse> = await api.get('/schedules', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.get(`/schedules/${id}`);
    return response.data;
  },

  create: async (schedule: ScheduleCreate): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.post('/schedules', schedule);
    return response.data;
  },

  update: async (id: number, schedule: ScheduleUpdate): Promise<Schedule> => {
    const response: AxiosResponse<Schedule> = await api.put(`/schedules/${id}`, schedule);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/schedules/${id}`);
  },

  // Scheduler control
  getStatus: async (): Promise<SchedulerStatus> => {
    const response: AxiosResponse<SchedulerStatus> = await api.get('/scheduler/status');
    return response.data;
  },

  start: async (): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post('/scheduler/start');
    return response.data;
  },

  stop: async (): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await api.post('/scheduler/stop');
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
        'auth': '/auth/health',
        'users': '/users/health', 
        'credentials': '/credentials/health',
        'targets': '/targets/health',
        'jobs': '/jobs/health',
        'executor': '/executor/health',
        'scheduler': '/scheduler/health'
      };
      
      const endpoint = serviceMap[service] || `/${service}/health`;
      const response = await axios.get(`${API_BASE_URL}${endpoint}`, {
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
    const services = ['auth', 'users', 'credentials', 'targets', 'jobs', 'executor', 'scheduler'];
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
      const executorResponse = await api.get('/executor/status');
      return executorResponse.data;
    } catch (error) {
      return { error: 'Failed to fetch system stats' };
    }
  }
};

export default api;