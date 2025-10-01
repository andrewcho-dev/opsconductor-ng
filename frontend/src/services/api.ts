import axios, { AxiosResponse } from 'axios';
import {
  User, UserCreate, UserUpdate, UserListResponse,
  Role, RoleCreate, RoleUpdate, RoleListResponse,
  Credential, CredentialCreate, CredentialListResponse, CredentialDecrypted,
  Job, JobCreate, JobListResponse,
  JobRun, JobRunListResponse, JobRunStep,

  LoginRequest, AuthResponse,

  SMTPSettings, SMTPSettingsResponse, SMTPTestRequest, SMTPTestResponse,
  CommunicationChannel, CommunicationChannelCreate, CommunicationChannelUpdate,
  CommunicationTestRequest, CommunicationTestResponse,
  SlackSettings, TeamsSettings, DiscordSettings, WebhookSettings,

  // New types
  Notification, NotificationCreate, NotificationListResponse,
  Template, TemplateCreate, TemplateListResponse,
  AuditLog, AuditLogListResponse,
  NetworkProbe, NetworkProbeCreate, NetworkAnalysis, NetworkAnalysisListResponse,
  Schedule, ScheduleCreate, ScheduleListResponse,
  StepLibrary, StepLibraryCreate, StepLibraryListResponse,
  AssetDiscovery, AssetDiscoveryCreate, AssetGroup, AssetGroupCreate
} from '../types';
import { AssetCreate } from '../types/asset';

console.log('🔥 API SERVICE LOADED AT', new Date().toISOString());

// Base API configuration
export const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // If running on development port 3000, use Kong proxy on port 8080
  if (window.location.port === '3000') {
    return `http://${window.location.hostname}:8080`;
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
  // Always use the Kong proxy instead of direct service ports
  return getApiBaseUrl();
};

// Create axios instance with dynamic baseURL
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 second timeout for AI requests
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
  list: async (skip = 0, limit = 100): Promise<RoleListResponse> => {
    const response: AxiosResponse<{success: boolean, data: Role[]}> = await api.get('/api/v1/roles', {
      params: { skip, limit }
    });
    // Transform the backend response to match the expected RoleListResponse format
    return {
      data: response.data.data,
      meta: {
        total_items: response.data.data.length,
        skip: skip,
        limit: limit,
        has_more: false
      },
      total: response.data.data.length
    };
  },

  get: async (id: number): Promise<Role> => {
    const response: AxiosResponse<{success: boolean, data: Role}> = await api.get(`/api/v1/roles/${id}`);
    return response.data.data; // Extract the actual role data from the wrapped response
  },

  create: async (roleData: RoleCreate): Promise<Role> => {
    const response: AxiosResponse<{success: boolean, data: Role}> = await api.post('/api/v1/roles', roleData);
    return response.data.data; // Extract the actual role data from the wrapped response
  },

  update: async (id: number, roleData: RoleUpdate): Promise<Role> => {
    const response: AxiosResponse<{success: boolean, data: Role}> = await api.put(`/api/v1/roles/${id}`, roleData);
    return response.data.data; // Extract the actual role data from the wrapped response
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/roles/${id}`);
  },

  // Legacy methods for backward compatibility
  listSimple: async (): Promise<AxiosResponse<{success: boolean, data: Array<{id: number, name: string, description: string}>}>> => {
    return api.get('/api/v1/available-roles');
  },

  listFull: async (): Promise<AxiosResponse<{success: boolean, data: Array<{id: number, name: string, description: string, permissions: string[], is_active: boolean, created_at: string, updated_at: string}>}>> => {
    return api.get('/api/v1/roles');
  }
};

// Asset API (replaces Target API)
export const assetApi = {
  list: async (skip = 0, limit = 100, filters?: any): Promise<any> => {
    const params: any = { skip, limit };
    if (filters) {
      Object.assign(params, filters);
    }
    const response = await api.get('/api/v1/assets', { params });
    return response.data;
  },

  get: async (id: number): Promise<any> => {
    const response = await api.get(`/api/v1/assets/${id}`);
    return response.data;
  },

  create: async (assetData: AssetCreate): Promise<any> => {
    const response = await api.post('/api/v1/assets', assetData);
    return response.data;
  },

  update: async (id: number, assetData: any): Promise<any> => {
    const response = await api.put(`/api/v1/assets/${id}`, assetData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/assets/${id}`);
  },

  test: async (id: number): Promise<any> => {
    const response = await api.post(`/api/v1/assets/${id}/test`);
    return response.data;
  },

  getMetadata: async (): Promise<any> => {
    const response = await api.get('/api/v1/metadata');
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
    // Define services with their Kong health endpoints
    const services = [
      { name: 'identity-service', path: '/api/health/identity-service' },
      { name: 'asset-service', path: '/api/health/asset-service' },
      { name: 'automation-service', path: '/api/health/automation-service' },
      { name: 'communication-service', path: '/api/health/communication-service' },
      { name: 'ai-brain', path: '/api/health/ai-brain' },
      { name: 'network-analyzer-service', path: '/api/health/network-analyzer-service' },
    ];

    const results: Record<string, any> = {};

    // Check each service through Kong
    const healthChecks = services.map(async (service) => {
      const startTime = Date.now();
      try {
        const response = await fetch(`${service.path}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(5000) // 5 second timeout per service
        });
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
          const healthData = await response.json();
          results[service.name] = {
            ...healthData,
            service: service.name,
            responseTime
          };
        } else {
          results[service.name] = {
            status: 'unhealthy',
            service: service.name,
            responseTime,
            error: `HTTP ${response.status}: ${response.statusText}`
          };
        }
      } catch (error) {
        const responseTime = Date.now() - startTime;
        results[service.name] = {
          status: 'unhealthy',
          service: service.name,
          responseTime,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });

    // Check infrastructure services
    const infraChecks = [
      // Kong Gateway - if we can make API calls through it, it's healthy
      (async () => {
        const startTime = Date.now();
        try {
          const response = await fetch('/api/health', {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
          });
          const responseTime = Date.now() - startTime;
          
          results['kong-gateway'] = {
            status: response.ok ? 'healthy' : 'unhealthy',
            service: 'kong-gateway',
            responseTime,
            version: 'Kong Gateway',
            error: response.ok ? undefined : `HTTP ${response.status}`
          };
        } catch (error) {
          const responseTime = Date.now() - startTime;
          results['kong-gateway'] = {
            status: 'unhealthy',
            service: 'kong-gateway',
            responseTime,
            error: error instanceof Error ? error.message : 'Unknown error'
          };
        }
      })(),

      // PostgreSQL - check through backend health endpoint
      (async () => {
        const startTime = Date.now();
        try {
          const response = await fetch('/api/health/database', {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
          });
          const responseTime = Date.now() - startTime;
          
          if (response.ok) {
            const dbHealth = await response.json();
            results['postgresql'] = {
              ...dbHealth,
              service: 'postgresql',
              responseTime
            };
          } else {
            results['postgresql'] = {
              status: 'unhealthy',
              service: 'postgresql',
              responseTime,
              error: `HTTP ${response.status}: ${response.statusText}`
            };
          }
        } catch (error) {
          const responseTime = Date.now() - startTime;
          results['postgresql'] = {
            status: 'unhealthy',
            service: 'postgresql',
            responseTime,
            error: error instanceof Error ? error.message : 'Unknown error'
          };
        }
      })(),

      // Redis - check through backend health endpoint
      (async () => {
        const startTime = Date.now();
        try {
          const response = await fetch('/api/health/redis', {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
          });
          const responseTime = Date.now() - startTime;
          
          if (response.ok) {
            const redisHealth = await response.json();
            results['redis'] = {
              ...redisHealth,
              service: 'redis',
              responseTime
            };
          } else {
            results['redis'] = {
              status: 'unhealthy',
              service: 'redis',
              responseTime,
              error: `HTTP ${response.status}: ${response.statusText}`
            };
          }
        } catch (error) {
          const responseTime = Date.now() - startTime;
          results['redis'] = {
            status: 'unhealthy',
            service: 'redis',
            responseTime,
            error: error instanceof Error ? error.message : 'Unknown error'
          };
        }
      })()
    ];

    // Wait for all health checks to complete
    await Promise.all([...healthChecks, ...infraChecks]);

    return results;
  },

  getSystemStats: async (): Promise<any> => {
    console.warn('getSystemStats is deprecated - use checkAllServices() instead');
    return {
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0,
      network_io: 0,
      uptime: 0
    };
  }
};

// Credentials API
export const credentialApi = {
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

  create: async (credentialData: CredentialCreate): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.post('/api/v1/credentials', credentialData);
    return response.data;
  },

  update: async (id: number, credentialData: Partial<CredentialCreate>): Promise<Credential> => {
    const response: AxiosResponse<Credential> = await api.put(`/api/v1/credentials/${id}`, credentialData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/credentials/${id}`);
  },

  decrypt: async (id: number): Promise<CredentialDecrypted> => {
    const response: AxiosResponse<CredentialDecrypted> = await api.post(`/api/v1/credentials/${id}/decrypt`);
    return response.data;
  },

  test: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response: AxiosResponse<{ success: boolean; message: string }> = await api.post(`/api/v1/credentials/${id}/test`);
    return response.data;
  }
};

// SMTP API (legacy compatibility)
export const smtpApi = {
  getSMTPSettings: async (): Promise<SMTPSettingsResponse> => {
    return communicationApi.getSmtpSettings();
  },

  saveSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    return communicationApi.saveSmtpSettings(settings);
  },

  updateSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    return communicationApi.saveSmtpSettings(settings);
  },

  testSMTPSettings: async (testRequest: SMTPTestRequest): Promise<SMTPTestResponse> => {
    return communicationApi.testSmtpSettings(testRequest);
  }
};

// Communication API
export const communicationApi = {
  // SMTP Settings
  getSmtpSettings: async (): Promise<SMTPSettingsResponse> => {
    try {
      const response: AxiosResponse<SMTPSettingsResponse> = await api.get('/api/v1/smtp/settings');
      return response.data;
    } catch (error: any) {
      // Return default settings if none exist
      if (error.response?.status === 404) {
        return {
          success: true,
          data: {
            id: 0,
            host: '',
            port: 587,
            username: '',
            password: '',
            use_tls: true,
            use_ssl: false,
            from_email: '',
            from_name: '',
            is_active: false,
            is_configured: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          message: 'Default SMTP settings returned'
        };
      }
      throw error;
    }
  },

  saveSmtpSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    const response: AxiosResponse<SMTPSettingsResponse> = await api.post('/api/v1/smtp/settings', settings);
    return response.data;
  },

  testSmtpSettings: async (testRequest: SMTPTestRequest): Promise<SMTPTestResponse> => {
    try {
      const response: AxiosResponse<SMTPTestResponse> = await api.post('/api/v1/smtp/test', testRequest);
      return response.data;
    } catch (error: any) {
      console.error('SMTP test failed:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Failed to test SMTP settings'
      };
    }
  },

  // Communication Channels
  listChannels: async (): Promise<CommunicationChannel[]> => {
    try {
      const response: AxiosResponse<{ success: boolean; data: CommunicationChannel[] }> = await api.get('/api/v1/channels');
      return response.data.data || [];
    } catch (error: any) {
      console.error('Failed to fetch channels:', error);
      return [];
    }
  },

  getChannel: async (id: number): Promise<CommunicationChannel | null> => {
    try {
      const response: AxiosResponse<CommunicationChannel> = await api.get(`/api/v1/channels/${id}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to fetch channel:', error);
      return null;
    }
  },

  getChannelByType: async (channelType: string): Promise<CommunicationChannel | null> => {
    try {
      const channels = await communicationApi.listChannels();
      return channels.find(channel => channel.channel_type === channelType) || null;
    } catch (error: any) {
      console.error('Failed to fetch channel by type:', error);
      return null;
    }
  },

  // Create or update channel
  saveChannel: async (channelData: CommunicationChannelCreate): Promise<CommunicationChannel> => {
    try {
      // Check if channel exists
      const existingChannel = await communicationApi.getChannelByType(channelData.channel_type);
      
      if (existingChannel) {
        // Update existing channel
        const response: AxiosResponse<CommunicationChannel> = await api.put(
          `/api/v1/channels/${existingChannel.id}`,
          channelData
        );
        return response.data;
      } else {
        // Create new channel
        const response: AxiosResponse<CommunicationChannel> = await api.post(
          '/api/v1/channels',
          channelData
        );
        return response.data;
      }
    } catch (error: any) {
      console.error('Failed to save communication channel:', error);
      throw error;
    }
  },

  // Test communication channel
  testChannel: async (channelType: string, testRequest: CommunicationTestRequest): Promise<CommunicationTestResponse> => {
    try {
      const response: AxiosResponse<CommunicationTestResponse> = await api.post(
        `/api/v1/channels/test/${channelType}`,
        testRequest
      );
      return response.data;
    } catch (error: any) {
      console.error('Communication test failed:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Failed to test communication channel',
        details: error.message
      };
    }
  },

  // Delete channel
  deleteChannel: async (channelId: number): Promise<void> => {
    try {
      await api.delete(`/api/v1/channels/${channelId}`);
    } catch (error: any) {
      console.error('Failed to delete communication channel:', error);
      throw error;
    }
  }
};

// AI Pipeline API - 4-Stage Pipeline Integration
export const aiApi = {
  process: async (request: string, context?: any): Promise<any> => {
    console.log('🚀 Sending AI pipeline request:', request);
    // Connect directly to AI pipeline on port 3005 (Docker mapped port)
    const aiPipelineUrl = `http://${window.location.hostname}:3005`;
    const response = await axios.post(`${aiPipelineUrl}/process`, {
      request,
      context: context || {},
      user_id: 'frontend-user',
      session_id: `session_${Date.now()}`
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000
    });
    console.log('✅ AI pipeline response received:', response.data);
    return response.data;
  },

  health: async (): Promise<any> => {
    // Connect directly to AI pipeline on port 3005 (Docker mapped port)
    const aiPipelineUrl = `http://${window.location.hostname}:3005`;
    const response = await axios.get(`${aiPipelineUrl}/health`, {
      timeout: 10000
    });
    return response.data;
  },

  // Legacy compatibility stubs (deprecated - these will be removed)
  monitoringDashboard: async (): Promise<any> => {
    console.warn('monitoringDashboard is deprecated - use aiApi.health() instead');
    return {
      current: { services: {}, overall_health: 'healthy' },
      history: [],
      analysis: { overall_health: 'healthy', alerts: [], recommendations: [] },
      statistics: {}
    };
  },

  getKnowledgeStats: async (): Promise<any> => {
    console.warn('getKnowledgeStats is deprecated');
    return { total_documents: 0, indexed_documents: 0, last_updated: new Date().toISOString() };
  },

  resetCircuitBreaker: async (serviceName: string): Promise<void> => {
    console.warn('resetCircuitBreaker is deprecated');
    // No-op for compatibility
  }
};

// Automation Service API
export const automationApi = {
  testConnection: async (connectionData: {
    host: string;
    port: number;
    service_type: string;
    credential_type?: string;
    username?: string;
    service_id?: number;
    target_id?: number;
  }): Promise<{
    success: boolean;
    error?: string;
    host: string;
    port: number;
    service_type: string;
  }> => {
    const response = await api.post('/api/v1/automation/test-connection', connectionData);
    return response.data;
  }
};

// Notifications API
export const notificationApi = {
  list: async (skip = 0, limit = 100, filters?: any): Promise<NotificationListResponse> => {
    const params: any = { skip, limit };
    if (filters) {
      Object.assign(params, filters);
    }
    const response = await api.get('/api/v1/notifications', { params });
    return response.data;
  },

  get: async (id: number): Promise<Notification> => {
    const response = await api.get(`/api/v1/notifications/${id}`);
    return response.data;
  },

  create: async (notificationData: NotificationCreate): Promise<Notification> => {
    const response = await api.post('/api/v1/notifications', notificationData);
    return response.data;
  },

  update: async (id: number, notificationData: Partial<NotificationCreate>): Promise<Notification> => {
    const response = await api.put(`/api/v1/notifications/${id}`, notificationData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/notifications/${id}`);
  },

  // Note: markAsRead and markAllAsRead not implemented in backend
};

// Templates API
export const templateApi = {
  list: async (skip = 0, limit = 100, filters?: any): Promise<TemplateListResponse> => {
    const params: any = { skip, limit };
    if (filters) {
      Object.assign(params, filters);
    }
    const response = await api.get('/api/v1/templates', { params });
    return response.data;
  },

  get: async (id: number): Promise<Template> => {
    const response = await api.get(`/api/v1/templates/${id}`);
    return response.data;
  },

  create: async (templateData: TemplateCreate): Promise<Template> => {
    const response = await api.post('/api/v1/templates', templateData);
    return response.data;
  },

  update: async (id: number, templateData: Partial<TemplateCreate>): Promise<Template> => {
    const response = await api.put(`/api/v1/templates/${id}`, templateData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/templates/${id}`);
  },

  preview: async (templateData: { template_type: string; subject_template?: string; body_template: string; variables: Record<string, any> }): Promise<{ subject?: string; body: string }> => {
    const response = await api.post('/api/v1/templates/preview', templateData);
    return response.data;
  }
};

// Audit Logs API
export const auditApi = {
  list: async (skip = 0, limit = 100, filters?: any): Promise<AuditLogListResponse> => {
    const params: any = { skip, limit };
    if (filters) {
      Object.assign(params, filters);
    }
    const response = await api.get('/api/v1/audit', { params });
    return response.data;
  },

  get: async (id: number): Promise<AuditLog> => {
    const response = await api.get(`/api/v1/audit/${id}`);
    return response.data;
  },

  export: async (filters?: any): Promise<Blob> => {
    const params = filters || {};
    const response = await api.get('/api/v1/audit/export', { 
      params,
      responseType: 'blob'
    });
    return response.data;
  }
};

// Network Analysis API
export const networkApi = {
  // Probes
  listProbes: async (skip = 0, limit = 100): Promise<{ probes: NetworkProbe[]; total: number }> => {
    const response = await api.get('/api/v1/network/probes', {
      params: { skip, limit }
    });
    return response.data;
  },

  getProbe: async (id: number): Promise<NetworkProbe> => {
    const response = await api.get(`/api/v1/network/probes/${id}`);
    return response.data;
  },

  createProbe: async (probeData: NetworkProbeCreate): Promise<NetworkProbe> => {
    const response = await api.post('/api/v1/network/probes', probeData);
    return response.data;
  },

  updateProbe: async (id: number, probeData: Partial<NetworkProbeCreate>): Promise<NetworkProbe> => {
    const response = await api.put(`/api/v1/network/probes/${id}`, probeData);
    return response.data;
  },

  deleteProbe: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/network/probes/${id}`);
  },

  runProbe: async (id: number): Promise<{ execution_id: string }> => {
    const response = await api.post(`/api/v1/network/probes/${id}/run`);
    return response.data;
  },

  // Analysis
  listAnalyses: async (skip = 0, limit = 100, probeId?: number): Promise<NetworkAnalysisListResponse> => {
    const params: any = { skip, limit };
    if (probeId) {
      params.probe_id = probeId;
    }
    const response = await api.get('/api/v1/network/analyses', { params });
    return response.data;
  },

  getAnalysis: async (id: number): Promise<NetworkAnalysis> => {
    const response = await api.get(`/api/v1/network/analyses/${id}`);
    return response.data;
  },

  // Monitoring
  getNetworkHealth: async (): Promise<any> => {
    const response = await api.get('/api/v1/network/health');
    return response.data;
  },

  getNetworkStats: async (): Promise<any> => {
    const response = await api.get('/api/v1/network/stats');
    return response.data;
  }
};

// Schedules API
export const scheduleApi = {
  list: async (skip = 0, limit = 100): Promise<ScheduleListResponse> => {
    const response = await api.get('/api/v1/schedules', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<Schedule> => {
    const response = await api.get(`/api/v1/schedules/${id}`);
    return response.data;
  },

  create: async (scheduleData: ScheduleCreate): Promise<Schedule> => {
    const response = await api.post('/api/v1/schedules', scheduleData);
    return response.data;
  },

  update: async (id: number, scheduleData: Partial<ScheduleCreate>): Promise<Schedule> => {
    const response = await api.put(`/api/v1/schedules/${id}`, scheduleData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/schedules/${id}`);
  },

  enable: async (id: number): Promise<void> => {
    await api.post(`/api/v1/schedules/${id}/enable`);
  },

  disable: async (id: number): Promise<void> => {
    await api.post(`/api/v1/schedules/${id}/disable`);
  },

  trigger: async (id: number): Promise<{ execution_id: string }> => {
    const response = await api.post(`/api/v1/schedules/${id}/trigger`);
    return response.data;
  }
};

// Step Libraries API
export const stepLibraryApi = {
  list: async (skip = 0, limit = 100, category?: string): Promise<StepLibraryListResponse> => {
    const params: any = { skip, limit };
    if (category) {
      params.category = category;
    }
    const response = await api.get('/api/v1/step-libraries', { params });
    return response.data;
  },

  get: async (id: number): Promise<StepLibrary> => {
    const response = await api.get(`/api/v1/step-libraries/${id}`);
    return response.data;
  },

  create: async (stepData: StepLibraryCreate): Promise<StepLibrary> => {
    const response = await api.post('/api/v1/step-libraries', stepData);
    return response.data;
  },

  update: async (id: number, stepData: Partial<StepLibraryCreate>): Promise<StepLibrary> => {
    const response = await api.put(`/api/v1/step-libraries/${id}`, stepData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/step-libraries/${id}`);
  },

  getCategories: async (): Promise<string[]> => {
    const response = await api.get('/api/v1/step-libraries/categories');
    return response.data.categories;
  },

  export: async (): Promise<Blob> => {
    const response = await api.get('/api/v1/step-libraries/export', {
      responseType: 'blob'
    });
    return response.data;
  },

  import: async (file: File): Promise<{ imported: number; errors: string[] }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/v1/step-libraries/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }
};

// Asset Discovery API
export const assetDiscoveryApi = {
  list: async (skip = 0, limit = 100): Promise<{ discoveries: AssetDiscovery[]; total: number }> => {
    const response = await api.get('/api/v1/discovery', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<AssetDiscovery> => {
    const response = await api.get(`/api/v1/discovery/${id}`);
    return response.data;
  },

  create: async (discoveryData: AssetDiscoveryCreate): Promise<AssetDiscovery> => {
    const response = await api.post('/api/v1/discovery', discoveryData);
    return response.data;
  },

  update: async (id: number, discoveryData: Partial<AssetDiscoveryCreate>): Promise<AssetDiscovery> => {
    const response = await api.put(`/api/v1/discovery/${id}`, discoveryData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/discovery/${id}`);
  },

  run: async (id: number): Promise<{ execution_id: string }> => {
    const response = await api.post(`/api/v1/discovery/${id}/run`);
    return response.data;
  }
};

// Asset Groups API
export const assetGroupApi = {
  list: async (skip = 0, limit = 100): Promise<{ groups: AssetGroup[]; total: number }> => {
    const response = await api.get('/api/v1/target-groups', {
      params: { skip, limit }
    });
    return response.data;
  },

  get: async (id: number): Promise<AssetGroup> => {
    const response = await api.get(`/api/v1/target-groups/${id}`);
    return response.data;
  },

  create: async (groupData: AssetGroupCreate): Promise<AssetGroup> => {
    const response = await api.post('/api/v1/target-groups', groupData);
    return response.data;
  },

  update: async (id: number, groupData: Partial<AssetGroupCreate>): Promise<AssetGroup> => {
    const response = await api.put(`/api/v1/target-groups/${id}`, groupData);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/target-groups/${id}`);
  },

  getAssets: async (id: number): Promise<any[]> => {
    const response = await api.get(`/api/v1/target-groups/${id}/assets`);
    return response.data.assets;
  },

  addAssets: async (id: number, assetIds: number[]): Promise<void> => {
    await api.post(`/api/v1/target-groups/${id}/assets`, { asset_ids: assetIds });
  },

  removeAssets: async (id: number, assetIds: number[]): Promise<void> => {
    await api.delete(`/api/v1/target-groups/${id}/assets`, { data: { asset_ids: assetIds } });
  }
};

export default api;