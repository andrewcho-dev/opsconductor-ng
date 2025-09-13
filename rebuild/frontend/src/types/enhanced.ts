// Enhanced types for multi-service target architecture

// Service Definition Types
export interface ServiceDefinition {
  id: number;
  service_type: string;
  display_name: string;
  category: string;
  default_port: number;
  is_secure_by_default: boolean;
  description?: string;
  is_common: boolean;
  created_at: string;
}

export interface ServiceDefinitionResponse {
  services: ServiceDefinition[];
  total: number;
}

// Target Service Types
export interface TargetServiceCreate {
  service_type: string;
  port: number;
  is_default?: boolean;
  is_secure?: boolean;
  is_enabled?: boolean;
  notes?: string;
  
  // Embedded credential fields
  credential_type?: string; // 'username_password', 'ssh_key', 'api_key', 'bearer_token'
  username?: string;
  password?: string;
  private_key?: string;
  public_key?: string;
  api_key?: string;
  bearer_token?: string;
  certificate?: string;
  passphrase?: string;
  domain?: string; // For Windows domain authentication
}

export interface TargetServiceUpdate {
  port?: number;
  is_secure?: boolean;
  is_enabled?: boolean;
  notes?: string;
}

export interface TargetService {
  id: number;
  service_type: string;
  port: number;
  is_default: boolean;
  is_secure: boolean;
  is_enabled: boolean;
  notes?: string;
  connection_status?: 'connected' | 'failed' | 'unknown';
  
  // Embedded credential fields (masked in responses)
  credential_type?: string;
  username?: string;
  password?: string; // Will be "***" if set
  private_key?: string; // Will be "***" if set
  public_key?: string;
  api_key?: string; // Will be "***" if set
  bearer_token?: string; // Will be "***" if set
  certificate?: string; // Will be "***" if set
  passphrase?: string; // Will be "***" if set
  domain?: string;
  
  created_at: string;
}

// Target Credential Types
export interface TargetCredentialCreate {
  credential_id: number;
  service_types?: string[];
  is_primary?: boolean;
}

export interface TargetCredential {
  id: number;
  credential_id: number;
  credential_name: string;
  credential_type: string;
  service_types: string[];
  is_primary: boolean;
  created_at: string;
}

// Enhanced Target Types
export interface EnhancedTargetCreate {
  name: string;
  hostname: string;
  ip_address?: string;
  os_type?: 'windows' | 'linux' | 'unix' | 'macos' | 'other';
  os_version?: string;
  description?: string;
  tags?: string[];
  services?: TargetServiceCreate[];
}

export interface EnhancedTargetUpdate {
  name?: string;
  hostname?: string;
  ip_address?: string;
  os_type?: 'windows' | 'linux' | 'unix' | 'macos' | 'other';
  os_version?: string;
  description?: string;
  tags?: string[];
  services?: TargetServiceCreate[];
}

export interface EnhancedTarget {
  id: number;
  name: string;
  hostname: string;
  ip_address?: string;
  os_type?: string;
  os_version?: string;
  description?: string;
  tags: string[];
  services: TargetService[];
  created_at: string;
  updated_at?: string;
}

export interface EnhancedTargetListResponse {
  targets: EnhancedTarget[];
  total: number;
}

// Bulk operations
export interface BulkServiceOperation {
  target_id: number;
  service_types: string[];
  operation: 'enable' | 'disable';
}

export interface BulkServiceResponse {
  success: boolean;
  updated_services: number;
  message: string;
}

// Migration types
export interface MigrationStatus {
  success: boolean;
  services_created: number;
  credentials_created: number;
  message: string;
}

// UI State types
export interface ServiceFormData {
  service_type: string;
  port: number;
  is_default: boolean;
  is_secure: boolean;
  is_enabled: boolean;
  notes: string;
  
  // Embedded credential fields
  credential_type: string;
  username: string;
  password: string;
  private_key: string;
  public_key: string;
  api_key: string;
  bearer_token: string;
  certificate: string;
  passphrase: string;
  domain: string;
}

export interface CredentialFormData {
  credential_id: number;
  service_types: string[];
  is_primary: boolean;
}

// Filter types
export interface TargetFilters {
  os_type?: string;
  service_type?: string;
  tag?: string;
  category?: string;
}

// Service categories for UI organization
export const SERVICE_CATEGORIES = {
  remote: 'Remote Management',
  web: 'Web Services',
  file: 'File Transfer',
  database: 'Database',
  network: 'Network',
  directory: 'Directory Services',
  email: 'Email Services',
  application: 'Applications',
  monitoring: 'Monitoring',
  virtualization: 'Virtualization',
  cloud: 'Cloud Services',
  other: 'Other'
} as const;

export type ServiceCategory = keyof typeof SERVICE_CATEGORIES;