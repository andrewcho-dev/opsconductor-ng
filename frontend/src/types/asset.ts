export interface Asset {
  id: number;
  name: string;
  hostname: string;
  ip_address?: string;
  description?: string;
  tags: string[];
  
  // Device/Hardware Information
  device_type?: string;
  hardware_make?: string;
  hardware_model?: string;
  serial_number?: string;
  
  // System Information
  os_type: string;
  os_version?: string;
  
  // Location Information
  physical_address?: string;
  data_center?: string;
  building?: string;
  room?: string;
  rack_position?: string;
  rack_location?: string;
  gps_coordinates?: string;
  
  // Status & Management
  status?: string;
  environment?: string;
  criticality?: string;
  owner?: string;
  support_contact?: string;
  contract_number?: string;
  
  // Primary Communication Service
  service_type: string;
  port: number;
  is_secure: boolean;
  
  // Primary Service Credentials - ALL COMPREHENSIVE FIELDS
  credential_type?: string;
  username?: string;
  public_key?: string;
  api_key?: string;
  bearer_token?: string;
  certificate?: string;
  passphrase?: string;
  domain?: string;
  
  // Database-specific fields
  database_type?: string;
  database_name?: string;
  
  // Secondary Communication - ALL COMPREHENSIVE FIELDS
  secondary_service_type?: string;
  secondary_port?: number;
  ftp_type?: string;
  secondary_username?: string;
  secondary_password?: string;
  
  // Additional Information
  notes?: string;
  additional_services?: any[];
  
  // System fields
  is_active: boolean;
  connection_status?: string;
  last_tested_at?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: number;
  updated_by?: number;
  
  // Legacy fields (for backward compatibility)
  architecture?: string;
  has_credentials?: boolean;
  additional_services_count?: number;
  last_seen?: string;
  metadata?: Record<string, any>;
}