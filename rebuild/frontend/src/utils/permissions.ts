// Permission checking utilities for RBAC

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  first_name?: string;
  last_name?: string;
}

// Define all available permissions in the system
export const PERMISSIONS = {
  // User management
  USERS_READ: 'users:read',
  USERS_CREATE: 'users:create',
  USERS_UPDATE: 'users:update',
  USERS_DELETE: 'users:delete',
  
  // Role management
  ROLES_READ: 'roles:read',
  ROLES_CREATE: 'roles:create',
  ROLES_UPDATE: 'roles:update',
  ROLES_DELETE: 'roles:delete',
  
  // Job management
  JOBS_READ: 'jobs:read',
  JOBS_CREATE: 'jobs:create',
  JOBS_UPDATE: 'jobs:update',
  JOBS_DELETE: 'jobs:delete',
  JOBS_EXECUTE: 'jobs:execute',
  
  // Target management
  TARGETS_READ: 'targets:read',
  TARGETS_CREATE: 'targets:create',
  TARGETS_UPDATE: 'targets:update',
  TARGETS_DELETE: 'targets:delete',
  
  // Execution monitoring
  EXECUTIONS_READ: 'executions:read',
  
  // Step library management
  STEP_LIBRARIES_READ: 'step-libraries:read',
  STEP_LIBRARIES_CREATE: 'step-libraries:create',
  STEP_LIBRARIES_UPDATE: 'step-libraries:update',
  STEP_LIBRARIES_DELETE: 'step-libraries:delete',
  
  // Settings
  SETTINGS_READ: 'settings:read',
  SETTINGS_UPDATE: 'settings:update',
  SMTP_CONFIG: 'smtp:config',
  
  // Notifications
  NOTIFICATIONS_READ: 'notifications:read',
  NOTIFICATIONS_CREATE: 'notifications:create',
  NOTIFICATIONS_UPDATE: 'notifications:update',
  NOTIFICATIONS_DELETE: 'notifications:delete',
  
  // System administration
  SYSTEM_ADMIN: 'system:admin',
} as const;

// Permission groups for easier role management
export const PERMISSION_GROUPS = {
  USER_MANAGEMENT: [
    PERMISSIONS.USERS_READ,
    PERMISSIONS.USERS_CREATE,
    PERMISSIONS.USERS_UPDATE,
    PERMISSIONS.USERS_DELETE,
  ],
  ROLE_MANAGEMENT: [
    PERMISSIONS.ROLES_READ,
    PERMISSIONS.ROLES_CREATE,
    PERMISSIONS.ROLES_UPDATE,
    PERMISSIONS.ROLES_DELETE,
  ],
  JOB_MANAGEMENT: [
    PERMISSIONS.JOBS_READ,
    PERMISSIONS.JOBS_CREATE,
    PERMISSIONS.JOBS_UPDATE,
    PERMISSIONS.JOBS_DELETE,
    PERMISSIONS.JOBS_EXECUTE,
  ],
  TARGET_MANAGEMENT: [
    PERMISSIONS.TARGETS_READ,
    PERMISSIONS.TARGETS_CREATE,
    PERMISSIONS.TARGETS_UPDATE,
    PERMISSIONS.TARGETS_DELETE,
  ],
  STEP_LIBRARY_MANAGEMENT: [
    PERMISSIONS.STEP_LIBRARIES_READ,
    PERMISSIONS.STEP_LIBRARIES_CREATE,
    PERMISSIONS.STEP_LIBRARIES_UPDATE,
    PERMISSIONS.STEP_LIBRARIES_DELETE,
  ],
  SETTINGS_MANAGEMENT: [
    PERMISSIONS.SETTINGS_READ,
    PERMISSIONS.SETTINGS_UPDATE,
    PERMISSIONS.SMTP_CONFIG,
  ],
  NOTIFICATION_MANAGEMENT: [
    PERMISSIONS.NOTIFICATIONS_READ,
    PERMISSIONS.NOTIFICATIONS_CREATE,
    PERMISSIONS.NOTIFICATIONS_UPDATE,
    PERMISSIONS.NOTIFICATIONS_DELETE,
  ],
} as const;

/**
 * Check if user has a specific permission
 */
export const hasPermission = (user: User | null, permission: string): boolean => {
  if (!user || !user.permissions) {
    return false;
  }
  
  // Admin wildcard permission grants everything
  if (user.permissions.includes('*')) {
    return true;
  }
  
  return user.permissions.includes(permission);
};

/**
 * Check if user has any of the specified permissions
 */
export const hasAnyPermission = (user: User | null, permissions: string[]): boolean => {
  if (!user || !user.permissions) {
    return false;
  }
  
  // Admin wildcard permission grants everything
  if (user.permissions.includes('*')) {
    return true;
  }
  
  return permissions.some(permission => user.permissions.includes(permission));
};

/**
 * Check if user has all of the specified permissions
 */
export const hasAllPermissions = (user: User | null, permissions: string[]): boolean => {
  if (!user || !user.permissions) {
    return false;
  }
  
  // Admin wildcard permission grants everything
  if (user.permissions.includes('*')) {
    return true;
  }
  
  return permissions.every(permission => user.permissions.includes(permission));
};

/**
 * Check if user has a specific role
 */
export const hasRole = (user: User | null, role: string): boolean => {
  if (!user) {
    return false;
  }
  
  return user.role === role;
};

/**
 * Check if user has any of the specified roles
 */
export const hasAnyRole = (user: User | null, roles: string[]): boolean => {
  if (!user) {
    return false;
  }
  
  return roles.includes(user.role);
};

/**
 * Check if user is admin (has admin role or wildcard permission)
 */
export const isAdmin = (user: User | null): boolean => {
  if (!user) {
    return false;
  }
  
  return user.role === 'admin' || (user.permissions && user.permissions.includes('*'));
};

/**
 * Get user's display name
 */
export const getUserDisplayName = (user: User | null): string => {
  if (!user) {
    return 'Unknown User';
  }
  
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  
  if (user.first_name) {
    return user.first_name;
  }
  
  return user.username;
};

/**
 * Get user's role display name
 */
export const getRoleDisplayName = (role: string): string => {
  const roleNames: Record<string, string> = {
    admin: 'Administrator',
    manager: 'Manager',
    operator: 'Operator',
    developer: 'Developer',
    viewer: 'Viewer',
  };
  
  return roleNames[role] || role.charAt(0).toUpperCase() + role.slice(1);
};