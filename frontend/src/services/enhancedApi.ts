import axios, { AxiosResponse } from 'axios';
import { getServiceUrl, getApiBaseUrl } from './api';
import {
  ServiceDefinitionResponse,
  TargetServiceCreate, TargetServiceUpdate, TargetService,
  TargetCredentialCreate, TargetCredential,
  EnhancedTarget, EnhancedTargetCreate, EnhancedTargetUpdate, EnhancedTargetListResponse,
  BulkServiceOperation, BulkServiceResponse,
  MigrationStatus,
  TargetFilters
} from '../types/enhanced';

// Create axios instance for targets service
const enhancedApi = axios.create({
  baseURL: getServiceUrl('targets'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token (same as main api.ts)
enhancedApi.interceptors.request.use(
  (config) => {
    // Always get fresh token from localStorage
    const currentToken = localStorage.getItem('access_token');
    if (currentToken) {
      config.headers.Authorization = `Bearer ${currentToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling (same as main api.ts)
enhancedApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle both 401 (Unauthorized) and 403 (Forbidden) errors
    if ((error.response?.status === 401 || error.response?.status === 403) && !originalRequest._retry) {
      originalRequest._retry = true;

      const currentRefreshToken = localStorage.getItem('refresh_token');
      if (currentRefreshToken) {
        try {
          const response = await axios.post(`${getApiBaseUrl()}/refresh`, {
            refresh_token: currentRefreshToken
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          
          // Update tokens in localStorage
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          // Retry the original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return enhancedApi(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Service Definitions API
export const serviceDefinitionApi = {
  list: async (category?: string, commonOnly?: boolean): Promise<ServiceDefinitionResponse> => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (commonOnly) params.append('common_only', 'true');
    
    const response: AxiosResponse<ServiceDefinitionResponse> = await enhancedApi.get(
      `/service-definitions?${params.toString()}`
    );
    return response.data;
  },

  getCategories: async (): Promise<string[]> => {
    const response = await serviceDefinitionApi.list();
    const categories = [...new Set(response.services.map(s => s.category))];
    return categories.sort();
  }
};

// Enhanced Targets API
export const enhancedTargetApi = {
  list: async (filters?: TargetFilters, skip = 0, limit = 100): Promise<EnhancedTargetListResponse> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    if (filters?.os_type) params.append('os_type', filters.os_type);
    if (filters?.service_type) params.append('service_type', filters.service_type);
    if (filters?.tag) params.append('tag', filters.tag);
    
    const response: AxiosResponse<EnhancedTargetListResponse> = await enhancedApi.get(
      `/targets?${params.toString()}`
    );
    return response.data;
  },

  get: async (id: number): Promise<EnhancedTarget> => {
    const response: AxiosResponse<EnhancedTarget> = await enhancedApi.get(`/targets/${id}`);
    return response.data;
  },

  create: async (target: EnhancedTargetCreate): Promise<EnhancedTarget> => {
    const response: AxiosResponse<EnhancedTarget> = await enhancedApi.post('/targets', target);
    return response.data;
  },

  update: async (id: number, target: EnhancedTargetUpdate): Promise<EnhancedTarget> => {
    const response: AxiosResponse<EnhancedTarget> = await enhancedApi.put(`/targets/${id}`, target);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await enhancedApi.delete(`/targets/${id}`);
  }
};

// Target Services API
export const targetServiceApi = {
  add: async (targetId: number, service: TargetServiceCreate): Promise<TargetService> => {
    const response: AxiosResponse<TargetService> = await enhancedApi.post(
      `/targets/${targetId}/services`, 
      service
    );
    return response.data;
  },

  update: async (targetId: number, serviceId: number, service: TargetServiceUpdate): Promise<TargetService> => {
    const response: AxiosResponse<TargetService> = await enhancedApi.put(
      `/targets/${targetId}/services/${serviceId}`, 
      service
    );
    return response.data;
  },

  delete: async (targetId: number, serviceId: number): Promise<void> => {
    await enhancedApi.delete(`/targets/${targetId}/services/${serviceId}`);
  },

  testConnection: async (serviceId: number): Promise<any> => {
    const response = await enhancedApi.post(`/targets/services/${serviceId}/test`);
    return response.data;
  },

  bulkOperation: async (operation: BulkServiceOperation): Promise<BulkServiceResponse> => {
    const response: AxiosResponse<BulkServiceResponse> = await enhancedApi.post(
      '/targets/services/bulk', 
      operation
    );
    return response.data;
  }
};

// Target Credentials API
export const targetCredentialApi = {
  add: async (targetId: number, credential: TargetCredentialCreate): Promise<TargetCredential> => {
    const response: AxiosResponse<TargetCredential> = await enhancedApi.post(
      `/targets/${targetId}/credentials`, 
      credential
    );
    return response.data;
  },

  update: async (targetId: number, credentialId: number, credential: Partial<TargetCredentialCreate>): Promise<TargetCredential> => {
    const response: AxiosResponse<TargetCredential> = await enhancedApi.put(
      `/targets/${targetId}/credentials/${credentialId}`, 
      credential
    );
    return response.data;
  },

  delete: async (targetId: number, credentialId: number): Promise<void> => {
    await enhancedApi.delete(`/targets/${targetId}/credentials/${credentialId}`);
  }
};

// Migration API
export const migrationApi = {
  migrateSchema: async (): Promise<MigrationStatus> => {
    const response: AxiosResponse<MigrationStatus> = await enhancedApi.post('/targets/migrate-schema');
    return response.data;
  }
};

// Health check
export const enhancedHealthApi = {
  check: async (): Promise<any> => {
    const response = await enhancedApi.get('/targets/health');
    return response.data;
  }
};

export default enhancedApi;