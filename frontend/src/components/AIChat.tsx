import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2, RefreshCw } from 'lucide-react';

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

const AIChat: React.FC = () => {
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
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  useEffect(() => {
    saveChatHistory(chatMessages);
  }, [chatMessages]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);
    setChatError(null);

    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ message: userMessage.content })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();
      
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        confidence: data.confidence,
        jobId: data.job_id,
        executionId: data.execution_id,
        status: data.execution_started ? 'pending' : undefined
      };

      setChatMessages(prev => [...prev, aiMessage]);

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
    localStorage.removeItem(CHAT_HISTORY_KEY);
  };

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

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-row">
          <h3 className="card-title">
            <Bot size={20} />
            AI Assistant
          </h3>
          <div className="card-actions">
            <button
              onClick={clearChatHistory}
              className="btn btn-sm"
              title="Clear chat history"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
        <p className="card-subtitle">
          Ask me to run automation tasks, check system status, or get help with OpsConductor
        </p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
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
                  onClick={() => setChatInput('List all targets')}
                  className="btn btn-sm"
                >
                  List Targets
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
            chatMessages.map((message) => (
              <div key={message.id} className={`chat-message chat-message-${message.type}`}>
                <div className="chat-message-header">
                  <div className="chat-message-icon" style={{ color: getMessageStatusColor(message) }}>
                    {getMessageIcon(message)}
                  </div>
                  <span className="chat-message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                  {message.confidence && (
                    <span className="chat-confidence">
                      {Math.round(message.confidence * 100)}% confident
                    </span>
                  )}
                </div>
                <div className="chat-message-content">
                  {message.content}
                </div>
              </div>
            ))
          )}
          {isChatLoading && (
            <div className="chat-message chat-message-ai">
              <div className="chat-message-header">
                <div className="chat-message-icon">
                  <Loader size={16} className="loading-spinner" />
                </div>
                <span className="chat-message-time">Now</span>
              </div>
              <div className="chat-message-content">
                Thinking...
              </div>
            </div>
          )}
          <div ref={chatMessagesEndRef} />
        </div>

        <form onSubmit={handleChatSubmit} className="chat-input-form">
          <div className="chat-input-container">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask me to run automation tasks..."
              className="chat-input"
              disabled={isChatLoading}
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || isChatLoading}
              className="chat-send-button"
            >
              {isChatLoading ? <Loader size={16} className="loading-spinner" /> : <Send size={16} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AIChat;