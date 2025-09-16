import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { userApi, targetApi, jobApi, jobRunApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ServiceHealthMonitor from '../components/ServiceHealthMonitor';
import { Users, Target, Settings, Play, Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2, RefreshCw } from 'lucide-react';

interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  jobId?: string;
  executionId?: string;
  confidence?: number;
  status?: 'pending' | 'success' | 'error';
}

interface ChatResponse {
  response: string;
  intent: string;
  confidence: number;
  job_id?: string;
  execution_id?: string;
  automation_job_id?: number;
  workflow?: any;
  execution_started: boolean;
}

const CHAT_HISTORY_KEY = 'opsconductor_ai_chat_history';

const Dashboard: React.FC = () => {
  const { isLoading: authLoading, isAuthenticated } = useAuth();
  const [stats, setStats] = useState({
    users: 0,
    targets: 0,
    jobs: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);

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
      console.warn('Failed to load chat history:', error);
    }
    
    return [
      {
        id: '1',
        type: 'system',
        content: 'Welcome to OpsConductor AI! I can help you automate tasks, check system health, get personalized recommendations, and more. Try asking: "What are my personalized recommendations?" or "Show me system health status".',
        timestamp: new Date()
      }
    ];
  };

  const [messages, setMessages] = useState<ChatMessage[]>(loadChatHistory());
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [serviceHealthLastUpdate, setServiceHealthLastUpdate] = useState<Date | null>(null);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages));
    } catch (error) {
      console.warn('Failed to save chat history:', error);
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const clearChatHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
      const welcomeMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'system',
        content: 'Welcome to OpsConductor AI! I can help you automate tasks, check system health, get personalized recommendations, and more. Try asking: "What are my personalized recommendations?" or "Show me system health status".',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const accessToken = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }

      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: userMessage.content
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ChatResponse = await response.json();

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: result.response,
        timestamp: new Date(),
        jobId: result.job_id,
        executionId: result.execution_id || undefined,
        confidence: result.confidence,
        status: result.intent === 'question' ? 'success' : (result.execution_started ? 'success' : 'error')
      };

      setMessages(prev => [...prev, aiMessage]);

      if (result.intent === 'job_creation' && result.workflow && result.execution_started) {
        const workflowMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          type: 'system',
          content: `Created workflow "${result.workflow.name}" with ${result.workflow.steps?.length || 0} steps targeting "${result.workflow.target_groups?.join(', ') || 'unknown targets'}". Job ID: ${result.automation_job_id || result.job_id}`,
          timestamp: new Date(),
          status: 'success'
        };
        setMessages(prev => [...prev, workflowMessage]);
      }

    } catch (error) {
      console.error('Error calling AI service:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `Sorry, I encountered an error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or check if the AI service is running.`,
        timestamp: new Date(),
        status: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getMessageIcon = (message: ChatMessage) => {
    switch (message.type) {
      case 'user':
        return <User size={16} style={{ color: 'var(--primary-blue)' }} />;
      case 'ai':
        return <Bot size={16} style={{ color: 'var(--success-green)' }} />;
      case 'system':
        return message.status === 'success' ? 
          <CheckCircle size={16} style={{ color: 'var(--success-green)' }} /> :
          message.status === 'error' ?
          <AlertCircle size={16} style={{ color: 'var(--danger-red)' }} /> :
          <Clock size={16} style={{ color: 'var(--neutral-500)' }} />;
      default:
        return null;
    }
  };

  const getMessageStyle = (message: ChatMessage) => {
    const baseStyle = "chat-message";
    
    switch (message.type) {
      case 'user':
        return `${baseStyle} chat-message-user`;
      case 'ai':
        return `${baseStyle} chat-message-ai`;
      case 'system':
        return `${baseStyle} chat-message-system`;
      default:
        return baseStyle;
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleRefreshServices = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const fetchStats = async () => {
    try {
      const requests = [
        userApi.list(0, 1),
        targetApi.list(0, 1),
        jobApi.list(0, 1),
        jobRunApi.list(0, 1)
      ];

      const [
        usersRes,
        targetsRes,
        jobsRes,
        runsRes
      ] = await Promise.allSettled(requests);

      const getTotal = (res: any) => {
        if (res.status !== 'fulfilled') return 0;
        // Handle new API response format with meta.total_items
        if (res.value?.meta?.total_items !== undefined) {
          return res.value.meta.total_items;
        }
        // Handle old API response format with total
        return res.value?.total ?? 0;
      };
      // Log failures for debugging but keep dashboard rendering
      if (usersRes.status === 'rejected') console.warn('Users stats failed:', usersRes.reason);
      if (targetsRes.status === 'rejected') console.warn('Targets stats failed:', targetsRes.reason);
      if (jobsRes.status === 'rejected') console.warn('Jobs stats failed:', jobsRes.reason);
      if (runsRes.status === 'rejected') console.warn('Runs stats failed:', runsRes.reason);

      setStats({
        users: getTotal(usersRes),
        targets: getTotal(targetsRes),
        jobs: getTotal(jobsRes),
        recentRuns: getTotal(runsRes)
      });
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      fetchStats();
    }
  }, [isAuthenticated, authLoading]);

  if (authLoading || loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard" style={{ 
      height: 'calc(100vh - 30px)', 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Ultra-compact header with inline stats */}
      <div className="dashboard-header" style={{ flexShrink: 0 }}>
        <div className="header-left">
          <h1>Dashboard</h1>
        </div>
        <div className="header-stats">
          <Link to="/user-management" className="stat-pill"><Users size={14} /> {stats.users}</Link>
          <Link to="/targets-management" className="stat-pill"><Target size={14} /> {stats.targets}</Link>
          <Link to="/job-management" className="stat-pill"><Settings size={14} /> {stats.jobs}</Link>
          <Link to="/job-runs" className="stat-pill"><Play size={14} /> {stats.recentRuns}</Link>

        </div>
      </div>

      {/* Full-width Service Health Card */}
      <div className="dashboard-section" style={{ 
        marginBottom: '12px',
        width: '100%',
        height: '120px',
        flexShrink: 0
      }}>
        <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Service Health</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {serviceHealthLastUpdate && (
              <span style={{ 
                fontSize: '12px', 
                color: 'var(--neutral-600)',
                fontWeight: 'normal'
              }}>
                Last updated: {serviceHealthLastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={handleRefreshServices}
              style={{
                background: 'none',
                border: '1px solid var(--neutral-300)',
                borderRadius: '4px',
                padding: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: 'var(--neutral-600)'
              }}
              title="Refresh service health"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </div>
        <div className="compact-content">
          <ServiceHealthMonitor 
            refreshTrigger={refreshTrigger} 
            onLastUpdateChange={setServiceHealthLastUpdate}
          />
        </div>
      </div>

      {/* AI Chat Interface - Takes remaining space */}
      <div className="dashboard-section" style={{ 
        flex: 1,
        margin: 0,
        borderRadius: '6px',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0
      }}>
        <div className="section-header" style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexShrink: 0
        }}>
          <span>AI Assistant</span>
          <button
            onClick={clearChatHistory}
            style={{ 
              background: 'none',
              border: '1px solid var(--neutral-300)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              color: 'var(--neutral-600)'
            }}
            title="Clear AI chat history"
          >
            <Trash2 size={12} />
            Clear Chat
          </button>
        </div>
        <div className="compact-content" style={{ 
          display: 'flex', 
          flexDirection: 'column',
          flex: 1,
          minHeight: 0,
          padding: 0
        }}>
          {/* Messages Area */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '8px',
            backgroundColor: 'var(--neutral-25)',
            minHeight: 0
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {messages.map((message) => (
                <div key={message.id} className={getMessageStyle(message)}>
                  <div style={{ flexShrink: 0 }}>
                    {getMessageIcon(message)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', lineHeight: '1.4' }}>
                      {message.content}
                    </div>
                    <div style={{ 
                      fontSize: '11px', 
                      color: 'var(--neutral-500)',
                      marginTop: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <span>{formatTimestamp(message.timestamp)}</span>
                      {message.confidence && (
                        <span className="status-badge status-badge-info">
                          {Math.round(message.confidence * 100)}%
                        </span>
                      )}
                      {message.jobId && (
                        <span className="status-badge status-badge-neutral">
                          {message.jobId.substring(0, 8)}...
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="chat-message chat-message-system">
                  <div style={{ flexShrink: 0 }}>
                    <Loader size={14} className="loading-spinner" />
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--neutral-600)' }}>
                    AI is processing your request...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area - Fixed at bottom */}
          <div style={{ 
            padding: '8px', 
            borderTop: '1px solid var(--neutral-200)',
            backgroundColor: 'var(--neutral-50)',
            flexShrink: 0
          }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '6px' }}>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask me anything... (e.g., 'What are my personalized recommendations?' or 'Show system health')"
                disabled={isLoading}
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  border: '1px solid var(--neutral-300)',
                  borderRadius: '4px',
                  fontSize: '13px',
                  outline: 'none',
                  backgroundColor: isLoading ? 'var(--neutral-100)' : 'white'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = 'var(--primary-blue)';
                  e.target.style.boxShadow = '0 0 0 2px var(--primary-blue-light)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'var(--neutral-300)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="btn btn-primary"
                style={{ fontSize: '13px', padding: '6px 12px' }}
              >
                {isLoading ? (
                  <Loader size={14} className="loading-spinner" />
                ) : (
                  <Send size={14} />
                )}
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;