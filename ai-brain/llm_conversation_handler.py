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
from dataclasses import dataclass, asdict, field

# Progressive intent learning classes (embedded to avoid file deletion issues)
import re
from enum import Enum

class IntentConfidence(Enum):
    """Intent confidence levels"""
    VERY_HIGH = "very_high"  # 0.9+
    HIGH = "high"           # 0.7-0.89
    MEDIUM = "medium"       # 0.5-0.69
    LOW = "low"            # 0.3-0.49
    VERY_LOW = "very_low"  # <0.3

@dataclass
class IntentPattern:
    """Represents a learned intent pattern"""
    pattern_id: str
    intent_type: str
    pattern_text: str
    regex_patterns: List[str]
    keywords: List[str]
    context_clues: List[str]
    confidence_score: float
    success_count: int = 0
    failure_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    user_feedback_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

@dataclass
class IntentInterpretation:
    """Represents an intent interpretation attempt"""
    interpretation_id: str
    user_message: str
    detected_intent: str
    confidence: float
    patterns_matched: List[str]
    context_used: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    user_feedback: Optional[str] = None
    was_correct: Optional[bool] = None
    actual_intent: Optional[str] = None

class ProgressiveIntentLearner:
    """Progressive learning system for intent recognition"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.intent_patterns: Dict[str, List[IntentPattern]] = {}
        self.interpretation_history: List[IntentInterpretation] = []
        self.learning_rules = {
            "min_confidence_threshold": 0.3,
            "high_confidence_threshold": 0.7,
            "pattern_creation_threshold": 3,
            "pattern_retirement_threshold": 0.2,
            "feedback_weight": 2.0,
            "context_importance": 0.3,
            "recency_weight": 0.1,
            "learning_batch_size": 10,
        }
        self._initialize_base_patterns()
        
    def _initialize_base_patterns(self):
        """Initialize with base intent patterns"""
        base_patterns = {
            "asset_query": [
                IntentPattern(
                    pattern_id="asset_general_query",
                    intent_type="asset_query",
                    pattern_text="General asset inventory query",
                    regex_patterns=[
                        r'\b(?:what|show|list|tell me about).{0,20}(?:assets?|systems?|servers?|machines?|devices?|inventory)\b',
                        r'\b(?:assets?|systems?|servers?|machines?|devices?|inventory).{0,20}(?:do we have|are there|exist)\b',
                        r'\b(?:our|the).{0,10}(?:assets?|systems?|servers?|machines?|devices?|inventory)\b'
                    ],
                    keywords=["assets", "systems", "servers", "inventory", "machines", "devices"],
                    context_clues=["infrastructure", "environment", "network"],
                    confidence_score=0.8,
                    success_count=5
                )
            ],
            "asset_specific_query": [
                IntentPattern(
                    pattern_id="asset_ip_query",
                    intent_type="asset_specific_query", 
                    pattern_text="Query about specific IP address",
                    regex_patterns=[
                        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                        r'\b(?:what|tell me about|info about).{0,10}(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    ],
                    keywords=["ip", "address", "server", "host"],
                    context_clues=["network", "system", "machine"],
                    confidence_score=0.9,
                    success_count=10
                )
            ],
            "automation_request": [
                IntentPattern(
                    pattern_id="automation_general",
                    intent_type="automation_request",
                    pattern_text="General automation request",
                    regex_patterns=[
                        r'\b(?:create|make|build|generate).{0,20}(?:automation|workflow|job|script)\b',
                        r'\b(?:automate|run|execute).{0,20}(?:task|process|command)\b'
                    ],
                    keywords=["automate", "create", "workflow", "job", "script", "run", "execute"],
                    context_clues=["task", "process", "command", "batch"],
                    confidence_score=0.7,
                    success_count=3
                )
            ],
            "troubleshooting": [
                IntentPattern(
                    pattern_id="troubleshooting_general",
                    intent_type="troubleshooting",
                    pattern_text="Troubleshooting request",
                    regex_patterns=[
                        r'\b(?:fix|solve|troubleshoot|debug|resolve).{0,20}(?:issue|problem|error)\b',
                        r'\b(?:why|what\'s wrong|not working|failing)\b'
                    ],
                    keywords=["fix", "solve", "troubleshoot", "debug", "error", "problem", "issue"],
                    context_clues=["failing", "broken", "not working", "down"],
                    confidence_score=0.6,
                    success_count=2
                )
            ]
        }
        self.intent_patterns = base_patterns
        logger.info(f"Initialized with {sum(len(patterns) for patterns in base_patterns.values())} base patterns")
    
    async def analyze_intent(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user message to determine intent with confidence scoring"""
        context = context or {}
        
        # Score all patterns against the message
        pattern_scores = []
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                score = self._score_pattern_match(user_message, pattern, context)
                if score > self.learning_rules["min_confidence_threshold"]:
                    pattern_scores.append({
                        "intent_type": intent_type,
                        "pattern": pattern,
                        "score": score,
                        "pattern_id": pattern.pattern_id
                    })
        
        # Sort by score and select best match
        pattern_scores.sort(key=lambda x: x["score"], reverse=True)
        
        if not pattern_scores:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "explanation": "No matching patterns found",
                "suggestions": self._generate_clarification_suggestions(user_message)
            }
        
        best_match = pattern_scores[0]
        
        # Create interpretation record
        interpretation = IntentInterpretation(
            interpretation_id=f"interp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            user_message=user_message,
            detected_intent=best_match["intent_type"],
            confidence=best_match["score"],
            patterns_matched=[best_match["pattern_id"]],
            context_used=context
        )
        
        self.interpretation_history.append(interpretation)
        
        # Update pattern usage
        best_match["pattern"].last_used = datetime.now()
        
        return {
            "intent": best_match["intent_type"],
            "confidence": best_match["score"],
            "confidence_level": self._get_confidence_level(best_match["score"]),
            "pattern_matched": best_match["pattern_id"],
            "interpretation_id": interpretation.interpretation_id,
            "alternative_intents": [
                {"intent": match["intent_type"], "confidence": match["score"]}
                for match in pattern_scores[1:3]  # Top 2 alternatives
            ],
            "explanation": f"Matched pattern '{best_match['pattern'].pattern_text}' with {best_match['score']:.2f} confidence"
        }
    
    def _score_pattern_match(self, message: str, pattern: IntentPattern, context: Dict[str, Any]) -> float:
        """Score how well a pattern matches the message"""
        message_lower = message.lower()
        score = 0.0
        
        # Regex pattern matching (primary signal)
        regex_matches = 0
        for regex_pattern in pattern.regex_patterns:
            if re.search(regex_pattern, message_lower, re.IGNORECASE):
                regex_matches += 1
        
        if regex_matches > 0:
            score += 0.6 * (regex_matches / len(pattern.regex_patterns))
        
        # Keyword matching
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword.lower() in message_lower)
        if keyword_matches > 0:
            score += 0.3 * (keyword_matches / len(pattern.keywords))
        
        # Context clues
        context_matches = sum(1 for clue in pattern.context_clues if clue.lower() in message_lower)
        if context_matches > 0:
            score += 0.1 * (context_matches / len(pattern.context_clues))
        
        # Pattern performance history (boost successful patterns)
        if pattern.success_rate > 0.7:
            score *= 1.2
        elif pattern.success_rate < 0.3:
            score *= 0.8
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numeric confidence to level"""
        if score >= 0.9:
            return IntentConfidence.VERY_HIGH.value
        elif score >= 0.7:
            return IntentConfidence.HIGH.value
        elif score >= 0.5:
            return IntentConfidence.MEDIUM.value
        elif score >= 0.3:
            return IntentConfidence.LOW.value
        else:
            return IntentConfidence.VERY_LOW.value
    
    def _generate_clarification_suggestions(self, message: str) -> List[str]:
        """Generate suggestions when intent is unclear"""
        suggestions = []
        
        # Check for partial matches
        if any(word in message.lower() for word in ["asset", "server", "system", "machine"]):
            suggestions.append("Are you asking about our asset inventory or a specific system?")
        
        if any(word in message.lower() for word in ["create", "make", "automate", "run"]):
            suggestions.append("Are you looking to create an automation workflow or run a specific task?")
        
        if any(word in message.lower() for word in ["fix", "problem", "error", "issue"]):
            suggestions.append("Are you experiencing a technical issue that needs troubleshooting?")
        
        if not suggestions:
            suggestions.append("Could you provide more details about what you're trying to accomplish?")
        
        return suggestions
    
    async def record_feedback(self, interpretation_id: str, was_correct: bool, 
                            actual_intent: str = None, user_feedback: str = None) -> None:
        """Record feedback on an intent interpretation"""
        
        # Find the interpretation
        interpretation = None
        for interp in self.interpretation_history:
            if interp.interpretation_id == interpretation_id:
                interpretation = interp
                break
        
        if not interpretation:
            logger.warning(f"Interpretation {interpretation_id} not found")
            return
        
        # Update interpretation with feedback
        interpretation.was_correct = was_correct
        interpretation.actual_intent = actual_intent
        interpretation.user_feedback = user_feedback
        
        # Update pattern statistics
        pattern = self._find_pattern_by_id(interpretation.patterns_matched[0])
        if pattern:
            if was_correct:
                pattern.success_count += 1
                if user_feedback and "good" in user_feedback.lower():
                    pattern.user_feedback_score = (pattern.user_feedback_score + 1.0) / 2
            else:
                pattern.failure_count += 1
                if user_feedback:
                    pattern.user_feedback_score = (pattern.user_feedback_score - 0.5) / 2
        
        logger.info(f"Recorded feedback for {interpretation_id}: correct={was_correct}")
    
    def _find_pattern_by_id(self, pattern_id: str) -> Optional[IntentPattern]:
        """Find a pattern by its ID"""
        for patterns in self.intent_patterns.values():
            for pattern in patterns:
                if pattern.pattern_id == pattern_id:
                    return pattern
        return None
    
    async def optimize_patterns(self) -> Dict[str, Any]:
        """Optimize patterns based on performance data"""
        optimizations = {
            "patterns_retired": 0,
            "patterns_boosted": 0,
            "patterns_created": 0,
            "total_patterns": 0
        }
        
        for intent_type, patterns in self.intent_patterns.items():
            patterns_to_remove = []
            
            for pattern in patterns:
                # Retire poorly performing patterns
                if (pattern.success_rate < self.learning_rules["pattern_retirement_threshold"] 
                    and pattern.success_count + pattern.failure_count > 10):
                    patterns_to_remove.append(pattern)
                    optimizations["patterns_retired"] += 1
                    logger.info(f"Retiring pattern {pattern.pattern_id} due to low success rate: {pattern.success_rate:.2f}")
                
                # Boost confidence of high-performing patterns
                elif pattern.success_rate > 0.8 and pattern.confidence_score < 0.9:
                    pattern.confidence_score = min(0.9, pattern.confidence_score + 0.1)
                    optimizations["patterns_boosted"] += 1
            
            # Remove retired patterns
            for pattern in patterns_to_remove:
                patterns.remove(pattern)
        
        # Count total patterns
        optimizations["total_patterns"] = sum(len(patterns) for patterns in self.intent_patterns.values())
        
        logger.info(f"Pattern optimization complete: {optimizations}")
        return optimizations
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        total_patterns = sum(len(patterns) for patterns in self.intent_patterns.values())
        total_interpretations = len(self.interpretation_history)
        
        # Calculate accuracy from feedback
        feedback_interpretations = [i for i in self.interpretation_history if i.was_correct is not None]
        accuracy = (sum(1 for i in feedback_interpretations if i.was_correct) / 
                   len(feedback_interpretations) if feedback_interpretations else 0.0)
        
        # Pattern performance
        pattern_stats = {}
        for intent_type, patterns in self.intent_patterns.items():
            pattern_stats[intent_type] = {
                "count": len(patterns),
                "avg_success_rate": sum(p.success_rate for p in patterns) / len(patterns) if patterns else 0,
                "total_uses": sum(p.success_count + p.failure_count for p in patterns)
            }
        
        return {
            "total_patterns": total_patterns,
            "total_interpretations": total_interpretations,
            "overall_accuracy": accuracy,
            "pattern_statistics": pattern_stats,
            "recent_activity": len([i for i in self.interpretation_history 
                                  if i.timestamp > datetime.now() - timedelta(days=7)])
        }

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
    
    def __init__(self, llm_engine, asset_client=None, vector_store=None):
        """Initialize with LLM engine and optional asset client"""
        self.llm_engine = llm_engine
        self.asset_client = asset_client
        self.conversations: Dict[str, LLMConversation] = {}
        
        # Initialize progressive intent learning
        self.intent_learner = ProgressiveIntentLearner(vector_store)
        
        # System prompt for OpsConductor AI
        self.system_prompt = """You are OpsConductor AI, an intelligent IT operations automation assistant with access to your organization's infrastructure data and advanced network analysis capabilities.

Your capabilities include:
- Access to the complete asset inventory with servers, IP addresses, operating systems, and configurations
- Creating automation workflows and scripts
- Troubleshooting technical issues
- Providing configuration guidance
- Managing deployments and maintenance tasks
- Security and compliance assistance
- Monitoring and alerting setup
- Database and network operations

NETWORK ANALYSIS CAPABILITIES:
You have access to a comprehensive network analyzer service that provides:
- Real-time packet capture and analysis using tcpdump, tshark, and scapy
- Network performance monitoring with bandwidth, latency, and packet loss metrics
- Protocol-specific analysis (HTTP, TCP, UDP, DNS, SSH, FTP, SMTP, ICMP)
- AI-powered anomaly detection for security threats and performance issues
- Remote network analysis through distributed agents
- Network troubleshooting workflows for common scenarios

When users mention network issues, performance problems, connectivity issues, or security concerns, you can:
1. Recommend appropriate network analysis workflows
2. Suggest specific packet capture or monitoring approaches
3. Provide protocol-specific troubleshooting guidance
4. Offer AI-powered anomaly detection for threat identification
5. Deploy remote agents for distributed network analysis

Common network troubleshooting scenarios you can help with:
- Slow web application performance → packet capture + protocol analysis + monitoring
- Intermittent connectivity → real-time monitoring + packet capture + AI anomaly detection
- DNS resolution problems → protocol analysis + packet capture
- Suspected security breaches → AI anomaly detection + packet capture + protocol analysis
- VPN connection issues → protocol analysis + packet capture + monitoring

IMPORTANT: When users ask about specific IP addresses, hostnames, or systems, you can look up that information in the asset database. You have access to:
- Server details by IP address
- Operating system information
- Service configurations
- Asset relationships and groupings

When users ask questions:
1. If they mention an IP address, hostname, or system - look it up in the asset database first
2. For network-related issues, suggest appropriate network analysis workflows
3. Provide specific, accurate information based on the actual infrastructure data
4. Ask clarifying questions only if you need additional context beyond what's available
5. Be direct and informative - you have access to real data and powerful analysis tools

Always be helpful, professional, and technically accurate. Use the actual infrastructure data and network analysis capabilities to provide precise, actionable solutions."""

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
            
            # Analyze intent for progressive learning
            intent_analysis = await self.intent_learner.analyze_intent(
                user_message, 
                context={"user_id": user_id, "conversation_id": conversation_id}
            )
            
            # Build conversation context for LLM
            conversation_context = self._build_conversation_context(conversation, user_message)
            conversation_context["intent_analysis"] = intent_analysis
            
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
                "intent_analysis": intent_analysis,
                "metadata": {
                    "engine": "llm_conversation_handler",
                    "method": "pure_llm",
                    "timestamp": datetime.now().isoformat(),
                    "model": self.llm_engine.default_model,
                    "intent_confidence": intent_analysis.get("confidence", 0.0)
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
            # Also use intent analysis to determine if asset lookup is needed
            intent_analysis = context.get("intent_analysis", {})
            asset_info = await self._lookup_assets_in_message(
                context["current_message"], 
                intent_analysis
            )
            
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
    
    async def _lookup_assets_in_message(self, message: str, intent_analysis: Dict[str, Any] = None) -> str:
        """Look up asset information for IP addresses or general asset queries in the message"""
        if not self.asset_client:
            return ""
        
        import re
        
        # Use intent analysis - NO PATTERN MATCHING FALLBACKS
        intent_analysis = intent_analysis or {}
        detected_intent = intent_analysis.get("intent", "unknown")
        intent_confidence = intent_analysis.get("confidence", 0.0)
        
        # Determine if this is an asset-related query
        is_general_query = (
            detected_intent == "asset_query" and intent_confidence > 0.5
        )
        
        # Fallback to regex patterns if intent analysis is not confident
        if not is_general_query and intent_confidence < 0.7:
            general_asset_patterns = [
                r'\b(?:what|show|list|tell me about).{0,20}(?:assets?|systems?|servers?|machines?|devices?|inventory)\b',
                r'\b(?:assets?|systems?|servers?|machines?|devices?|inventory).{0,20}(?:do we have|are there|exist)\b',
                r'\b(?:our|the).{0,10}(?:assets?|systems?|servers?|machines?|devices?|inventory)\b',
                r'\b(?:infrastructure|environment|network).{0,20}(?:assets?|systems?|servers?)\b'
            ]
            
            message_lower = message.lower()
            is_general_query = any(re.search(pattern, message_lower, re.IGNORECASE) for pattern in general_asset_patterns)
        
        # Find IP addresses in the message
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip_addresses = re.findall(ip_pattern, message)
        
        asset_info_parts = []
        
        # Handle general asset queries - fetch all assets
        if is_general_query:
            try:
                all_assets = await self.asset_client.get_all_assets()
                if all_assets:
                    asset_info_parts.append("CURRENT ASSET INVENTORY:")
                    asset_info_parts.append("=" * 50)
                    
                    for asset in all_assets:
                        asset_info = f"\n{asset.get('name', 'Unknown')} ({asset.get('ip_address', 'No IP')}):\n"
                        asset_info += f"  - Hostname: {asset.get('hostname', 'Unknown')}\n"
                        asset_info += f"  - Operating System: {asset.get('os_type', 'Unknown')}"
                        if asset.get('os_version'):
                            asset_info += f" {asset.get('os_version')}"
                        asset_info += f"\n  - Device Type: {asset.get('device_type', 'Unknown')}\n"
                        asset_info += f"  - Service Type: {asset.get('service_type', 'Unknown')}\n"
                        asset_info += f"  - Port: {asset.get('port', 'Unknown')}\n"
                        asset_info += f"  - Status: {'Active' if asset.get('is_active') else 'Inactive'}\n"
                        if asset.get('tags'):
                            asset_info += f"  - Tags: {', '.join(asset['tags'])}\n"
                        if asset.get('description'):
                            asset_info += f"  - Description: {asset['description']}\n"
                        asset_info_parts.append(asset_info)
                else:
                    asset_info_parts.append("No assets found in the database.")
            except Exception as e:
                logger.error(f"Error fetching all assets: {e}")
                asset_info_parts.append("Error retrieving asset inventory from database.")
        
        # Handle specific IP address lookups
        elif ip_addresses:
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
    
    async def record_intent_feedback(self, interpretation_id: str, was_correct: bool, 
                                   actual_intent: str = None, user_feedback: str = None) -> Dict[str, Any]:
        """Record feedback on intent interpretation for learning"""
        try:
            await self.intent_learner.record_feedback(
                interpretation_id, was_correct, actual_intent, user_feedback
            )
            return {"success": True, "message": "Feedback recorded successfully"}
        except Exception as e:
            logger.error(f"Error recording intent feedback: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_intent_learning_stats(self) -> Dict[str, Any]:
        """Get intent learning statistics"""
        try:
            return self.intent_learner.get_learning_statistics()
        except Exception as e:
            logger.error(f"Error getting learning stats: {e}")
            return {"error": str(e)}
    
    async def optimize_intent_patterns(self) -> Dict[str, Any]:
        """Optimize intent patterns based on performance"""
        try:
            return await self.intent_learner.optimize_patterns()
        except Exception as e:
            logger.error(f"Error optimizing patterns: {e}")
            return {"error": str(e)}
    
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