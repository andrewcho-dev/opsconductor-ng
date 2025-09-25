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
            
            # Create comprehensive prompt for LLM intent analysis
            intent_prompt = f"""
            You are an expert DevOps engineer analyzing user intent to determine how to fulfill their request.
            
            AI UNDERSTANDING DATA:
            {json.dumps(ai_understanding, indent=2)}
            
            TASK: Analyze this AI understanding and determine the detailed intent processing information.
            
            IMPORTANT GUIDELINES:
            1. Classify the intent type based on what the user actually wants to do
            2. Assess risk level based on the potential impact of the operations
            3. Determine what resources/information will be needed
            4. Extract target systems, operations, and parameters
            5. Be thorough and accurate - this drives the entire fulfillment process
            
            INTENT TYPES:
            - QUERY: Information requests, status checks, read-only operations
            - AUTOMATION: Running commands, scripts, or automated tasks
            - DEPLOYMENT: Installing, deploying, or configuring software/services
            - MONITORING: Setting up monitoring, alerts, or recurring checks
            - MAINTENANCE: Updates, patches, cleanup, or maintenance tasks
            - CONVERSATION: General discussion, help requests, non-actionable chat
            
            RISK LEVELS:
            - LOW: Read-only operations, safe queries, information gathering
            - MEDIUM: Standard operations with limited impact, reversible changes
            - HIGH: Operations that could affect system availability or data
            - CRITICAL: Operations that could cause system outages or data loss
            
            RESPOND WITH JSON ONLY:
            {{
                "intent_type": "query|automation|deployment|monitoring|maintenance|conversation",
                "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "confidence": 0.0-1.0,
                "description": "clear description of what the user wants to accomplish",
                "requires_asset_info": true/false,
                "requires_network_info": true/false,
                "requires_credentials": true/false,
                "target_systems": ["system1", "system2"],
                "operations": ["operation1", "operation2"],
                "parameters": {{"key": "value"}},
                "reasoning": "detailed explanation of the analysis and decisions"
            }}
            
            EXAMPLES:
            - "check server status" → QUERY, LOW risk, requires_asset_info=true
            - "restart nginx service" → AUTOMATION, MEDIUM risk, requires_credentials=true
            - "deploy new application" → DEPLOYMENT, HIGH risk, requires all info
            - "ping server every 5 minutes" → MONITORING, LOW risk, requires_asset_info=true
            - "update all packages" → MAINTENANCE, HIGH risk, requires_credentials=true
            """
            
            logger.info("Sending intent analysis request to LLM")
            llm_response = await self.llm_engine.generate(intent_prompt)
            
            # Extract generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            logger.info(f"LLM intent analysis response: {generated_text}")
            
            # Clean and parse JSON response
            try:
                # Remove any markdown code blocks
                if "```json" in generated_text:
                    generated_text = generated_text.split("```json")[1].split("```")[0]
                elif "```" in generated_text:
                    generated_text = generated_text.split("```")[1].split("```")[0]
                
                intent_analysis = json.loads(generated_text.strip())
                logger.info(f"Parsed LLM intent analysis: {intent_analysis}")
                
                # Convert LLM response to ProcessedIntent
                return await self._convert_llm_analysis_to_intent(ai_understanding, intent_analysis)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM intent analysis as JSON: {e}")
                logger.error(f"Raw LLM Response: {generated_text}")
                raise RuntimeError(f"LLM returned invalid JSON for intent analysis: {e}")
                
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