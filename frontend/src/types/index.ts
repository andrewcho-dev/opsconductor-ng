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
export interface KeycloakUser {
  id: string;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  roles?: string[];
  // Additional Keycloak standard claims
  name?: string;
  given_name?: string;
  family_name?: string;
  preferred_username?: string;
  realm_access?: {
    roles: string[];
  };
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: KeycloakUser;
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
// No UserListResponse needed - user management through Keycloak only

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
  id?: number;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  use_tls: boolean;
  use_ssl: boolean;
  from_email: string;
  from_name?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SMTPSettingsData extends SMTPSettings {
  is_configured?: boolean;
}

export interface SMTPSettingsResponse {
  success: boolean;
  data: SMTPSettingsData | null;
  message?: string;
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

// Role Types - REMOVED - Use Keycloak roles only
// Roles are managed through Keycloak realm roles and client roles

// Notification Types (matching backend communication service)
export interface Notification {
  id: number;
  notification_id: string;
  template_id?: number;
  channel_id?: number;
  recipient: string;
  subject?: string;
  message: string;
  status: string;
  attempts: number;
  max_attempts: number;
  error_message?: string;
  metadata: Record<string, any>;
  scheduled_at: string;
  sent_at?: string;
  created_at: string;
}

export interface NotificationCreate {
  template_id?: number;
  channel_id?: number;
  recipient: string;
  subject?: string;
  message: string;
  metadata?: Record<string, any>;
  scheduled_at?: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  skip: number;
  limit: number;
}

// Template Types (matching backend communication service)
export interface Template {
  id: number;
  name: string;
  template_type: string;
  subject_template?: string;
  body_template: string;
  metadata: Record<string, any>;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateCreate {
  name: string;
  template_type: string;
  subject_template?: string;
  body_template: string;
  metadata?: Record<string, any>;
  is_active?: boolean;
}

export interface TemplateListResponse {
  templates: Template[];
  total: number;
  skip: number;
  limit: number;
}

// Audit Log Types (matching backend communication service)
export interface AuditLog {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: string;
  user_id?: number;
  action: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface AuditLogListResponse {
  audit_logs: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}

// Network Analysis Types
export interface NetworkProbe {
  id: number;
  name: string;
  description?: string;
  host: string;
  port?: number;
  probe_type: 'ping' | 'port_scan' | 'service_discovery' | 'packet_capture';
  configuration: Record<string, any>;
  is_active: boolean;
  last_run?: string;
  next_run?: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface NetworkProbeCreate {
  name: string;
  description?: string;
  host: string;
  port?: number;
  probe_type: 'ping' | 'port_scan' | 'service_discovery' | 'packet_capture';
  configuration?: Record<string, any>;
  is_active?: boolean;
}

export interface NetworkAnalysis {
  id: number;
  probe_id: number;
  analysis_type: 'connectivity' | 'performance' | 'security' | 'discovery';
  results: Record<string, any>;
  ai_insights?: string;
  anomalies_detected: boolean;
  risk_score?: number;
  recommendations?: string[];
  started_at: string;
  completed_at?: string;
  status: 'running' | 'completed' | 'failed';
}

export interface NetworkAnalysisListResponse {
  analyses: NetworkAnalysis[];
  total: number;
  skip: number;
  limit: number;
}

// Schedule Types
export interface Schedule {
  id: number;
  name: string;
  description?: string;
  cron_expression: string;
  timezone: string;
  job_id: number;
  job_name?: string;
  is_active: boolean;
  last_run?: string;
  next_run?: string;
  run_count: number;
  failure_count: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduleCreate {
  name: string;
  description?: string;
  cron_expression: string;
  timezone?: string;
  job_id: number;
  is_active?: boolean;
}

export interface ScheduleListResponse {
  schedules: Schedule[];
  total: number;
  skip: number;
  limit: number;
}

// Step Library Types
export interface StepLibrary {
  id: number;
  name: string;
  description?: string;
  category: string;
  step_type: string;
  parameters_schema: Record<string, any>;
  implementation: Record<string, any>;
  version: string;
  is_active: boolean;
  usage_count: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface StepLibraryCreate {
  name: string;
  description?: string;
  category: string;
  step_type: string;
  parameters_schema: Record<string, any>;
  implementation: Record<string, any>;
  version?: string;
  is_active?: boolean;
}

export interface StepLibraryListResponse {
  steps: StepLibrary[];
  total: number;
  skip: number;
  limit: number;
}

// Asset Discovery Types
export interface AssetDiscovery {
  id: number;
  name: string;
  description?: string;
  discovery_type: 'network_scan' | 'cloud_discovery' | 'agent_based';
  target_range: string;
  configuration: Record<string, any>;
  is_active: boolean;
  last_run?: string;
  next_run?: string;
  assets_discovered: number;
  status: 'idle' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface AssetDiscoveryCreate {
  name: string;
  description?: string;
  discovery_type: 'network_scan' | 'cloud_discovery' | 'agent_based';
  target_range: string;
  configuration?: Record<string, any>;
  is_active?: boolean;
}

// Asset Group Types
export interface AssetGroup {
  id: number;
  name: string;
  description?: string;
  group_type: 'static' | 'dynamic';
  criteria?: Record<string, any>;
  asset_count: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface AssetGroupCreate {
  name: string;
  description?: string;
  group_type: 'static' | 'dynamic';
  criteria?: Record<string, any>;
}



