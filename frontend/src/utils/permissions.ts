// Permission checking utilities for Keycloak-based RBAC
import { KeycloakUser } from '../types';

// Define permissions based on Keycloak realm roles
export const KEYCLOAK_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager', 
  OPERATOR: 'operator',
  DEVELOPER: 'developer',
  VIEWER: 'viewer',
} as const;

// Basic permissions - simplified since Keycloak handles complex RBAC
export const PERMISSIONS = {
  // Core system access
  SYSTEM_ACCESS: 'system:access',
  SYSTEM_ADMIN: 'system:admin',
  
  // Asset management
  ASSETS_READ: 'assets:read',
  ASSETS_WRITE: 'assets:write',
  
  // Job/workflow management
  JOBS_READ: 'jobs:read',
  JOBS_WRITE: 'jobs:write',
  JOBS_EXECUTE: 'jobs:execute',
  
  // Settings
  SETTINGS_READ: 'settings:read',
  SETTINGS_WRITE: 'settings:write',
  SMTP_CONFIG: 'smtp:config',
  
  // Network analysis
  NETWORK_ANALYSIS: 'network:analysis',
  
} as const;

/**
 * Check if Keycloak user has a specific realm role
 */
export const hasRole = (user: KeycloakUser | null, role: string): boolean => {
  if (!user?.realm_access?.roles) {
    return false;
  }
  return user.realm_access.roles.includes(role);
};

/**
 * Check if user has any of the specified roles
 */
export const hasAnyRole = (user: KeycloakUser | null, roles: string[]): boolean => {
  if (!user?.realm_access?.roles) {
    return false;
  }
  return roles.some(role => user.realm_access!.roles.includes(role));
};

/**
 * Check if user has admin role
 */
export const isAdmin = (user: KeycloakUser | null): boolean => {
  return hasRole(user, KEYCLOAK_ROLES.ADMIN);
};

/**
 * Check if user can manage system settings
 */
export const canManageSettings = (user: KeycloakUser | null): boolean => {
  return hasAnyRole(user, [KEYCLOAK_ROLES.ADMIN, KEYCLOAK_ROLES.MANAGER]);
};

/**
 * Check if user can execute jobs
 */
export const canExecuteJobs = (user: KeycloakUser | null): boolean => {
  return hasAnyRole(user, [
    KEYCLOAK_ROLES.ADMIN, 
    KEYCLOAK_ROLES.MANAGER, 
    KEYCLOAK_ROLES.OPERATOR
  ]);
};

/**
 * Check if user can manage assets
 */
export const canManageAssets = (user: KeycloakUser | null): boolean => {
  return hasAnyRole(user, [
    KEYCLOAK_ROLES.ADMIN, 
    KEYCLOAK_ROLES.MANAGER, 
    KEYCLOAK_ROLES.OPERATOR
  ]);
};

/**
 * Check if user can view system (basic access)
 */
export const canViewSystem = (user: KeycloakUser | null): boolean => {
  // All authenticated users with any role can view
  return (user?.realm_access?.roles?.length ?? 0) > 0;
};

/**
 * Get user's display name from Keycloak token
 */
export const getUserDisplayName = (user: KeycloakUser | null): string => {
  if (!user) {
    return 'Unknown User';
  }
  
  if (user.name) {
    return user.name;
  }
  
  if (user.given_name && user.family_name) {
    return `${user.given_name} ${user.family_name}`;
  }
  
  if (user.given_name) {
    return user.given_name;
  }
  
  return user.preferred_username || user.username || user.email || 'User';
};

/**
 * Get user's primary role for display
 */
export const getUserPrimaryRole = (user: KeycloakUser | null): string => {
  if (!user?.realm_access?.roles) {
    return 'No Role';
  }
  
  const roles = user.realm_access.roles;
  
  // Priority order for displaying role
  const rolePriority = [
    KEYCLOAK_ROLES.ADMIN,
    KEYCLOAK_ROLES.MANAGER,
    KEYCLOAK_ROLES.DEVELOPER,
    KEYCLOAK_ROLES.OPERATOR,
    KEYCLOAK_ROLES.VIEWER
  ];
  
  for (const role of rolePriority) {
    if (roles.includes(role)) {
      return role.charAt(0).toUpperCase() + role.slice(1);
    }
  }
  
  // Return first role if no priority match
  return roles[0]?.charAt(0).toUpperCase() + roles[0]?.slice(1) || 'User';
};

/**
 * LEGACY COMPATIBILITY: hasPermission function that maps to Keycloak roles
 * This allows existing code to work while migrating to pure Keycloak RBAC
 */
export const hasPermission = (user: KeycloakUser | null, permission: string): boolean => {
  if (!user) return false;
  
  // Admin has all permissions
  if (isAdmin(user)) return true;
  
  // Map legacy permissions to Keycloak role checks
  switch (permission) {
    case 'users:read':
    case 'users:create':
    case 'users:update':
    case 'users:delete':
    case 'roles:read':
    case 'roles:create':
    case 'roles:update':
    case 'roles:delete':
      // User/role management is admin-only since it's handled by Keycloak
      return isAdmin(user);
      
    case 'jobs:read':
      return canViewSystem(user);
    case 'jobs:create':
    case 'jobs:update':
    case 'jobs:delete':
    case 'jobs:execute':
      return canExecuteJobs(user);
      
    case 'targets:read':
    case 'assets:read':
      return canViewSystem(user);
    case 'targets:create':
    case 'targets:update':
    case 'targets:delete':
    case 'assets:create':
    case 'assets:update':
    case 'assets:delete':
      return canManageAssets(user);
      
    case 'settings:read':
    case 'settings:update':
    case 'smtp:config':
      return canManageSettings(user);
      
    case 'network:analysis:read':
    case 'network:analysis:write':
    case 'network:capture:start':
    case 'network:capture:stop':
    case 'network:monitoring:read':
    case 'network:monitoring:write':
      return hasAnyRole(user, [KEYCLOAK_ROLES.ADMIN, KEYCLOAK_ROLES.MANAGER, KEYCLOAK_ROLES.OPERATOR]);
      
    case 'system:admin':
      return isAdmin(user);
      
    default:
      // Default to viewer access for unknown permissions
      return canViewSystem(user);
  }
};