import React, { useState, useRef, useEffect, useImperativeHandle } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2, RefreshCw, Copy, Check, Bug, Eye, Brain, Target, Zap, Shield, TrendingUp, Activity, AlertTriangle, Info, ChevronDown, ChevronRight, X } from 'lucide-react';
import { aiApi } from '../services/api';
import ThinkingVisualization from './ThinkingVisualization';

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
  fulfillmentId?: string;
  fulfillmentStatus?: 'planning' | 'gathering_info' | 'ready' | 'executing' | 'completed' | 'failed' | 'cancelled';
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
  fulfillment_id?: string;
  fulfillment_status?: string;
  execution_plan?: any;
  estimated_duration?: number;
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
  debugMode?: boolean;
}

export interface AIChatRef {
  clearChat: () => void;
  clearChatHistory: () => void;
}

const AIChat = React.forwardRef<AIChatRef, AIChatProps>(({ onClearChat, onFirstMessage, activeChatId, debugMode = false }, ref) => {
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
  const showThinkingVisualization = debugMode;
  const [thinkingSessionId, setThinkingSessionId] = useState<string | null>(null);
  const [isThinkingConnected, setIsThinkingConnected] = useState(false);
  const [expandedDebugPanels, setExpandedDebugPanels] = useState<Set<string>>(new Set());
  const [debugModalMessage, setDebugModalMessage] = useState<ChatMessage | null>(null);
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

  // Utility functions for confidence and risk display
  const getConfidenceClass = (confidence?: number) => {
    if (!confidence) return 'confidence-low';
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
  };

  const formatConfidence = (confidence?: number) => {
    return confidence ? `${(confidence * 100).toFixed(1)}%` : 'N/A';
  };

  const getRiskClass = (riskLevel?: string) => {
    if (!riskLevel) return 'risk-low';
    const level = riskLevel.toLowerCase();
    if (level === 'high') return 'risk-high';
    if (level === 'medium') return 'risk-medium';
    return 'risk-low';
  };

  const formatRiskLevel = (riskLevel?: string) => {
    return riskLevel ? riskLevel.toUpperCase() : 'UNKNOWN';
  };

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

    // Clear thinking session ID when starting new chat - will be set from backend response
    setThinkingSessionId(null);

    try {
      // Get the last AI message to extract conversation_id if available
      const lastAiMessage = chatMessages.slice().reverse().find(msg => msg.type === 'ai');
      const conversationId = lastAiMessage?.conversationId;
      
      const data = await aiApi.chat({
        message: userMessage.content,
        user_id: "1", // TODO: Get from auth context
        conversation_id: conversationId,
        debug_mode: debugMode
      });
      
      // Check if there's an error in the response
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Update thinking session ID if provided by backend
      console.log('🔍 Backend response data:', data);
      console.log('🔍 Debug mode:', debugMode);
      console.log('🔍 Thinking session ID from backend:', (data as any).thinking_session_id);
      
      if ((data as any).thinking_session_id && debugMode) {
        console.log('🧠 Setting thinking session ID from backend:', (data as any).thinking_session_id);
        setThinkingSessionId((data as any).thinking_session_id);
      } else {
        console.log('🔍 Not setting thinking session ID - debugMode:', debugMode, 'thinking_session_id:', (data as any).thinking_session_id);
      }
      
      // Create AI message with routing info if available
      let aiContent = data.response || data.error || 'No response received';
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
        fulfillmentId: (data as any).fulfillment_id,
        fulfillmentStatus: (data as any).fulfillment_status,
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

  const toggleDebugPanel = (messageId: string) => {
    setExpandedDebugPanels(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
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

    const intent = message.debugInfo.intent_classification;
    const routing = message.debugInfo.routing;
    const isExpanded = expandedDebugPanels.has(message.id);

    return (
      <div className="debug-info-panel">
        {/* Collapsible Header */}
        <div 
          className="debug-panel-header clickable"
          onClick={() => toggleDebugPanel(message.id)}
        >
          <div className="debug-panel-title">
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Brain className="debug-section-icon" />
            AI Debug Information
            {!isExpanded && (
              <span className="debug-summary">
                {intent?.intent_type && ` • ${intent.intent_type}`}
                {intent?.confidence && ` • ${formatConfidence(intent.confidence)}`}
                {routing?.response_time && ` • ${routing.response_time}ms`}
              </span>
            )}
          </div>
          <div className="debug-panel-badge">
            {intent?.metadata?.engine || 'AI Engine'}
          </div>
        </div>

        {/* Expandable Content */}
        {isExpanded && (
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
          {intent && (intent as any)?.context_analysis && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Shield className="debug-section-icon" />
                  Context Analysis
                </div>
                <span className={`risk-indicator ${getRiskClass((intent as any).context_analysis.risk_level)}`}>
                  <AlertTriangle size={14} />
                  {formatRiskLevel((intent as any).context_analysis.risk_level)}
                </span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Context Confidence</span>
                <span className="debug-field-value">{formatConfidence((intent as any).context_analysis.confidence_score)}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Risk Level</span>
                <span className="debug-field-value">{formatRiskLevel((intent as any).context_analysis.risk_level)}</span>
              </div>

              <div className="debug-field">
                <span className="debug-field-label">Requirements Count</span>
                <span className="debug-field-value">{(intent as any).context_analysis.requirements_count || 0}</span>
              </div>

              {/* Recommendations */}
              {(intent as any).context_analysis.recommendations && (intent as any).context_analysis.recommendations.length > 0 && (
                <div>
                  <div className="debug-field-label" style={{ marginTop: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
                    Recommendations
                  </div>
                  <div className="recommendations-list">
                    {(intent as any).context_analysis.recommendations.map((rec: any, index: number) => (
                      <div key={index} className="recommendation-item">
                        <AlertTriangle className="recommendation-icon" />
                        <span className="recommendation-text">
                          {typeof rec === 'string' ? rec : (rec?.title || rec?.description || JSON.stringify(rec))}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Alternative Intents Section */}
          {intent && (intent as any)?.alternatives && (intent as any).alternatives.length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <TrendingUp className="debug-section-icon" />
                  Alternative Intents
                </div>
              </div>

              <div className="alternatives-list">
                {(intent as any).alternatives.map((alt: any, index: number) => (
                  <div key={index} className="alternative-item">
                    <span className="alternative-name">{alt.intent}</span>
                    <span className="alternative-confidence">{formatConfidence(alt.confidence)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entities Section */}
          {intent && (intent as any)?.entities && (intent as any).entities.length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Zap className="debug-section-icon" />
                  Extracted Entities
                </div>
              </div>

              <div className="entities-list">
                {(intent as any).entities.map((entity: any, index: number) => (
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

          {/* Multi-Brain Consultations Section */}
          {intent && (intent.metadata as any)?.brains_consulted && (intent.metadata as any).brains_consulted.length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Brain className="debug-section-icon" />
                  Multi-Brain Consultations
                </div>
              </div>
              
              <div className="brains-consulted-list">
                {(intent.metadata as any).brains_consulted.map((brain: string, index: number) => (
                  <div key={index} className="brain-consulted-item">
                    <span className="brain-name">{brain}</span>
                    <span className="brain-status">✓ Consulted</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SME Consultations Section */}
          {intent && (intent.metadata as any)?.sme_consultations && Object.keys((intent.metadata as any).sme_consultations).length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Shield className="debug-section-icon" />
                  SME Brain Consultations
                </div>
              </div>
              
              <div className="sme-consultations-list">
                {Object.entries((intent.metadata as any).sme_consultations).map(([domain, consultation]: [string, any], index: number) => (
                  <div key={index} className="sme-consultation-item">
                    <div className="sme-domain">{domain.replace(/_/g, ' ').toUpperCase()}</div>
                    <div className="sme-details">
                      {consultation.confidence && (
                        <span className={`sme-confidence ${getConfidenceClass(consultation.confidence)}`}>
                          {formatConfidence(consultation.confidence)}
                        </span>
                      )}
                      {consultation.recommendations && consultation.recommendations.length > 0 && (
                        <div className="sme-recommendations">
                          {consultation.recommendations.slice(0, 2).map((rec: any, recIndex: number) => (
                            <div key={recIndex} className="sme-recommendation">
                              {typeof rec === 'string' ? rec : (rec?.title || rec?.description || JSON.stringify(rec))}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical Plan Section */}
          {intent && (intent.metadata as any)?.technical_plan && Object.keys((intent.metadata as any).technical_plan).length > 0 && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Target className="debug-section-icon" />
                  Technical Plan
                </div>
              </div>
              
              <div className="technical-plan-details">
                {(intent.metadata as any).technical_plan.confidence_score && (
                  <div className="debug-field">
                    <span className="debug-field-label">Plan Confidence</span>
                    <span className="debug-field-value">{formatConfidence((intent.metadata as any).technical_plan.confidence_score)}</span>
                  </div>
                )}
                {(intent.metadata as any).technical_plan.complexity_level && (
                  <div className="debug-field">
                    <span className="debug-field-label">Complexity</span>
                    <span className="debug-field-value">{(intent.metadata as any).technical_plan.complexity_level}</span>
                  </div>
                )}
                {(intent.metadata as any).technical_plan.estimated_duration && (
                  <div className="debug-field">
                    <span className="debug-field-label">Est. Duration</span>
                    <span className="debug-field-value">{(intent.metadata as any).technical_plan.estimated_duration}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Job Details Section (for job creation) */}
          {(intent?.metadata as any)?.job_details && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Zap className="debug-section-icon" />
                  Job Creation Details
                </div>
              </div>
              
              <div className="job-details">
                {intent && (intent.metadata as any).job_details?.job_id && (
                  <div className="debug-field">
                    <span className="debug-field-label">Job ID</span>
                    <span className="debug-field-value code">{(intent.metadata as any).job_details.job_id}</span>
                  </div>
                )}
                {intent && (intent.metadata as any).job_details?.automation_job_id && (
                  <div className="debug-field">
                    <span className="debug-field-label">Automation Job ID</span>
                    <span className="debug-field-value">{(intent.metadata as any).job_details.automation_job_id}</span>
                  </div>
                )}
                {intent && (intent.metadata as any).job_details?.workflow_steps !== undefined && (
                  <div className="debug-field">
                    <span className="debug-field-label">Workflow Steps</span>
                    <span className="debug-field-value">{(intent.metadata as any).job_details.workflow_steps}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Fulfillment Status Section */}
          {(message.fulfillmentId || message.fulfillmentStatus) && (
            <div className="debug-section">
              <div className="debug-section-header">
                <div className="debug-section-title">
                  <Zap className="debug-section-icon" />
                  Fulfillment Status
                </div>
                <span className={`fulfillment-status-indicator ${message.fulfillmentStatus || 'unknown'}`}>
                  {message.fulfillmentStatus?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>

              {message.fulfillmentId && (
                <div className="debug-field">
                  <span className="debug-field-label">Fulfillment ID</span>
                  <span className="debug-field-value code">{message.fulfillmentId}</span>
                </div>
              )}

              {message.fulfillmentStatus && (
                <div className="debug-field">
                  <span className="debug-field-label">Status</span>
                  <span className="debug-field-value">{message.fulfillmentStatus}</span>
                </div>
              )}

              {/* Fulfillment Progress Bar */}
              {message.fulfillmentStatus && ['executing', 'completed'].includes(message.fulfillmentStatus) && (
                <div className="fulfillment-progress">
                  <div className="progress-label">Execution Progress</div>
                  <div className="progress-bar">
                    <div 
                      className={`progress-fill ${message.fulfillmentStatus === 'completed' ? 'completed' : 'executing'}`}
                      style={{ width: message.fulfillmentStatus === 'completed' ? '100%' : '75%' }}
                    />
                  </div>
                </div>
              )}
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
        )}
      </div>
    );
  };

  const renderDebugInfoModal = (message: ChatMessage) => {
    if (!message.debugInfo) return null;

    const intent = message.debugInfo.intent_classification;
    const routing = message.debugInfo.routing;

    return (
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
              <span className="debug-field-label">Method</span>
              <span className="debug-field-value">{intent.method || 'Unknown'}</span>
            </div>

            <div className="debug-field">
              <span className="debug-field-label">Engine</span>
              <span className="debug-field-value">{intent.metadata?.engine || 'Unknown'}</span>
            </div>

            {intent.reasoning && (
              <div className="debug-field">
                <span className="debug-field-label">AI Reasoning</span>
                <span className="debug-field-value">{intent.reasoning}</span>
              </div>
            )}

            {intent.alternatives && intent.alternatives.length > 0 && (
              <div className="debug-field">
                <span className="debug-field-label">Alternative Intents</span>
                <div className="alternatives-list">
                  {intent.alternatives.map((alt, index) => (
                    <div key={index} className="alternative-item">
                      <span className="alt-intent">{alt.intent}</span>
                      <span className={`alt-confidence ${getConfidenceClass(alt.confidence)}`}>
                        {formatConfidence(alt.confidence)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {intent.entities && intent.entities.length > 0 && (
              <div className="debug-field">
                <span className="debug-field-label">Entities</span>
                <div className="entities-list">
                  {intent.entities.map((entity, index) => (
                    <div key={index} className="entity-item">
                      <span className="entity-value">{entity.value}</span>
                      <span className="entity-type">{entity.type}</span>
                      <span className={`entity-confidence ${getConfidenceClass(entity.confidence)}`}>
                        {formatConfidence(entity.confidence)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {intent.context_analysis && (
              <div className="debug-field">
                <span className="debug-field-label">Context Analysis</span>
                <div className="context-analysis">
                  <div className="context-metrics">
                    <span className="context-item">
                      <strong>Confidence:</strong> 
                      <span className={`confidence-badge ${getConfidenceClass(intent.context_analysis.confidence_score)}`}>
                        {formatConfidence(intent.context_analysis.confidence_score)}
                      </span>
                    </span>
                    <span className="context-item">
                      <strong>Risk Level:</strong> 
                      <span className={`risk-badge risk-${intent.context_analysis.risk_level?.toLowerCase()}`}>
                        {intent.context_analysis.risk_level}
                      </span>
                    </span>
                    <span className="context-item">
                      <strong>Requirements:</strong> {intent.context_analysis.requirements_count}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Routing Information Section */}
        {routing && (
          <div className="debug-section">
            <div className="debug-section-header">
              <div className="debug-section-title">
                <Zap className="debug-section-icon" />
                Routing Information
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

        {/* Multi-Brain Consultations Section */}
        {intent && (intent.metadata as any)?.brains_consulted && (intent.metadata as any).brains_consulted.length > 0 && (
          <div className="debug-section">
            <div className="debug-section-header">
              <div className="debug-section-title">
                <Brain className="debug-section-icon" />
                Multi-Brain Consultations
              </div>
            </div>
            
            <div className="brains-consulted-list">
              {(intent.metadata as any).brains_consulted.map((brain: string, index: number) => (
                <div key={index} className="brain-consulted-item">
                  <span className="brain-name">{brain}</span>
                  <span className="brain-status">✓ Consulted</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SME Consultations Section */}
        {intent && (intent.metadata as any)?.sme_consultations && Object.keys((intent.metadata as any).sme_consultations).length > 0 && (
          <div className="debug-section">
            <div className="debug-section-header">
              <div className="debug-section-title">
                <Shield className="debug-section-icon" />
                SME Consultations
              </div>
            </div>
            
            <div className="sme-consultations-list">
              {Object.entries((intent.metadata as any).sme_consultations).map(([sme, details]: [string, any], index) => (
                <div key={index} className="sme-consultation-item">
                  <div className="sme-header">
                    <span className="sme-name">{sme}</span>
                    <span className={`sme-status ${details.consulted ? 'consulted' : 'not-consulted'}`}>
                      {details.consulted ? '✓ Consulted' : '✗ Not Consulted'}
                    </span>
                  </div>
                  {details.reasoning && (
                    <div className="sme-reasoning">{details.reasoning}</div>
                  )}
                </div>
              ))}
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
    );
  };

  const formatMessageContent = (content: string, messageId: string) => {
    // Safety check for undefined content
    if (!content || typeof content !== 'string') {
      return <span>No content available</span>;
    }
    
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

          .chat-main-content {
            display: flex;
            flex: 1;
            gap: 16px;
            overflow: hidden;
          }
          .chat-main-content.full-width {
            gap: 0;
          }
          .thinking-panel {
            flex: 0 0 25%;
            min-width: 0;
            overflow-y: auto;
            border-right: 2px solid var(--neutral-200);
            padding-right: 16px;
          }
          .chat-messages-area {
            flex: 0 0 75%;
            min-width: 0;
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
            background: var(--neutral-50);
            color: var(--neutral-800);
            align-self: stretch;
            border: 1px solid var(--neutral-200);
            border-radius: 12px;
            width: 100%;
            padding: 16px;
            line-height: 1.6;
            position: relative;
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
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: var(--neutral-800);
            line-height: 1.4;
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
          
          /* Multi-Brain Debug Styles */
          .brains-consulted-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
          }
          
          .brain-consulted-item {
            display: flex;
            align-items: center;
            gap: 4px;
            background: var(--primary-blue-light);
            border: 1px solid var(--primary-blue);
            border-radius: 4px;
            padding: 3px 6px;
            font-size: 10px;
          }
          
          .brain-name {
            font-weight: bold;
            color: var(--primary-blue-dark);
          }
          
          .brain-status {
            color: var(--success-green);
            font-size: 9px;
          }
          
          .sme-consultations-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 6px;
          }
          
          .sme-consultation-item {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
            padding: 6px;
          }
          
          .sme-domain {
            font-weight: bold;
            color: var(--primary-blue-dark);
            font-size: 10px;
            margin-bottom: 4px;
          }
          
          .sme-details {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
          
          .sme-confidence {
            align-self: flex-start;
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
          }
          
          .sme-recommendations {
            display: flex;
            flex-direction: column;
            gap: 2px;
          }
          
          .sme-recommendation {
            font-size: 9px;
            color: var(--neutral-600);
            padding: 2px 4px;
            background: var(--warning-orange-light);
            border-radius: 3px;
          }
          
          .technical-plan-details {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 6px;
          }
          
          .job-details {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 6px;
          }
          
          .debug-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--neutral-300);
          }
          
          .debug-panel-header.clickable {
            cursor: pointer;
            transition: background-color 0.2s ease;
            padding: 8px;
            margin: -8px;
            border-radius: 6px;
          }
          
          .debug-panel-header.clickable:hover {
            background-color: var(--neutral-100);
          }
          
          .debug-panel-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: bold;
            color: var(--primary-blue-dark);
            font-size: 12px;
          }
          
          .debug-summary {
            color: var(--neutral-600);
            font-weight: normal;
            font-size: 11px;
            margin-left: 8px;
          }
          
          .debug-panel-badge {
            background: var(--primary-blue);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
          }
          
          .debug-sections-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
          }
          
          .debug-section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
          }
          
          .debug-section-title {
            display: flex;
            align-items: center;
            gap: 4px;
            font-weight: bold;
            color: var(--primary-blue);
            font-size: 11px;
          }
          
          .debug-section-icon {
            width: 12px;
            height: 12px;
          }
          
          .debug-field {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3px;
          }
          
          .debug-field-label {
            font-size: 10px;
            color: var(--neutral-600);
            font-weight: normal;
          }
          
          .debug-field-value {
            font-size: 10px;
            color: var(--neutral-800);
            font-weight: bold;
          }
          
          .debug-field-value.code {
            font-family: 'Courier New', monospace;
            background: var(--neutral-100);
            padding: 1px 3px;
            border-radius: 2px;
          }
          
          .confidence-bar {
            width: 100%;
            height: 4px;
            background: var(--neutral-200);
            border-radius: 2px;
            margin: 4px 0;
            overflow: hidden;
          }
          
          .confidence-fill {
            height: 100%;
            transition: width 0.3s ease;
          }
          
          .confidence-fill.high {
            background: var(--success-green);
          }
          
          .confidence-fill.medium {
            background: var(--warning-orange);
          }
          
          .confidence-fill.low {
            background: var(--danger-red);
          }
          
          .risk-indicator {
            display: flex;
            align-items: center;
            gap: 3px;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
          }
          
          .risk-high {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          
          .risk-medium {
            background: var(--warning-orange-light);
            color: var(--warning-orange-dark);
          }
          
          .risk-low {
            background: var(--success-green-light);
            color: var(--success-green-dark);
          }
          
          .alternatives-list {
            display: flex;
            flex-direction: column;
            gap: 3px;
            margin-top: 6px;
          }
          
          .alternative-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 3px 6px;
            background: var(--neutral-50);
            border-radius: 3px;
          }
          
          .alternative-name {
            font-size: 10px;
            color: var(--neutral-700);
          }
          
          .alternative-confidence {
            font-size: 9px;
            color: var(--neutral-500);
            font-weight: bold;
          }
          
          .entities-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 6px;
          }
          
          .entity-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 6px;
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 4px;
          }
          
          .entity-details {
            display: flex;
            flex-direction: column;
            gap: 1px;
          }
          
          .entity-value {
            font-size: 10px;
            font-weight: bold;
            color: var(--neutral-800);
          }
          
          .entity-type {
            font-size: 9px;
            color: var(--neutral-500);
            text-transform: uppercase;
          }
          
          .entity-confidence {
            font-size: 9px;
            color: var(--neutral-600);
            font-weight: bold;
          }
          
          .performance-metrics {
            display: flex;
            gap: 12px;
            margin-top: 6px;
            margin-bottom: 6px;
          }
          
          .metric-item {
            text-align: center;
          }
          
          .metric-value {
            font-size: 12px;
            font-weight: bold;
            color: var(--primary-blue);
          }
          
          .metric-label {
            font-size: 9px;
            color: var(--neutral-600);
            margin-top: 2px;
          }
          
          .recommendations-list {
            display: flex;
            flex-direction: column;
            gap: 3px;
            margin-top: 6px;
          }
          
          .recommendation-item {
            display: flex;
            align-items: flex-start;
            gap: 4px;
            padding: 3px 6px;
            background: var(--warning-orange-light);
            border-radius: 3px;
          }
          
          .recommendation-icon {
            width: 10px;
            height: 10px;
            color: var(--warning-orange);
            margin-top: 1px;
            flex-shrink: 0;
          }
          
          .recommendation-text {
            font-size: 9px;
            color: var(--warning-orange-dark);
            line-height: 1.2;
          }
          
          /* Intent Analysis Display Styles */
          .intent-analysis-display {
            background: linear-gradient(135deg, var(--primary-blue-light) 0%, var(--neutral-50) 100%);
            border: 2px solid var(--primary-blue);
            border-radius: 12px;
            margin: 12px 0;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
          }
          
          .intent-analysis-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--primary-blue);
          }
          
          .intent-icon {
            width: 20px;
            height: 20px;
            color: var(--primary-blue);
          }
          
          .intent-title {
            font-weight: 600;
            color: var(--primary-blue-dark);
            font-size: 14px;
          }
          
          .intent-confidence {
            margin-left: auto;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
          }
          
          .intent-analysis-content {
            display: flex;
            flex-direction: column;
            gap: 12px;
          }
          
          .intent-type {
            font-size: 14px;
            color: var(--neutral-800);
          }
          
          .intent-reasoning {
            font-size: 13px;
            color: var(--neutral-700);
            background: white;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid var(--primary-blue);
            line-height: 1.5;
          }
          
          .intent-context {
            background: white;
            padding: 10px;
            border-radius: 8px;
          }
          
          .context-details {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
          }
          
          .context-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--neutral-700);
          }
          
          .risk-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
          }
          
          .risk-low {
            background: var(--success-green-light);
            color: var(--success-green-dark);
          }
          
          .risk-medium {
            background: var(--warning-orange-light);
            color: var(--warning-orange-dark);
          }
          
          .risk-high {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          
          .risk-unknown {
            background: var(--neutral-200);
            color: var(--neutral-600);
          }

          /* Debug Info Icon Styles */
          .debug-info-icon {
            position: absolute;
            top: 8px;
            right: 8px;
            background: var(--neutral-100);
            border: 1px solid var(--neutral-300);
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            color: var(--primary-blue);
            z-index: 10;
          }

          .debug-info-icon:hover {
            background: var(--primary-blue-light);
            border-color: var(--primary-blue);
            transform: scale(1.05);
          }

          /* Debug Modal Styles */
          .debug-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 20px;
          }

          .debug-modal {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
            max-width: 90vw;
            max-height: 90vh;
            width: 800px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
          }

          .debug-modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            border-bottom: 1px solid var(--neutral-200);
            background: var(--neutral-50);
          }

          .debug-modal-header h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            color: var(--neutral-800);
          }

          .debug-modal-close {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            color: var(--neutral-500);
            transition: all 0.2s ease;
          }

          .debug-modal-close:hover {
            background: var(--neutral-200);
            color: var(--neutral-700);
          }

          .debug-modal-content {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
          }

          /* Make chat bubbles relative positioned for the debug icon */
          .chat-bubble {
            position: relative;
          }
        `}
      </style>



      {/* Main Content Area - Split Layout */}
      <div className={`chat-main-content ${!showThinkingVisualization ? 'full-width' : ''}`}>
        {/* Real-time Thinking Visualization */}
        {showThinkingVisualization && (
          <div className="thinking-panel">
            {thinkingSessionId ? (
              <ThinkingVisualization
                sessionId={thinkingSessionId}
                isActive={true}
                onConnectionChange={setIsThinkingConnected}
              />
            ) : (
              <div style={{ 
                padding: '20px', 
                textAlign: 'center', 
                color: 'var(--neutral-500)',
                fontSize: '14px'
              }}>
                <Brain size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                <div>AI Thinking Stream</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  Send a message to see real-time AI thinking
                </div>
              </div>
            )}
          </div>
        )}

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
                    {/* Debug Info Icon - only show for AI messages with debug info */}
                    {debugMode && message.type === 'ai' && message.debugInfo && (
                      <button
                        className="debug-info-icon"
                        onClick={() => setDebugModalMessage(message)}
                        title="View AI Debug Information"
                      >
                        <Brain size={14} />
                      </button>
                    )}
                  </div>
                  {/* Intent Analysis Display - Always visible for AI messages */}
                  {message.type === 'ai' && message.debugInfo?.intent_classification && (
                    <div className="intent-analysis-display">
                      <div className="intent-analysis-header">
                        <Brain className="intent-icon" />
                        <span className="intent-title">AI Intent Understanding</span>
                        <span className={`intent-confidence ${getConfidenceClass(message.debugInfo.intent_classification.confidence)}`}>
                          {formatConfidence(message.debugInfo.intent_classification.confidence)}
                        </span>
                      </div>
                      <div className="intent-analysis-content">
                        <div className="intent-type">
                          <strong>Intent Type:</strong> {message.debugInfo.intent_classification.intent_type}
                        </div>
                        {message.debugInfo.intent_classification.reasoning && (
                          <div className="intent-reasoning">
                            <strong>AI Understanding:</strong> {message.debugInfo.intent_classification.reasoning}
                          </div>
                        )}
                        {message.debugInfo.intent_classification.context_analysis && (
                          <div className="intent-context">
                            <div className="context-details">
                              <span className="context-item">
                                <strong>Risk Level:</strong> 
                                <span className={`risk-badge risk-${message.debugInfo.intent_classification.context_analysis.risk_level?.toLowerCase()}`}>
                                  {message.debugInfo.intent_classification.context_analysis.risk_level}
                                </span>
                              </span>
                              <span className="context-item">
                                <strong>Requirements:</strong> {message.debugInfo.intent_classification.context_analysis.requirements_count}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
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

      {/* Debug Info Modal */}
      {debugModalMessage && (
        <div className="debug-modal-overlay" onClick={() => setDebugModalMessage(null)}>
          <div className="debug-modal" onClick={(e) => e.stopPropagation()}>
            <div className="debug-modal-header">
              <h3>
                <Brain size={20} />
                AI Debug Information
              </h3>
              <button
                className="debug-modal-close"
                onClick={() => setDebugModalMessage(null)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="debug-modal-content">
              {renderDebugInfoModal(debugModalMessage)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default AIChat;