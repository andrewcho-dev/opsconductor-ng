/**
 * API Configuration
 * Centralized configuration for all API endpoints
 */

export interface ApiConfig {
  baseUrl: string;
  automationServiceUrl: string;
  selectorBasePath: string;
  auditEnabled: boolean;
  auditKey?: string;
}

/**
 * Get API configuration from environment variables
 * Runtime guards ensure safe fallbacks if env vars are missing or invalid
 */
export const getApiConfig = (): ApiConfig => {
  // Runtime guards for environment variables
  const baseUrl = typeof process.env.REACT_APP_API_URL === 'string' && process.env.REACT_APP_API_URL.trim()
    ? process.env.REACT_APP_API_URL.trim()
    : 'http://localhost:3000';
  
  const automationServiceUrl = typeof process.env.REACT_APP_AUTOMATION_SERVICE_URL === 'string' && process.env.REACT_APP_AUTOMATION_SERVICE_URL.trim()
    ? process.env.REACT_APP_AUTOMATION_SERVICE_URL.trim()
    : 'http://127.0.0.1:8010';
  
  const selectorBasePath = typeof process.env.REACT_APP_SELECTOR_BASE_PATH === 'string' && process.env.REACT_APP_SELECTOR_BASE_PATH.trim()
    ? process.env.REACT_APP_SELECTOR_BASE_PATH.trim()
    : '/api/selector';
  
  const auditEnabled = process.env.REACT_APP_AUDIT_ENABLE === 'true';
  
  const auditKey = typeof process.env.REACT_APP_AUDIT_KEY === 'string' && process.env.REACT_APP_AUDIT_KEY.trim()
    ? process.env.REACT_APP_AUDIT_KEY.trim()
    : undefined;
  
  return {
    baseUrl,
    automationServiceUrl,
    selectorBasePath,
    auditEnabled,
    auditKey,
  };
};

/**
 * Get full selector API URL
 */
export const getSelectorBaseUrl = (): string => {
  const config = getApiConfig();
  return `${config.automationServiceUrl}${config.selectorBasePath}`;
};

/**
 * Get audit API URL
 */
export const getAuditBaseUrl = (): string => {
  const config = getApiConfig();
  return `${config.automationServiceUrl}/audit`;
};

export default getApiConfig;