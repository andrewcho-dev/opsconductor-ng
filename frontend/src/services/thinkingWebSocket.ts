/**
 * WebSocket client for real-time AI thinking visualization
 * Implements the BIGBRAIN.md real-time thinking stream system
 */

export interface ThinkingStep {
  id: string;
  session_id: string;
  timestamp: string;
  thinking_type: 'analysis' | 'decision' | 'planning' | 'evaluation' | 'execution' | 'reflection';
  thinking_content: string;
  reasoning_chain: string[];
  confidence_level: number;
  alternatives_considered?: string[];
  decision_factors?: string[];
  metadata?: {
    step_number?: number;
    total_steps?: number;
    processing_time?: number;
    model_used?: string;
  };
}

export interface ProgressUpdate {
  id: string;
  session_id: string;
  timestamp: string;
  progress_type: 'started' | 'progress' | 'completed' | 'error';
  operation: string;
  progress_percentage?: number;
  current_step?: string;
  estimated_remaining?: number;
  details?: string;
}

export interface ThinkingWebSocketMessage {
  type: 'connection_established' | 'thinking_step' | 'progress_update' | 'keepalive' | 'history' | 'stats' | 'pong';
  session_id?: string;
  timestamp?: string;
  message?: string;
  data?: ThinkingStep | ProgressUpdate | any;
  thinking_history?: ThinkingStep[];
  progress_history?: ProgressUpdate[];
}

export type ThinkingEventHandler = (step: ThinkingStep) => void;
export type ProgressEventHandler = (update: ProgressUpdate) => void;
export type ConnectionEventHandler = (connected: boolean) => void;

export class ThinkingWebSocketClient {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private isDestroyed = false;

  // Event handlers
  private thinkingHandlers: ThinkingEventHandler[] = [];
  private progressHandlers: ProgressEventHandler[] = [];
  private connectionHandlers: ConnectionEventHandler[] = [];

  // State
  private isConnected = false;
  private thinkingHistory: ThinkingStep[] = [];
  private progressHistory: ProgressUpdate[] = [];

  constructor(sessionId: string, baseUrl: string = '') {
    this.sessionId = sessionId;
    // Determine WebSocket URL based on current location
    if (baseUrl) {
      this.baseUrl = baseUrl;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // For WebSocket connections, connect directly to AI Brain service (port 3005)
      // since Kong doesn't have WebSocket-specific configuration
      const hostname = window.location.hostname;
      this.baseUrl = `${protocol}//${hostname}:3005`;
    }
  }

  /**
   * Connect to the thinking WebSocket
   */
  async connect(): Promise<boolean> {
    if (this.isConnecting || this.isConnected || this.isDestroyed) {
      return this.isConnected;
    }

    this.isConnecting = true;

    try {
      // Connect to the thinking WebSocket endpoint (direct to AI Brain service)
      const wsUrl = `${this.baseUrl}/ws/thinking/${this.sessionId}`;
      console.log('🔌 Connecting to thinking WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);

      return new Promise((resolve) => {
        if (!this.ws) {
          resolve(false);
          return;
        }

        this.ws.onopen = () => {
          console.log('✅ Thinking WebSocket connected');
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.notifyConnectionHandlers(true);
          
          // Request history on connection
          this.requestHistory();
          
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: ThinkingWebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('🔌 Thinking WebSocket closed:', event.code, event.reason);
          this.isConnected = false;
          this.isConnecting = false;
          this.ws = null;
          this.notifyConnectionHandlers(false);

          // Attempt reconnection if not manually closed
          if (!this.isDestroyed && event.code !== 1000) {
            this.attemptReconnect();
          }
          
          resolve(false);
        };

        this.ws.onerror = (error) => {
          console.error('❌ Thinking WebSocket error:', error);
          this.isConnecting = false;
          resolve(false);
        };

        // Timeout after 10 seconds
        setTimeout(() => {
          if (this.isConnecting) {
            console.warn('⏰ WebSocket connection timeout');
            this.isConnecting = false;
            resolve(false);
          }
        }, 10000);
      });

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      return false;
    }
  }

  /**
   * Disconnect from the WebSocket
   */
  disconnect(): void {
    this.isDestroyed = true;
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.notifyConnectionHandlers(false);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: ThinkingWebSocketMessage): void {
    switch (message.type) {
      case 'connection_established':
        console.log('🎉 Thinking stream connection established');
        break;

      case 'thinking_step':
        if (message.data) {
          const step = message.data as ThinkingStep;
          this.thinkingHistory.push(step);
          this.notifyThinkingHandlers(step);
        }
        break;

      case 'progress_update':
        if (message.data) {
          const update = message.data as ProgressUpdate;
          this.progressHistory.push(update);
          this.notifyProgressHandlers(update);
        }
        break;

      case 'history':
        if (message.thinking_history) {
          this.thinkingHistory = message.thinking_history;
        }
        if (message.progress_history) {
          this.progressHistory = message.progress_history;
        }
        console.log('📚 Received thinking history:', this.thinkingHistory.length, 'steps');
        break;

      case 'keepalive':
        // Send pong response
        this.sendMessage({ type: 'ping' });
        break;

      case 'pong':
        // Keepalive response received
        break;

      default:
        console.log('📨 Unknown WebSocket message type:', message.type);
    }
  }

  /**
   * Send a message to the WebSocket
   */
  private sendMessage(message: any): void {
    if (this.ws && this.isConnected) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('❌ Failed to send WebSocket message:', error);
      }
    }
  }

  /**
   * Request thinking and progress history
   */
  requestHistory(): void {
    this.sendMessage({ type: 'get_history' });
  }

  /**
   * Request session statistics
   */
  requestStats(): void {
    this.sendMessage({ type: 'get_stats' });
  }

  /**
   * Attempt to reconnect to the WebSocket
   */
  private attemptReconnect(): void {
    if (this.isDestroyed || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('🚫 Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isDestroyed) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Event handler registration
   */
  onThinking(handler: ThinkingEventHandler): () => void {
    this.thinkingHandlers.push(handler);
    return () => {
      const index = this.thinkingHandlers.indexOf(handler);
      if (index > -1) {
        this.thinkingHandlers.splice(index, 1);
      }
    };
  }

  onProgress(handler: ProgressEventHandler): () => void {
    this.progressHandlers.push(handler);
    return () => {
      const index = this.progressHandlers.indexOf(handler);
      if (index > -1) {
        this.progressHandlers.splice(index, 1);
      }
    };
  }

  onConnection(handler: ConnectionEventHandler): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Notify event handlers
   */
  private notifyThinkingHandlers(step: ThinkingStep): void {
    this.thinkingHandlers.forEach(handler => {
      try {
        handler(step);
      } catch (error) {
        console.error('❌ Error in thinking handler:', error);
      }
    });
  }

  private notifyProgressHandlers(update: ProgressUpdate): void {
    this.progressHandlers.forEach(handler => {
      try {
        handler(update);
      } catch (error) {
        console.error('❌ Error in progress handler:', error);
      }
    });
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('❌ Error in connection handler:', error);
      }
    });
  }

  /**
   * Getters for current state
   */
  get connected(): boolean {
    return this.isConnected;
  }

  get thinking(): ThinkingStep[] {
    return [...this.thinkingHistory];
  }

  get progress(): ProgressUpdate[] {
    return [...this.progressHistory];
  }

  /**
   * Clear history
   */
  clearHistory(): void {
    this.thinkingHistory = [];
    this.progressHistory = [];
  }
}