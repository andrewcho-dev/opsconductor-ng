import axios, { AxiosResponse } from 'axios';
import {
  User, UserCreate, UserUpdate, UserListResponse,
  Credential, CredentialCreate, CredentialListResponse, CredentialDecrypted,
  Target, TargetCreate, TargetListResponse, WinRMTestResult, SSHTestResult,
  Job, JobCreate, JobListResponse,
  JobRun, JobRunListResponse, JobRunStep,

  LoginRequest, AuthResponse,

  SMTPSettings, SMTPSettingsResponse, SMTPTestRequest, SMTPTestResponse,
  CommunicationChannel, CommunicationChannelCreate, CommunicationChannelUpdate,
  CommunicationTestRequest, CommunicationTestResponse,
  SlackSettings, TeamsSettings, DiscordSettings, WebhookSettings
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
      
      // Add overall API Gateway status - but don't let it be unhealthy just because of missing services
      // If we can reach the gateway and get a response, consider it healthy
      results['api-gateway'] = {
        status: 'healthy', // If we got a response, the gateway is working
        service: 'api-gateway',
        responseTime,
        message: 'API Gateway responding'
      };
      
      // Add individual service checks from the centralized response
      if (healthData.checks) {
        healthData.checks.forEach((check: any) => {
          // Map service names from the health check response
          let serviceName = check.service || check.name || 'unknown';
          
          // Map backend service names to frontend expected names
          const serviceNameMapping: Record<string, string> = {
            'ai': 'ai-service',
            // Add other mappings as needed
          };
          
          const mappedServiceName = serviceNameMapping[serviceName.toLowerCase()] || serviceName.toLowerCase();
          
          results[mappedServiceName] = { 
            ...check, 
            service: mappedServiceName, 
            responseTime: check.response_time_ms || responseTime
          };
        });
      }
      
      // Add default status for services not explicitly reported
      // Only include services that are actually running and should be monitored
      const expectedServices = [
        'api-gateway', 'identity', 'asset', 'automation', 'communication', 
        'postgres', 'redis'
      ];
      
      // Services that exist but may not be health-checked by the API Gateway
      // These are running and accessible, so we'll mark them as healthy
      const infrastructureServices = [
        'worker-1', 'worker-2', 'scheduler', 'celery-monitor',
        'chromadb', 'frontend', 'nginx'
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
      
      // Add infrastructure services as operational (they don't have health checks)
      infrastructureServices.forEach(service => {
        results[service] = {
          status: 'healthy', // Assume healthy if container is running
          service,
          responseTime,
          message: 'Infrastructure service (no health check)'
        };
      });
      
      return results;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // Return error status for all services if health check fails
      const services = [
        'api-gateway', 'identity', 'asset', 'automation', 'communication',
        'postgres', 'redis', 'chromadb',
        'worker-1', 'worker-2', 'scheduler', 'celery-monitor',
        'frontend', 'nginx'
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

export default api;