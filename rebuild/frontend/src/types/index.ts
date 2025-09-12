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
  job_execution_id: number;
  step_id: string;
  step_name: string;
  step_type: string;
  status: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  execution_order: number;
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



// Notification Types
export interface NotificationPreferences {
  email_enabled: boolean;
  email_address?: string;
  webhook_enabled: boolean;
  webhook_url?: string;
  slack_enabled: boolean;
  slack_webhook_url?: string;
  slack_channel?: string;
  teams_enabled: boolean;
  teams_webhook_url?: string;
  notify_on_success: boolean;
  notify_on_failure: boolean;
  notify_on_start: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  quiet_hours_timezone: string;
}

export interface NotificationPreferencesResponse extends NotificationPreferences {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationChannel {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  is_active: boolean;
  configuration_schema?: Record<string, any>;
  created_at: string;
}

export interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  use_tls: boolean;
  from_email: string;
  from_name: string;
}

export interface SMTPSettingsResponse extends Omit<SMTPSettings, 'password'> {
  password: string; // Masked
  is_configured: boolean;
}

export interface SMTPTestRequest {
  test_email: string;
}

export interface SMTPTestResponse {
  success: boolean;
  message: string;
}

// Discovery Types
export interface DiscoveryJob {
  id: number;
  name: string;
  target_range: string;
  scan_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  configuration: DiscoveryConfig;
  results: Record<string, any>;
  created_by: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface DiscoveryService {
  name: string;
  port: number;
  protocol: 'tcp' | 'udp';
  category: string;
  enabled: boolean;
}

export interface DiscoveryConfig {
  cidr_ranges?: string[];
  services?: DiscoveryService[];
  ports?: string;
  os_detection?: boolean;
  timeout?: number;
  // AD Query specific
  domain?: string;
  ou?: string;
  // Cloud API specific
  provider?: 'aws' | 'azure' | 'gcp';
  region?: string;
  credentials?: Record<string, any>;
}

export interface DiscoveryResultsSummary {
  total_hosts?: number;
  windows_hosts?: number;
  linux_hosts?: number;
  duplicates_found?: number;
  services_detected?: number;
}

export interface DiscoveredTarget {
  id: number;
  discovery_job_id: number;
  hostname?: string;
  ip_address: string;
  os_type?: string;
  os_version?: string;
  services: DiscoveredService[];
  preferred_service?: DiscoveredService;
  system_info: Record<string, any>;
  duplicate_status: 'unique' | 'duplicate' | 'similar';
  existing_target_id?: number;
  import_status: 'pending' | 'imported' | 'ignored' | 'duplicate_skipped';
  discovered_at: string;
}

export interface DiscoveredService {
  protocol: string;
  port: number;
  service_name?: string;
  version?: string;
  is_secure?: boolean;
}

export interface DiscoveryTemplate {
  id: number;
  name: string;
  description?: string;
  discovery_type: string;
  config: DiscoveryConfig;
  created_by: number;
  created_at: string;
}

export interface DiscoveryJobCreate {
  name: string;
  discovery_type: string;
  config: DiscoveryConfig;
}

export interface DiscoveryJobUpdate {
  name?: string;
  config?: DiscoveryConfig;
}

export interface DiscoveredTargetUpdate {
  hostname?: string;
  os_type?: string;
  os_version?: string;
  import_status?: 'pending' | 'imported' | 'ignored' | 'duplicate_skipped';
}

export interface DiscoveryTemplateCreate {
  name: string;
  description?: string;
  discovery_type: string;
  config: DiscoveryConfig;
}

export interface DiscoveryJobListResponse {
  discovery_jobs: DiscoveryJob[];
  total: number;
}

export interface DiscoveredTargetListResponse {
  targets: DiscoveredTarget[];
  total: number;
}

export interface DiscoveryTemplateListResponse {
  templates: DiscoveryTemplate[];
  total: number;
}

export interface TargetImportRequest {
  target_ids: number[];
  import_options?: {
    auto_assign_credentials?: boolean;
    default_credential_id?: number;
    add_tags?: string[];
    target_group?: string;
  };
}

