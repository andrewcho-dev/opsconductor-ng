"""
LLM-Powered Conversation Handler

This module provides a pure LLM-based conversation system that completely bypasses
hardcoded intent matching and template responses. All conversation analysis and
response generation is handled by the LLM engine.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    user_message: str
    ai_response: str
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class LLMConversation:
    """Represents an LLM-powered conversation"""
    id: str
    user_id: str
    turns: List[ConversationTurn]
    created_at: datetime
    updated_at: datetime
    context: Dict[str, Any]
    status: str = "active"  # active, completed, error

class LLMConversationHandler:
    """
    Pure LLM-powered conversation handler that uses the LLM for all analysis and responses.
    No hardcoded intents, no pattern matching, no templates - just pure AI conversation.
    """
    
    def __init__(self, llm_engine, asset_client=None):
        """Initialize with LLM engine and optional asset client"""
        self.llm_engine = llm_engine
        self.asset_client = asset_client
        self.conversations: Dict[str, LLMConversation] = {}
        
        # System prompt for OpsConductor AI
        self.system_prompt = """You are OpsConductor AI, an intelligent IT operations automation assistant with access to your organization's infrastructure data.

Your capabilities include:
- Access to the complete asset inventory with servers, IP addresses, operating systems, and configurations
- Creating automation workflows and scripts
- Troubleshooting technical issues
- Providing configuration guidance
- Managing deployments and maintenance tasks
- Security and compliance assistance
- Monitoring and alerting setup
- Database and network operations

IMPORTANT: When users ask about specific IP addresses, hostnames, or systems, you can look up that information in the asset database. You have access to:
- Server details by IP address
- Operating system information
- Service configurations
- Asset relationships and groupings

When users ask questions:
1. If they mention an IP address, hostname, or system - look it up in the asset database first
2. Provide specific, accurate information based on the actual infrastructure data
3. Ask clarifying questions only if you need additional context beyond what's in the asset database
4. Be direct and informative - you have access to real data, so use it

Always be helpful, professional, and technically accurate. Use the actual infrastructure data to provide precise answers."""

    async def process_message(self, user_message: str, user_id: str = "default", conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message using pure LLM analysis and response generation.
        
        Args:
            user_message: The user's input message
            user_id: User identifier
            conversation_id: Optional existing conversation ID
            
        Returns:
            Dict containing the AI response and conversation metadata
        """
        try:
            logger.info(f"Processing LLM message from user {user_id}: {user_message[:100]}...")
            
            # Get or create conversation
            if conversation_id and conversation_id in self.conversations:
                conversation = self.conversations[conversation_id]
                logger.info(f"Continuing existing conversation {conversation_id}")
            else:
                conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                conversation = LLMConversation(
                    id=conversation_id,
                    user_id=user_id,
                    turns=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    context={}
                )
                self.conversations[conversation_id] = conversation
                logger.info(f"Created new conversation {conversation_id}")
            
            # Build conversation context for LLM
            conversation_context = self._build_conversation_context(conversation, user_message)
            
            # Generate LLM response
            ai_response = await self._generate_llm_response(conversation_context)
            
            # Create conversation turn
            turn = ConversationTurn(
                user_message=user_message,
                ai_response=ai_response,
                timestamp=datetime.now(),
                context=conversation_context,
                metadata={
                    "method": "llm_powered",
                    "model": self.llm_engine.default_model,
                    "turn_number": len(conversation.turns) + 1
                }
            )
            
            # Add turn to conversation
            conversation.turns.append(turn)
            conversation.updated_at = datetime.now()
            
            # Extract any context updates from the LLM response
            await self._update_conversation_context(conversation, user_message, ai_response)
            
            logger.info(f"Generated LLM response for conversation {conversation_id}")
            
            return {
                "success": True,
                "response": ai_response,
                "conversation_id": conversation_id,
                "conversation_state": conversation.status,
                "turn_number": len(conversation.turns),
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "method": "pure_llm",
                    "timestamp": datetime.now().isoformat(),
                    "model": self.llm_engine.default_model
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing LLM message: {e}")
            return {
                "success": False,
                "response": f"I encountered an error processing your message: {str(e)}. Please try again.",
                "conversation_id": conversation_id if 'conversation_id' in locals() else None,
                "error": str(e),
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "method": "error_fallback",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _build_conversation_context(self, conversation: LLMConversation, current_message: str) -> Dict[str, Any]:
        """Build context for LLM including conversation history"""
        
        # Build conversation history
        history = []
        for turn in conversation.turns[-5:]:  # Last 5 turns for context
            history.append({
                "user": turn.user_message,
                "assistant": turn.ai_response,
                "timestamp": turn.timestamp.isoformat()
            })
        
        return {
            "conversation_id": conversation.id,
            "user_id": conversation.user_id,
            "current_message": current_message,
            "conversation_history": history,
            "conversation_context": conversation.context,
            "turn_number": len(conversation.turns) + 1,
            "created_at": conversation.created_at.isoformat(),
            "is_new_conversation": len(conversation.turns) == 0
        }
    
    async def _generate_llm_response(self, context: Dict[str, Any]) -> str:
        """Generate response using LLM with asset lookup capability"""
        
        try:
            # Check if the message contains IP addresses and look them up
            asset_info = await self._lookup_assets_in_message(context["current_message"])
            
            # Build the enhanced system prompt with asset information
            enhanced_system_prompt = self.system_prompt
            if asset_info:
                enhanced_system_prompt += f"\n\nCURRENT ASSET INFORMATION:\n{asset_info}"
            
            if context["is_new_conversation"]:
                # For new conversations, use the chat method with enhanced system prompt
                response_data = await self.llm_engine.chat(
                    message=context["current_message"],
                    system_prompt=enhanced_system_prompt
                )
            else:
                # Include conversation history in context
                history_text = ""
                for turn in context["conversation_history"]:
                    history_text += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
                
                conversation_context = f"Previous conversation:\n{history_text}"
                
                response_data = await self.llm_engine.chat(
                    message=context["current_message"],
                    context=conversation_context,
                    system_prompt=enhanced_system_prompt
                )
            
            return response_data.get("response", "I'm having trouble generating a response right now.").strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I'm having trouble generating a response right now. Could you please rephrase your request or try again?"
    
    async def _lookup_assets_in_message(self, message: str) -> str:
        """Look up asset information for any IP addresses mentioned in the message"""
        if not self.asset_client:
            return ""
        
        import re
        
        # Find IP addresses in the message
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip_addresses = re.findall(ip_pattern, message)
        
        if not ip_addresses:
            return ""
        
        asset_info_parts = []
        for ip in ip_addresses:
            try:
                asset = await self.asset_client.get_asset_by_ip(ip)
                if asset:
                    asset_info = f"IP {ip}:\n"
                    asset_info += f"  - Name: {asset.get('name', 'Unknown')}\n"
                    asset_info += f"  - Hostname: {asset.get('hostname', 'Unknown')}\n"
                    asset_info += f"  - Operating System: {asset.get('os_type', 'Unknown')}\n"
                    asset_info += f"  - OS Version: {asset.get('os_version', 'Unknown')}\n"
                    asset_info += f"  - Device Type: {asset.get('device_type', 'Unknown')}\n"
                    asset_info += f"  - Service Type: {asset.get('service_type', 'Unknown')}\n"
                    asset_info += f"  - Port: {asset.get('port', 'Unknown')}\n"
                    asset_info += f"  - Status: {'Active' if asset.get('is_active') else 'Inactive'}\n"
                    if asset.get('tags'):
                        asset_info += f"  - Tags: {', '.join(asset['tags'])}\n"
                    if asset.get('description'):
                        asset_info += f"  - Description: {asset['description']}\n"
                    asset_info_parts.append(asset_info)
                else:
                    asset_info_parts.append(f"IP {ip}: Not found in asset database")
            except Exception as e:
                logger.error(f"Error looking up asset for IP {ip}: {e}")
                asset_info_parts.append(f"IP {ip}: Error retrieving asset information")
        
        return "\n".join(asset_info_parts) if asset_info_parts else ""
    
    async def _update_conversation_context(self, conversation: LLMConversation, user_message: str, ai_response: str):
        """Update conversation context based on the interaction"""
        
        # Use LLM to extract any important context or state changes
        context_prompt = f"""Analyze this conversation turn and extract any important context, state changes, or information that should be remembered for future turns.

User message: {user_message}
AI response: {ai_response}

Current context: {json.dumps(conversation.context, indent=2)}

Return a JSON object with any context updates. If no updates are needed, return an empty object {{}}.
Focus on:
- Technical requirements or specifications mentioned
- System names, IPs, or infrastructure details
- Task progress or completion status
- User preferences or constraints
- Any ongoing workflows or processes

JSON response:"""
        
        try:
            # Use the generate method instead of generate_response
            response_data = await self.llm_engine.generate(context_prompt)
            context_response = response_data.get("generated_text", "")
            
            # Try to parse JSON response
            try:
                context_updates = json.loads(context_response.strip())
                if isinstance(context_updates, dict):
                    conversation.context.update(context_updates)
                    logger.info(f"Updated conversation context: {context_updates}")
            except json.JSONDecodeError:
                logger.warning(f"Could not parse context updates as JSON: {context_response}")
                
        except Exception as e:
            logger.error(f"Error updating conversation context: {e}")
    
    def get_conversation(self, conversation_id: str) -> Optional[LLMConversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str) -> List[LLMConversation]:
        """Get all conversations for a user"""
        return [conv for conv in self.conversations.values() if conv.user_id == user_id]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "status": conversation.status,
            "turn_count": len(conversation.turns),
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "context": conversation.context,
            "last_message": conversation.turns[-1].user_message if conversation.turns else None,
            "last_response": conversation.turns[-1].ai_response if conversation.turns else None
        }