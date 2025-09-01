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
  created_at: string;
  token_version: number;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  role: 'admin' | 'operator' | 'viewer';
}

export interface UserUpdate {
  email?: string;
  username?: string;
  password?: string;
  role?: 'admin' | 'operator' | 'viewer';
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
  credential_type: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CredentialCreate {
  name: string;
  description?: string;
  credential_type: string;
  credential_data: Record<string, any>;
}

export interface CredentialDecrypted extends Credential {
  credential_data: Record<string, any>;
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
  version: number;
  definition: Record<string, any>;
  created_by: number;
  is_active: boolean;
  created_at: string;
}

export interface JobCreate {
  name: string;
  version?: number;
  definition: Record<string, any>;
  is_active?: boolean;
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
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled';
  requested_by: number;
  parameters: Record<string, any>;
  queued_at: string;
  started_at?: string;
  finished_at?: string;
  correlation_id?: string;
}

export interface JobRunStep {
  id: number;
  job_run_id: number;
  idx: number;
  type: string;
  target_id?: number;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'aborted';
  shell?: string;
  timeoutsec?: number;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  metrics?: Record<string, any>;
  started_at?: string;
  finished_at?: string;
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
  users: User[];
  total: number;
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
}

export interface JobRunListResponse {
  runs: JobRun[];
  total: number;
}

// Schedule Types
export interface Schedule {
  id: number;
  job_id: number;
  cron: string;
  timezone: string;
  next_run?: string;
  next_run_at?: string;
  last_run_at?: string;
  is_active: boolean;
  created_at: string;
}

export interface ScheduleCreate {
  job_id: number;
  cron: string;
  timezone?: string;
  is_active?: boolean;
}

export interface ScheduleUpdate {
  cron?: string;
  timezone?: string;
  is_active?: boolean;
}

export interface ScheduleListResponse {
  schedules: Schedule[];
  total: number;
}

export interface SchedulerStatus {
  scheduler_running: boolean;
  is_running: boolean;
  active_schedules: number;
  next_execution?: string;
  last_check?: string;
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
  discovery_type: string;
  config: DiscoveryConfig;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_by: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  results_summary?: DiscoveryResultsSummary;
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
  jobs: DiscoveryJob[];
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

