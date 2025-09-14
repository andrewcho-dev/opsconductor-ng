import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { enhancedApi } from '../services/enhancedApi';

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

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to OpsConductor AI! I can help you automate tasks using natural language. Try saying something like "update stationcontroller on CIS servers" or "restart nginx on web servers".',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
        return <User size={16} className="text-blue-600" />;
      case 'ai':
        return <Bot size={16} className="text-green-600" />;
      case 'system':
        return message.status === 'success' ? 
          <CheckCircle size={16} className="text-green-600" /> :
          message.status === 'error' ?
          <AlertCircle size={16} className="text-red-600" /> :
          <Clock size={16} className="text-gray-600" />;
      default:
        return null;
    }
  };

  const getMessageStyle = (message: ChatMessage) => {
    const baseStyle = "flex gap-3 p-4 rounded-lg max-w-4xl";
    
    switch (message.type) {
      case 'user':
        return `${baseStyle} bg-blue-50 border border-blue-200 ml-auto`;
      case 'ai':
        return `${baseStyle} bg-green-50 border border-green-200`;
      case 'system':
        return `${baseStyle} bg-gray-50 border border-gray-200`;
      default:
        return baseStyle;
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="ai-chat-container" style={{ height: 'calc(100vh - 80px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="chat-header" style={{ 
        padding: '20px', 
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        <h1 style={{ 
          margin: 0, 
          fontSize: '24px', 
          fontWeight: 'bold',
          color: '#1f2937',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <Bot size={28} className="text-green-600" />
          AI Assistant
        </h1>
        <p style={{ 
          margin: '5px 0 0 0', 
          color: '#6b7280',
          fontSize: '14px'
        }}>
          Describe what you want to automate in natural language
        </p>
      </div>

      {/* Messages */}
      <div className="chat-messages" style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '20px',
        backgroundColor: '#ffffff'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((message) => (
            <div key={message.id} className={getMessageStyle(message)}>
              <div style={{ flexShrink: 0 }}>
                {getMessageIcon(message)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontSize: '14px', 
                  lineHeight: '1.5',
                  color: '#374151'
                }}>
                  {message.content}
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#9ca3af',
                  marginTop: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>{formatTimestamp(message.timestamp)}</span>
                  {message.confidence && (
                    <span>Confidence: {Math.round(message.confidence * 100)}%</span>
                  )}
                  {message.jobId && (
                    <span>Job: {message.jobId.substring(0, 8)}...</span>
                  )}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 p-4 rounded-lg max-w-4xl bg-gray-50 border border-gray-200">
              <Loader size={16} className="text-gray-600 animate-spin" />
              <div style={{ fontSize: '14px', color: '#6b7280' }}>
                AI is processing your request...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="chat-input" style={{ 
        padding: '20px', 
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your automation request... (e.g., 'restart nginx on web servers')"
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              outline: 'none',
              backgroundColor: isLoading ? '#f3f4f6' : '#ffffff'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#3b82f6';
              e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#d1d5db';
              e.target.style.boxShadow = 'none';
            }}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            style={{
              padding: '12px 20px',
              backgroundColor: (!inputValue.trim() || isLoading) ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: (!inputValue.trim() || isLoading) ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            {isLoading ? (
              <Loader size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIChat;