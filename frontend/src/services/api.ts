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
// Explicitly construct the API URL to ensure HTTPS and correct port
// Service port mapping for development (kept for reference)
// const SERVICE_PORTS = {
//   auth: 3001,
//   users: 3002,
//   credentials: 3004,
//   targets: 3005,
//   jobs: 3006,
//   executor: 3007,


// };

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
          // Test Kong by making a simple API call through it
          const response = await fetch('/api/v1/users', {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
          });
          const responseTime = Date.now() - startTime;
          // Kong is healthy if it responds (even with auth errors)
          results['kong'] = {
            status: (response.status < 500) ? 'healthy' : 'unhealthy',
            service: 'kong',
            responseTime,
            message: 'API Gateway responding'
          };
        } catch (error) {
          const responseTime = Date.now() - startTime;
          results['kong'] = {
            status: 'unhealthy',
            service: 'kong',
            responseTime,
            error: error instanceof Error ? error.message : 'Unknown error'
          };
        }
      })(),
      
      // PostgreSQL - check via a simple query through one of the services
      (async () => {
        try {
          // We can infer postgres health from the identity service health check
          // which includes database connectivity
          results['postgres'] = {
            status: 'unknown',
            service: 'postgres',
            message: 'Status inferred from service health checks'
          };
        } catch (error) {
          results['postgres'] = {
            status: 'unknown',
            service: 'postgres',
            error: 'Cannot directly check database'
          };
        }
      })(),
      
      // Redis - similar approach
      (async () => {
        results['redis'] = {
          status: 'unknown',
          service: 'redis',
          message: 'Status inferred from service health checks'
        };
      })(),
      
      // ChromaDB - infer health from AI Brain service which uses it
      (async () => {
        // ChromaDB health will be inferred from AI Brain service health
        // since AI Brain depends on ChromaDB for vector storage
        results['chromadb'] = {
          status: 'unknown',
          service: 'chromadb',
          message: 'Status inferred from AI Brain service health'
        };
      })(),
    ];

    // Wait for all health checks to complete
    await Promise.allSettled([...healthChecks, ...infraChecks]);

    // Infer postgres and redis status from service health checks
    const servicesWithDbChecks = ['identity-service', 'asset-service', 'automation-service', 'communication-service'];
    let postgresHealthy = false;
    let redisHealthy = false;

    servicesWithDbChecks.forEach(serviceName => {
      const serviceHealth = results[serviceName];
      if (serviceHealth && serviceHealth.checks) {
        serviceHealth.checks.forEach((check: any) => {
          if (check.name === 'database' && check.status === 'healthy') {
            postgresHealthy = true;
          }
          if (check.name === 'redis' && check.status === 'healthy') {
            redisHealthy = true;
          }
        });
      }
    });

    // Update postgres and redis status based on service checks
    if (results['postgres']) {
      results['postgres'].status = postgresHealthy ? 'healthy' : 'unhealthy';
      results['postgres'].message = postgresHealthy ? 'Database connectivity confirmed via services' : 'Database issues detected in service checks';
    }

    if (results['redis']) {
      results['redis'].status = redisHealthy ? 'healthy' : 'unhealthy';
      results['redis'].message = redisHealthy ? 'Redis connectivity confirmed via services' : 'Redis issues detected in service checks';
    }

    // Infer ChromaDB status from AI Brain service health
    const aiBrainHealth = results['ai-brain'];
    if (results['chromadb'] && aiBrainHealth) {
      if (aiBrainHealth.status === 'healthy') {
        results['chromadb'].status = 'healthy';
        results['chromadb'].message = 'ChromaDB connectivity confirmed via AI Brain service';
      } else {
        results['chromadb'].status = 'unhealthy';
        results['chromadb'].message = 'ChromaDB issues detected - AI Brain service unhealthy';
      }
    }

    return results;
  },

  checkService: async (service: string): Promise<{ status: string; service: string; responseTime?: number; error?: string }> => {
    // For individual service checks, get all services and extract the specific one
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
      // Get system stats from individual service health checks
      const allServices = await healthApi.checkAllServices();
      const servicesList = Object.values(allServices);
      
      const healthyServices = servicesList.filter((service: any) => service.status === 'healthy').length;
      const unhealthyServices = servicesList.filter((service: any) => service.status === 'unhealthy').length;
      const totalServices = servicesList.length;
      
      // Determine overall status
      let overallStatus = 'healthy';
      if (unhealthyServices > 0) {
        overallStatus = unhealthyServices >= totalServices / 2 ? 'unhealthy' : 'degraded';
      }
      
      const stats = {
        overall_status: overallStatus,
        services_count: totalServices,
        healthy_services: healthyServices,
        unhealthy_services: unhealthyServices,
        timestamp: new Date().toISOString(),
        message: `System health check completed - ${healthyServices}/${totalServices} services healthy`
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

// SMTP Settings API (using channels)
export const smtpApi = {
  getSMTPSettings: async (): Promise<SMTPSettingsResponse> => {
    // Get SMTP channel from channels API
    const response = await api.get('/api/v1/channels');
    const channels = response.data.channels || [];
    const smtpChannel = channels.find((channel: any) => channel.channel_type === 'smtp');
    
    if (!smtpChannel) {
      return {
        success: true,
        data: null,
        message: 'No SMTP configuration found'
      };
    }
    
    // Transform channel data to SMTP settings format
    const config = smtpChannel.configuration || {};
    return {
      success: true,
      data: {
        id: smtpChannel.id,
        host: config.host || '',
        port: config.port || 587,
        username: config.username || '',
        password: '***', // Never return actual password
        use_tls: config.use_tls !== false,
        use_ssl: config.use_ssl || false,
        from_email: config.from_email || '',
        from_name: config.from_name || 'OpsConductor',
        is_active: smtpChannel.is_active,
        is_configured: !!config.host && !!config.from_email,
        created_at: smtpChannel.created_at,
        updated_at: smtpChannel.updated_at
      },
      message: 'SMTP settings retrieved successfully'
    };
  },

  updateSMTPSettings: async (settings: SMTPSettings): Promise<SMTPSettingsResponse> => {
    // First, check if SMTP channel exists
    const channelsResponse = await api.get('/api/v1/channels');
    const channels = channelsResponse.data.channels || [];
    const existingSmtpChannel = channels.find((channel: any) => channel.channel_type === 'smtp');
    
    const channelData = {
      name: 'SMTP Email',
      channel_type: 'smtp',
      configuration: {
        host: settings.host,
        port: settings.port,
        username: settings.username,
        password: settings.password,
        use_tls: settings.use_tls,
        use_ssl: settings.use_ssl || false,
        from_email: settings.from_email,
        from_name: settings.from_name || 'OpsConductor'
      },
      is_active: true
    };
    
    let response;
    if (existingSmtpChannel) {
      // Update existing channel
      response = await api.put(`/api/v1/channels/${existingSmtpChannel.id}`, channelData);
    } else {
      // Create new channel
      response = await api.post('/api/v1/channels', channelData);
    }
    
    const channel = response.data.data || response.data;
    const config = channel.configuration || {};
    
    return {
      success: true,
      data: {
        id: channel.id,
        host: config.host,
        port: config.port,
        username: config.username,
        password: '***', // Never return actual password
        use_tls: config.use_tls,
        use_ssl: config.use_ssl,
        from_email: config.from_email,
        from_name: config.from_name,
        is_active: channel.is_active,
        is_configured: true,
        created_at: channel.created_at,
        updated_at: channel.updated_at
      },
      message: 'SMTP settings saved successfully'
    };
  },

  testSMTPSettings: async (testRequest: SMTPTestRequest): Promise<SMTPTestResponse> => {
    try {
      const response: AxiosResponse<SMTPTestResponse> = await api.post('/api/v1/notifications/smtp/test', testRequest);
      return response.data;
    } catch (error: any) {
      console.error('SMTP test failed:', error);
      return {
        success: false,
        message: error.response?.data?.detail || 'Failed to test SMTP settings'
      };
    }
  }
};





// Communication Channels API
export const communicationApi = {
  // Get all channels
  getChannels: async (): Promise<CommunicationChannel[]> => {
    try {
      const response: AxiosResponse<{ channels: CommunicationChannel[] }> = await api.get('/api/v1/channels');
      return response.data.channels;
    } catch (error: any) {
      console.error('Failed to fetch communication channels:', error);
      throw error;
    }
  },

  // Get channel by type
  getChannelByType: async (channelType: string): Promise<CommunicationChannel | null> => {
    try {
      const channels = await communicationApi.getChannels();
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

// AI Chat API
export const aiApi = {
  chat: async (request: {
    message: string;
    user_id?: number;
    conversation_id?: string;
    debug_mode?: boolean;
  }): Promise<{
    response: string;
    intent: string;
    confidence: number;
    conversation_id?: string;
    job_id?: string;
    execution_id?: string;
    automation_job_id?: number;
    workflow?: any;
    execution_started: boolean;
    _routing?: {
      service: string;
      service_type: string;
      response_time: number;
      cached: boolean;
    };
    intent_classification?: {
      intent_type: string;
      confidence: number;
      method: string;
      alternatives: Array<{
        intent: string;
        confidence: number;
      }>;
      entities: Array<{
        value: string;
        type: string;
        confidence: number;
        normalized_value?: string;
      }>;
      context_analysis: {
        confidence_score: number;
        risk_level: string;
        requirements_count: number;
        recommendations: string[];
      };
      reasoning: string;
      metadata: {
        engine: string;
        success: boolean;
      };
    };
    timestamp?: string;
    error?: string;
  }> => {
    console.log('🚀 Sending AI chat request:', request);
    const response = await api.post('/api/v1/ai/chat', request);
    console.log('✅ AI chat response received:', response.data);
    return response.data;
  },

  health: async (): Promise<{
    status: string;
    services: Record<string, any>;
    timestamp: string;
  }> => {
    const response = await api.get('/api/v1/ai/health');
    return response.data;
  },

  monitoringDashboard: async (): Promise<{
    current: {
      services: Record<string, any>;
      overall_health: string;
    };
    history: any[];
    analysis: {
      overall_health: string;
      alerts: Array<{
        severity: string;
        service: string;
        message: string;
      }>;
      recommendations: string[];
    };
    statistics: Record<string, any>;
  }> => {
    const response = await api.get('/api/v1/ai/monitoring/dashboard');
    return response.data;
  },

  resetCircuitBreaker: async (serviceName: string): Promise<void> => {
    await api.post(`/api/v1/ai/circuit-breaker/reset/${serviceName}`);
  },

  getKnowledgeStats: async (): Promise<any> => {
    const response = await api.get('/api/v1/ai/knowledge-stats');
    return response.data;
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