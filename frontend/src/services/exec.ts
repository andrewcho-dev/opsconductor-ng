/**
 * Exec Service
 * Service for calling automation-service /ai/execute endpoint
 */
import axios from 'axios';

// Get automation service base URL
const getAutomationServiceUrl = (): string => {
  // Use environment variable or default to localhost:8010
  return process.env.REACT_APP_AUTOMATION_SERVICE_URL || 'http://localhost:8010';
};

// Get exec base path
const getExecBasePath = (): string => {
  return process.env.REACT_APP_EXEC_BASE_PATH || '/ai/execute';
};

// Check if exec sandbox is enabled
export const isExecEnabled = (): boolean => {
  return process.env.REACT_APP_EXEC_ENABLE === 'true';
};

/**
 * Exec request interface
 */
export interface ExecRequest {
  input: string;
  tool?: string;
  trace_id?: string;
}

/**
 * Error detail from backend
 */
export interface ErrorDetail {
  code: string;
  message: string;
}

/**
 * Exec response interface
 */
export interface ExecResponse {
  success: boolean;
  output?: string;
  error?: ErrorDetail;
  trace_id: string;
  duration_ms: number;
  tool: string;
}

/**
 * Execute a tool via automation-service proxy
 * 
 * @param input - Input text for the tool
 * @param tool - Tool name (default: "echo")
 * @param traceId - Optional trace ID for request tracking
 * @returns Promise<ExecResponse>
 */
export async function execRun(
  input: string,
  tool: string = 'echo',
  traceId?: string
): Promise<ExecResponse> {
  const url = `${getAutomationServiceUrl()}${getExecBasePath()}`;
  
  console.log(`[Exec] start input="${input.substring(0, 80)}" tool=${tool}`);
  
  const startTime = performance.now();
  
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add trace ID to header if provided
    if (traceId) {
      headers['X-Trace-Id'] = traceId;
    }
    
    const response = await axios.post<ExecResponse>(
      url,
      {
        input,
        tool,
        trace_id: traceId,
      },
      { headers }
    );
    
    const duration = performance.now() - startTime;
    
    console.log(
      `[Exec] done duration=${duration.toFixed(2)}ms success=${response.data.success} trace_id=${response.data.trace_id}`
    );
    
    return response.data;
  } catch (error: any) {
    const duration = performance.now() - startTime;
    
    // Handle HTTP error responses
    if (error.response?.data) {
      const errorData = error.response.data;
      
      console.error(
        `[Exec] error duration=${duration.toFixed(2)}ms status=${error.response.status} trace_id=${errorData.trace_id || 'unknown'}`
      );
      
      // If backend returned structured error, use it
      if (errorData.error) {
        return {
          success: false,
          error: errorData.error,
          trace_id: errorData.trace_id || 'unknown',
          duration_ms: errorData.duration_ms || duration,
          tool: errorData.tool || tool,
        };
      }
    }
    
    // Generic error handling
    console.error(`[Exec] error duration=${duration.toFixed(2)}ms`, error);
    
    return {
      success: false,
      error: {
        code: 'client_error',
        message: error.message || 'Unknown error occurred',
      },
      trace_id: 'unknown',
      duration_ms: duration,
      tool,
    };
  }
}