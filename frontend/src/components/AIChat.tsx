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
      if (response.success && response.result) {
        // Extract the AI response message
        aiContent = response.result.message || response.result.response?.message || 'AI processing completed successfully.';
        
        // Add some context about what the AI determined
        const decision = response.result.decision;
        const selection = response.result.selection;
        const plan = response.result.plan;
        
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
      } else {
        aiContent = response.error || 'Sorry, I encountered an error processing your request.';
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aiContent,
        sender: 'ai',
        timestamp: new Date()
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
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: message.sender === 'user' ? '#3b82f6' : '#f3f4f6',
                color: message.sender === 'user' ? 'white' : '#1f2937',
                fontSize: '14px',
                lineHeight: '1.5',
                wordWrap: 'break-word'
              }}>
                {message.content}
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