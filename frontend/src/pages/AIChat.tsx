import React, { useState, useEffect, useRef } from 'react';
import { Target, Trash2, Plus, Edit2, Check, X, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import AIChat, { AIChatRef } from '../components/AIChat';
import { assetApi } from '../services/api';

interface ChatSession {
  id: string;
  title: string;
  preview: string;
  lastMessage: Date;
  messageCount: number;
}

const AIChatPage: React.FC = () => {
  const [stats, setStats] = useState({
    assets: 0
  });
  const aiChatRef = useRef<AIChatRef>(null);
  
  // Chat session management
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);
  


  // Save chat sessions to localStorage
  const saveChatSessions = (sessions: ChatSession[]) => {
    try {
      localStorage.setItem('opsconductor_chat_sessions', JSON.stringify(sessions));
      console.log('Chat sessions saved to localStorage:', sessions); // Debug log
    } catch (error) {
      console.error('Failed to save chat sessions:', error);
    }
  };

  // Load chat sessions from localStorage
  useEffect(() => {
    const loadChatSessions = () => {
      try {
        const saved = localStorage.getItem('opsconductor_chat_sessions');
        if (saved) {
          const sessions = JSON.parse(saved).map((session: any) => ({
            ...session,
            lastMessage: new Date(session.lastMessage)
          }));
          setChatSessions(sessions);
          console.log('Loaded chat sessions:', sessions); // Debug log
          
          // Set active chat to the most recent one
          if (sessions.length > 0) {
            const mostRecent = sessions.sort((a: ChatSession, b: ChatSession) => 
              b.lastMessage.getTime() - a.lastMessage.getTime()
            )[0];
            console.log('Setting active chat to:', mostRecent.id); // Debug log
            setActiveChatId(mostRecent.id);
          }
        }
      } catch (error) {
        console.error('Failed to load chat sessions:', error);
      }
    };

    loadChatSessions();
  }, []);

  // Debug logging
  useEffect(() => {
    console.log('Debug - activeChatId:', activeChatId, 'chatSessions.length:', chatSessions.length);
  }, [activeChatId, chatSessions]);

  // Create initial chat if none exist
  useEffect(() => {
    if (chatSessions.length === 0 && activeChatId === null) {
      // Check if there's existing chat history in localStorage
      const existingHistory = localStorage.getItem('opsconductor_ai_chat_history');
      let title = 'New Chat';
      let preview = 'Start a conversation...';
      let messageCount = 0;
      
      if (existingHistory) {
        try {
          const messages = JSON.parse(existingHistory);
          if (messages.length > 0) {
            // Find the first user message to generate title
            const firstUserMessage = messages.find((msg: any) => msg.type === 'user');
            if (firstUserMessage) {
              title = generateChatTitle(firstUserMessage.content);
              preview = firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
            }
            messageCount = messages.length;
          }
        } catch (error) {
          console.error('Failed to parse existing chat history:', error);
        }
      }
      
      const newChat: ChatSession = {
        id: `chat_${Date.now()}`,
        title,
        preview,
        lastMessage: new Date(),
        messageCount
      };
      
      setChatSessions([newChat]);
      setActiveChatId(newChat.id);
      saveChatSessions([newChat]);
    }
  }, [chatSessions.length, activeChatId]);

  // Handle clicking outside to save edit
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (editingChatId && editInputRef.current && !editInputRef.current.contains(event.target as Node)) {
        // Check if click is not on save/cancel buttons
        const target = event.target as Element;
        if (!target.closest('.chat-edit-buttons')) {
          saveEditingChat();
        }
      }
    };

    if (editingChatId) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [editingChatId, editingTitle]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Get basic stats from individual APIs
        const assetsRes = await assetApi.list(0, 1);
        
        const getTotal = (res: any) => {
          if (res?.meta?.total_items !== undefined) return res.meta.total_items;
          if (res?.data?.total !== undefined) return res.data.total;
          return res?.total ?? 0;
        };
        
        setStats({
          assets: getTotal(assetsRes)
        });
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      }
    };

    fetchStats();
  }, []);

  // Create a new chat session
  const createNewChat = () => {
    // Save current chat history before creating new chat
    if (activeChatId) {
      const currentHistory = localStorage.getItem('opsconductor_ai_chat_history');
      if (currentHistory) {
        const currentChatHistoryKey = `opsconductor_ai_chat_history_${activeChatId}`;
        localStorage.setItem(currentChatHistoryKey, currentHistory);
      }
    }
    
    const newChat: ChatSession = {
      id: `chat_${Date.now()}`,
      title: 'New Chat',
      preview: 'Start a conversation...',
      lastMessage: new Date(),
      messageCount: 0
    };
    
    const updatedSessions = [newChat, ...chatSessions];
    setChatSessions(updatedSessions);
    setActiveChatId(newChat.id);
    saveChatSessions(updatedSessions);
    
    // Clear the main chat history for the new chat
    localStorage.removeItem('opsconductor_ai_chat_history');
    
    // Clear the AIChat component
    if (aiChatRef.current) {
      aiChatRef.current.clearChat();
    }
  };

  // Switch to a different chat session
  const switchToChat = (chatId: string) => {
    if (chatId === activeChatId) return; // Don't switch to the same chat
    
    // Save current chat history before switching
    if (activeChatId) {
      const currentHistory = localStorage.getItem('opsconductor_ai_chat_history');
      if (currentHistory) {
        const currentChatHistoryKey = `opsconductor_ai_chat_history_${activeChatId}`;
        localStorage.setItem(currentChatHistoryKey, currentHistory);
      }
    }
    
    setActiveChatId(chatId);
    // Load the specific chat history for this session
    const chatHistoryKey = `opsconductor_ai_chat_history_${chatId}`;
    const existingHistory = localStorage.getItem(chatHistoryKey);
    
    if (existingHistory) {
      // Set the chat history for this specific session
      localStorage.setItem('opsconductor_ai_chat_history', existingHistory);
    } else {
      // Clear chat history if no history exists for this session
      localStorage.removeItem('opsconductor_ai_chat_history');
    }
    
    // Refresh the AIChat component to load the new chat
    if (aiChatRef.current) {
      aiChatRef.current.clearChat();
    }
  };

  // Update chat session when messages change
  const updateChatSession = (chatId: string, title?: string, preview?: string) => {
    setChatSessions(prev => {
      const updated = prev.map(session => {
        if (session.id === chatId) {
          return {
            ...session,
            title: title || session.title,
            preview: preview || session.preview,
            lastMessage: new Date(),
            messageCount: session.messageCount + 1
          };
        }
        return session;
      });
      saveChatSessions(updated);
      return updated;
    });
  };

  // Handle first message to set chat title
  const handleFirstMessage = (message: string) => {
    // Use setTimeout to defer the state update and avoid setState during render
    setTimeout(() => {
      if (activeChatId) {
        const currentSession = chatSessions.find(s => s.id === activeChatId);
        if (currentSession && currentSession.title === 'New Chat') {
          const newTitle = generateChatTitle(message);
          updateChatSession(activeChatId, newTitle, message);
        }
      }
    }, 0);
  };

  const handleClearChat = () => {
    // Clear the AIChat component
    if (aiChatRef.current) {
      aiChatRef.current.clearChat();
    }
    // Also clear the session-specific history
    if (activeChatId) {
      const chatHistoryKey = `opsconductor_ai_chat_history_${activeChatId}`;
      localStorage.removeItem(chatHistoryKey);
    }
  };

  // Delete the currently active conversation
  const deleteActiveConversation = () => {
    if (!activeChatId || chatSessions.length <= 1) return; // Don't delete if it's the only chat
    
    // Remove the chat session
    const updatedSessions = chatSessions.filter(session => session.id !== activeChatId);
    setChatSessions(updatedSessions);
    saveChatSessions(updatedSessions);
    
    // Remove the chat history
    const chatHistoryKey = `opsconductor_ai_chat_history_${activeChatId}`;
    localStorage.removeItem(chatHistoryKey);
    
    // Switch to the most recent remaining chat
    if (updatedSessions.length > 0) {
      const mostRecent = updatedSessions.sort((a, b) => 
        b.lastMessage.getTime() - a.lastMessage.getTime()
      )[0];
      switchToChat(mostRecent.id);
    } else {
      // Create a new chat if no chats remain
      createNewChat();
    }
  };

  // Save chat history for the current session
  const handleChatHistoryChange = () => {
    if (activeChatId) {
      const currentHistory = localStorage.getItem('opsconductor_ai_chat_history');
      if (currentHistory) {
        const chatHistoryKey = `opsconductor_ai_chat_history_${activeChatId}`;
        localStorage.setItem(chatHistoryKey, currentHistory);
      }
    }
  };

  const startEditingChat = (chatId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent switching to the chat
    setEditingChatId(chatId);
    setEditingTitle(currentTitle);
  };

  const saveEditingChat = () => {
    if (editingChatId && editingTitle.trim()) {
      const updatedSessions = chatSessions.map(session =>
        session.id === editingChatId
          ? { ...session, title: editingTitle.trim() }
          : session
      );
      setChatSessions(updatedSessions);
      saveChatSessions(updatedSessions);
      console.log('Chat name saved:', editingTitle.trim()); // Debug log
    }
    setEditingChatId(null);
    setEditingTitle('');
  };

  const cancelEditingChat = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleEditKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveEditingChat();
    } else if (e.key === 'Escape') {
      cancelEditingChat();
    }
  };

  // Generate chat title from first message (first sentence)
  const generateChatTitle = (firstMessage: string): string => {
    // Find the first sentence (ending with . ! or ?)
    const sentenceMatch = firstMessage.match(/^[^.!?]*[.!?]/);
    if (sentenceMatch) {
      const sentence = sentenceMatch[0].trim();
      // If sentence is too long, truncate to ~40 characters
      if (sentence.length > 40) {
        return sentence.substring(0, 37) + '...';
      }
      return sentence;
    }
    
    // If no sentence ending found, take first ~40 characters
    if (firstMessage.length > 40) {
      return firstMessage.substring(0, 37) + '...';
    }
    
    return firstMessage || 'New Chat';
  };

  return (
    <div className="dense-dashboard">
      <style>
        {`
          .chat-layout {
            display: flex;
            gap: 12px;
            height: calc(100vh - 110px);
          }
          .chat-sidebar {
            width: 20%;
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
          }
          .chat-main {
            flex: 1;
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 110px);
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .btn-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            border-radius: 4px;
            background: transparent;
            color: var(--neutral-600);
            cursor: pointer;
            transition: all 0.15s ease;
          }
          .btn-icon:hover {
            background: var(--neutral-200);
            color: var(--neutral-800);
          }
          .btn-icon:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .btn-icon.btn-danger:not(:disabled):hover {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }
          .debug-toggle-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border: none;
            border-radius: 4px;
            background: transparent;
            color: var(--neutral-500);
            cursor: pointer;
            transition: all 0.15s ease;
          }
          .debug-toggle-icon:hover {
            background: var(--neutral-100);
            color: var(--neutral-700);
          }
          .debug-toggle-icon.active {
            background: var(--warning-orange-light);
            color: var(--warning-orange);
          }
          .debug-toggle-icon.active:hover {
            background: var(--warning-orange);
            color: white;
          }
          .chat-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
          }
          .chat-list-item {
            padding: 6px 8px;
            margin-bottom: 2px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
            border: 1px solid transparent;
          }
          .chat-list-item:hover {
            background: var(--neutral-100);
          }
          .chat-list-item.active {
            background: var(--primary-blue-light);
            border-color: var(--primary-blue);
            color: var(--primary-blue);
          }
          .chat-list-item-title {
            font-size: 16px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
            flex: 1;
          }
          .chat-list-item-content {
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
          }
          .chat-edit-input {
            flex: 1;
            background: white;
            border: 1px solid var(--primary-blue);
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 14px;
            font-weight: 500;
            outline: none;
          }
          .chat-edit-buttons {
            display: flex;
            gap: 4px;
          }
          .chat-edit-btn {
            background: none;
            border: none;
            padding: 2px;
            cursor: pointer;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.15s ease;
          }
          .chat-edit-btn:hover {
            background: var(--neutral-200);
          }
          .chat-edit-btn.save {
            color: var(--success-green);
          }
          .chat-edit-btn.cancel {
            color: var(--danger-red);
          }
          .chat-item-edit-icon {
            opacity: 0;
            transition: opacity 0.15s ease;
            background: none;
            border: none;
            padding: 4px;
            cursor: pointer;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--neutral-500);
          }
          .chat-list-item:hover .chat-item-edit-icon {
            opacity: 1;
          }
          .chat-item-edit-icon:hover {
            background: var(--neutral-200);
            color: var(--neutral-700);
          }
          .new-chat-button {
            margin: 8px;
            padding: 8px 12px;
            background: var(--primary-blue);
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
          }
          .new-chat-button:hover {
            background: var(--primary-blue-dark);
          }
        `}
      </style>
      
      {/* Dashboard Header - matching Assets page template */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>AI Assistant</h1>
        </div>
        <div className="header-stats">
          <button
            onClick={deleteActiveConversation}
            className="btn-icon btn-danger"
            title="Delete current conversation"
            disabled={!activeChatId || chatSessions.length <= 1}
          >
            <Trash2 size={18} />
          </button>
          <Link to="/assets" className="stat-pill">
            <Target size={14} />
            <span>{stats.assets} Assets</span>
          </Link>
        </div>
      </div>

      {/* Chat Layout with Sidebar */}
      <div className="chat-layout">
        {/* Chat Sessions Sidebar */}
        <div className="chat-sidebar">
          <div className="section-header">
            <span>Chats</span>
            <button
              onClick={createNewChat}
              className="btn-icon"
              title="New chat"
            >
              <Plus size={12} />
            </button>
          </div>
          <div className="chat-list">
            {chatSessions.map((session) => (
              <div
                key={session.id}
                className={`chat-list-item ${session.id === activeChatId ? 'active' : ''}`}
                onClick={() => editingChatId !== session.id && switchToChat(session.id)}
                title={editingChatId === session.id ? undefined : session.title} // Show full title on hover
              >
                <div className="chat-list-item-content">
                  {editingChatId === session.id ? (
                    <>
                      <input
                        ref={editInputRef}
                        type="text"
                        className="chat-edit-input"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={handleEditKeyPress}
                        autoFocus
                      />
                      <div className="chat-edit-buttons">
                        <button
                          className="chat-edit-btn save"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={saveEditingChat}
                          title="Save"
                        >
                          <Check size={12} />
                        </button>
                        <button
                          className="chat-edit-btn cancel"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={cancelEditingChat}
                          title="Cancel"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="chat-list-item-title">{session.title}</div>
                      <button
                        className="chat-item-edit-icon"
                        onClick={(e) => startEditingChat(session.id, session.title, e)}
                        title="Edit chat name"
                      >
                        <Edit2 size={12} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="chat-main">
          <AIChat 
            ref={aiChatRef} 
            onFirstMessage={handleFirstMessage}
            activeChatId={activeChatId}
          />
        </div>
      </div>
    </div>
  );
};

export default AIChatPage;