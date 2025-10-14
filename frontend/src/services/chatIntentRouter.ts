/**
 * ChatIntentRouter - Routes chat messages to appropriate backend services
 * 
 * Supports:
 * - Echo execution (ping, exact echo)
 * - Tool selector search (natural language queries)
 */

import { v4 as uuidv4 } from './uuid';

// Environment configuration
const getAutomationServiceUrl = (): string => {
  return process.env.REACT_APP_AUTOMATION_SERVICE_URL || 'http://localhost:3000';
};

const getSelectorBasePath = (): string => {
  return process.env.REACT_APP_SELECTOR_BASE_PATH || '/api/selector';
};

const isChatDirectExecEnabled = (): boolean => {
  return process.env.REACT_APP_CHAT_DIRECT_EXEC !== 'false'; // Default to true
};

// Intent types
export type ChatIntent = 'exec.echo' | 'selector.search' | 'unknown';

export interface ChatIntentResult {
  intent: ChatIntent;
  platform?: 'windows' | 'linux';
  query?: string;
  input?: string;
}

// Response types
export interface ExecResponse {
  success: boolean;
  output: string;
  error: string | null;
  trace_id: string;
  duration_ms: number;
  tool: string;
}

export interface SelectorTool {
  name: string;
  description: string;
  platform?: string;
  category?: string;
}

export interface SelectorResponse {
  tools: SelectorTool[];
  query: string;
  count: number;
  trace_id?: string;
}

/**
 * Analyze user message and determine intent
 */
export function analyzeIntent(message: string): ChatIntentResult {
  const trimmed = message.trim();
  const lower = trimmed.toLowerCase();

  // Exact "ping" match (case-insensitive)
  if (lower === 'ping') {
    return {
      intent: 'exec.echo',
      input: 'ping'
    };
  }

  // "Please echo this back exactly:" prefix
  const echoPrefix = 'please echo this back exactly:';
  if (lower.startsWith(echoPrefix)) {
    const remainder = trimmed.substring(echoPrefix.length).trim();
    return {
      intent: 'exec.echo',
      input: remainder
    };
  }

  // Otherwise, treat as selector search
  // Detect platform hints
  let platform: 'windows' | 'linux' | undefined;
  if (lower.includes('windows')) {
    platform = 'windows';
  } else if (lower.includes('linux')) {
    platform = 'linux';
  }

  return {
    intent: 'selector.search',
    query: trimmed,
    platform
  };
}

/**
 * Execute echo tool via /ai/execute endpoint
 */
export async function executeEcho(input: string, traceId?: string): Promise<ExecResponse> {
  const startTime = performance.now();
  const trace = traceId || uuidv4();
  
  console.log(`[ChatExec] Executing echo tool: input="${input.substring(0, 50)}${input.length > 50 ? '...' : ''}", trace_id=${trace}`);

  try {
    const url = `${getAutomationServiceUrl()}/ai/execute`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-Id': trace
      },
      body: JSON.stringify({
        tool: 'echo',
        input: input
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const duration = performance.now() - startTime;

    console.log(`[ChatExec] Echo completed: duration=${duration.toFixed(2)}ms, trace_id=${data.trace_id || trace}`);

    return {
      success: data.success ?? true,
      output: data.output || '',
      error: data.error || null,
      trace_id: data.trace_id || trace,
      duration_ms: data.duration_ms || duration,
      tool: data.tool || 'echo'
    };
  } catch (error) {
    const duration = performance.now() - startTime;
    console.error(`[ChatExec] Echo failed: duration=${duration.toFixed(2)}ms, error=${error}`);
    
    return {
      success: false,
      output: '',
      error: error instanceof Error ? error.message : 'Unknown error',
      trace_id: trace,
      duration_ms: duration,
      tool: 'echo'
    };
  }
}

/**
 * Search for tools via selector API
 */
export async function searchTools(
  query: string,
  platform?: 'windows' | 'linux',
  k: number = 3,
  traceId?: string
): Promise<SelectorResponse> {
  const startTime = performance.now();
  const trace = traceId || uuidv4();
  
  console.log(`[ChatSelector] Searching tools: query="${query.substring(0, 50)}${query.length > 50 ? '...' : ''}", platform=${platform || 'any'}, k=${k}, trace_id=${trace}`);

  try {
    const baseUrl = getAutomationServiceUrl();
    const selectorPath = getSelectorBasePath();
    
    // Build query params
    const params = new URLSearchParams({
      query: query,
      k: k.toString()
    });
    
    if (platform) {
      params.append('platform', platform);
    }

    const url = `${baseUrl}${selectorPath}/search?${params.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-Id': trace
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const duration = performance.now() - startTime;

    const tools: SelectorTool[] = data.tools || data.results || [];
    
    console.log(`[ChatSelector] Search completed: duration=${duration.toFixed(2)}ms, count=${tools.length}, trace_id=${trace}`);

    return {
      tools,
      query,
      count: tools.length,
      trace_id: trace
    };
  } catch (error) {
    const duration = performance.now() - startTime;
    console.error(`[ChatSelector] Search failed: duration=${duration.toFixed(2)}ms, error=${error}`);
    
    return {
      tools: [],
      query,
      count: 0,
      trace_id: trace
    };
  }
}

/**
 * Main router function - analyzes intent and executes appropriate action
 */
export async function routeChatMessage(message: string): Promise<{
  intent: ChatIntent;
  execResponse?: ExecResponse;
  selectorResponse?: SelectorResponse;
  error?: string;
}> {
  // Check if feature is enabled
  if (!isChatDirectExecEnabled()) {
    return {
      intent: 'unknown',
      error: 'Chat direct execution is disabled'
    };
  }

  const intentResult = analyzeIntent(message);
  const traceId = uuidv4();

  try {
    switch (intentResult.intent) {
      case 'exec.echo': {
        const execResponse = await executeEcho(intentResult.input!, traceId);
        return {
          intent: 'exec.echo',
          execResponse
        };
      }

      case 'selector.search': {
        const selectorResponse = await searchTools(
          intentResult.query!,
          intentResult.platform,
          3,
          traceId
        );
        return {
          intent: 'selector.search',
          selectorResponse
        };
      }

      default:
        return {
          intent: 'unknown',
          error: 'Unable to determine intent'
        };
    }
  } catch (error) {
    return {
      intent: intentResult.intent,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export default {
  analyzeIntent,
  executeEcho,
  searchTools,
  routeChatMessage,
  isChatDirectExecEnabled
};