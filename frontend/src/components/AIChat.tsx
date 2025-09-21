import React, { useState, useRef, useEffect, useImperativeHandle } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2, RefreshCw, Copy, Check, Bug, Eye, Brain, Target, Zap, Shield, TrendingUp, Activity, AlertTriangle, Info } from 'lucide-react';
import { aiApi } from '../services/api';

interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  jobId?: string;
  executionId?: string;
  confidence?: number;
  status?: 'pending' | 'success' | 'error';
  conversationId?: string;
  debugInfo?: {
    intent_classification?: {
      intent_type: string;
      confidence: number;
      method: string;
      alternatives: Array<{
        intent: string;
        confidence: number;
      }>;
      entities: Array<{
        value: string;
        type: string;
        confidence: number;
        normalized_value?: string;
      }>;
      context_analysis: {
        confidence_score: number;
        risk_level: string;
        requirements_count: number;
        recommendations: string[];
      };
      reasoning: string;
      metadata: {
        engine: string;
        success: boolean;
      };
    };
    routing?: {
      service: string;
      service_type: string;
      response_time: number;
      cached: boolean;
    };
    raw_response?: any;
  };
}

interface ChatResponse {
  success?: boolean;
  response: string;
  intent?: string;
  confidence?: number;
  conversation_id?: string;
  job_id?: string;
  execution_id?: string;
  automation_job_id?: number;
  workflow?: any;
  execution_started?: boolean;
  _routing?: {
    service: string;
    service_type: string;
    response_time: number;
    cached: boolean;
  };
  intent_classification?: {
    intent_type: string;
    confidence: number;
    method: string;
    alternatives: Array<{
      intent: string;
      confidence: number;
    }>;
    entities: Array<{
      value: string;
      type: string;
      confidence: number;
      normalized_value?: string;
    }>;
    context_analysis: {
      confidence_score: number;
      risk_level: string;
      requirements_count: number;
      recommendations: string[];
    };
    reasoning: string;
    metadata: {
      engine: string;
      success: boolean;
    };
  };
  timestamp?: string;
  error?: string;
}

const CHAT_HISTORY_KEY = 'opsconductor_ai_chat_history';

interface AIChatProps {
  onClearChat?: () => void;
  onFirstMessage?: (message: string) => void;
  activeChatId?: string | null;
}

export interface AIChatRef {
  clearChat: () => void;
  clearChatHistory: () => void;
}

const AIChat = React.forwardRef<AIChatRef, AIChatProps>(({ onClearChat, onFirstMessage, activeChatId }, ref) => {
  // AI Chat state
  const loadChatHistory = (): ChatMessage[] => {
    try {
      const saved = localStorage.getItem(CHAT_HISTORY_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
    return [];
  };

  const saveChatHistory = (messages: ChatMessage[]) => {
    try {
      localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages));
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  };

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(loadChatHistory);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [debugMode, setDebugMode] = useState(() => {
    try {
      const saved = localStorage.getItem('opsconductor_ai_debug_mode');
      return saved === 'true';
    } catch {
      return false;
    }
  });
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);

  // Remove auto-scroll entirely - let users scroll manually

  useEffect(() => {
    saveChatHistory(chatMessages);
  }, [chatMessages]);

  // Reset conversation ID and reload chat history when switching chats
  useEffect(() => {
    // Reload chat history from localStorage when activeChatId changes
    const newHistory = loadChatHistory();
    setChatMessages(newHistory);
    
    // Find the most recent conversation ID from the loaded messages
    const lastAiMessage = newHistory.slice().reverse().find(msg => msg.type === 'ai' && msg.conversationId);
    if (lastAiMessage?.conversationId) {
      setCurrentConversationId(lastAiMessage.conversationId);
    } else {
      setCurrentConversationId(null);
    }
  }, [activeChatId]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    };

    setChatMessages(prev => {
      const newMessages = [...prev, userMessage];
      // Call onFirstMessage if this is the first user message
      if (prev.length === 0 && onFirstMessage) {
        onFirstMessage(userMessage.content);
      }
      return newMessages;
    });
    setChatInput('');
    setIsChatLoading(true);
    setChatError(null);

    try {
      // Get the last AI message to extract conversation_id if available
      const lastAiMessage = chatMessages.slice().reverse().find(msg => msg.type === 'ai');
      const conversationId = lastAiMessage?.conversationId;
      
      const data = await aiApi.chat({
        message: userMessage.content,
        user_id: 1, // TODO: Get from auth context
        conversation_id: conversationId
      });
      
      // Check if there's an error in the response
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Create AI message with routing info if available
      let aiContent = data.response;
      if (data._routing && !debugMode) {
        const cached = data._routing.cached ? ' (cached)' : '';
        const responseTime = (data._routing.response_time && typeof data._routing.response_time === 'number') 
          ? data._routing.response_time.toFixed(2) 
          : '0.00';
        const service = data._routing.service || 'ai_brain';
        aiContent += `\n\n[Processed by ${service} in ${responseTime}s${cached}]`;
      }
      
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiContent,
        timestamp: new Date(),
        confidence: data.confidence,
        jobId: data.job_id,
        executionId: data.execution_id,
        conversationId: data.conversation_id,
        status: data.execution_started ? 'pending' : undefined,
        debugInfo: {
          intent_classification: data.intent_classification,
          routing: data._routing,
          raw_response: data
        }
      };

      setChatMessages(prev => [...prev, aiMessage]);
      
      // Update current conversation ID
      if (data.conversation_id) {
        setCurrentConversationId(data.conversation_id);
      }

      // If execution started, add a system message
      if (data.execution_started && data.automation_job_id) {
        const systemMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          type: 'system',
          content: `🚀 Automation job #${data.automation_job_id} has been started. You can monitor its progress in the Job Monitoring section.`,
          timestamp: new Date(),
          status: 'success'
        };
        setChatMessages(prev => [...prev, systemMessage]);
      }

    } catch (error: any) {
      console.error('Chat error:', error);
      setChatError(error.message || 'Failed to send message');
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `❌ Error: ${error.message || 'Failed to process your request'}`,
        timestamp: new Date(),
        status: 'error'
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const clearChatHistory = () => {
    setChatMessages([]);
    setCurrentConversationId(null);
    localStorage.removeItem(CHAT_HISTORY_KEY);
    onClearChat?.();
  };

  const reloadChatHistory = () => {
    const newHistory = loadChatHistory();
    setChatMessages(newHistory);
    
    // Find the most recent conversation ID from the loaded messages
    const lastAiMessage = newHistory.slice().reverse().find(msg => msg.type === 'ai' && msg.conversationId);
    if (lastAiMessage?.conversationId) {
      setCurrentConversationId(lastAiMessage.conversationId);
    } else {
      setCurrentConversationId(null);
    }
  };

  const toggleDebugMode = () => {
    const newDebugMode = !debugMode;
    setDebugMode(newDebugMode);
    try {
      localStorage.setItem('opsconductor_ai_debug_mode', newDebugMode.toString());
    } catch (error) {
      console.warn('Failed to save debug mode preference:', error);
    }
  };

  useImperativeHandle(ref, () => ({
    clearChat: reloadChatHistory,
    clearChatHistory: clearChatHistory
  }));

  const getMessageIcon = (message: ChatMessage) => {
    switch (message.type) {
      case 'user':
        return <User size={16} />;
      case 'ai':
        return <Bot size={16} />;
      case 'system':
        if (message.status === 'success') return <CheckCircle size={16} />;
        if (message.status === 'error') return <AlertCircle size={16} />;
        return <Clock size={16} />;
      default:
        return null;
    }
  };

  const getMessageStatusColor = (message: ChatMessage) => {
    if (message.status === 'success') return 'var(--success-green)';
    if (message.status === 'error') return 'var(--danger-red)';
    if (message.status === 'pending') return 'var(--warning-orange)';
    return 'var(--neutral-600)';
  };

  const [copiedBlocks, setCopiedBlocks] = useState<Set<string>>(new Set());

  const copyToClipboard = async (text: string, blockId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedBlocks(prev => new Set(prev).add(blockId));
      setTimeout(() => {
        setCopiedBlocks(prev => {
          const newSet = new Set(prev);
          newSet.delete(blockId);
          return newSet;
        });
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const renderDebugInfo = (message: ChatMessage) => {
    if (!debugMode || !message.debugInfo) return null;

    const getConfidenceClass = (confidence?: number) => {
      if (!confidence) return 'confidence-low';
      if (confidence >= 0.8) return 'confidence-high';
      if (confidence >= 0.5) return 'confidence-medium';
      return 'confidence-low';
    };

    const getRiskClass = (riskLevel?: string) => {
      if (!riskLevel) return 'risk-low';
      const level = riskLevel.toLowerCase();
      if (level === 'high') return 'risk-high';
      if (level === 'medium') return 'risk-medium';
      return 'risk-low';
    };

    const formatConfidence = (confidence?: number) => {
      return confidence ? `${(confidence * 100).toFixed(1)}%` : 'N/A';
    };

    const formatRiskLevel = (riskLevel?: string) => {
      return riskLevel ? riskLevel.toUpperCase() : 'UNKNOWN';
    };

    const intent = message.debugInfo.intent_classification;
    const routing = message.debugInfo.routing;

    return (
      <div className="debug-info-panel">
        {/* Header */}
        <div className="debug-panel-header">
          <div className="debug-panel-title">
            <Brain className="debug-section-icon" />
            AI Debug Information
          </div>
          <div className="debug-panel-badge">
            {intent?.metadata?.engine || 'AI Engine'}
          </div>
        </div>

        <div className="debug-sections-grid">
          {/* Intent Classification Section */}
          {intent && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Target className="debug-section-icon" />
                  Intent Classification
                </div>
                <span className={`confidence-indicator ${getConfidenceClass(intent.confidence)}`}>
                  {formatConfidence(intent.confidence)}
                </span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Intent Type</span>
                <span className="debug-field-value code">{intent.intent_type || 'Unknown'}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Classification Method</span>
                <span className="debug-field-value">{intent.method || 'Unknown'}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Confidence Score</span>
                <span className="debug-field-value">{formatConfidence(intent.confidence)}</span>
              </div>

              {/* Confidence Bar */}
              <div className="confidence-bar">
                <div 
                  className={`confidence-fill ${getConfidenceClass(intent.confidence).replace('confidence-', '')}`}
                  style={{ width: `${(intent.confidence || 0) * 100}%` }}
                />
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Reasoning</span>
                <span className="debug-field-value">{intent.reasoning || 'No reasoning provided'}</span>
              </div>
            </div>
          )}

          {/* Context Analysis Section */}
          {intent?.context_analysis && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Shield className="debug-section-icon" />
                  Context Analysis
                </div>
                <span className={`risk-indicator ${getRiskClass(intent.context_analysis.risk_level)}`}>
                  <AlertTriangle size={14} />
                  {formatRiskLevel(intent.context_analysis.risk_level)}
                </span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Context Confidence</span>
                <span className="debug-field-value">{formatConfidence(intent.context_analysis.confidence_score)}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Risk Level</span>
                <span className="debug-field-value">{formatRiskLevel(intent.context_analysis.risk_level)}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Requirements Count</span>
                <span className="debug-field-value">{intent.context_analysis.requirements_count || 0}</span>
              </div>

              {/* Recommendations */}
              {intent.context_analysis.recommendations && intent.context_analysis.recommendations.length > 0 && (
                <div>
                  <div className="debug-field-label" style={{ marginTop: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
                    Recommendations
                  </div>
                  <div className="recommendations-list">
                    {intent.context_analysis.recommendations.map((rec, index) => (
                      <div key={index} className="recommendation-item">
                        <AlertTriangle className="recommendation-icon" />
                        <span className="recommendation-text">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Alternative Intents Section */}
          {intent?.alternatives && intent.alternatives.length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <TrendingUp className="debug-section-icon" />
                  Alternative Intents
                </div>
              </div>

              <div className="alternatives-list">
                {intent.alternatives.map((alt, index) => (
                  <div key={index} className="alternative-item">
                    <span className="alternative-name">{alt.intent}</span>
                    <span className="alternative-confidence">{formatConfidence(alt.confidence)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entities Section */}
          {intent?.entities && intent.entities.length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Zap className="debug-section-icon" />
                  Extracted Entities
                </div>
              </div>

              <div className="entities-list">
                {intent.entities.map((entity, index) => (
                  <div key={index} className="entity-item">
                    <div className="entity-details">
                      <span className="entity-value">{entity.value}</span>
                      <span className="entity-type">{entity.type}</span>
                    </div>
                    <span className="entity-confidence">{formatConfidence(entity.confidence)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Metrics Section */}
          {routing && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Activity className="debug-section-icon" />
                  Performance Metrics
                </div>
              </div>

              <div className="performance-metrics">
                <div className="metric-item">
                  <div className="metric-value">{routing.response_time?.toFixed(2) || '0.00'}s</div>
                  <div className="metric-label">Response Time</div>
                </div>
                <div className="metric-item">
                  <div className="metric-value">{routing.cached ? 'YES' : 'NO'}</div>
                  <div className="metric-label">Cached</div>
                </div>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Service</span>
                <span className="debug-field-value code">{routing.service}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Service Type</span>
                <span className="debug-field-value">{routing.service_type}</span>
              </div>
            </div>
          )}

          {/* Raw Response Section */}
          {message.debugInfo.raw_response && (
            <div className="debug-section" style={{ gridColumn: '1 / -1' }}>
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Info className="debug-section-icon" />
                  Raw Response Data
                </div>
              </div>
              <div className="debug-json">
                {JSON.stringify(message.debugInfo.raw_response, null, 2)}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const formatMessageContent = (content: string, messageId: string) => {
    // Detect code blocks with triple backticks
    const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    let blockIndex = 0;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${blockIndex}`}>
            {content.slice(lastIndex, match.index)}
          </span>
        );
      }

      const language = match[1] || 'text';
      const code = match[2].trim();
      const blockId = `${messageId}-${blockIndex}`;
      const isCopied = copiedBlocks.has(blockId);

      parts.push(
        <div key={`code-${blockIndex}`} className="code-block">
          <div className="code-header">
            <span>{language}</span>
            <button
              className={`copy-button ${isCopied ? 'copied' : ''}`}
              onClick={() => copyToClipboard(code, blockId)}
            >
              {isCopied ? <Check size={12} /> : <Copy size={12} />}
              {isCopied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="code-content">{code}</div>
        </div>
      );

      lastIndex = match.index + match[0].length;
      blockIndex++;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <span key={`text-${blockIndex}`}>
          {content.slice(lastIndex)}
        </span>
      );
    }

    return parts.length > 1 ? <div>{parts}</div> : content;
  };

  return (
    <div className="chatgpt-container">
      <style>
        {`
          .chatgpt-container {
            display: flex;
            flex-direction: column;
            height: 100%;
            background: var(--neutral-50);
          }
          .chat-messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px 0;
            display: flex;
            flex-direction: column;
          }
          .chat-content-wrapper {
            display: grid;
            grid-template-columns: 2fr 8fr 2fr;
            gap: 16px;
            width: 100%;
          }
          .chat-messages-column {
            grid-column: 2;
            display: flex;
            flex-direction: column;
            gap: 16px;
          }
          .chat-bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            position: relative;
            width: fit-content;
            font-size: 16px;
          }
          .chat-bubble-user {
            background: var(--neutral-200);
            color: var(--neutral-800);
            align-self: flex-end;
            margin-left: auto;
            border-bottom-right-radius: 4px;
          }
          .chat-bubble-ai {
            background: transparent;
            color: var(--neutral-800);
            align-self: stretch;
            border: none;
            border-radius: 0;
            width: 100%;
            padding: 16px 0;
            line-height: 1.6;
          }
          .chat-bubble-system {
            background: var(--warning-orange-light);
            color: var(--warning-orange-dark);
            align-self: center;
            border-radius: 12px;
            font-size: 12px;
            max-width: 90%;
            text-align: center;
          }

          .chat-empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--neutral-500);
            text-align: center;
          }
          .chat-suggestions {
            display: flex;
            gap: 8px;
            margin-top: 16px;
            flex-wrap: wrap;
            justify-content: center;
          }
          .chat-input-area {
            padding: 32px 0 16px 0;
            background: white;
            border-top: 2px solid var(--neutral-300);
            display: grid;
            grid-template-columns: 2fr 8fr 2fr;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
          }
          .conversation-id-display {
            grid-column: 2;
            text-align: center;
            font-size: 11px;
            color: var(--neutral-500);
            margin-top: 8px;
            font-family: monospace;
          }
          .chat-input-wrapper {
            grid-column: 2;
            position: relative;
          }
          .chat-input-field {
            width: 100%;
            min-height: 56px;
            max-height: 140px;
            padding: 16px 60px 16px 20px;
            border: 2px solid var(--neutral-300);
            border-radius: 28px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            background: white;
            resize: none;
            font-family: inherit;
            line-height: 1.5;
          }
          .chat-input-field:focus {
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px var(--primary-blue-light), 0 2px 8px rgba(0, 0, 0, 0.1);
          }
          .chat-input-field:disabled {
            background: var(--neutral-100);
            color: var(--neutral-500);
          }
          .chat-send-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 18px;
            background: var(--primary-blue);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
          }
          .chat-send-btn:hover:not(:disabled) {
            background: var(--primary-blue-dark);
          }
          .chat-send-btn:disabled {
            background: var(--neutral-300);
            cursor: not-allowed;
          }
          .loading-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 16px 0;
            background: transparent;
            border: none;
            border-radius: 0;
            align-self: stretch;
            width: 100%;
            color: var(--neutral-600);
            font-size: 16px;
          }
          .code-block {
            background: var(--neutral-100);
            border: 1px solid var(--neutral-200);
            border-radius: 8px;
            margin: 12px 0;
            position: relative;
            overflow: hidden;
          }
          .code-header {
            background: var(--neutral-200);
            padding: 8px 12px;
            font-size: 12px;
            color: var(--neutral-600);
            border-bottom: 1px solid var(--neutral-300);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .code-content {
            padding: 16px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.4;
            overflow-x: auto;
            white-space: pre;
            color: var(--neutral-800);
          }
          .copy-button {
            background: var(--neutral-300);
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            cursor: pointer;
            color: var(--neutral-700);
            transition: background-color 0.15s ease;
          }
          .copy-button:hover {
            background: var(--neutral-400);
          }
          .copy-button.copied {
            background: var(--success-green);
            color: white;
          }
          
          .debug-toggle-area {
            padding: 8px 16px;
            background: var(--neutral-100);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: flex-end;
          }
          
          .debug-toggle-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--neutral-200);
            border: 1px solid var(--neutral-300);
            border-radius: 6px;
            color: var(--neutral-700);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
          }
          
          .debug-toggle-btn:hover {
            background: var(--neutral-300);
            border-color: var(--neutral-400);
          }
          
          .debug-toggle-btn.active {
            background: var(--primary-blue);
            border-color: var(--primary-blue);
            color: white;
          }
          
          .debug-info-panel {
            background: var(--neutral-100);
            border: 1px solid var(--neutral-300);
            border-radius: 8px;
            padding: 12px;
            margin-top: 8px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: var(--neutral-700);
          }
          
          .debug-section {
            margin-bottom: 12px;
          }
          
          .debug-section:last-child {
            margin-bottom: 0;
          }
          
          .debug-section-title {
            font-weight: bold;
            color: var(--primary-blue);
            margin-bottom: 4px;
            font-size: 12px;
          }
          
          .debug-json {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 8px;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 200px;
            overflow-y: auto;
          }
          
          .confidence-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
          }
          
          .confidence-high {
            background: var(--success-green-light);
            color: var(--success-green-dark);
          }
          
          .confidence-medium {
            background: var(--warning-orange-light);
            color: var(--warning-orange-dark);
          }
          
          .confidence-low {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
        `}
      </style>

      {/* Debug Mode Toggle */}
      <div className="debug-toggle-area">
        <button
          onClick={toggleDebugMode}
          className={`debug-toggle-btn ${debugMode ? 'active' : ''}`}
          title={debugMode ? 'Hide debug information' : 'Show debug information'}
        >
          {debugMode ? <Eye size={16} /> : <Bug size={16} />}
          {debugMode ? 'Normal View' : 'Debug Mode'}
        </button>
      </div>

      {/* Messages Area */}
      <div className="chat-messages-area">
        <div className="chat-content-wrapper">
          <div className="chat-messages-column">
            {chatMessages.length === 0 ? (
              <div className="chat-empty-state">
                <Bot size={48} style={{ color: 'var(--neutral-400)' }} />
                <p>Hi! I'm your AI assistant. Ask me to run automation tasks or help with OpsConductor.</p>
                <div className="chat-suggestions">
                  <button 
                    onClick={() => setChatInput('Show me the system status')}
                    className="btn btn-sm"
                  >
                    System Status
                  </button>
                  <button 
                    onClick={() => setChatInput('List all assets')}
                    className="btn btn-sm"
                  >
                    List Assets
                  </button>
                  <button 
                    onClick={() => setChatInput('Show recent job runs')}
                    className="btn btn-sm"
                  >
                    Recent Jobs
                  </button>
                </div>
              </div>
            ) : (
              // Reverse the order so newest messages appear on top
              [...chatMessages].reverse().map((message) => (
                <div key={message.id}>
                  <div className={`chat-bubble chat-bubble-${message.type}`}>
                    {message.type === 'ai' ? formatMessageContent(message.content, message.id) : message.content}
                  </div>
                  {renderDebugInfo(message)}
                </div>
              ))
            )}
            
            {/* Loading indicator */}
            {isChatLoading && (
              <div>
                <div className="loading-indicator">
                  <Loader size={16} className="loading-spinner" />
                  <span>Thinking...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Fixed Input Area */}
      <div className="chat-input-area">
        <form onSubmit={handleChatSubmit} className="chat-input-wrapper">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask me to run automation tasks..."
            className="chat-input-field"
            disabled={isChatLoading}
          />
          <button
            type="submit"
            disabled={!chatInput.trim() || isChatLoading}
            className="chat-send-btn"
          >
            {isChatLoading ? <Loader size={16} className="loading-spinner" /> : <Send size={16} />}
          </button>
        </form>
        <div className="conversation-id-display">
          {currentConversationId ? `Conversation: ${currentConversationId}` : 'No conversation ID yet'}
        </div>
      </div>
    </div>
  );
});

export default AIChat;