import React, { useState, useRef, useEffect, useImperativeHandle } from 'react';
import { Send, Bot, User, Loader, AlertCircle, CheckCircle, Clock, Trash2, RefreshCw, Copy, Check } from 'lucide-react';
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
      if (data._routing) {
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
        status: data.execution_started ? 'pending' : undefined
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
        `}
      </style>

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
                <div key={message.id} className={`chat-bubble chat-bubble-${message.type}`}>
                  {message.type === 'ai' ? formatMessageContent(message.content, message.id) : message.content}
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