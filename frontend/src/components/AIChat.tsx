import React, { forwardRef, useImperativeHandle, useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import { aiApi } from '../services/api';
import MessageContent from './MessageContent';

export interface AIChatRef {
  clearChat: () => void;
}

interface AIChatProps {
  onFirstMessage?: (title: string) => void;
  activeChatId?: string | null;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  responseType?: string;
  executionId?: string;
  approvalData?: any;
  isLoading?: boolean;
  loadingStatus?: string;
  executionStatus?: string;
  targetHosts?: string[];  // Array of target hosts from execution plan
}

const AIChat = forwardRef<AIChatRef, AIChatProps>((props, ref) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Generate persistent session ID - ONE per chat TAB (tied to activeChatId)
  const [sessionId, setSessionId] = useState<string>(() => {
    // Each chat tab gets its own session ID
    const chatId = props.activeChatId || 'default';
    const storageKey = `opsconductor_session_${chatId}`;
    
    // Try to load existing session ID for this chat tab
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      return saved;
    }
    
    // Generate new session ID for this chat tab
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    localStorage.setItem(storageKey, newSessionId);
    return newSessionId;
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history when activeChatId changes
  useEffect(() => {
    const loadChatHistory = () => {
      try {
        const saved = localStorage.getItem('opsconductor_ai_chat_history');
        if (saved) {
          const history = JSON.parse(saved).map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
          setMessages(history);
        } else {
          // Clear messages if no history exists for this chat
          setMessages([]);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
        setMessages([]);
      }
    };
    loadChatHistory();
  }, [props.activeChatId]);

  // Save chat history when messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem('opsconductor_ai_chat_history', JSON.stringify(messages));
      } catch (error) {
        console.error('Failed to save chat history:', error);
      }
    }
  }, [messages]);

  // Update session ID when switching chat tabs
  useEffect(() => {
    const chatId = props.activeChatId || 'default';
    const storageKey = `opsconductor_session_${chatId}`;
    
    // Try to load existing session ID for this chat tab
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      setSessionId(saved);
    } else {
      // Generate new session ID for this new chat tab
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
      localStorage.setItem(storageKey, newSessionId);
      setSessionId(newSessionId);
    }
  }, [props.activeChatId]);

  useImperativeHandle(ref, () => ({
    clearChat: () => {
      setMessages([]);
      localStorage.removeItem('opsconductor_ai_chat_history');
      // Generate NEW session ID for this chat tab when clearing
      const chatId = props.activeChatId || 'default';
      const storageKey = `opsconductor_session_${chatId}`;
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
      localStorage.setItem(storageKey, newSessionId);
      setSessionId(newSessionId);
    }
  }));

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Call onFirstMessage if this is the first message
    if (messages.length === 0 && props.onFirstMessage) {
      props.onFirstMessage(userMessage.content.substring(0, 50) + (userMessage.content.length > 50 ? '...' : ''));
    }

    // Add loading message
    const loadingMessageId = (Date.now() + 1).toString();
    const loadingMessage: Message = {
      id: loadingMessageId,
      content: 'AI is thinking...',
      sender: 'ai',
      timestamp: new Date(),
      isLoading: true,
      loadingStatus: 'Processing your request...'
    };
    setMessages(prev => [...prev, loadingMessage]);

    // Call the real AI Pipeline API with progress callback and session ID
    try {
      const response = await aiApi.process(
        userMessage.content,
        {},
        (status: string) => {
          // Update loading message with progress
          setMessages(prev => prev.map(msg => 
            msg.id === loadingMessageId 
              ? { ...msg, loadingStatus: status }
              : msg
          ));
        },
        sessionId  // Pass the persistent session ID for this chat tab
      );
      
      let aiContent = '';
      let responseType = 'information';
      let executionId: string | null = null;
      let approvalData: any = null;
      let targetHosts: string[] = [];
      
      if (response.success && response.result) {
        const result = response.result;
        responseType = result.response?.response_type || 'information';
        executionId = result.execution_id || result.response?.execution_id || null;
        
        // Extract target hosts from execution plan
        if (result.intermediate_results?.stage_c?.plan?.steps) {
          const steps = result.intermediate_results.stage_c.plan.steps;
          const hosts: string[] = steps
            .map((step: any) => step.inputs?.target_host)
            .filter((host: any) => host) as string[];
          targetHosts = [...new Set(hosts)]; // Remove duplicates
        }
        
        // Handle approval requests specially
        if (responseType === 'approval_request') {
          approvalData = {
            message: result.response?.message || '',
            executionSummary: result.response?.execution_summary || {},
            approvalPoints: result.response?.approval_points || [],
            suggestedActions: result.response?.suggested_actions || []
          };
          aiContent = 'I need your approval to proceed with this action.';
        } else {
          // Extract the AI response message
          aiContent = result.message || result.response?.message || 'AI processing completed successfully.';
          
          // Add some context about what the AI determined
          const decision = result.decision;
          const selection = result.selection;
          const plan = result.plan;
          
          if (decision) {
            aiContent += `\n\n**Analysis:**\n`;
            aiContent += `• Intent: ${decision.intent?.category}/${decision.intent?.action}\n`;
            aiContent += `• Confidence: ${decision.confidence_level?.value} (${(decision.overall_confidence * 100).toFixed(1)}%)\n`;
            aiContent += `• Risk Level: ${decision.risk_level?.value}\n`;
          }
          
          if (selection && selection.selected_tools?.length > 0) {
            aiContent += `\n**Tools Selected:** ${selection.selected_tools.map((t: any) => t.tool_name).join(', ')}\n`;
          }
          
          if (plan && plan.plan?.steps?.length > 0) {
            aiContent += `\n**Execution Plan:** ${plan.plan.steps.length} steps planned\n`;
          }
        }
      } else {
        aiContent = response.error || 'Sorry, I encountered an error processing your request.';
      }

      // Replace loading message with actual response
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessageId
          ? {
              ...msg,
              content: aiContent,
              isLoading: false,
              loadingStatus: undefined,
              responseType,
              executionId,
              approvalData,
              targetHosts
            } as Message
          : msg
      ));

      // Start polling for execution status if we have an execution ID
      if (executionId) {
        pollExecutionStatus(loadingMessageId, executionId);
      }
    } catch (error) {
      console.error('AI API Error:', error);
      // Replace loading message with error
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessageId
          ? {
              ...msg,
              content: `Sorry, I'm having trouble connecting to the AI system. Please check that the backend is running.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
              isLoading: false,
              loadingStatus: undefined
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  // Poll execution status
  const pollExecutionStatus = async (messageId: string, executionId: string) => {
    const maxPolls = 60; // Poll for up to 5 minutes (60 * 5 seconds)
    let pollCount = 0;

    const poll = async () => {
      if (pollCount >= maxPolls) {
        console.log('Stopped polling execution status (max polls reached)');
        return;
      }

      const status = await aiApi.getExecutionStatus(executionId);
      if (status) {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId
            ? { ...msg, executionStatus: status.status }
            : msg
        ));

        // Continue polling if execution is still running
        if (status.status === 'running' || status.status === 'pending') {
          pollCount++;
          setTimeout(poll, 5000); // Poll every 5 seconds
        }
      }
    };

    // Start polling after 2 seconds
    setTimeout(poll, 2000);
  };

  const handleApproval = async (messageId: string, approved: boolean) => {
    const message = messages.find(m => m.id === messageId);
    if (!message || !message.executionId) return;

    try {
      // Call approval API
      const response = await fetch(`http://localhost:3005/pipeline/approve/${message.executionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved })
      });

      const result = await response.json();
      
      // Update the message to show approval status
      setMessages(prev => prev.map(m => {
        if (m.id === messageId) {
          return {
            ...m,
            content: approved 
              ? `✅ Approved and executing...\n\n${m.content}` 
              : `❌ Rejected\n\n${m.content}`,
            approvalData: null // Remove approval UI
          };
        }
        return m;
      }));

      // If approved, add execution result message
      if (approved && result.success) {
        const executionMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `Execution completed successfully!\n\nExecution ID: ${message.executionId}`,
          sender: 'ai',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, executionMessage]);
      }
    } catch (error) {
      console.error('Approval error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Failed to process approval: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  return (
    <>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes loadingDots {
          0%, 20% { opacity: 0.3; }
          50% { opacity: 1; }
          100% { opacity: 0.3; }
        }
        
        .loading-dots span {
          animation: loadingDots 1.4s infinite;
        }
        
        .loading-dots span:nth-child(1) {
          animation-delay: 0s;
        }
        
        .loading-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        .loading-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }
      `}</style>
      
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden'
      }}>
      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px 250px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: '#6b7280',
            fontSize: '14px'
          }}>
            <Bot size={48} style={{ color: '#d1d5db', marginBottom: '16px' }} />
            <p style={{ margin: '0 0 8px 0', fontWeight: '500' }}>
              Welcome to AI Chat
            </p>
            <p style={{ margin: 0 }}>
              Ask me anything about your infrastructure, automation, or operations.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                flexDirection: message.sender === 'user' ? 'row-reverse' : 'row'
              }}
            >
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: message.sender === 'user' ? '#3b82f6' : '#6366f1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {message.sender === 'user' ? (
                  <User size={16} style={{ color: 'white' }} />
                ) : (
                  <Bot size={16} style={{ color: 'white' }} />
                )}
              </div>
              <div style={{
                width: '85%',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {/* Target Hosts Badge */}
                {message.targetHosts && message.targetHosts.length > 0 && (
                  <div style={{
                    display: 'flex',
                    gap: '6px',
                    flexWrap: 'wrap',
                    marginBottom: '4px'
                  }}>
                    {message.targetHosts.map((host, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '4px 10px',
                          borderRadius: '6px',
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: '500',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        <span style={{ fontSize: '10px' }}>🖥️</span>
                        {host}
                      </div>
                    ))}
                  </div>
                )}
                
                <div style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: message.sender === 'user' ? '#3b82f6' : '#f3f4f6',
                  color: message.sender === 'user' ? 'white' : '#1f2937',
                  fontSize: '16px',
                  lineHeight: '1.8',
                  wordWrap: 'break-word',
                  boxSizing: 'border-box'
                }}>
                  <MessageContent 
                    content={message.content} 
                    isUser={message.sender === 'user'} 
                  />
                  
                  {/* Loading indicator */}
                  {message.isLoading && (
                    <div style={{ 
                      marginTop: '8px', 
                      display: 'flex', 
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '12px',
                      color: '#6b7280'
                    }}>
                      <div className="loading-dots">
                        <span>.</span><span>.</span><span>.</span>
                      </div>
                      <span>{message.loadingStatus}</span>
                    </div>
                  )}
                </div>
                
                {/* Execution Status Badge */}
                {message.executionStatus && (
                  <div style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    backgroundColor: 
                      message.executionStatus === 'completed' ? '#d1fae5' :
                      message.executionStatus === 'running' ? '#dbeafe' :
                      message.executionStatus === 'failed' ? '#fee2e2' :
                      '#f3f4f6',
                    color:
                      message.executionStatus === 'completed' ? '#065f46' :
                      message.executionStatus === 'running' ? '#1e40af' :
                      message.executionStatus === 'failed' ? '#991b1b' :
                      '#374151',
                    fontSize: '12px',
                    fontWeight: '500',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}>
                    {message.executionStatus === 'running' && (
                      <div className="spinner" style={{
                        width: '12px',
                        height: '12px',
                        border: '2px solid currentColor',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
                    )}
                    Execution: {message.executionStatus}
                  </div>
                )}
                
                {/* Approval UI */}
                {message.approvalData && (
                  <div style={{
                    padding: '16px',
                    borderRadius: '12px',
                    backgroundColor: '#fef3c7',
                    border: '1px solid #fbbf24',
                    fontSize: '13px'
                  }}>
                    <div style={{ fontWeight: '600', marginBottom: '12px', color: '#92400e' }}>
                      ⚠️ Approval Required
                    </div>
                    
                    {message.approvalData.executionSummary && (
                      <div style={{ marginBottom: '12px', color: '#78350f' }}>
                        <div><strong>Steps:</strong> {message.approvalData.executionSummary.total_steps}</div>
                        <div><strong>Duration:</strong> ~{message.approvalData.executionSummary.estimated_duration}s</div>
                        <div><strong>Risk:</strong> {message.approvalData.executionSummary.risk_level}</div>
                        <div><strong>Tools:</strong> {message.approvalData.executionSummary.tools_involved?.join(', ')}</div>
                      </div>
                    )}
                    
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                      <button
                        onClick={() => handleApproval(message.id, true)}
                        style={{
                          flex: 1,
                          padding: '8px 16px',
                          borderRadius: '6px',
                          border: 'none',
                          backgroundColor: '#10b981',
                          color: 'white',
                          fontSize: '13px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#059669'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#10b981'}
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => handleApproval(message.id, false)}
                        style={{
                          flex: 1,
                          padding: '8px 16px',
                          borderRadius: '6px',
                          border: 'none',
                          backgroundColor: '#ef4444',
                          color: 'white',
                          fontSize: '13px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
                      >
                        ✗ Reject
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#6366f1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={16} style={{ color: 'white' }} />
            </div>
            <div style={{
              padding: '12px 16px',
              borderRadius: '12px',
              backgroundColor: '#f3f4f6',
              color: '#6b7280',
              fontSize: '14px'
            }}>
              <div style={{
                display: 'flex',
                gap: '4px',
                alignItems: 'center'
              }}>
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: '#9ca3af',
                  animation: 'pulse 1.5s ease-in-out infinite'
                }} />
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: '#9ca3af',
                  animation: 'pulse 1.5s ease-in-out infinite 0.2s'
                }} />
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: '#9ca3af',
                  animation: 'pulse 1.5s ease-in-out infinite 0.4s'
                }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '16px 250px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#ffffff'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={isLoading}
              style={{
                width: '100%',
                minHeight: '44px',
                maxHeight: '120px',
                padding: '12px 16px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px',
                fontFamily: 'inherit',
                resize: 'none',
                outline: 'none',
                transition: 'border-color 0.2s',
                backgroundColor: isLoading ? '#f9fafb' : '#ffffff'
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
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: (!inputValue.trim() || isLoading) ? '#d1d5db' : '#3b82f6',
              color: 'white',
              cursor: (!inputValue.trim() || isLoading) ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.2s',
              flexShrink: 0
            }}
            onMouseEnter={(e) => {
              if (!(!inputValue.trim() || isLoading)) {
                e.currentTarget.style.backgroundColor = '#2563eb';
              }
            }}
            onMouseLeave={(e) => {
              if (!(!inputValue.trim() || isLoading)) {
                e.currentTarget.style.backgroundColor = '#3b82f6';
              }
            }}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 80%, 100% {
            opacity: 0.3;
          }
          40% {
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
});

AIChat.displayName = 'AIChat';

export default AIChat;