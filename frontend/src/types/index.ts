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
  to_email: string;
  subject?: string;
  message?: string;
}

export interface SMTPTestResponse {
  success: boolean;
  message: string;
}

// Communication Channel Types
export interface CommunicationChannel {
  id: number;
  name: string;
  channel_type: 'email' | 'slack' | 'teams' | 'discord' | 'webhook';
  configuration: Record<string, any>;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CommunicationChannelCreate {
  name: string;
  channel_type: 'email' | 'slack' | 'teams' | 'discord' | 'webhook';
  configuration: Record<string, any>;
  is_active?: boolean;
}

export interface CommunicationChannelUpdate {
  name?: string;
  channel_type?: 'email' | 'slack' | 'teams' | 'discord' | 'webhook';
  configuration?: Record<string, any>;
  is_active?: boolean;
}

// Slack Configuration
export interface SlackSettings {
  webhook_url: string;
  channel?: string;
  username?: string;
  icon_emoji?: string;
  icon_url?: string;
}

// Microsoft Teams Configuration
export interface TeamsSettings {
  webhook_url: string;
  title?: string;
  theme_color?: string;
}

// Discord Configuration
export interface DiscordSettings {
  webhook_url: string;
  username?: string;
  avatar_url?: string;
}

// Generic Webhook Configuration
export interface WebhookSettings {
  url: string;
  method: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  auth_type?: 'none' | 'basic' | 'bearer' | 'api_key';
  auth_config?: {
    username?: string;
    password?: string;
    token?: string;
    api_key?: string;
    api_key_header?: string;
  };
  payload_template?: string;
  content_type?: string;
}

// Test Request/Response for all communication methods
export interface CommunicationTestRequest {
  channel_type: 'email' | 'slack' | 'teams' | 'discord' | 'webhook';
  test_message: string;
  test_subject?: string;
  recipient?: string; // For email
}

export interface CommunicationTestResponse {
  success: boolean;
  message: string;
  details?: string;
}

// Role Types
export interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  name: string;
  description: string;
  permissions: string[];
  is_active?: boolean;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permissions?: string[];
  is_active?: boolean;
}

export interface RoleListResponse {
  data: Role[];
  meta: {
    total_items: number;
    skip: number;
    limit: number;
    has_more: boolean;
  };
  total: number; // For backward compatibility
}



