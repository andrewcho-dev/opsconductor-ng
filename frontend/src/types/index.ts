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
  protocol: string;
  port: number;
  credential_ref: number;
  tags: string[];
  metadata: Record<string, any>;
  depends_on: number[];
  created_at: string;
}

export interface TargetCreate {
  name: string;
  hostname: string;
  protocol: string;
  port: number;
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
  active_schedules: number;
  next_execution?: string;
  last_check?: string;
}