/**
 * Selector API Service
 * Handles tool selection API calls
 */

import { http, HttpError } from '../lib/http';
import { getSelectorBaseUrl, getAuditBaseUrl, getApiConfig } from '../config/api';
import {
  SelectorSearchRequest,
  SelectorSearchResponse,
  AuditAIQueryRequest,
  AuditResponse,
} from '../types/selector';

/**
 * Search for tools using the selector API
 */
export const searchTools = async (
  request: SelectorSearchRequest
): Promise<SelectorSearchResponse> => {
  const baseUrl = getSelectorBaseUrl();
  
  // Runtime guard: validate request
  if (!request || typeof request !== 'object') {
    throw new Error('Invalid search request');
  }
  
  if (typeof request.query !== 'string' || !request.query.trim()) {
    throw new Error('Query is required');
  }
  
  // Build query parameters
  const params = new URLSearchParams();
  params.append('query', request.query);
  
  if (request.k !== undefined) {
    params.append('k', request.k.toString());
  }
  
  if (request.platforms && request.platforms.length > 0) {
    request.platforms.forEach(platform => {
      params.append('platform', platform);
    });
  }
  
  const url = `${baseUrl}/search?${params.toString()}`;
  
  try {
    const response = await http.get<SelectorSearchResponse>(url);
    
    // Runtime guard: validate response structure
    if (!response || typeof response !== 'object') {
      console.error('[Selector] Invalid response structure:', response);
      throw new Error('Invalid response from server');
    }
    
    // Ensure results is an array
    if (!Array.isArray(response.results)) {
      console.warn('[Selector] Response missing results array, defaulting to empty');
      response.results = [];
    }
    
    // Ensure from_cache is boolean
    if (typeof response.from_cache !== 'boolean') {
      response.from_cache = false;
    }
    
    // Ensure duration_ms is number
    if (typeof response.duration_ms !== 'number') {
      response.duration_ms = 0;
    }
    
    return response;
  } catch (error) {
    // Re-throw with additional context
    if (error instanceof Error && 'status' in error) {
      const httpError = error as HttpError;
      
      // Add user-friendly message for common errors
      if (httpError.status === 400) {
        httpError.message = `Validation error: ${httpError.data?.message || httpError.message}`;
      } else if (httpError.status === 503) {
        httpError.message = `Service temporarily unavailable. ${httpError.data?.hint || 'Please try again.'}`;
      }
    }
    throw error;
  }
};

/**
 * Record an audit trail for AI query (fire-and-forget)
 */
export const recordAuditTrail = async (
  request: AuditAIQueryRequest
): Promise<void> => {
  const config = getApiConfig();
  
  // Skip if audit is disabled
  if (!config.auditEnabled) {
    return;
  }
  
  const baseUrl = getAuditBaseUrl();
  const url = `${baseUrl}/ai-query`;
  
  try {
    const headers: Record<string, string> = {};
    
    // Add internal key if configured
    if (config.auditKey) {
      headers['X-Internal-Key'] = config.auditKey;
    }
    
    await http.post<AuditResponse>(url, request, { headers });
  } catch (error) {
    // Log error but don't throw (fire-and-forget)
    console.warn('Failed to record audit trail:', error);
  }
};

/**
 * Generate a trace ID for audit records
 */
export const generateTraceId = (): string => {
  return `sel-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
};

/**
 * Get current user ID from localStorage or return 'anonymous'
 */
export const getCurrentUserId = (): string => {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr && typeof userStr === 'string') {
      const user = JSON.parse(userStr);
      
      // Runtime guard: ensure user is an object
      if (user && typeof user === 'object') {
        // Try multiple common user ID fields
        const userId = user.id || user.user_id || user.username || user.email;
        if (typeof userId === 'string' && userId.trim()) {
          return userId.trim();
        }
      }
    }
  } catch (e) {
    // Ignore parse errors
    console.debug('[Selector] Failed to parse user from localStorage:', e);
  }
  return 'anonymous';
};

const selectorApi = {
  searchTools,
  recordAuditTrail,
  generateTraceId,
  getCurrentUserId,
};

export default selectorApi;