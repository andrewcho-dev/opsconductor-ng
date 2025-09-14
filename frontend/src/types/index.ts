// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// User Types
export interface User {
  id: number;
  email: string;
  username: string;
  role: 'admin' | 'operator' | 'viewer';
  permissions?: string[];
  is_admin: boolean; // For backward compatibility
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  first_name?: string;
  last_name?: string;
  telephone?: string;
  title?: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  role: 'admin' | 'operator' | 'viewer';
  is_admin?: boolean;
  is_active?: boolean;
  first_name?: string;
  last_name?: string;
  telephone?: string;
  title?: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
  password?: string;
  role?: 'admin' | 'operator' | 'viewer';
  is_admin?: boolean;
  is_active?: boolean;
  first_name?: string;
  last_name?: string;
  telephone?: string;
  title?: string;
}

// Auth Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Credential Types
export interface Credential {
  id: number;
  name: string;
  description?: string;
  credential_type: 'password' | 'key' | 'certificate';
  // Authentication fields (non-sensitive)
  username?: string;
  domain?: string;
  // Validity fields
  valid_from?: string;
  valid_until?: string;
  next_rotation_date?: string;
  // System fields
  created_at: string;
  updated_at?: string;
}

export interface CredentialCreate {
  name: string;
  description?: string;
  credential_type: 'password' | 'key' | 'certificate';
  // Authentication fields
  username?: string;
  password?: string;
  domain?: string;
  private_key?: string;
  public_key?: string;
  certificate?: string;
  certificate_chain?: string;
  passphrase?: string;
  // Validity fields
  valid_from?: string;
  valid_until?: string;
  next_rotation_date?: string;
}

export interface CredentialDecrypted extends Credential {
  // Sensitive fields (only returned when explicitly decrypting)
  password?: string;
  private_key?: string;
  public_key?: string;
  certificate?: string;
  certificate_chain?: string;
  passphrase?: string;
}

// Target Types
export interface Target {
  id: number;
  name: string;
  hostname: string;
  ip_address?: string;
  protocol: string;
  port: number;
  os_type: string;
  credential_ref: number;
  tags: string[];
  metadata: Record<string, any>;
  depends_on: number[];
  created_at: string;
}

export interface TargetCreate {
  name: string;
  hostname: string;
  ip_address?: string;
  protocol: string;
  port: number;
  os_type: string;
  credential_ref: number;
  tags?: string[];
  metadata?: Record<string, any>;
  depends_on?: number[];
}

// Job Types
export interface Job {
  id: number;
  name: string;
  description?: string;
  workflow_definition: Record<string, any>;
  schedule_expression?: string;
  is_enabled: boolean;
  tags: string[];
  metadata: Record<string, any>;
  created_by: number;
  updated_by: number;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  name: string;
  description?: string;
  workflow_definition?: Record<string, any>;
  schedule_expression?: string;
  is_enabled?: boolean;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface JobStep {
  id?: string;
  type: string;
  name?: string;
  target: string;
  shell?: string;
  command?: string;
  timeoutSec: number;
  config?: Record<string, any>;
}

export interface JobRun {
  id: number;
  job_id: number;
  job_name: string;
  execution_id: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'canceled';
  trigger_type: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  started_by?: number;
  created_at: string;
}

export interface JobRunStep {
  id: number;
  job_execution_id?: number;
  step_id: string;
  name: string;  // API returns 'name' not 'step_name'
  type: string;  // API returns 'type' not 'step_type'
  status: string;
  output: Record<string, any>;  // API returns 'output' not 'output_data'
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  execution_order?: number;
  // Legacy fields for backward compatibility
  step_name?: string;
  step_type?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
}

export interface WinRMTestResult {
  test: {
    status: 'success' | 'error';
    details: {
      message?: string;
      whoami?: string;
      powershellVersion?: string;
      hostname?: string;
      port?: number;
      transport?: string;
    };
  };
  note?: string;
}

export interface SSHTestResult {
  test: {
    status: 'success' | 'error';
    details: {
      message?: string;
      whoami?: string;
      hostname?: string;
      port?: number;
      os_info?: {
        name?: string;
        version?: string;
        kernel?: string;
        architecture?: string;
        uptime?: string;
      };
    };
  };
  note?: string;
}

// List Response Types
export interface UserListResponse {
  data: User[];
  meta: {
    total_items: number;
    skip: number;
    limit: number;
    has_more: boolean;
  };
  total: number; // For backward compatibility
}

export interface CredentialListResponse {
  credentials: Credential[];
  total: number;
}

export interface TargetListResponse {
  targets: Target[];
  total: number;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  skip: number;
  limit: number;
}

export interface JobRunListResponse {
  executions: JobRun[];
  total: number;
  skip: number;
  limit: number;
}





export interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  use_tls: boolean;
  use_ssl?: boolean;
  from_email: string;
  from_name: string;
}

export interface SMTPSettingsData extends Omit<SMTPSettings, 'password'> {
  id?: number;
  password: string; // Masked
  use_ssl?: boolean;
  is_active?: boolean;
  is_configured: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SMTPSettingsResponse {
  success: boolean;
  data: SMTPSettingsData | null;
  message: string;
}

export interface SMTPTestRequest {
  test_email: string;
}

export interface SMTPTestResponse {
  success: boolean;
  message: string;
}



