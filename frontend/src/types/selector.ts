/**
 * Selector API Types
 * Based on automation-service/selector/README.md
 */

/**
 * Tool result from selector search
 */
export interface SelectorTool {
  name: string;
  short_desc: string;
}

/**
 * Selector search request parameters
 */
export interface SelectorSearchRequest {
  query: string;
  platforms?: string[];
  k?: number;
}

/**
 * Selector search response (200 OK)
 */
export interface SelectorSearchResponse {
  query: string;
  platforms: string[];
  k: number;
  results: SelectorTool[];
  from_cache: boolean;
  duration_ms: number;
}

/**
 * Selector validation error (400 Bad Request)
 */
export interface SelectorValidationError {
  error: 'ValidationError';
  code: string;
  message: string;
}

/**
 * Selector degraded mode error (503 Service Unavailable)
 */
export interface SelectorDegradedError {
  error: 'DependencyUnavailable';
  code: string;
  degraded: boolean;
  hint: string;
  retry_after_sec: number;
}

/**
 * Union type for all selector errors
 */
export type SelectorError = SelectorValidationError | SelectorDegradedError;

/**
 * Audit record for AI query
 */
export interface AuditAIQueryRequest {
  trace_id: string;
  user_id: string;
  input: string;
  output: string;
  tools: Array<{
    name: string;
    latency_ms: number;
    ok: boolean;
  }>;
  duration_ms: number;
  created_at: string;
}

/**
 * Audit response (202 Accepted)
 */
export interface AuditResponse {
  status: 'accepted';
  message: string;
  record_id: string;
}