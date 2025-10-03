import React, { forwardRef, useImperativeHandle, useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import { aiApi } from '../services/api';

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
}

const AIChat = forwardRef<AIChatRef, AIChatProps>((props, ref) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history on mount
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
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
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

  useImperativeHandle(ref, () => ({
    clearChat: () => {
      setMessages([]);
      localStorage.removeItem('opsconductor_ai_chat_history');
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

    // Call the real AI Pipeline API
    try {
      const response = await aiApi.process(userMessage.content);
      
      let aiContent = '';
      let responseType = 'information';
      let executionId = null;
      let approvalData = null;
      
      if (response.success && response.result) {
        const result = response.result;
        responseType = result.response?.response_type || 'information';
        executionId = result.response?.execution_id || null;
        
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

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aiContent,
        sender: 'ai',
        timestamp: new Date(),
        responseType,
        executionId,
        approvalData
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('AI API Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I'm having trouble connecting to the AI system. Please check that the backend is running.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#ffffff',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f8f9fa',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <Bot size={20} style={{ color: '#6366f1' }} />
        <h3 style={{ 
          margin: 0, 
          fontSize: '16px', 
          fontWeight: '600',
          color: '#1f2937'
        }}>
          AI Assistant
        </h3>
      </div>

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
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
                maxWidth: '70%',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: message.sender === 'user' ? '#3b82f6' : '#f3f4f6',
                  color: message.sender === 'user' ? 'white' : '#1f2937',
                  fontSize: '14px',
                  lineHeight: '1.5',
                  wordWrap: 'break-word',
                  whiteSpace: 'pre-wrap'
                }}>
                  {message.content}
                </div>
                
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
        padding: '16px 20px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#ffffff'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
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
                fontSize: '14px',
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
    </div>
  );
});

AIChat.displayName = 'AIChat';

export default AIChat;