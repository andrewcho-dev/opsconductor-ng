/**
 * Step Library Service
 * Manages dynamic loading of step libraries and their definitions
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost';
const STEP_LIBRARIES_SERVICE_URL = `${API_BASE_URL}:3011`;

// Types
export interface StepParameter {
  type: string;
  required: boolean;
  default?: any;
  description: string;
  validation?: Record<string, any>;
  options?: any[];
}

export interface StepDefinition {
  id: string;
  name: string;
  type: string;
  category: string;
  library: string;
  library_id: number;
  icon: string;
  description: string;
  color: string;
  inputs: number;
  outputs: number;
  parameters: Record<string, StepParameter>;
  platform_support: string[];
  required_permissions: string[];
  examples: any[];
  tags: string[];
}

export interface LibraryInfo {
  id: number;
  name: string;
  version: string;
  display_name: string;
  description: string;
  author: string;
  is_enabled: boolean;
  is_premium: boolean;
  installation_date: string;
  last_used?: string;
  step_count: number;
  status: string;
}

export interface StepLibraryResponse {
  steps: StepDefinition[];
  total_count: number;
  categories: string[];
  libraries: string[];
}

export interface LibraryInstallResult {
  library_id: number;
  name: string;
  version: string;
  step_count: number;
  status: string;
}

class StepLibraryService {
  private cache: Map<string, any> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private listeners: Set<() => void> = new Set();

  /**
   * Get all available step definitions
   */
  async getAvailableSteps(
    category?: string,
    library?: string,
    platform?: string,
    forceRefresh = false
  ): Promise<StepLibraryResponse> {
    const cacheKey = `steps_${category || 'all'}_${library || 'all'}_${platform || 'all'}`;
    
    // Check cache first
    if (!forceRefresh && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (library) params.append('library', library);
      if (platform) params.append('platform', platform);

      const response = await axios.get(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/steps?${params.toString()}`
      );

      const data: StepLibraryResponse = response.data;
      
      // Cache the result
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      return data;
    } catch (error) {
      console.error('Failed to fetch step definitions:', error);
      
      // Return fallback core steps if service is unavailable
      return this.getFallbackSteps();
    }
  }

  /**
   * Get all installed libraries
   */
  async getInstalledLibraries(enabledOnly = false): Promise<LibraryInfo[]> {
    const cacheKey = `libraries_${enabledOnly}`;
    
    // Check cache
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const params = enabledOnly ? '?enabled_only=true' : '';
      const response = await axios.get(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/libraries${params}`
      );

      const data: LibraryInfo[] = response.data;
      
      // Cache the result
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      return data;
    } catch (error) {
      console.error('Failed to fetch libraries:', error);
      return [];
    }
  }

  /**
   * Install a new library from file upload
   */
  async installLibrary(file: File, licenseKey?: string): Promise<LibraryInstallResult> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (licenseKey) {
        formData.append('license_key', licenseKey);
      }

      const response = await axios.post(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/libraries/install`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // Clear cache after installation
      this.clearCache();
      this.notifyListeners();

      return response.data;
    } catch (error: any) {
      console.error('Failed to install library:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to install library'
      );
    }
  }

  /**
   * Uninstall a library
   */
  async uninstallLibrary(libraryId: number): Promise<void> {
    try {
      await axios.delete(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/libraries/${libraryId}`
      );

      // Clear cache after uninstallation
      this.clearCache();
      this.notifyListeners();
    } catch (error: any) {
      console.error('Failed to uninstall library:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to uninstall library'
      );
    }
  }

  /**
   * Enable or disable a library
   */
  async toggleLibrary(libraryId: number, enabled: boolean): Promise<void> {
    try {
      await axios.put(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/libraries/${libraryId}/toggle`,
        null,
        {
          params: { enabled }
        }
      );

      // Clear cache after toggle
      this.clearCache();
      this.notifyListeners();
    } catch (error: any) {
      console.error('Failed to toggle library:', error);
      throw new Error(
        error.response?.data?.detail || 'Failed to toggle library'
      );
    }
  }

  /**
   * Get library details
   */
  async getLibraryDetails(libraryId: number): Promise<any> {
    try {
      const response = await axios.get(
        `${STEP_LIBRARIES_SERVICE_URL}/api/v1/libraries/${libraryId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch library details:', error);
      throw error;
    }
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Add a listener for library changes
   */
  addChangeListener(listener: () => void): void {
    this.listeners.add(listener);
  }

  /**
   * Remove a change listener
   */
  removeChangeListener(listener: () => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Notify all listeners of changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener());
  }

  /**
   * Get fallback steps when service is unavailable
   */
  private getFallbackSteps(): StepLibraryResponse {
    const fallbackSteps: StepDefinition[] = [
      {
        id: 'core.flow.start',
        name: 'Start',
        type: 'flow.start',
        category: 'flow',
        library: 'core',
        library_id: 1,
        icon: 'play',
        description: 'Job start point',
        color: '#28a745',
        inputs: 0,
        outputs: 1,
        parameters: {},
        platform_support: ['windows', 'linux', 'macos'],
        required_permissions: [],
        examples: [],
        tags: ['flow', 'start']
      },
      {
        id: 'core.flow.end',
        name: 'End',
        type: 'flow.end',
        category: 'flow',
        library: 'core',
        library_id: 1,
        icon: 'square',
        description: 'Job end point',
        color: '#dc3545',
        inputs: 1,
        outputs: 0,
        parameters: {},
        platform_support: ['windows', 'linux', 'macos'],
        required_permissions: [],
        examples: [],
        tags: ['flow', 'end']
      },
      {
        id: 'core.target.assign',
        name: 'Target Assignment',
        type: 'target.assign',
        category: 'targets',
        library: 'core',
        library_id: 1,
        icon: 'target',
        description: 'Assign job execution to specific target',
        color: '#28a745',
        inputs: 1,
        outputs: 1,
        parameters: {
          target_names: {
            type: 'string',
            required: true,
            description: 'Target names (comma-separated)',
            default: ''
          }
        },
        platform_support: ['windows', 'linux', 'macos'],
        required_permissions: [],
        examples: [],
        tags: ['target', 'assignment']
      }
    ];

    return {
      steps: fallbackSteps,
      total_count: fallbackSteps.length,
      categories: ['flow', 'targets'],
      libraries: ['core']
    };
  }

  /**
   * Convert step definition to node template format for compatibility
   */
  convertToNodeTemplate(step: StepDefinition): any {
    return {
      id: step.type,
      name: step.name,
      type: step.type,
      category: step.category,
      library: step.library,
      icon: step.icon,
      description: step.description,
      inputs: step.inputs,
      outputs: step.outputs,
      defaultConfig: this.generateDefaultConfig(step.parameters),
      color: step.color,
      parameters: step.parameters
    };
  }

  /**
   * Generate default configuration from parameters
   */
  private generateDefaultConfig(parameters: Record<string, StepParameter>): any {
    const config: any = {};
    
    Object.entries(parameters).forEach(([key, param]) => {
      if (param.default !== undefined) {
        config[key] = param.default;
      } else if (param.required) {
        // Set appropriate default based on type
        switch (param.type) {
          case 'string':
            config[key] = '';
            break;
          case 'number':
            config[key] = 0;
            break;
          case 'boolean':
            config[key] = false;
            break;
          case 'array':
            config[key] = [];
            break;
          case 'object':
            config[key] = {};
            break;
          default:
            config[key] = null;
        }
      }
    });

    return config;
  }

  /**
   * Check if step libraries service is available
   */
  async checkServiceHealth(): Promise<boolean> {
    try {
      const response = await axios.get(`${STEP_LIBRARIES_SERVICE_URL}/health`, {
        timeout: 5000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const stepLibraryService = new StepLibraryService();
export default stepLibraryService;