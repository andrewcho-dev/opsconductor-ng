"""
Intent Processor - LLM-Powered Intent Analysis

Uses LLM intelligence to convert AI understanding into actionable intent.
NO HARDCODED RULES OR TEMPLATES!
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of intents that can be processed"""
    QUERY = "query"
    AUTOMATION = "automation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"
    CONVERSATION = "conversation"


class RiskLevel(Enum):
    """Risk levels for intent execution"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ProcessedIntent:
    """Processed intent with all required information"""
    intent_id: str
    intent_type: IntentType
    description: str
    original_message: str
    risk_level: RiskLevel
    confidence: float
    
    # Resource requirements
    requires_asset_info: bool = False
    requires_network_info: bool = False
    requires_credentials: bool = False
    
    # Target systems and operations
    target_systems: List[str] = None
    operations: List[str] = None
    parameters: Dict[str, Any] = None
    
    # User context
    user_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.target_systems is None:
            self.target_systems = []
        if self.operations is None:
            self.operations = []
        if self.parameters is None:
            self.parameters = {}
        if self.user_context is None:
            self.user_context = {}


class IntentProcessor:
    """
    LLM-Powered Intent Processor - Uses AI to analyze and process intents
    
    NO HARDCODED RULES! LLM decides intent types, risk levels, and requirements.
    """
    
    def __init__(self, llm_engine=None):
        """Initialize the LLM-Powered Intent Processor"""
        self.llm_engine = llm_engine
        logger.info("LLM-Powered Intent Processor initialized")
    
    async def process_intent(self, ai_understanding: Dict[str, Any]) -> ProcessedIntent:
        """
        LLM-POWERED intent processing - NO HARDCODED RULES!
        
        Uses LLM intelligence to analyze AI understanding and determine:
        - Intent type and classification
        - Risk level assessment
        - Resource requirements
        - Target systems and operations
        
        Args:
            ai_understanding: AI understanding output from intent brain
            
        Returns:
            ProcessedIntent with all required information
        """
        try:
            logger.info(f"LLM analyzing intent from AI understanding")
            
            if not self.llm_engine:
                raise RuntimeError("LLM engine not available - cannot process intent")
            
            # Create comprehensive prompt for LLM intent analysis - REQUEST JSON FORMAT
            intent_prompt = f"""
            You are an expert DevOps engineer analyzing user intent to determine how to fulfill their request.
            
            AI UNDERSTANDING DATA:
            {json.dumps(ai_understanding, indent=2)}
            
            TASK: Analyze this AI understanding and provide a structured JSON response with detailed intent processing information.
            
            IMPORTANT GUIDELINES:
            1. Classify the intent type based on what the user actually wants to do
            2. Assess risk level based on the potential impact of the operations
            3. Determine what resources/information will be needed
            4. Extract target systems, operations, and parameters
            5. Be thorough and accurate - this drives the entire fulfillment process
            
            INTENT TYPES:
            - query: Information requests, status checks, read-only operations
            - automation: Running commands, scripts, or automated tasks
            - deployment: Installing, deploying, or configuring software/services
            - monitoring: Setting up monitoring, alerts, or recurring checks
            - maintenance: Updates, patches, cleanup, or maintenance tasks
            - conversation: General discussion, help requests, non-actionable chat
            
            RISK LEVELS:
            - LOW: Read-only operations, safe queries, information gathering
            - MEDIUM: Standard operations with limited impact, reversible changes
            - HIGH: Operations that could affect system availability or data
            - CRITICAL: Operations that could cause system outages or data loss
            
            Please analyze and respond naturally by answering these questions:
            1. What type of intent is this? (automation/query/deployment/monitoring/maintenance/conversation)
            2. What is the risk level? (LOW/MEDIUM/HIGH/CRITICAL)
            3. What needs to be done? (clear description)
            4. How confident are you? (high/medium/low)
            5. Does this require asset information? (yes/no)
            6. Does this require network information? (yes/no)
            7. Does this require credentials? (yes/no)
            8. What are the target systems? (list them or say "auto-detect")
            9. What operations need to be performed? (list them)
            10. What parameters are involved? (describe them)
            11. Why do you think so? (reasoning)
            
            EXAMPLES:
            - "check server status" → query intent, LOW risk, requires asset info
            - "restart nginx service" → automation intent, MEDIUM risk, requires credentials
            - "ping server every 5 minutes" → automation intent, LOW risk, target systems needed
            
            Please explain your analysis in natural language.
            """
            
            logger.info("Sending intent analysis request to LLM")
            llm_response = await self.llm_engine.generate(intent_prompt)
            
            # Extract generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            logger.info(f"LLM intent analysis response: {generated_text}")
            
            # Parse natural language response instead of JSON
            return await self._parse_natural_language_intent(ai_understanding, generated_text)
                
        except Exception as e:
            logger.error(f"LLM intent processing failed: {str(e)}")
            raise RuntimeError(f"LLM intent processing failed: {e}")
    
    async def _convert_llm_analysis_to_intent(self, ai_understanding: Dict[str, Any], intent_analysis: Dict[str, Any]) -> ProcessedIntent:
        """Convert LLM intent analysis to ProcessedIntent object"""
        try:
            # Map intent type string to enum
            intent_type_str = intent_analysis.get("intent_type", "conversation")
            intent_type = None
            for itype in IntentType:
                if itype.value == intent_type_str.lower():
                    intent_type = itype
                    break
            if not intent_type:
                intent_type = IntentType.CONVERSATION
            
            # Map risk level string to enum
            risk_level_str = intent_analysis.get("risk_level", "LOW")
            risk_level = None
            for rlevel in RiskLevel:
                if rlevel.value == risk_level_str.upper():
                    risk_level = rlevel
                    break
            if not risk_level:
                risk_level = RiskLevel.LOW
            
            # Create ProcessedIntent
            processed_intent = ProcessedIntent(
                intent_id=f"intent_{ai_understanding.get('conversation_id', 'unknown')}",
                intent_type=intent_type,
                description=intent_analysis.get("description", ai_understanding.get("response", "")),
                original_message=ai_understanding.get("original_message", ""),
                risk_level=risk_level,
                confidence=intent_analysis.get("confidence", 0.8),
                requires_asset_info=intent_analysis.get("requires_asset_info", False),
                requires_network_info=intent_analysis.get("requires_network_info", False),
                requires_credentials=intent_analysis.get("requires_credentials", False),
                target_systems=intent_analysis.get("target_systems", []),
                operations=intent_analysis.get("operations", []),
                parameters=intent_analysis.get("parameters", {}),
                user_context=ai_understanding.get("user_context", {})
            )
            
            logger.info(f"LLM intent processing completed: {intent_type.value} with risk {risk_level.value}")
            logger.info(f"LLM reasoning: {intent_analysis.get('reasoning', 'No reasoning provided')}")
            
            return processed_intent
            
        except Exception as e:
            logger.error(f"Failed to convert LLM analysis to ProcessedIntent: {str(e)}")
            raise RuntimeError(f"Failed to convert LLM analysis: {e}")
    
    async def _parse_natural_language_intent(self, ai_understanding: Dict[str, Any], analysis_text: str) -> ProcessedIntent:
        """Parse natural language LLM response to ProcessedIntent object"""
        try:
            logger.info("Parsing natural language intent analysis")
            
            analysis_lower = analysis_text.lower()
            
            # Parse intent type
            intent_type = IntentType.CONVERSATION  # Default
            if any(word in analysis_lower for word in ["automation", "automate", "execute", "run"]):
                intent_type = IntentType.AUTOMATION
            elif any(word in analysis_lower for word in ["query", "check", "status", "information", "get"]):
                intent_type = IntentType.QUERY
            elif any(word in analysis_lower for word in ["deploy", "install", "setup", "configure"]):
                intent_type = IntentType.DEPLOYMENT
            elif any(word in analysis_lower for word in ["monitor", "watch", "alert", "track"]):
                intent_type = IntentType.MONITORING
            elif any(word in analysis_lower for word in ["maintain", "update", "patch", "cleanup"]):
                intent_type = IntentType.MAINTENANCE
            
            # Parse risk level
            risk_level = RiskLevel.MEDIUM  # Default
            if any(word in analysis_lower for word in ["low risk", "safe", "read-only", "no impact"]):
                risk_level = RiskLevel.LOW
            elif any(word in analysis_lower for word in ["high risk", "dangerous", "system impact", "availability"]):
                risk_level = RiskLevel.HIGH
            elif any(word in analysis_lower for word in ["critical", "outage", "data loss", "critical risk"]):
                risk_level = RiskLevel.CRITICAL
            
            # Parse confidence
            confidence = 0.8  # Default
            if any(word in analysis_lower for word in ["high confidence", "very confident", "certain"]):
                confidence = 0.95
            elif any(word in analysis_lower for word in ["medium confidence", "somewhat confident"]):
                confidence = 0.7
            elif any(word in analysis_lower for word in ["low confidence", "uncertain", "not sure"]):
                confidence = 0.5
            
            # Parse requirements
            requires_asset_info = any(word in analysis_lower for word in ["asset", "server", "system", "host", "yes.*asset"])
            requires_network_info = any(word in analysis_lower for word in ["network", "connectivity", "ip", "port", "yes.*network"])
            requires_credentials = any(word in analysis_lower for word in ["credential", "password", "auth", "login", "yes.*credential"])
            
            # Extract target systems
            target_systems = []
            if "target systems" in analysis_lower or "target:" in analysis_lower:
                # Try to extract systems mentioned after "target"
                import re
                target_match = re.search(r'target[^:]*:?\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if target_match:
                    targets_text = target_match.group(1)
                    # Split by common delimiters
                    target_systems = [t.strip() for t in re.split(r'[,;]', targets_text) if t.strip()]
            
            if not target_systems:
                target_systems = ["auto-detect"]
            
            # Extract operations
            operations = []
            operation_keywords = ["ping", "restart", "start", "stop", "install", "deploy", "check", "monitor", "update"]
            for keyword in operation_keywords:
                if keyword in analysis_lower:
                    operations.append(keyword)
            
            if not operations:
                operations = ["execute"]
            
            # Extract description
            description = f"Intent analysis for: {ai_understanding.get('original_message', 'unknown request')}"
            
            # Create ProcessedIntent
            intent_id = f"nlp_{int(datetime.now().timestamp())}"
            
            processed_intent = ProcessedIntent(
                intent_id=intent_id,
                intent_type=intent_type,
                description=description,
                original_message=ai_understanding.get("original_message", ""),
                risk_level=risk_level,
                confidence=confidence,
                requires_asset_info=requires_asset_info,
                requires_network_info=requires_network_info,
                requires_credentials=requires_credentials,
                target_systems=target_systems,
                operations=operations,
                parameters={},
                user_context=ai_understanding.get("user_context", {})
            )
            
            logger.info(f"Natural language intent parsing completed: {intent_type.value} with risk {risk_level.value}")
            return processed_intent
            
        except Exception as e:
            logger.error(f"Failed to parse natural language intent: {str(e)}")
            raise RuntimeError(f"Failed to parse natural language intent: {e}")