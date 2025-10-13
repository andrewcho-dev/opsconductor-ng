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
 */
export const getApiConfig = (): ApiConfig => {
  return {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:3000',
    automationServiceUrl: process.env.REACT_APP_AUTOMATION_SERVICE_URL || 'http://127.0.0.1:8010',
    selectorBasePath: process.env.REACT_APP_SELECTOR_BASE_PATH || '/api/selector',
    auditEnabled: process.env.REACT_APP_AUDIT_ENABLE === 'true',
    auditKey: process.env.REACT_APP_AUDIT_KEY || undefined,
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