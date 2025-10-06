"""
Conversation History Manager

Stores and retrieves conversation history per session_id to enable
multi-turn conversations where the AI can reference previous messages.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    

class ConversationHistoryManager:
    """
    Manages conversation history for multi-turn AI conversations.
    
    Features:
    - Stores conversation history per session_id
    - Limits history to prevent token overflow
    - Provides formatted history for LLM context injection
    """
    
    def __init__(self, max_messages_per_session: int = 20):
        """
        Initialize conversation history manager.
        
        Args:
            max_messages_per_session: Maximum number of messages to keep per session
                                     (prevents token overflow in LLM context)
        """
        self.max_messages = max_messages_per_session
        # Store: session_id -> List[ConversationMessage]
        self._conversations: Dict[str, List[ConversationMessage]] = defaultdict(list)
        logger.info(f"ConversationHistoryManager initialized (max {max_messages_per_session} messages per session)")
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Unique session identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        if not session_id:
            logger.warning("Cannot add message: session_id is empty")
            return
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        self._conversations[session_id].append(message)
        
        # Trim history if it exceeds max_messages (keep most recent)
        if len(self._conversations[session_id]) > self.max_messages:
            removed_count = len(self._conversations[session_id]) - self.max_messages
            self._conversations[session_id] = self._conversations[session_id][-self.max_messages:]
            logger.debug(f"Trimmed {removed_count} old messages from session {session_id}")
        
        logger.debug(f"Added {role} message to session {session_id} (total: {len(self._conversations[session_id])} messages)")
    
    def get_history(self, session_id: str, max_messages: Optional[int] = None) -> List[ConversationMessage]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            max_messages: Optional limit on number of messages to return (most recent)
        
        Returns:
            List of ConversationMessage objects (oldest to newest)
        """
        if not session_id:
            return []
        
        history = self._conversations.get(session_id, [])
        
        if max_messages and len(history) > max_messages:
            return history[-max_messages:]
        
        return history
    
    def get_formatted_history(self, session_id: str, max_messages: Optional[int] = None) -> str:
        """
        Get formatted conversation history for LLM context injection.
        
        Args:
            session_id: Unique session identifier
            max_messages: Optional limit on number of messages to return
        
        Returns:
            Formatted string with conversation history
        """
        history = self.get_history(session_id, max_messages)
        
        if not history:
            return ""
        
        formatted_lines = ["## Previous Conversation History:"]
        formatted_lines.append("")
        
        for msg in history:
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted_lines.append(f"**{role_label}:** {msg.content}")
            formatted_lines.append("")
        
        formatted_lines.append("---")
        formatted_lines.append("")
        
        return "\n".join(formatted_lines)
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self._conversations:
            message_count = len(self._conversations[session_id])
            del self._conversations[session_id]
            logger.info(f"Cleared {message_count} messages from session {session_id}")
    
    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._conversations)
    
    def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        return len(self._conversations.get(session_id, []))
    
    def get_all_sessions(self) -> List[str]:
        """Get list of all active session IDs."""
        return list(self._conversations.keys())


# Global conversation history manager instance
_conversation_manager: Optional[ConversationHistoryManager] = None


def get_conversation_manager() -> ConversationHistoryManager:
    """Get or create the global conversation history manager."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationHistoryManager(max_messages_per_session=20)
    return _conversation_manager