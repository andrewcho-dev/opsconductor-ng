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
export type ChatIntent = 
  | 'exec.echo' 
  | 'tool.execute' 
  | 'selector.search' 
  | 'unknown';

export interface ChatIntentResult {
  intent: ChatIntent;
  platform?: 'windows' | 'linux';
  query?: string;
  input?: string;
  toolName?: string;
  toolParams?: Record<string, any>;
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

export interface ToolExecutionResponse {
  success: boolean;
  tool: string;
  output: any;
  error: string | null;
  trace_id: string;
  duration_ms: number;
  exit_code?: number;
}

/**
 * Analyze user message and determine intent
 */
export function analyzeIntent(message: string): ChatIntentResult {
  const trimmed = message.trim();
  const lower = trimmed.toLowerCase();

  // 1. Exact "ping" match (case-insensitive)
  if (lower === 'ping') {
    return {
      intent: 'exec.echo',
      input: 'ping'
    };
  }

  // 2. "Please echo this back exactly:" prefix
  const echoPrefix = 'please echo this back exactly:';
  if (lower.startsWith(echoPrefix)) {
    const remainder = trimmed.substring(echoPrefix.length).trim();
    return {
      intent: 'exec.echo',
      input: remainder
    };
  }

  // 3. Windows list directory: "show/list directory/contents of c drive on <host>"
  const winDirMatch = lower.match(/^(show|list)\s+(directory|contents)\s+of\s+(?:the\s+)?c\s+drive\s+on\s+([A-Za-z0-9\.\-:_]+)$/i);
  if (winDirMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'windows_list_directory',
      toolParams: {
        host: winDirMatch[3],
        path: 'C:\\'
      }
    };
  }

  // 4. DNS lookup: "dns lookup/resolve <domain>"
  const dnsMatch = lower.match(/^dns\s+(lookup|resolve)\s+([A-Za-z0-9\.\-]+)$/i);
  if (dnsMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'dns_lookup',
      toolParams: {
        domain: dnsMatch[2],
        record_type: 'A'
      }
    };
  }

  // 5. TCP port check: "check port <port> on <host>"
  const portMatch = lower.match(/^check\s+port\s+(\d+)\s+on\s+([A-Za-z0-9\.\-:_]+)$/i);
  if (portMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'tcp_port_check',
      toolParams: {
        host: portMatch[2],
        port: parseInt(portMatch[1], 10)
      }
    };
  }

  // 6. HTTP check: "http check <url>" or "fetch/get/head <url>"
  const httpMatch = lower.match(/^(?:http\s+check|fetch|get|head)\s+(https?:\/\/\S+)$/i);
  if (httpMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'http_check',
      toolParams: {
        url: httpMatch[1],
        method: 'GET'
      }
    };
  }

  // 7. Traceroute: "traceroute <host>"
  const traceMatch = lower.match(/^traceroute\s+([A-Za-z0-9\.\-:_]+)$/i);
  if (traceMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'traceroute',
      toolParams: {
        host: traceMatch[1]
      }
    };
  }

  // 8. Ping: "ping <host>"
  const pingMatch = lower.match(/^ping\s+([A-Za-z0-9\.\-:_]+)$/i);
  if (pingMatch) {
    return {
      intent: 'tool.execute',
      toolName: 'shell_ping',
      toolParams: {
        host: pingMatch[1]
      }
    };
  }

  // 9. If message contains "tools" or "tool", use selector search
  if (lower.includes('tool')) {
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

  // 10. Default: selector search
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
 * Execute a tool via /ai/tools/execute endpoint
 */
export async function executeTool(
  toolName: string,
  params: Record<string, any>,
  traceId?: string
): Promise<ToolExecutionResponse> {
  const startTime = performance.now();
  const trace = traceId || uuidv4();
  
  console.log(`[ChatTool] Executing tool: name="${toolName}", params=${JSON.stringify(params)}, trace_id=${trace}`);

  try {
    const url = `${getAutomationServiceUrl()}/ai/tools/execute`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-Id': trace
      },
      body: JSON.stringify({
        name: toolName,
        params: params
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }

    const data = await response.json();
    const duration = performance.now() - startTime;

    console.log(`[ChatTool] Tool execution completed: duration=${duration.toFixed(2)}ms, success=${data.success}, trace_id=${data.trace_id || trace}`);

    return {
      success: data.success ?? false,
      tool: data.tool || toolName,
      output: data.output || data.result || null,
      error: data.error || null,
      trace_id: data.trace_id || trace,
      duration_ms: data.duration_ms || duration,
      exit_code: data.exit_code
    };
  } catch (error) {
    const duration = performance.now() - startTime;
    console.error(`[ChatTool] Tool execution failed: duration=${duration.toFixed(2)}ms, error=${error}`);
    
    return {
      success: false,
      tool: toolName,
      output: null,
      error: error instanceof Error ? error.message : 'Unknown error',
      trace_id: trace,
      duration_ms: duration
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
  toolResponse?: ToolExecutionResponse;
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

      case 'tool.execute': {
        const toolResponse = await executeTool(
          intentResult.toolName!,
          intentResult.toolParams!,
          traceId
        );
        return {
          intent: 'tool.execute',
          toolResponse
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
  executeTool,
  searchTools,
  routeChatMessage,
  isChatDirectExecEnabled
};