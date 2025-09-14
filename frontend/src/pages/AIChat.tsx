import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2 } from 'lucide-react';

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

interface WorkflowResult {
  job_id: string;
  execution_id?: string;
  workflow: any;
  message: string;
  confidence: number;
  execution_started: boolean;
  automation_job_id?: number;
}

const CHAT_HISTORY_KEY = 'opsconductor_ai_chat_history';

const AIChat: React.FC = () => {
  // Load chat history from localStorage or use default welcome message
  const loadChatHistory = (): ChatMessage[] => {
    try {
      const saved = localStorage.getItem(CHAT_HISTORY_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    } catch (error) {
      console.warn('Failed to load chat history:', error);
    }
    
    // Return default welcome message if no history or error
    return [
      {
        id: '1',
        type: 'system',
        content: 'Welcome to OpsConductor AI! I can help you automate tasks using natural language. Try saying something like "update stationcontroller on CIS servers" or "restart nginx on web servers".',
        timestamp: new Date()
      }
    ];
  };

  const [messages, setMessages] = useState<ChatMessage[]>(loadChatHistory());
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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
        content: 'Welcome to OpsConductor AI! I can help you automate tasks using natural language. Try saying something like "update stationcontroller on CIS servers" or "restart nginx on web servers".',
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
      // Get authentication token
      const accessToken = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }

      // Call AI service to execute the job
      const response = await fetch('/api/v1/ai/execute-job', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          description: userMessage.content,
          execute_immediately: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: WorkflowResult = await response.json();

      // Create AI response message
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: result.message,
        timestamp: new Date(),
        jobId: result.job_id,
        executionId: result.execution_id || undefined,
        confidence: result.confidence,
        status: result.execution_started ? 'success' : 'error'
      };

      setMessages(prev => [...prev, aiMessage]);

      // If execution started, add workflow details
      if (result.workflow && result.execution_started) {
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

  return (
    <div className="dense-dashboard">
      {/* Dashboard-style header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>AI Assistant</h1>
        </div>
        <div className="header-stats">
          <span style={{ 
            fontSize: '12px', 
            color: 'var(--neutral-600)',
            padding: '4px 8px'
          }}>
            Describe what you want to automate in natural language
          </span>
          <button
            onClick={clearChatHistory}
            className="btn btn-secondary"
            style={{ 
              fontSize: '12px', 
              padding: '4px 8px',
              marginLeft: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
            title="Clear chat history"
          >
            <Trash2 size={12} />
            Clear History
          </button>
        </div>
      </div>

      {/* Full-page chat layout */}
      <div className="dashboard-section" style={{ 
        height: 'calc(100vh - 110px)',
        margin: 0,
        borderRadius: '6px'
      }}>
        <div className="section-header">AI Chat</div>
        <div className="compact-content" style={{ 
          display: 'flex', 
          flexDirection: 'column',
          height: '100%',
          padding: 0
        }}>
          {/* Messages Area */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '8px',
            backgroundColor: 'var(--neutral-25)'
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
            backgroundColor: 'var(--neutral-50)'
          }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '6px' }}>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your automation request... (e.g., 'restart nginx on web servers')"
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

export default AIChat;